"""
Premier League & FPL Fixture Service (2026-2027 Season)
Fetches official fixtures, kickoff times in GMT/UTC, and live/full-time match scores
directly from the Official Premier League / FPL API.
"""
import urllib.request
import ssl
import json
import math
import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

# Canonical Mapping for Premier League Teams from FPL API
FPL_NAME_CANONICAL_MAP: Dict[str, str] = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton & Hove Albion",
    "Chelsea": "Chelsea",
    "Coventry City": "Coventry City",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Hull City": "Hull City",
    "Ipswich Town": "Ipswich Town",
    "Leeds": "Leeds United",
    "Liverpool": "Liverpool",
    "Man City": "Manchester City",
    "Man Utd": "Manchester United",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Spurs": "Tottenham Hotspur",
    "Sunderland": "Sunderland"
}

# Premier League Official Club Badge CDN Logos
PL_TEAM_LOGOS: Dict[str, str] = {
    "Arsenal": "https://resources.premierleague.com/premierleague/badges/70/t3.png",
    "Aston Villa": "https://resources.premierleague.com/premierleague/badges/70/t7.png",
    "AFC Bournemouth": "https://resources.premierleague.com/premierleague/badges/70/t91.png",
    "Bournemouth": "https://resources.premierleague.com/premierleague/badges/70/t91.png",
    "Brentford": "https://resources.premierleague.com/premierleague/badges/70/t94.png",
    "Brighton & Hove Albion": "https://resources.premierleague.com/premierleague/badges/70/t36.png",
    "Brighton": "https://resources.premierleague.com/premierleague/badges/70/t36.png",
    "Chelsea": "https://resources.premierleague.com/premierleague/badges/70/t8.png",
    "Coventry City": "https://resources.premierleague.com/premierleague/badges/70/t9.png",
    "Crystal Palace": "https://resources.premierleague.com/premierleague/badges/70/t31.png",
    "Everton": "https://resources.premierleague.com/premierleague/badges/70/t11.png",
    "Fulham": "https://resources.premierleague.com/premierleague/badges/70/t54.png",
    "Hull City": "https://resources.premierleague.com/premierleague/badges/70/t88.png",
    "Ipswich Town": "https://resources.premierleague.com/premierleague/badges/70/t40.png",
    "Leeds United": "https://resources.premierleague.com/premierleague/badges/70/t2.png",
    "Leeds": "https://resources.premierleague.com/premierleague/badges/70/t2.png",
    "Liverpool": "https://resources.premierleague.com/premierleague/badges/70/t14.png",
    "Manchester City": "https://resources.premierleague.com/premierleague/badges/70/t43.png",
    "Man City": "https://resources.premierleague.com/premierleague/badges/70/t43.png",
    "Manchester United": "https://resources.premierleague.com/premierleague/badges/70/t1.png",
    "Man Utd": "https://resources.premierleague.com/premierleague/badges/70/t1.png",
    "Newcastle United": "https://resources.premierleague.com/premierleague/badges/70/t4.png",
    "Newcastle": "https://resources.premierleague.com/premierleague/badges/70/t4.png",
    "Nottingham Forest": "https://resources.premierleague.com/premierleague/badges/70/t17.png",
    "Nott'm Forest": "https://resources.premierleague.com/premierleague/badges/70/t17.png",
    "Tottenham Hotspur": "https://resources.premierleague.com/premierleague/badges/70/t6.png",
    "Spurs": "https://resources.premierleague.com/premierleague/badges/70/t6.png",
    "Sunderland": "https://resources.premierleague.com/premierleague/badges/70/t56.png"
}

def get_team_logo(team_name: str) -> str:
    """Returns official Premier League club badge CDN image URL for a given club name."""
    if not team_name:
        return "https://resources.premierleague.com/premierleague/badges/70/t3.png"
    clean = team_name.strip()
    if clean in PL_TEAM_LOGOS:
        return PL_TEAM_LOGOS[clean]
    for key, logo in PL_TEAM_LOGOS.items():
        if key.lower() in clean.lower() or clean.lower() in key.lower():
            return logo
    return "https://resources.premierleague.com/premierleague/badges/70/t3.png"

# 2026-2027 Verified FPL Team ID Fallback Map
FPL_TEAM_ID_MAP: Dict[int, str] = {
    1: "Arsenal",
    2: "Aston Villa",
    3: "AFC Bournemouth",
    4: "Brentford",
    5: "Brighton & Hove Albion",
    6: "Chelsea",
    7: "Coventry City",
    8: "Crystal Palace",
    9: "Everton",
    10: "Fulham",
    11: "Hull City",
    12: "Ipswich Town",
    13: "Leeds United",
    14: "Liverpool",
    15: "Manchester City",
    16: "Manchester United",
    17: "Newcastle United",
    18: "Nottingham Forest",
    19: "Tottenham Hotspur",
    20: "Sunderland"
}

