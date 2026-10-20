"""Run with: python tests/test_nlp_parser.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp_parser import extract_predictions_from_comment
from src.fuzzy_matcher import detect_fuzzy_prediction_candidates
import src.scoring_engine as engine


def pairs(text):
    return [(p["team_a"], p["score_a"], p["team_b"], p["score_b"]) for p in extract_predictions_from_comment(text)]


# "Team score vs Team score" — the form that was dropped for @LibanAbdi-n5l in GW7.
liban = """Everton 2 vs Chelsea 2
Brentford 1 vs Liverpool 2
Fulham 1 vs Hull City 3
Manchester City 3 vs Ipswich Town 1
Newcastle United 4 vs Aston Villa 3
Bournemouth 1 vs Sunderland 0
Brighton 4 vs Crystal Palace 1
Leeds United 2 vs Manchester United 0
Nottingham Forest 0 vs Arsenal 2
Tottenham Hotspur 2 vs Coventry City 1"""

assert pairs(liban) == [
    ("Everton", 2, "Chelsea", 2),
    ("Brentford", 1, "Liverpool", 2),
    ("Fulham", 1, "Hull City", 3),
    ("Manchester City", 3, "Ipswich Town", 1),
    ("Newcastle United", 4, "Aston Villa", 3),
    ("AFC Bournemouth", 1, "Sunderland", 0),
    ("Brighton & Hove Albion", 4, "Crystal Palace", 1),
    ("Leeds United", 2, "Manchester United", 0),
    ("Nottingham Forest", 0, "Arsenal", 2),
    ("Tottenham Hotspur", 2, "Coventry City", 1),
], pairs(liban)

# Same shape on one line, and a lone "v".
assert pairs("Everton 2 vs Chelsea 2 Brentford 1 v Liverpool 2") == [
    ("Everton", 2, "Chelsea", 2),
    ("Brentford", 1, "Liverpool", 2),
]

# Forms that already scored must keep the same reading.
assert pairs("Man United 2 Forest 1") == [("Manchester United", 2, "Nottingham Forest", 1)]
assert pairs("Everton 2-2 Chelsea") == [("Everton", 2, "Chelsea", 2)]
assert pairs("Everton vs Chelsea 2-1") == [("Everton", 2, "Chelsea", 1)]
assert pairs("2-1 Arsenal vs Chelsea") == [("Arsenal", 2, "Chelsea", 1)]
assert pairs("Villa 2 Arsenal 1") == [("Aston Villa", 2, "Arsenal", 1)]

# Names that were missing, and an extra word that must not be scored as another club.
assert pairs("Coventry city 1 Brighton Hove Albion 3") == [("Coventry City", 1, "Brighton & Hove Albion", 3)]
assert pairs("Newcastle utd 1 Leeds 0") == [("Newcastle United", 1, "Leeds United", 0)]
assert pairs("Hull City 2 Chelsea 1") == [("Hull City", 2, "Chelsea", 1)]
assert pairs("Leeds united 2 Newcastle United 1") == [("Leeds United", 2, "Newcastle United", 1)]
assert pairs("Sunderland united 0 Arsenal 2") == []

sunderland = [{"id": 36, "home": "Sunderland", "away": "Arsenal", "home_act": 0, "away_act": 2, "kickoff": "2026-09-12T19:00:00Z"}]
line = "Sunderland united 0 Arsenal 2"
cands = detect_fuzzy_prediction_candidates(line, sunderland, "@NZ_COYS_SPURS", "c1", "2026-09-10T18:03:54Z", [], {}, 4)
assert len(cands) == 1 and cands[0]["pred_home"] == 0 and cands[0]["pred_away"] == 2, cands
assert cands[0]["status"] == "pending" and cands[0]["home_team"] == "Sunderland"
assert "united" in cands[0]["raw_line"]

comment = {"comment_id": "c-nz", "author": "@NZ_COYS_SPURS", "text": line,
           "published_at": "2026-09-10T18:03:54Z", "updated_at": "2026-09-10T18:03:54Z", "is_edited": False}
with tempfile.TemporaryDirectory() as tmp:
    engine.HISTORY_FILE = os.path.join(tmp, "history.json")
    pending_records, _, pending_cands = engine.audit_and_score_gameweek([comment], sunderland, 4, admin_approvals={})
assert pending_records == [] and len(pending_cands) == 1

approved = {"GW_4": {"@NZ_COYS_SPURS": {"36": {"status": "approved", "pred_home": 0, "pred_away": 2}}}}
with tempfile.TemporaryDirectory() as tmp:
    engine.HISTORY_FILE = os.path.join(tmp, "history.json")
    records, valid, _ = engine.audit_and_score_gameweek([comment], sunderland, 4, admin_approvals=approved)
assert records[0]["total_points"] == 3, records[0]["total_points"]
assert records[0]["fixtures"]["Sunderland vs Arsenal"]["pred"] == "0-2"
assert "@NZ_COYS_SPURS" in valid

print("nlp parser ok")
