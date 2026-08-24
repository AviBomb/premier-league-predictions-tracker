"""
Integrity & Scoring Engine (Rolling Match Deadlines & Edit Audit)
- Evaluates individual match deadlines per fixture:
  * If a comment is posted after a specific match kicked off, only that match is Void* (0 pts).
  * The remaining upcoming matches posted before their respective kickoffs are VALID and counted.
  * If all fixtures for the gameweek have already concluded before submission, the entire comment is Late (0 pts).
- Zero-tolerance integrity rule for edited comments:
  * Any edited comment is 100% Disqualified across all fixtures to prevent mid-game tampering.
- Tracks comment edit history across snapshots and generates highlighted visual diffs.
- Performs canonical fixture re-orientation.
- Applies Admin-Approved typo/spelling corrections.
- Scores exact predictions (3pts), outcome (1pt), miss (0pt).
"""
import os
import json
import difflib
import html
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from src.nlp_parser import extract_predictions_from_comment
from src.fuzzy_matcher import detect_fuzzy_prediction_candidates

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "comment_history.json")


def load_comment_history() -> Dict[str, Any]:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_comment_history(history: Dict[str, Any]):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def generate_highlighted_diff(old_text: str, new_text: str) -> str:
    """Generates an HTML snippet highlighting line-by-line added and removed tokens."""
    if not old_text or not new_text:
        safe_new = html.escape(new_text or "").replace("\n", "<br>")
        return f"<div class='diff-add'>+ {safe_new}</div>"
    if old_text == new_text:
        return ""

    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    diff_html = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for line in old_lines[i1:i2]:
                diff_html.append(f"<div class='diff-line' style='color:#ccc;'>{html.escape(line)}</div>")
        elif tag == 'replace':
            for line in old_lines[i1:i2]:
                diff_html.append(f"<div class='diff-line diff-del'>- {html.escape(line)}</div>")
            for line in new_lines[j1:j2]:
                diff_html.append(f"<div class='diff-line diff-add'>+ {html.escape(line)}</div>")
        elif tag == 'delete':
            for line in old_lines[i1:i2]:
                diff_html.append(f"<div class='diff-line diff-del'>- {html.escape(line)}</div>")
        elif tag == 'insert':
            for line in new_lines[j1:j2]:
                diff_html.append(f"<div class='diff-line diff-add'>+ {html.escape(line)}</div>")

    return "".join(diff_html)


def score_fixture(pred_h: int, pred_a: int, act_h: Optional[int], act_a: Optional[int]) -> Tuple[int, str]:
    """
    Scoring Logic:
    - 3 Points: Exact scoreline
    - 1 Point: Correct match outcome (Win / Loss / Draw)
    - 0 Points: Incorrect outcome or missed prediction
    """
    if act_h is None or act_a is None:
        return 0, "Pending"
    if pred_h == act_h and pred_a == act_a:
        return 3, "Exact"
    if (pred_h > pred_a and act_h > act_a) or \
       (pred_h < pred_a and act_h < act_a) or \
       (pred_h == pred_a and act_h == act_a):
        return 1, "Outcome"
    return 0, "Miss"


