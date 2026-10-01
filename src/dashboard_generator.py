"""
Premier League Live Dashboard Generator
- Fills templates/dashboard.html with a small embedded shell: gameweek index, the live gameweek's
  fixtures + crowd picks, and the Premier League snapshot (table, AI predictions, deadline).
- Writes the heavy data to data/site/*.json, which the page fetches on demand:
  * leaderboard.json      season standings + rank history, rank movement and gameweek wins
  * gw_N.json             fixtures, crowd picks and per-predictor summaries for one gameweek
  * gw_N_details.json     raw comments, edit history and fixture breakdowns (loaded by the inspector)
"""
import hashlib
import html
import json
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.integrity import detect_integrity_flags

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(ROOT, "templates", "dashboard.html")
COMMON_JS_PATH = os.path.join(ROOT, "assets", "common.js")
ADMIN_PATH = os.path.join(ROOT, "admin.html")


def asset_version(path: str) -> str:
    """Short content hash used as a cache-busting ?v= value."""
    with open(path, "rb") as f:
        return hashlib.sha1(f.read().replace(b"\r\n", b"\n")).hexdigest()[:10]


def stamp_admin_common_js(version: str):
    """Keeps admin.html's assets/common.js?v= in step with the shared file (admin.html is static, not templated)."""
    if not os.path.exists(ADMIN_PATH):
        return
    with open(ADMIN_PATH, encoding="utf-8", newline="") as f:
        text = f.read()
    updated = re.sub(r"assets/common\.js\?v=[\w-]+", f"assets/common.js?v={version}", text)
    if updated != text:
        with open(ADMIN_PATH, "w", encoding="utf-8", newline="") as f:
            f.write(updated)


SUMMARY_FIELDS = ("comment_id", "author", "status", "submission_gmt", "matches_found", "exact_scores", "outcome_scores", "total_points")
DETAIL_FIELDS = ("raw_text", "is_edited", "updated_gmt", "edit_delta_str", "lateness_str", "timing_analysis",
                 "has_recorded_diff", "diff_html", "revisions", "fixtures")


def to_script_json(value: Any) -> str:
    """JSON that is safe to embed inside a <script> element."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def valid_entries(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """First Valid* record per author: the same rule the scoring engine uses to feed the season leaderboard."""
    entries: Dict[str, Dict[str, Any]] = {}
    for r in records:
        if str(r.get("status", "")).startswith("Valid") and r["author"] not in entries:
            entries[r["author"]] = r
    return entries


def gameweek_complete(fixtures: List[Dict[str, Any]]) -> bool:
    return bool(fixtures) and all(f.get("finished") or f.get("status") == "FT" for f in fixtures)


def outcome_of(pred: str) -> Optional[str]:
    try:
        h, a = (int(x) for x in pred.split("-"))
    except (ValueError, AttributeError):
        return None
    return "h" if h > a else ("d" if h == a else "a")


def crowd_insights(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Per fixture: share of home/draw/away picks and the most popular scoreline (edited comments excluded)."""
    picks: Dict[str, List[str]] = {}
    for r in records:
        if r.get("is_edited"):
            continue
        for key, item in (r.get("fixtures") or {}).items():
            pred = str(item.get("pred", "N/A")).replace(" ", "")
            if outcome_of(pred):
                picks.setdefault(key, []).append(pred)
    crowd = {}
    for key, preds in picks.items():
        n = len(preds)
        outcomes = Counter(outcome_of(p) for p in preds)
        top, top_n = Counter(preds).most_common(1)[0]
        crowd[key] = {
            "n": n, "h": round(100 * outcomes["h"] / n), "d": round(100 * outcomes["d"] / n),
            "a": round(100 * outcomes["a"] / n), "top": top, "top_pct": round(100 * top_n / n)
        }
    return crowd


def competition_ranks(totals: Dict[str, List[int]]) -> Dict[str, int]:
    """1, 2, 2, 4 style ranks ordered by points, exact scores, then outcomes."""
    order = sorted(totals, key=lambda a: (-totals[a][0], -totals[a][1], -totals[a][2]))
    ranks: Dict[str, int] = {}
    prev_key, prev_rank = None, 0
    for pos, author in enumerate(order, 1):
        key = tuple(totals[author])
        prev_rank = prev_rank if key == prev_key else pos
        ranks[author], prev_key = prev_rank, key
    return ranks