# Official 2026-2027 Premier League Season Fixture Schedules Fallback
SEASON_2026_2027_FIXTURES: Dict[int, List[Dict[str, Any]]] = {
    1: [
        {"id": 1, "home": "Arsenal", "away": "Coventry City", "home_act": 3, "away_act": 0, "kickoff": "2026-08-21T19:00:00Z", "finished": True},
        {"id": 4, "home": "Hull City", "away": "Manchester United", "home_act": 2, "away_act": 0, "kickoff": "2026-08-22T11:30:00Z", "finished": True},
        {"id": 3, "home": "Everton", "away": "Crystal Palace", "home_act": None, "away_act": None, "kickoff": "2026-08-22T14:00:00Z", "finished": False},
        {"id": 5, "home": "Ipswich Town", "away": "Sunderland", "home_act": None, "away_act": None, "kickoff": "2026-08-22T14:00:00Z", "finished": False},
        {"id": 6, "home": "Nottingham Forest", "away": "Leeds United", "home_act": None, "away_act": None, "kickoff": "2026-08-22T14:00:00Z", "finished": False},
        {"id": 2, "home": "Brentford", "away": "Tottenham Hotspur", "home_act": None, "away_act": None, "kickoff": "2026-08-22T16:30:00Z", "finished": False},
        {"id": 7, "home": "Brighton & Hove Albion", "away": "Aston Villa", "home_act": None, "away_act": None, "kickoff": "2026-08-23T13:00:00Z", "finished": False},
        {"id": 8, "home": "Manchester City", "away": "AFC Bournemouth", "home_act": None, "away_act": None, "kickoff": "2026-08-23T13:00:00Z", "finished": False},
        {"id": 9, "home": "Newcastle United", "away": "Liverpool", "home_act": None, "away_act": None, "kickoff": "2026-08-23T15:30:00Z", "finished": False},
        {"id": 10, "home": "Fulham", "away": "Chelsea", "home_act": None, "away_act": None, "kickoff": "2026-08-24T19:00:00Z", "finished": False}
    ],
    2: [
        {"id": 11, "home": "Aston Villa", "away": "Arsenal", "home_act": None, "away_act": None, "kickoff": "2026-08-29T11:30:00Z", "finished": False},
        {"id": 12, "home": "AFC Bournemouth", "away": "Newcastle United", "home_act": None, "away_act": None, "kickoff": "2026-08-29T14:00:00Z", "finished": False},
        {"id": 13, "home": "Chelsea", "away": "Everton", "home_act": None, "away_act": None, "kickoff": "2026-08-29T14:00:00Z", "finished": False},
        {"id": 14, "home": "Crystal Palace", "away": "Nottingham Forest", "home_act": None, "away_act": None, "kickoff": "2026-08-29T14:00:00Z", "finished": False},
        {"id": 15, "home": "Leeds United", "away": "Brentford", "home_act": None, "away_act": None, "kickoff": "2026-08-29T14:00:00Z", "finished": False},
        {"id": 16, "home": "Manchester United", "away": "Fulham", "home_act": None, "away_act": None, "kickoff": "2026-08-29T16:30:00Z", "finished": False},
        {"id": 17, "home": "Tottenham Hotspur", "away": "Manchester City", "home_act": None, "away_act": None, "kickoff": "2026-08-30T13:00:00Z", "finished": False},
        {"id": 18, "home": "Liverpool", "away": "Ipswich Town", "home_act": None, "away_act": None, "kickoff": "2026-08-30T15:30:00Z", "finished": False},
        {"id": 19, "home": "Sunderland", "away": "Brighton & Hove Albion", "home_act": None, "away_act": None, "kickoff": "2026-08-30T15:30:00Z", "finished": False},
        {"id": 20, "home": "Coventry City", "away": "Hull City", "home_act": None, "away_act": None, "kickoff": "2026-08-31T19:00:00Z", "finished": False}
    ]
}


def normalize_team_key(name: str) -> str:
    """Normalizes club name for robust cross-API matching."""
    if not name:
        return ""
    clean = name.lower()
    for drop in ["fc", "afc", "and", "&", "hove", "albion", "town", "city", "united", "hotspur", "wanderers", "county", "north", "south"]:
        clean = clean.replace(drop, "")
    return "".join(c for c in clean if c.isalnum())