def format_duration(seconds: int) -> str:
    """Formats seconds into hours and minutes."""
    if seconds < 0:
        seconds = abs(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def audit_and_score_gameweek(
    comments: List[Dict[str, Any]],
    fixtures: List[Dict[str, Any]],
    gw_number: int,
    admin_approvals: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Processes all comments against the target fixtures with Rolling Match Deadlines.
    """
    if admin_approvals is None:
        admin_approvals = {}

    gw_key = f"GW_{gw_number}"
    gw_approvals = admin_approvals.get(gw_key, {})

    comment_history = load_comment_history()
    history_updated = False

    # Parse fixture kickoff datetimes in UTC
    fixture_kickoffs = {}
    for f in fixtures:
        f_dt = datetime.fromisoformat(f["kickoff"].replace("Z", "+00:00"))
        fixture_kickoffs[f["id"]] = f_dt

    if fixture_kickoffs:
        earliest_kickoff = min(fixture_kickoffs.values())
        latest_kickoff = max(fixture_kickoffs.values())
        kickoff_gmt_str = earliest_kickoff.strftime("%Y-%m-%d %H:%M:%S GMT")
    else:
        earliest_kickoff = datetime.now(timezone.utc)
        latest_kickoff = datetime.now(timezone.utc)
        kickoff_gmt_str = "TBD"
    print(f"[*] Gameweek {gw_number} Earliest Kickoff: {kickoff_gmt_str}")

    audited_records = []
    valid_leaderboard_entries = {}
    all_fuzzy_candidates = []

    for c in comments:
        c_id = c["comment_id"]
        author = c["author"]
        channel_url = c.get("author_channel_url", "")
        pub_str = str(c.get("published_at", ""))
        upd_str = str(c.get("updated_at", pub_str))
        is_edited = str(c.get("is_edited", "")).strip().lower() in ["true", "1"] or c.get("is_edited") is True
        raw_text = c["text"]

        # Track history in comment_history cache
        if c_id not in comment_history:
            comment_history[c_id] = {
                "initial_text": raw_text,
                "initial_pub": pub_str,
                "revisions": [],
                "latest_text": raw_text,
                "latest_upd": upd_str
            }
            history_updated = True
        else:
            entry = comment_history[c_id]
            if entry.get("latest_text") != raw_text:
                entry["revisions"].append({
                    "timestamp": entry.get("latest_upd", pub_str),
                    "text": entry.get("latest_text", raw_text)
                })
                entry["latest_text"] = raw_text
                entry["latest_upd"] = upd_str
                history_updated = True

        hist_entry = comment_history[c_id]
        original_comment_text = hist_entry.get("initial_text", raw_text)
        revisions_list = hist_entry.get("revisions", [])

        # Timing & Audit Calculations
        pub_dt = None
        upd_dt = None
        submission_gmt = "N/A"
        updated_gmt = "N/A"
        timing_analysis = ""
        lateness_str = ""
        edit_delta_str = ""

        try:
            pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            submission_gmt = pub_dt.strftime("%Y-%m-%d %H:%M:%S GMT")
            if upd_str:
                upd_dt = datetime.fromisoformat(upd_str.replace("Z", "+00:00"))
                updated_gmt = upd_dt.strftime("%Y-%m-%d %H:%M:%S GMT")
                if is_edited and upd_dt > pub_dt:
                    diff_sec = int((upd_dt - pub_dt).total_seconds())
                    edit_delta_str = f"Edited {format_duration(diff_sec)} after original post"
        except Exception:
            pass

        # Generate Visual Diff if Edited
        has_recorded_diff = False
        diff_html = ""
        if is_edited:
            if original_comment_text and original_comment_text != raw_text:
                diff_html = generate_highlighted_diff(original_comment_text, raw_text)
                has_recorded_diff = True

        # 1. NLP Exact Extraction
        raw_preds = extract_predictions_from_comment(raw_text)
        user_fixture_preds = {}
        exact_pairs = []
        exact_preds_dict = {}

        for p in raw_preds:
            t_a, t_b = p["team_a"], p["team_b"]
            s_a, s_b = p["score_a"], p["score_b"]

            for f in fixtures:
                h, a = f["home"], f["away"]
                if t_a == h and t_b == a:
                    user_fixture_preds[(h, a)] = (s_a, s_b)
                    exact_pairs.append((h, a))
                    exact_preds_dict[f"{h} vs {a}"] = f"{s_a} - {s_b}"
                elif t_a == a and t_b == h:
                    user_fixture_preds[(h, a)] = (s_b, s_a)
                    exact_pairs.append((h, a))
                    exact_preds_dict[f"{h} vs {a}"] = f"{s_b} - {s_a}"

        # 2. Fuzzy Typo / Spelling Mistake Detection (For unedited comments on pending/upcoming matches)
        if not is_edited:
            fuzzy_cands = detect_fuzzy_prediction_candidates(
                comment_text=raw_text,
                fixtures=fixtures,
                author=author,
                comment_id=c_id,
                published_at=pub_str,
                existing_exact_pairs=exact_pairs,
                existing_exact_preds=exact_preds_dict,
                gw_number=gw_number
            )

            user_approvals = gw_approvals.get(author, {})
            if not user_approvals:
                clean_auth = author.lower().strip().lstrip('@')
                for k, v in gw_approvals.items():
                    if k.lower().strip().lstrip('@') == clean_auth:
                        user_approvals = v
                        break

            for cand in fuzzy_cands:
                fix_id = cand["fixture_id"]
                fix_id_str = str(fix_id)
                f_kickoff = fixture_kickoffs.get(fix_id)

                is_before_kickoff = (pub_dt is None or f_kickoff is None or pub_dt <= f_kickoff)
                if fix_id_str in user_approvals:
                    cand_status = user_approvals[fix_id_str].get("status", "pending")
                    cand["status"] = cand_status

                    if cand_status == "approved" and is_before_kickoff:
                        h, a = cand["home_team"], cand["away_team"]
                        user_fixture_preds[(h, a)] = (cand["pred_home"], cand["pred_away"])

                if is_before_kickoff:
                    all_fuzzy_candidates.append(cand)

        # Strict Exclusion: If a comment/reply has 0 matches predicted, do not pick or display it
        if len(user_fixture_preds) == 0:
            continue

        # 3. Rolling Match Deadline Scoring Evaluation
        total_pts, exact_cnt, outcome_cnt = 0, 0, 0
        fixture_breakdown = {}
        late_matches_count = 0
        valid_matches_count = 0

        for f in fixtures:
            h, a = f["home"], f["away"]
            act_h, act_a = f.get("home_act"), f.get("away_act")
            f_key = f"{h} vs {a}"
            f_kickoff = fixture_kickoffs.get(f["id"])

            is_match_late = False
            if pub_dt and f_kickoff and pub_dt > f_kickoff:
                is_match_late = True

            if (h, a) in user_fixture_preds:
                ph, pa = user_fixture_preds[(h, a)]
                pts, res_type = score_fixture(ph, pa, act_h, act_a)

                if is_edited:
                    awarded = 0
                    result_desc = f"{res_type} (Disqualified - Edited Comment)"
                elif is_match_late:
                    awarded = 0
                    result_desc = "Void* (Submitted after match kickoff - Not Counted)"
                    late_matches_count += 1
                else:
                    awarded = pts
                    result_desc = res_type
                    valid_matches_count += 1
                    if awarded == 3:
                        exact_cnt += 1
                    elif awarded == 1:
                        outcome_cnt += 1

                fixture_breakdown[f_key] = {
                    "pred": f"{ph}-{pa}",
                    "actual": f"{act_h}-{act_a}" if act_h is not None else "TBD",
                    "points": awarded,
                    "result": result_desc,
                    "is_late": is_match_late
                }
                total_pts += awarded
            else:
                fixture_breakdown[f_key] = {
                    "pred": "N/A",
                    "actual": f"{act_h}-{act_a}" if act_h is not None else "TBD",
                    "points": 0,
                    "result": "No Prediction",
                    "is_late": is_match_late
                }

        # 4. Determine Overall Integrity Status
        if is_edited:
            status = "Disqualified (Comment was Edited)"
            timing_analysis = f"Comment was edited on YouTube. Initially posted: {submission_gmt} | Last edited: {updated_gmt}"
            if edit_delta_str:
                timing_analysis += f" ({edit_delta_str})"
        elif pub_dt and pub_dt > latest_kickoff:
            status = "Late Submission (All matches concluded)"
            delta_sec = int((pub_dt - latest_kickoff).total_seconds())
            lateness_str = f"Late by {format_duration(delta_sec)} after entire gameweek"
            timing_analysis = f"Submitted {format_duration(delta_sec)} after final kickoff ({submission_gmt})"
        elif late_matches_count > 0:
            status = f"Valid* (Late for {late_matches_count} match{'es' if late_matches_count > 1 else ''})"
            timing_analysis = f"Submitted {submission_gmt}. {late_matches_count} match(es) voided due to kickoff deadline, remaining matches active."
            lateness_str = f"Late for {late_matches_count} match(es)"
        else:
            status = "Valid"
            delta_sec = int((earliest_kickoff - pub_dt).total_seconds()) if pub_dt else 0
            timing_analysis = f"Submitted {format_duration(delta_sec)} before earliest kickoff ({submission_gmt})"

        record = {
            "comment_id": c_id,
            "author": author,
            "channel_url": channel_url,
            "published_at": pub_str,
            "updated_at": upd_str,
            "submission_gmt": submission_gmt,
            "updated_gmt": updated_gmt,
            "edit_delta_str": edit_delta_str,
            "lateness_str": lateness_str,
            "timing_analysis": timing_analysis,
            "is_edited": is_edited,
            "has_recorded_diff": has_recorded_diff,
            "status": status,
            "raw_text": raw_text,
            "original_comment_text": original_comment_text,
            "revisions": revisions_list,
            "diff_html": diff_html,
            "matches_found": len(user_fixture_preds),
            "valid_matches_count": valid_matches_count,
            "late_matches_count": late_matches_count,
            "exact_scores": exact_cnt,
            "outcome_scores": outcome_cnt,
            "total_points": total_pts,
            "fixtures": fixture_breakdown
        }
        audited_records.append(record)

        if status.startswith("Valid") and author not in valid_leaderboard_entries:
            valid_leaderboard_entries[author] = record

    if history_updated:
        save_comment_history(comment_history)

    return audited_records, valid_leaderboard_entries, all_fuzzy_candidates
