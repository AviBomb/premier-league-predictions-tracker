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

# Ten scorelines written on one line, each "Team score-score Team".
one_line = "Brentford 1-3 Chelsea Spurs 1-1 Aston Villa Brighton 0-2 Arsenal Everton 4-1 Ipswich Newcastle 4-3 Hull Nottingham Forest 1-1 Coventry Bournemouth 0-1 Liverpool Leeds United 3-0 Crystal Palace Man City 3-1 Sunderland Fulham 1-2 Man United"
# "Team score vs score Team", including several on separate lines.
gomachado = """Everton 1 vs 3 Chelsea
Brentford 2 vs 1 liverpool
Fulham 1 vs 1 Hull
Man city 3 vs 0 ipswich
Newcastle 1 vs 1 aston villa
Leeds 2 vs 1 man united
Brighton 3 vs 1 Crystal palace
Forest 0 vs 2 arsenal
Bournemouth 1 vs 0 sunderland
Tottenham 1 vs 1 coventry"""
assert pairs(gomachado) == [
    ("Everton", 1, "Chelsea", 3),
    ("Brentford", 2, "Liverpool", 1),
    ("Fulham", 1, "Hull City", 1),
    ("Manchester City", 3, "Ipswich Town", 0),
    ("Newcastle United", 1, "Aston Villa", 1),
    ("Leeds United", 2, "Manchester United", 1),
    ("Brighton & Hove Albion", 3, "Crystal Palace", 1),
    ("Nottingham Forest", 0, "Arsenal", 2),
    ("AFC Bournemouth", 1, "Sunderland", 0),
    ("Tottenham Hotspur", 1, "Coventry City", 1),
], pairs(gomachado)

assert pairs(one_line) == [
    ("Brentford", 1, "Chelsea", 3),
    ("Tottenham Hotspur", 1, "Aston Villa", 1),
    ("Brighton & Hove Albion", 0, "Arsenal", 2),
    ("Everton", 4, "Ipswich Town", 1),
    ("Newcastle United", 4, "Hull City", 3),
    ("Nottingham Forest", 1, "Coventry City", 1),
    ("AFC Bournemouth", 0, "Liverpool", 1),
    ("Leeds United", 3, "Crystal Palace", 0),
    ("Manchester City", 3, "Sunderland", 1),
    ("Fulham", 1, "Manchester United", 2),
], pairs(one_line)

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

# Every separator and order seen in GW1-7 comments.
assert pairs("Arsenal 2x0 Coventry") == [("Arsenal", 2, "Coventry City", 0)]
assert pairs("Everton 1 x 3 Man United") == [("Everton", 1, "Manchester United", 3)]
assert pairs("Palace 1x 2 City") == [("Crystal Palace", 1, "Manchester City", 2)]
assert pairs("Arsenal 3, Coventry City 0") == [("Arsenal", 3, "Coventry City", 0)]
assert pairs("Hull ~ 1, Man U ~ 2") == [("Hull City", 1, "Manchester United", 2)]
assert pairs("liverpool-3,fulham-1") == [("Liverpool", 3, "Fulham", 1)]
assert pairs("brighton=1 v arsenal=1") == [("Brighton & Hove Albion", 1, "Arsenal", 1)]
assert pairs("LIVERPOOL  3=0 Fulham") == [("Liverpool", 3, "Fulham", 0)]
assert pairs("Arsenal vs Coventry City 3--0") == [("Arsenal", 3, "Coventry City", 0)]
assert pairs("Villa-Forest / 3-1") == [("Aston Villa", 3, "Nottingham Forest", 1)]
assert pairs("EVE v CRY (0-0)") == [("Everton", 0, "Crystal Palace", 0)]
assert pairs("Arsenal vs Coventry City (2-1)") == [("Arsenal", 2, "Coventry City", 1)]
assert pairs("Spurs v Newcastle1:3") == [("Tottenham Hotspur", 1, "Newcastle United", 3)]
assert pairs("Crystal Palace vs Nottingham Forest2-2") == [("Crystal Palace", 2, "Nottingham Forest", 2)]
assert pairs("Arsenalv Leeds 1:0") == [("Arsenal", 1, "Leeds United", 0)]
assert pairs("Brighton 0-3 varsenal") == [("Brighton & Hove Albion", 0, "Arsenal", 3)]
assert pairs("Brighton 3 Crystal Pallace 0") == [("Brighton & Hove Albion", 3, "Crystal Palace", 0)]
assert pairs("Aston Villa 2 Nottingham Forrest 0") == [("Aston Villa", 2, "Nottingham Forest", 0)]
assert pairs("Aston Villa 3 N. Forest 1") == [("Aston Villa", 3, "Nottingham Forest", 1)]
assert pairs("Fulham 0 C.Palace 0") == [("Fulham", 0, "Crystal Palace", 0)]
assert pairs("Fulham 1 Cry Palace 1") == [("Fulham", 1, "Crystal Palace", 1)]
assert pairs("Everton 1 Man. United 3") == [("Everton", 1, "Manchester United", 3)]
assert pairs("Chelsea\u2019 4 Hull city 0") == [("Chelsea", 4, "Hull City", 0)]
assert pairs("Hull City 0\u0337-3 Manchester United") == [("Hull City", 0, "Manchester United", 3)]
assert pairs("Everton versus Palace 1-0") == [("Everton", 1, "Crystal Palace", 0)]
# Side-by-side words that are one club name are not two teams.
assert pairs("Leeds United 2-1 Man United") == [("Leeds United", 2, "Manchester United", 1)]
assert pairs("Leeds United 0-2") == []

