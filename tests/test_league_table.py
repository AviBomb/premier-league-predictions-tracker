"""Run with: python tests/test_league_table.py"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.fixture_service import build_league_snapshot, predict_scoreline, update_ai_record


def fixture(home, away, hs, as_, kickoff, finished=True, event=1, fid=None):
    return {"id": fid or f"{home}{away}{event}", "team_h": home, "team_a": away, "team_h_score": hs, "team_a_score": as_,
            "kickoff_time": kickoff, "finished": finished, "event": event}


def test_league_snapshot():
    teams = {1: "Arsenal", 2: "Chelsea", 3: "Everton"}
    snap = build_league_snapshot([
        fixture(1, 2, 2, 0, "2026-08-01T15:00:00Z"),
        fixture(2, 3, 1, 1, "2026-08-08T15:00:00Z"),
        fixture(3, 1, 3, 1, "2026-08-15T15:00:00Z"),
        fixture(1, 3, None, None, "2026-08-22T15:00:00Z", finished=False, event=2),
        fixture(2, 1, None, None, "2026-08-29T15:00:00Z", finished=False, event=3),
    ], teams)
    rows = {r["team"]: r for r in snap["table"]}

    assert [r["team"] for r in snap["table"]] == ["Everton", "Arsenal", "Chelsea"]
    assert [r["position"] for r in snap["table"]] == [1, 2, 3]
    assert rows["Everton"]["points"] == 4 and rows["Everton"]["gd"] == 2
    assert rows["Everton"]["form"] == ["D", "W"]
    assert rows["Arsenal"]["played"] == 2 and rows["Arsenal"]["gd"] == 0

    assert rows["Arsenal"]["next"]["opponent"] == "Everton" and rows["Arsenal"]["next"]["venue"] == "H"
    assert rows["Everton"]["next"]["venue"] == "A"
    assert rows["Chelsea"]["next"]["opponent"] == "Arsenal" and rows["Chelsea"]["next"]["gw"] == 3

    preds = snap["predictions"]
    assert preds["gw"] == 2 and len(preds["matches"]) == 1
    m = preds["matches"][0]
    assert m["home"] == "Arsenal" and m["away"] == "Everton"
    assert 99 <= m["p_home"] + m["p_draw"] + m["p_away"] <= 101
    assert snap["deadlines"] == {"1": "2026-08-01T15:00:00Z", "2": "2026-08-22T15:00:00Z", "3": "2026-08-29T15:00:00Z"}


def test_ai_record():
    teams = {1: "Arsenal", 2: "Chelsea", 3: "Everton"}
    fixtures = [
        fixture(1, 2, 2, 0, "2026-08-01T15:00:00Z", event=1, fid=11),
        fixture(3, 1, 1, 1, "2026-08-08T15:00:00Z", event=2, fid=21),
        fixture(2, 3, None, None, "2026-08-22T15:00:00Z", finished=False, event=3, fid=31),
        fixture(1, 3, None, None, "2026-09-05T15:00:00Z", finished=False, event=4, fid=41),
    ]
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as tmp:
        store_path = os.path.join(tmp, "ai.json")
        record = update_ai_record(fixtures, teams, {}, store_path, now=now)
        store = json.load(open(store_path))
        assert store["1"]["11"]["backtest"] is True and store["2"]["21"]["backtest"] is True
        assert store["3"]["31"]["backtest"] is False, "next gameweek is predicted ahead of kickoff"
        assert "4" not in store, "only the next gameweek is tracked ahead of time"
        assert record["matches"] == 2 and len(record["gws"]) == 2

        locked = dict(store["3"]["31"])
        fixtures[2].update(team_h_score=5, team_a_score=5, finished=True)
        update_ai_record(fixtures, teams, {}, store_path, now=datetime(2026, 8, 23, tzinfo=timezone.utc))
        store = json.load(open(store_path))
        assert store["3"]["31"] == locked, "a pick is locked once its match has kicked off"


def test_predict_scoreline():
    strong = predict_scoreline(2.6, 0.6)
    assert strong["p_home"] > strong["p_away"] and strong["pred_home"] > strong["pred_away"]
    even = predict_scoreline(1.1, 1.1)
    assert even["p_home"] == even["p_away"]
    upset = predict_scoreline(0.5, 2.2)
    assert upset["pred_away"] > upset["pred_home"]


if __name__ == "__main__":
    test_league_snapshot()
    test_ai_record()
    test_predict_scoreline()
    print("league table + predictions + AI record: ok")
