"""Run with: python tests/test_profile_history.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.dashboard_generator import enrich_leaderboard


def rec(author, cid, status, pts=0):
    return {"author": author, "comment_id": cid, "status": status, "total_points": pts}


def test_disqualified_gameweek_keeps_reason():
    all_gw = {
        "1": {"audited_records": [rec("@a", "c1", "Valid", 5), rec("@b", "c2", "Valid", 3)]},
        "2": {"audited_records": [rec("@a", "c3", "Disqualified (Comment was Edited)", 0), rec("@b", "c4", "Valid", 2)]},
        "3": {"audited_records": [rec("@b", "c5", "Valid", 1)]},
    }
    rows = enrich_leaderboard([{"Author": "@a"}, {"Author": "@b"}], all_gw)
    hist = {r["Author"]: r["history"] for r in rows}

    assert hist["@a"][0] == [1, 5, 1, "c1"]
    assert hist["@a"][1] == [2, None, 1, "c3", "Disqualified (Comment was Edited)"]
    assert hist["@a"][2] == [3, None, 2, None]
    assert hist["@b"][1] == [2, 2, 1, "c4"]


def test_disqualified_before_first_valid_gameweek_is_shown():
    all_gw = {
        "1": {"audited_records": [rec("@a", "c1", "Disqualified (Comment was Edited)"), rec("@b", "c2", "Valid", 3)]},
        "2": {"audited_records": [rec("@a", "c3", "Valid", 1)]},
    }
    rows = enrich_leaderboard([{"Author": "@a"}], all_gw)

    assert rows[0]["history"] == [[1, None, None, "c1", "Disqualified (Comment was Edited)"], [2, 1, 2, "c3"]]


if __name__ == "__main__":
    test_disqualified_gameweek_keeps_reason()
    test_disqualified_before_first_valid_gameweek_is_shown()
    print("ok")