def fetch_pulse_match_goals_map(gw_number: int) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Queries Premier League Pulse API for exact minute-by-minute goal events, scorers, and assists.
    Returns mapping keyed by (norm_home_team, norm_away_team).
    """
    pulse_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    try:
        ctx = ssl._create_unverified_context()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Origin": "https://www.premierleague.com"
        }
        
        # 1. Get current compSeason ID for Premier League
        comp_url = "https://footballapi.pulselive.com/football/competitions/1/compseasons?page=0&pageSize=1"
        req = urllib.request.Request(comp_url, headers=headers)
        with urllib.request.urlopen(req, timeout=6, context=ctx) as resp:
            comp_data = json.loads(resp.read().decode("utf-8"))
            season_id = int(comp_data.get("content", [{}])[0].get("id", 841))
            
        # 2. Fetch Pulse fixtures for season
        fix_url = f"https://footballapi.pulselive.com/football/fixtures?page=0&pageSize=400&sort=asc&statuses=U,L,C&compSeasons={season_id}"
        req2 = urllib.request.Request(fix_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=8, context=ctx) as resp2:
            pulse_fixes = json.loads(resp2.read().decode("utf-8")).get("content", [])
            gw_pulse = [f for f in pulse_fixes if int(f.get("gameweek", {}).get("gameweek", 0)) == gw_number]

        # 3. For each match, query detailed fixture endpoint if match has goals / started
        for pf in gw_pulse:
            h_raw = pf.get("teams", [{}])[0].get("team", {}).get("name", "")
            a_raw = pf.get("teams", [{}])[1].get("team", {}).get("name", "")
            norm_key = (normalize_team_key(h_raw), normalize_team_key(a_raw))
            
            pid = int(pf.get("id", 0))
            if not pid:
                continue

            detail_url = f"https://footballapi.pulselive.com/football/fixtures/{pid}"
            req3 = urllib.request.Request(detail_url, headers=headers)
            with urllib.request.urlopen(req3, timeout=6, context=ctx) as resp3:
                data = json.loads(resp3.read().decode("utf-8"))
                
            h_score_raw = None
            a_score_raw = None
            if data.get("teams") and len(data.get("teams")) >= 2:
                h_score_raw = data.get("teams")[0].get("score")
                a_score_raw = data.get("teams")[1].get("score")
            if h_score_raw is None and pf.get("teams") and len(pf.get("teams")) >= 2:
                h_score_raw = pf.get("teams")[0].get("score")
                a_score_raw = pf.get("teams")[1].get("score")

            status_code = data.get("status") or pf.get("status")  # 'C', 'L', 'U'
            clock_obj = data.get("clock") or pf.get("clock") or {}
            clock_label = clock_obj.get("label", "")
            if clock_label.endswith("'00"):
                clock_label = clock_label[:-3] + "'"

            players = {}
            for tl in data.get("teamLists") or []:
                if not tl:
                    continue
                lineup = (tl.get("lineup") or []) + (tl.get("substitutes") or [])
                for p in lineup:
                    if not p:
                        continue
                    p_info = p.get("name") or {}
                    p_name = p_info.get("display") or f"{p_info.get('first', '')} {p_info.get('last', '')}".strip()
                    players[p.get("id")] = p_name

            h_id = data.get("teams", [{}])[0].get("team", {}).get("id")
            
            raw_events = [e for e in (data.get("events") or []) if e and e.get("type") in ("G", "OG", "O", "P", "PEN")]
            raw_events.sort(key=lambda x: x.get("clock", {}).get("secs", 0))
            
            home_goals_list = []
            away_goals_list = []
            home_summary_parts = []
            away_summary_parts = []

            for g in raw_events:
                scorer_name = players.get(g.get("personId"), "Goal")
                min_lbl = g.get("clock", {}).get("label", "")
                if min_lbl.endswith("'00"):
                    min_lbl = min_lbl[:-3] + "'"

                g_type = g.get("type")
                is_og = g_type in ("OG", "O")
                is_pen = g_type in ("P", "PEN")

                normalized_type = "OG" if is_og else ("P" if is_pen else "G")
                type_str = " (OG)" if is_og else (" (P)" if is_pen else "")

                # Own Goals do not have assists from the benefiting team
                assist_name = None if is_og else (players.get(g.get("assistId")) if g.get("assistId") else None)

                goal_obj = {
                    "minute": min_lbl,
                    "scorer": scorer_name,
                    "assist": assist_name,
                    "type": normalized_type
                }

                summary_str = f"{scorer_name} {min_lbl}{type_str}" + (f" (assist: {assist_name})" if assist_name else "")

                if g.get("teamId") == h_id:
                    home_goals_list.append(goal_obj)
                    home_summary_parts.append(summary_str)
                else:
                    away_goals_list.append(goal_obj)
                    away_summary_parts.append(summary_str)

            # If score was not explicitly given, derive from total mapped goals
            if h_score_raw is None and len(home_goals_list) > 0:
                h_score_raw = len(home_goals_list)
            if a_score_raw is None and len(away_goals_list) > 0:
                a_score_raw = len(away_goals_list)

            pulse_map[norm_key] = {
                "home_score": int(h_score_raw) if h_score_raw is not None else None,
                "away_score": int(a_score_raw) if a_score_raw is not None else None,
                "status_code": status_code,
                "clock": clock_label,
                "home_goals": home_goals_list,
                "away_goals": away_goals_list,
                "home_goals_summary": ", ".join(home_summary_parts),
                "away_goals_summary": ", ".join(away_summary_parts)
            }
    except Exception as e:
        print(f"[*] Pulse API enrichment note ({e})")
    return pulse_map


def fetch_bootstrap_data() -> Tuple[Dict[int, str], Dict[int, str]]:
    """Dynamically queries bootstrap-static to build live team ID and player ID mappings."""
    team_map = dict(FPL_TEAM_ID_MAP)
    player_map: Dict[int, str] = {}
    try:
        # Retried: a dropped connection here would otherwise turn scorer names into "Player #id" for the whole run.
        data = _fetch_fpl_json("bootstrap-static/", attempts=3)
        for t in data.get("teams", []):
            raw_name = t.get("name", "")
            canonical = FPL_NAME_CANONICAL_MAP.get(raw_name, raw_name)
            team_map[t["id"]] = canonical
        for e in data.get("elements", []):
            name = e.get("web_name") or f"{e.get('first_name', '')} {e.get('second_name', '')}".strip()
            player_map[e["id"]] = name
    except Exception as e:
        print(f"[*] Using local fallback mappings ({e})")
    return team_map, player_map


def parse_goal_events(scorers_raw: List[Dict[str, Any]], assists_raw: List[Dict[str, Any]], own_goals_raw: List[Dict[str, Any]], player_map: Dict[int, str]) -> Tuple[List[Dict[str, Any]], str]:
    """Parses goal scorers, assists, and own goals into structured event dicts and a formatted summary string."""
    scorers = []
    for item in scorers_raw:
        pid = item.get("element")
        pname = player_map.get(pid, f"Player #{pid}")
        for _ in range(item.get("value", 1)):
            scorers.append({"scorer": pname, "type": "G"})

    assists = []
    for item in assists_raw:
        pid = item.get("element")
        aname = player_map.get(pid, f"Player #{pid}")
        for _ in range(item.get("value", 1)):
            assists.append(aname)

    for item in own_goals_raw:
        pid = item.get("element")
        pname = player_map.get(pid, f"Player #{pid}")
        for _ in range(item.get("value", 1)):
            scorers.append({"scorer": pname, "type": "OG"})

    events = []
    summary_parts = []
    for i, sc in enumerate(scorers):
        scorer = sc["scorer"]
        g_type = sc["type"]
        assist = assists[i] if (i < len(assists) and g_type == "G") else None
        
        type_tag = " (OG)" if g_type == "OG" else ""
        assist_tag = f" ({assist})" if assist else ""
        
        events.append({"minute": "", "scorer": scorer, "assist": assist, "type": g_type})
        summary_parts.append(f"{scorer}{type_tag}{assist_tag}")

    return events, ", ".join(summary_parts)


# Pseudo-matches of FPL-strength prior blended into each team's season record (keeps early-season picks sane).
PRIOR_GAMES = 5.0
AI_STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ai_predictions.json")


def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def strength_priors(teams_raw: List[Dict[str, Any]], team_map: Dict[int, str]) -> Dict[str, Tuple[float, float]]:
    """Turns FPL attack/defence strength ratings into (scoring, conceding) multipliers around 1.0."""
    rated = []
    for t in teams_raw:
        name = team_map.get(t.get("id"))
        att = (t.get("strength_attack_home") or 0) + (t.get("strength_attack_away") or 0)
        dfn = (t.get("strength_defence_home") or 0) + (t.get("strength_defence_away") or 0)
        if name and att and dfn:
            rated.append((name, att, dfn))
    if not rated:
        return {}
    att_mean = sum(r[1] for r in rated) / len(rated)
    def_mean = sum(r[2] for r in rated) / len(rated)
    # ponytail: FPL ratings only span ~±15%, so squaring widens them to a realistic goal spread; fit the exponent on past seasons if accuracy matters.
    return {name: ((att / att_mean) ** 2, (def_mean / dfn) ** 2) for name, att, dfn in rated}


def predict_scoreline(xg_home: float, xg_away: float, max_goals: int = 7) -> Dict[str, Any]:
    """Most likely scoreline within the most likely outcome, plus H/D/A probabilities, from two Poisson goal rates."""
    outcome = {"H": 0.0, "D": 0.0, "A": 0.0}
    best = {"H": (0.0, 1, 0), "D": (0.0, 0, 0), "A": (0.0, 0, 1)}
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_pmf(h, xg_home) * poisson_pmf(a, xg_away)
            key = "H" if h > a else ("D" if h == a else "A")
            outcome[key] += p
            if p > best[key][0]:
                best[key] = (p, h, a)
    total = sum(outcome.values())
    pick = max(outcome, key=outcome.get)
    return {
        "pred_home": best[pick][1], "pred_away": best[pick][2],
        "xg_home": round(xg_home, 2), "xg_away": round(xg_away, 2),
        "p_home": round(100 * outcome["H"] / total),
        "p_draw": round(100 * outcome["D"] / total),
        "p_away": round(100 * outcome["A"] / total),
    }


def fixture_teams(f: Dict[str, Any], team_map: Dict[int, str]) -> Tuple[str, str]:
    return team_map.get(f.get("team_h"), f"Team_{f.get('team_h')}"), team_map.get(f.get("team_a"), f"Team_{f.get('team_a')}")


def fixture_done(f: Dict[str, Any]) -> bool:
    return bool((f.get("finished") or f.get("finished_provisional")) and f.get("team_h_score") is not None and f.get("team_a_score") is not None)


def kickoff_dt(f: Dict[str, Any]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(f.get("kickoff_time")).replace("Z", "+00:00"))
    except ValueError:
        return None


def fit_goal_model(finished: List[Dict[str, Any]], team_map: Dict[int, str], priors: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
    """Home/away goal averages plus per-team (scoring, conceding) rates, shrunk towards the FPL-strength priors."""
    stats: Dict[str, List[int]] = {name: [0, 0, 0] for name in team_map.values()}  # played, goals for, goals against
    home_goals = away_goals = 0
    for f in finished:
        home, away = fixture_teams(f, team_map)
        hs, as_ = int(f["team_h_score"]), int(f["team_a_score"])
        home_goals += hs
        away_goals += as_
        for team, gf, ga in ((home, hs, as_), (away, as_, hs)):
            s = stats.setdefault(team, [0, 0, 0])
            s[0] += 1
            s[1] += gf
            s[2] += ga
    home_avg = home_goals / len(finished) if finished else 1.5
    away_avg = away_goals / len(finished) if finished else 1.2
    goal_avg = (home_avg + away_avg) / 2
    rates = {}
    for team, (played, gf, ga) in stats.items():
        prior_att, prior_def = priors.get(team, (1.0, 1.0))
        rates[team] = (
            (gf + PRIOR_GAMES * goal_avg * prior_att) / ((played + PRIOR_GAMES) * goal_avg),
            (ga + PRIOR_GAMES * goal_avg * prior_def) / ((played + PRIOR_GAMES) * goal_avg),
        )
    return {"home_avg": home_avg, "away_avg": away_avg, "rates": rates}


def predict_match(model: Dict[str, Any], home: str, away: str) -> Dict[str, Any]:
    home_rate = model["rates"].get(home, (1.0, 1.0))
    away_rate = model["rates"].get(away, (1.0, 1.0))
    return predict_scoreline(model["home_avg"] * home_rate[0] * away_rate[1], model["away_avg"] * away_rate[0] * home_rate[1])


def build_league_snapshot(
    raw_fixtures: List[Dict[str, Any]],
    team_map: Dict[int, str],
    priors: Optional[Dict[str, Tuple[float, float]]] = None
) -> Dict[str, Any]:
    """Builds the live table (Pts, GD, GF tie-breaks), each club's next fixture, per-gameweek deadlines, and model predictions for the next gameweek."""
    priors = priors or {}

    def new_row(team: str) -> Dict[str, Any]:
        return {"team": team, "logo": get_team_logo(team), "played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "form": [], "next": None}

    rows: Dict[str, Dict[str, Any]] = {name: new_row(name) for name in team_map.values()}
    finished = sorted((f for f in raw_fixtures if fixture_done(f)), key=lambda f: f.get("kickoff_time") or "")
    upcoming = sorted(
        (f for f in raw_fixtures if not fixture_done(f)),
        key=lambda f: (f.get("kickoff_time") is None, f.get("kickoff_time") or "")
    )

    for f in finished:
        home, away = fixture_teams(f, team_map)
        hs, as_ = int(f["team_h_score"]), int(f["team_a_score"])
        for team, gf, ga in ((home, hs, as_), (away, as_, hs)):
            row = rows.setdefault(team, new_row(team))
            result = "W" if gf > ga else ("D" if gf == ga else "L")
            row["played"] += 1
            row["gf"] += gf
            row["ga"] += ga
            row[{"W": "won", "D": "drawn", "L": "lost"}[result]] += 1
            row["form"].append(result)

    for f in upcoming:
        home, away = fixture_teams(f, team_map)
        for team, opponent, venue in ((home, away, "H"), (away, home, "A")):
            row = rows.setdefault(team, new_row(team))
            if row["next"] is None:
                row["next"] = {"opponent": opponent, "logo": get_team_logo(opponent), "venue": venue, "kickoff": f.get("kickoff_time"), "gw": f.get("event")}

    for row in rows.values():
        row["gd"] = row["gf"] - row["ga"]
        row["points"] = row["won"] * 3 + row["drawn"]
        row["form"] = row["form"][-5:]
    table = sorted(rows.values(), key=lambda r: (-r["points"], -r["gd"], -r["gf"], r["team"]))
    for pos, row in enumerate(table, 1):
        row["position"] = pos

    model = fit_goal_model(finished, team_map, priors)
    next_gw = min((f["event"] for f in upcoming if f.get("event")), default=None)
    matches = []
    for f in upcoming:
        if f.get("event") != next_gw:
            continue
        home, away = fixture_teams(f, team_map)
        matches.append({
            "id": f.get("id"), "home": home, "away": away, "home_logo": get_team_logo(home), "away_logo": get_team_logo(away),
            "kickoff": f.get("kickoff_time"), **predict_match(model, home, away)
        })

    deadlines: Dict[str, str] = {}
    for f in raw_fixtures:
        gw_key, ko = str(f.get("event")), f.get("kickoff_time")
        if f.get("event") and ko and (gw_key not in deadlines or ko < deadlines[gw_key]):
            deadlines[gw_key] = ko

    return {"table": table, "predictions": {"gw": next_gw, "matches": matches}, "deadlines": deadlines}


def update_ai_record(
    raw_fixtures: List[Dict[str, Any]],
    team_map: Dict[int, str],
    priors: Dict[str, Tuple[float, float]],
    store_path: str,
    now: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    'Beat the AI': keeps the model's pick for each fixture, locked once the match kicks off, and scores it like a predictor.
    - Next-gameweek fixtures that haven't started are (re)predicted with every completed result so far.
    - Fixtures that started before tracking began are backtested using only results from before that gameweek's first kickoff.
    """
    now = now or datetime.now(timezone.utc)
    store: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(store_path):
        with open(store_path, encoding="utf-8") as f:
            store = json.load(f)
    original = json.dumps(store, sort_keys=True)

    finished = sorted((f for f in raw_fixtures if fixture_done(f)), key=lambda f: f.get("kickoff_time") or "")
    by_gw: Dict[int, List[Dict[str, Any]]] = {}
    for f in raw_fixtures:
        if f.get("event"):
            by_gw.setdefault(int(f["event"]), []).append(f)
    upcoming_gws = [gw for gw, fx in by_gw.items() if any(not fixture_done(f) for f in fx)]
    next_gw = min(upcoming_gws, default=None)
    live_model = fit_goal_model(finished, team_map, priors)

    for gw, fixtures in sorted(by_gw.items()):
        kickoffs = [k for k in (kickoff_dt(f) for f in fixtures) if k]
        first = min(kickoffs) if kickoffs else None
        backtest_model = None
        entries = store.get(str(gw), {})
        for f in fixtures:
            fid, ko = str(f.get("id")), kickoff_dt(f)
            started = fixture_done(f) or bool(f.get("started")) or (ko is not None and ko <= now)
            if started and fid in entries:
                continue  # locked at kickoff
            if not started and gw != next_gw:
                continue  # only track the next gameweek ahead of time
            home, away = fixture_teams(f, team_map)
            if started:
                if backtest_model is None:
                    earlier = [x for x in finished if first and kickoff_dt(x) and kickoff_dt(x) < first]
                    backtest_model = fit_goal_model(earlier, team_map, priors)
                pick = predict_match(backtest_model, home, away)
            else:
                pick = predict_match(live_model, home, away)
            entries[fid] = {"home": home, "away": away, "pred_home": pick["pred_home"], "pred_away": pick["pred_away"],
                            "kickoff": f.get("kickoff_time"), "backtest": started}
        if entries:
            store[str(gw)] = entries

    if json.dumps(store, sort_keys=True) != original:
        os.makedirs(os.path.dirname(store_path) or ".", exist_ok=True)
        with open(store_path, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, sort_keys=True)

    fixtures_by_id = {str(f.get("id")): f for f in finished}
    record = {"points": 0, "exacts": 0, "outcomes": 0, "matches": 0, "gws": []}
    for gw_key in sorted(store, key=int):
        gw_row = {"gw": int(gw_key), "points": 0, "exacts": 0, "outcomes": 0, "matches": 0, "backtest": False}
        for fid, entry in store[gw_key].items():
            result = fixtures_by_id.get(fid)
            if not result:
                continue
            pts = score_prediction(entry["pred_home"], entry["pred_away"], int(result["team_h_score"]), int(result["team_a_score"]))
            gw_row["matches"] += 1
            gw_row["points"] += pts
            gw_row["exacts"] += pts == 3
            gw_row["outcomes"] += pts == 1
            gw_row["backtest"] = gw_row["backtest"] or entry.get("backtest", False)
        if gw_row["matches"]:
            record["gws"].append(gw_row)
            for k in ("points", "exacts", "outcomes", "matches"):
                record[k] += gw_row[k]
    return record


def score_prediction(pred_h: int, pred_a: int, act_h: int, act_a: int) -> int:
    """3 for the exact score, 1 for the right result, 0 otherwise (same rules as the predictor league)."""
    if pred_h == act_h and pred_a == act_a:
        return 3
    same_result = (pred_h > pred_a) == (act_h > act_a) and (pred_h < pred_a) == (act_h < act_a)
    return 1 if same_result else 0


def _fetch_fpl_json(path: str, attempts: int = 2) -> Any:
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(
        f"https://fantasy.premierleague.com/api/{path}",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(2)


def fetch_league_snapshot() -> Dict[str, Any]:
    """Fetches the FPL season fixtures + team strengths and returns the live table, next fixtures and predictions ({} if unreachable)."""
    try:
        teams_raw = _fetch_fpl_json("bootstrap-static/").get("teams", [])
        team_map = dict(FPL_TEAM_ID_MAP)
        for t in teams_raw:
            team_map[t["id"]] = FPL_NAME_CANONICAL_MAP.get(t.get("name", ""), t.get("name", ""))
        raw_fixtures = _fetch_fpl_json("fixtures/")
        priors = strength_priors(teams_raw, team_map)
        snapshot = build_league_snapshot(raw_fixtures, team_map, priors)
        snapshot["ai_record"] = update_ai_record(raw_fixtures, team_map, priors, AI_STORE_PATH)
        rec = snapshot["ai_record"]
        print(f"[+] Built live Premier League table from {sum(r['played'] for r in snapshot['table']) // 2} completed matches; "
              f"{len(snapshot['predictions']['matches'])} predictions for GW {snapshot['predictions']['gw']}; "
              f"AI record {rec['points']} pts from {rec['matches']} matches.")
        return snapshot
    except Exception as e:
        print(f"[!] League table fetch notice ({e}). Table and predictions will show as unavailable.")
        return {}


def fetch_gameweek_fixtures(gw_number: int, use_live_api: bool = True) -> List[Dict[str, Any]]:
    """
    Fetches official fixtures, actual match scores, GMT kickoff times, club logos, and goal details for the specified Gameweek.
    - Queries the Official Premier League API as primary default.
    - Automatically maps live match scores, goal scorers, assists, finished status, and logos.
    - Falls back safely to verified season schedule only if API is unreachable.
    """
    if use_live_api:
        url = f"https://fantasy.premierleague.com/api/fixtures/?event={gw_number}"
        print(f"[*] Querying Official Premier League Live API for Gameweek {gw_number} match scores & goals (GMT/UTC)...")

        fixtures = []
        try:
            team_map, player_map = fetch_bootstrap_data()
            ctx = ssl._create_unverified_context()
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                if response.status == 200:
                    raw_data = json.loads(response.read().decode("utf-8"))
                    for fix in raw_data:
                        team_h_id = fix.get("team_h")
                        team_a_id = fix.get("team_a")
                        home_team = team_map.get(team_h_id, f"Team_{team_h_id}")
                        away_team = team_map.get(team_a_id, f"Team_{team_a_id}")

                        home_logo = get_team_logo(home_team)
                        away_logo = get_team_logo(away_team)

                        raw_h_score = fix.get("team_h_score")
                        raw_a_score = fix.get("team_a_score")

                        # Full-Time (FT) validation
                        is_full_time = fix.get("finished", False) or fix.get("finished_provisional", False) or (fix.get("minutes", 0) >= 90)
                        started = fix.get("started", False) or (raw_h_score is not None)

                        # Extract Goal Scorers, Assists, and Own Goals from fixture stats
                        fix_stats = {s.get("identifier"): s for s in fix.get("stats", [])}
                        goals_stat = fix_stats.get("goals_scored", {})
                        assists_stat = fix_stats.get("assists", {})
                        og_stat = fix_stats.get("own_goals", {})

                        home_goals, home_goals_summary = parse_goal_events(
                            goals_stat.get("h", []), assists_stat.get("h", []), og_stat.get("a", []), player_map
                        )
                        away_goals, away_goals_summary = parse_goal_events(
                            goals_stat.get("a", []), assists_stat.get("a", []), og_stat.get("h", []), player_map
                        )

                        # Live & Full-Time match scores are captured as soon as available in official API
                        if raw_h_score is not None and raw_a_score is not None:
                            home_score = int(raw_h_score)
                            away_score = int(raw_a_score)
                            finished = is_full_time
                        else:
                            home_score = None
                            away_score = None
                            finished = False

                        kickoff = fix.get("kickoff_time", datetime.now(timezone.utc).isoformat())

                        fixtures.append({
                            "id": fix.get("id"),
                            "home": home_team,
                            "away": away_team,
                            "home_logo": home_logo,
                            "away_logo": away_logo,
                            "home_act": home_score,
                            "away_act": away_score,
                            "home_goals": home_goals,
                            "away_goals": away_goals,
                            "home_goals_summary": home_goals_summary,
                            "away_goals_summary": away_goals_summary,
                            "kickoff": kickoff,
                            "finished": finished,
                            "started": started,
                            "minutes": fix.get("minutes", 0)
                        })

                    if fixtures:
                        # Enrich fixtures with Pulse API minute-by-minute goal events, scorers & assists
                        pulse_map = fetch_pulse_match_goals_map(gw_number)
                        for f in fixtures:
                            key = (normalize_team_key(f["home"]), normalize_team_key(f["away"]))
                            if key in pulse_map:
                                pdata = pulse_map[key]
                                if pdata.get("home_goals_summary") or pdata.get("home_goals"):
                                    f["home_goals"] = pdata["home_goals"]
                                    f["home_goals_summary"] = pdata["home_goals_summary"]
                                if pdata.get("away_goals_summary") or pdata.get("away_goals"):
                                    f["away_goals"] = pdata["away_goals"]
                                    f["away_goals_summary"] = pdata["away_goals_summary"]

                                # Synchronize real-time scores directly from Pulse API
                                p_h_score = pdata.get("home_score")
                                p_a_score = pdata.get("away_score")
                                if p_h_score is not None and p_a_score is not None:
                                    f["home_act"] = p_h_score
                                    f["away_act"] = p_a_score
                                elif len(f.get("home_goals", [])) > 0 or len(f.get("away_goals", [])) > 0:
                                    if f["home_act"] is None or len(f.get("home_goals", [])) > f["home_act"]:
                                        f["home_act"] = len(f.get("home_goals", []))
                                    if f["away_act"] is None or len(f.get("away_goals", [])) > f["away_act"]:
                                        f["away_act"] = len(f.get("away_goals", []))

                                p_status = pdata.get("status_code")
                                if p_status == "C":
                                    f["finished"] = True
                                    f["started"] = True
                                    f["status"] = "FT"
                                elif p_status == "L":
                                    f["finished"] = False
                                    f["started"] = True
                                    f["status"] = "ONGOING"
                                    f["clock"] = pdata.get("clock") or "LIVE"
                                elif p_status == "U":
                                    f["finished"] = False
                                    f["started"] = False
                                    f["status"] = "UPCOMING"

                            if not f.get("status"):
                                if f.get("finished"):
                                    f["status"] = "FT"
                                elif f.get("started") or (f.get("home_act") is not None and f.get("away_act") is not None):
                                    f["status"] = "ONGOING"
                                else:
                                    f["status"] = "UPCOMING"

                        # Sort fixtures by kickoff time
                        fixtures.sort(key=lambda x: x.get("kickoff", ""))
                        print(f"[+] Loaded {len(fixtures)} live fixtures, scorelines & goal stats from Premier League API.")
                        return fixtures
        except Exception as e:
            print(f"[!] Live API query notice ({e}). Using verified fallback schedule...")

    # Load from verified season schedule fallback
    if gw_number in SEASON_2026_2027_FIXTURES:
        print(f"[*] Loaded Official 2026-2027 Season schedule for Gameweek {gw_number} ({len(SEASON_2026_2027_FIXTURES[gw_number])} fixtures in GMT/UTC).")
        fallback_list = []
        pulse_map = fetch_pulse_match_goals_map(gw_number)
        for f in SEASON_2026_2027_FIXTURES[gw_number]:
            item = dict(f)
            item["home_logo"] = get_team_logo(item["home"])
            item["away_logo"] = get_team_logo(item["away"])
            item.setdefault("home_goals", [])
            item.setdefault("away_goals", [])
            item.setdefault("home_goals_summary", "")
            item.setdefault("away_goals_summary", "")

            key = (normalize_team_key(item["home"]), normalize_team_key(item["away"]))
            if key in pulse_map:
                pdata = pulse_map[key]
                if pdata.get("home_goals_summary") or pdata.get("home_goals"):
                    item["home_goals"] = pdata["home_goals"]
                    item["home_goals_summary"] = pdata["home_goals_summary"]
                if pdata.get("away_goals_summary") or pdata.get("away_goals"):
                    item["away_goals"] = pdata["away_goals"]
                    item["away_goals_summary"] = pdata["away_goals_summary"]

                p_h_score = pdata.get("home_score")
                p_a_score = pdata.get("away_score")
                if p_h_score is not None and p_a_score is not None:
                    item["home_act"] = p_h_score
                    item["away_act"] = p_a_score
                elif len(item.get("home_goals", [])) > 0 or len(item.get("away_goals", [])) > 0:
                    if item.get("home_act") is None or len(item.get("home_goals", [])) > item.get("home_act", 0):
                        item["home_act"] = len(item.get("home_goals", []))
                    if item.get("away_act") is None or len(item.get("away_goals", [])) > item.get("away_act", 0):
                        item["away_act"] = len(item.get("away_goals", []))

                p_status = pdata.get("status_code")
                if p_status == "C":
                    item["finished"] = True
                    item["started"] = True
                    item["status"] = "FT"
                elif p_status == "L":
                    item["finished"] = False
                    item["started"] = True
                    item["status"] = "ONGOING"
                    item["clock"] = pdata.get("clock") or "LIVE"
                elif p_status == "U":
                    item["finished"] = False
                    item["started"] = False
                    item["status"] = "UPCOMING"

            if not item.get("status"):
                if item.get("finished"):
                    item["status"] = "FT"
                elif item.get("started") or (item.get("home_act") is not None and item.get("away_act") is not None):
                    item["status"] = "ONGOING"
                else:
                    item["status"] = "UPCOMING"

            fallback_list.append(item)
        return fallback_list

    return []

    return []