def enrich_leaderboard(rows: List[Dict[str, Any]], all_gw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Adds rank history per gameweek, rank movement since the previous gameweek, and gameweek wins."""
    per_gw = {int(g): valid_entries(d.get("audited_records", [])) for g, d in all_gw.items()}
    totals: Dict[str, List[int]] = {}
    ranks_after: Dict[int, Dict[str, int]] = {}
    history: Dict[str, List[List[Any]]] = {}
    for g in sorted(per_gw):
        for author, r in per_gw[g].items():
            t = totals.setdefault(author, [0, 0, 0])
            t[0] += r.get("total_points", 0)
            t[1] += r.get("exact_scores", 0)
            t[2] += r.get("outcome_scores", 0)
        ranks_after[g] = competition_ranks(totals)
        for author in totals:
            entry = per_gw[g].get(author)
            history.setdefault(author, []).append([
                g, entry.get("total_points", 0) if entry else None, ranks_after[g][author], entry.get("comment_id") if entry else None
            ])

    gw_wins: Dict[str, List[int]] = {}
    for g, entries in per_gw.items():
        if entries and gameweek_complete(all_gw[str(g)].get("fixtures", [])):
            best = max(r.get("total_points", 0) for r in entries.values())
            for author, r in entries.items():
                if best > 0 and r.get("total_points", 0) == best:
                    gw_wins.setdefault(author, []).append(g)

    last_two = sorted(ranks_after)[-2:]
    for row in rows:
        author = row.get("Author")
        row["history"] = history.get(author, [])
        row["gw_wins"] = sorted(gw_wins.get(author, []))
        if len(last_two) == 2:
            row["prev_rank"] = ranks_after[last_two[0]].get(author)
            row["now_rank"] = ranks_after[last_two[1]].get(author)
    return rows


def write_site_files(site_dir: str, active_gw: int, all_gw: Dict[str, Any], board: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """Writes data/site/*.json (only when content changed) and returns (gameweek index, live gameweek payload, build id)."""
    os.makedirs(site_dir, exist_ok=True)
    files: Dict[str, Any] = {"leaderboard.json": board}
    integrity: Dict[str, Any] = {}
    files["integrity.json"] = integrity
    index: Dict[str, Any] = {}
    active_payload: Dict[str, Any] = {"fixtures": [], "crowd": {}}
    for g in sorted(all_gw, key=int):
        records = all_gw[g].get("audited_records", [])
        fixtures = all_gw[g].get("fixtures", [])
        crowd = crowd_insights(records)
        files[f"gw_{g}.json"] = {"fixtures": fixtures, "crowd": crowd, "records": [{k: r.get(k) for k in SUMMARY_FIELDS} for r in records]}
        files[f"gw_{g}_details.json"] = {r["comment_id"]: {k: r.get(k) for k in DETAIL_FIELDS} for r in records}
        index[g] = {"count": len(records), "complete": gameweek_complete(fixtures)}
        integrity[g] = detect_integrity_flags(records)
        if int(g) == int(active_gw):
            active_payload = {"fixtures": fixtures, "crowd": crowd}

    digest = hashlib.sha1()
    for name in sorted(files):
        text = json.dumps(files[name], ensure_ascii=False, separators=(",", ":"))
        digest.update(name.encode("utf-8"))
        digest.update(text.encode("utf-8"))
        path = os.path.join(site_dir, name)
        existing = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                existing = f.read()
        if existing != text:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
    return index, active_payload, digest.hexdigest()[:12]


def generate_live_dashboard(
    active_gw: int,
    all_gameweeks_data: Dict[str, Any],
    df_leaderboard: pd.DataFrame,
    output_path: str = "dashboard.html",
    league_data: Optional[Dict[str, Any]] = None,
    video_url: str = ""
) -> str:
    board = json.loads(df_leaderboard.drop(columns=["Channel_URL"], errors="ignore").to_json(orient="records")) if not df_leaderboard.empty else []
    board = enrich_leaderboard(board, all_gameweeks_data)
    site_dir = os.path.join(os.path.dirname(os.path.abspath(output_path)), "data", "site")
    index, active_payload, build_id = write_site_files(site_dir, active_gw, all_gameweeks_data, board)

    safe_video = video_url if re.match(r"^https://(www\.)?youtube\.com/", video_url or "") else ""
    common_version = asset_version(COMMON_JS_PATH)
    stamp_admin_common_js(common_version)
    values = {
        "COMMON_JS_VERSION": common_version,
        "ACTIVE_GW": str(int(active_gw)),
        "GW_INDEX_JSON": to_script_json(index),
        "ACTIVE_GW_JSON": to_script_json(active_payload),
        "LEAGUE_JSON": to_script_json(league_data or {}),
        "BUILD_ID": build_id,
        "VIDEO_URL": html.escape(safe_video, quote=True),
    }
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    # Single pass, so placeholder-like text inside the injected JSON is never substituted again.
    page = re.sub(r"__([A-Z_]+)__", lambda m: values.get(m.group(1), m.group(0)), template)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page)
    return output_path
