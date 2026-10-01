"""Run with: python tests/test_manual_override.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.scoring_engine as engine

FIXTURES = [
    {"id": 1, "home": "Arsenal", "away": "Chelsea", "home_act": 2, "away_act": 1, "kickoff": "2026-08-22T14:00:00Z"},
    {"id": 2, "home": "Everton", "away": "Fulham", "home_act": 0, "away_act": 0, "kickoff": "2026-08-22T16:30:00Z"},
]


def comment(author, text):
    return {"comment_id": f"c-{author}", "author": author, "text": text,
            "published_at": "2026-08-21T10:00:00Z", "updated_at": "2026-08-21T10:00:00Z", "is_edited": False}


def test_manual_entries():
    approvals = {"GW_1": {
        # Adds a missing match to an existing comment
        "@alice": {"2": {"status": "approved", "manual": True, "pred_home": 0, "pred_away": 0, "reason": "garbled line"}},
        # Predictor whose comment was deleted
        "@bob": {"1": {"status": "approved", "manual": True, "pred_home": 2, "pred_away": 1, "reason": "comment deleted"}},
        # A rejected manual entry never counts
        "@carol": {"1": {"status": "rejected", "manual": True, "pred_home": 2, "pred_away": 1}},
    }}
    comments = [comment("@alice", "Arsenal 1-0 Chelsea")]
    with tempfile.TemporaryDirectory() as tmp:
        engine.HISTORY_FILE = os.path.join(tmp, "history.json")
        records, valid, _ = engine.audit_and_score_gameweek(comments, FIXTURES, 1, admin_approvals=approvals)

    by_author = {r["author"]: r for r in records}
    assert set(by_author) == {"@alice", "@bob"}, by_author.keys()
    alice = by_author["@alice"]
    assert alice["matches_found"] == 2 and alice["total_points"] == 1 + 3, alice["total_points"]
    bob = by_author["@bob"]
    assert bob["status"] == "Valid (Admin entry)" and bob["total_points"] == 3
    assert "comment deleted" in bob["timing_analysis"]
    assert "@bob" in valid and "@carol" not in valid


if __name__ == "__main__":
    test_manual_entries()
    print("manual override: ok")
