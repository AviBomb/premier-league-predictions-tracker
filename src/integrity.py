"""
Spam and duplicate detection for one gameweek's audited comments. Informational only: nothing here
changes scoring, it just lists patterns for an admin to look at.
- identical_picks       3+ different accounts posting exactly the same scorelines across 6+ matches
- copied_text           the same comment wording (40+ characters) posted by different accounts
- repeat_submissions    one account posting several prediction comments (only the first valid one scores)
"""
import re
from collections import defaultdict
from typing import Any, Dict, List

MIN_SHARED_ACCOUNTS = 3
MIN_MATCHES = 6
MIN_TEXT_LENGTH = 40
SCORE = re.compile(r"^\d{1,2}-\d{1,2}$")


def _picks(record: Dict[str, Any]) -> tuple:
    preds = []
    for key, item in (record.get("fixtures") or {}).items():
        pred = str(item.get("pred", "")).replace(" ", "")
        if SCORE.match(pred):
            preds.append((key, pred))
    return tuple(sorted(preds))


def _normalized_text(record: Dict[str, Any]) -> str:
    return re.sub(r"\s+", " ", str(record.get("raw_text") or "")).strip().lower()


def _flag(kind: str, members: List[Dict[str, Any]], detail: str) -> Dict[str, Any]:
    return {
        "type": kind,
        "authors": sorted({m["author"] for m in members}),
        "comment_ids": [m["comment_id"] for m in members],
        "detail": detail,
    }


def detect_integrity_flags(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    posts = [r for r in records if r.get("author") and r.get("comment_id") and not str(r.get("status", "")).endswith("(Admin entry)")]
    flags: List[Dict[str, Any]] = []

    by_picks: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    by_text: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_author: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in posts:
        picks = _picks(r)
        if len(picks) >= MIN_MATCHES:
            by_picks[picks].append(r)
            by_author[r["author"]].append(r)
        text = _normalized_text(r)
        if len(text) >= MIN_TEXT_LENGTH:
            by_text[text].append(r)

    for picks, members in by_picks.items():
        accounts = {m["author"] for m in members}
        if len(accounts) >= MIN_SHARED_ACCOUNTS:
            flags.append(_flag("identical_picks", members, f"{len(accounts)} accounts posted the same {len(picks)} scorelines"))

    for text, members in by_text.items():
        accounts = {m["author"] for m in members}
        if len(accounts) >= 2:
            snippet = text[:60] + ("..." if len(text) > 60 else "")
            flags.append(_flag("copied_text", members, f"{len(accounts)} accounts posted the same text: \"{snippet}\""))

    for author, members in by_author.items():
        if len(members) >= 2:
            flags.append(_flag("repeat_submissions", members, f"{len(members)} prediction comments from one account; only the first valid one scores"))

    order = {"identical_picks": 0, "copied_text": 1, "repeat_submissions": 2}
    flags.sort(key=lambda f: (order[f["type"]], -len(f["comment_ids"])))
    return flags