# Not auto-scored: joke scores, video timestamps, and "(2-1 liverpool)" where the 2 could be either side.
assert pairs("Palace 50 City 15") == []
assert pairs("Man City 1-45 Sunderland") == []
assert pairs("07:19 Ipswich 1v  Sunderland") == []
assert pairs("Liverpool vs Forest (2-1 liverpool)") == []
assert pairs("Chelsea 2 Bournemouth AFC 1") == []

# One line, full stops between matches; real fixtures stop "1 Coventry. Hull 1" from stealing the text.
gw1 = [{"id": i, "home": h, "away": a} for i, (h, a) in enumerate([
    ("Arsenal", "Coventry City"), ("Hull City", "Manchester United"), ("Everton", "Crystal Palace"),
    ("Ipswich Town", "Sunderland"), ("Nottingham Forest", "Leeds United"), ("Brentford", "Tottenham Hotspur"),
    ("Brighton & Hove Albion", "Aston Villa"), ("Manchester City", "AFC Bournemouth"),
    ("Newcastle United", "Liverpool"), ("Fulham", "Chelsea"),
], start=1)]
lilpeth_gw1 = "Arsenal 3-1 Coventry. Hull 1-2 Man Utd. Everton 1-0 Palace. Ipswich 1-1 Sunderland. Forest 2-3 Leeds. B'ford 0-1 Spurs. Bri 2-2 Villa. City 3-2 B'mouth. Newcastle 0-2 Liverpool. Fulham 1-3 Chelsea"
got = [(p["team_a"], p["score_a"], p["team_b"], p["score_b"]) for p in extract_predictions_from_comment(lilpeth_gw1, fixtures=gw1)]
assert got == [
    ("Arsenal", 3, "Coventry City", 1),
    ("Hull City", 1, "Manchester United", 2),
    ("Everton", 1, "Crystal Palace", 0),
    ("Ipswich Town", 1, "Sunderland", 1),
    ("Nottingham Forest", 2, "Leeds United", 3),
    ("Manchester City", 3, "AFC Bournemouth", 2),
    ("Newcastle United", 0, "Liverpool", 2),
    ("Fulham", 1, "Chelsea", 3),
], got


def queued(text, fixtures):
    found = detect_fuzzy_prediction_candidates(text, fixtures, "@u", "c", "2026-08-20T00:00:00Z", [], {}, 1)
    return [(c["home_team"], c["pred_home"], c["pred_away"], c["away_team"], c["reason"]) for c in found]


# Doubtful lines go to the admin queue with a reason and a best-guess score.
assert queued("Liverpool vs Forest (2-1 liverpool)", [{"id": 1, "home": "Liverpool", "away": "Nottingham Forest"}]) == [
    ("Liverpool", 2, 1, "Nottingham Forest", "prose")]
assert queued("Bournemouth vs Everton (3-1 everton)", [{"id": 1, "home": "AFC Bournemouth", "away": "Everton"}]) == [
    ("AFC Bournemouth", 1, 3, "Everton", "prose")]
assert queued("Everton versus Palace - Everton win 1-0", gw1) == [("Everton", 1, 0, "Crystal Palace", "prose")]
assert queued("Chelsea 2 Bournemouth AFC 1", [{"id": 1, "home": "Chelsea", "away": "AFC Bournemouth"}]) == [
    ("Chelsea", 2, 1, "AFC Bournemouth", "extra word")]
assert queued("Fulham 1 Machester United 0", [{"id": 1, "home": "Fulham", "away": "Manchester United"}]) == [
    ("Fulham", 1, 0, "Manchester United", "typo")]
assert queued("Palace 50 City 15", [{"id": 1, "home": "Crystal Palace", "away": "Manchester City"}]) == [
    ("Crystal Palace", 50, 15, "Manchester City", "unusual score")]
assert queued("Bournemouth v Everton 14-1", [{"id": 1, "home": "AFC Bournemouth", "away": "Everton"}]) == [
    ("AFC Bournemouth", 14, 1, "Everton", "unusual score")]
assert queued("07:19 Ipswich 1v  Sunderland", gw1) == []
assert queued("Newcastle 0 Liverpool 500", gw1) == []

print("nlp parser ok")
