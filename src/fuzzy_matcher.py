"""
Fuzzy Matcher and Typo Detection Engine
Identifies spelling mistakes, phonetic similarities, and alternative team spellings
with confidence scoring (75% to 100% confidence) for Admin Approval.
Strictly filters out conversational noise lines (e.g. 'Missed these', 'My predictions').
"""
import re
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional, Tuple

ALL_CLUBS = [
    "Arsenal", "Aston Villa", "AFC Bournemouth", "Brentford", "Brighton & Hove Albion",
    "Chelsea", "Coventry City", "Crystal Palace", "Everton", "Fulham",
    "Hull City", "Ipswich Town", "Leeds United", "Liverpool", "Manchester City",
    "Manchester United", "Newcastle United", "Nottingham Forest", "Sunderland", "Tottenham Hotspur"
]

CLUB_VARIANTS = {
    "Arsenal": ["arsenal", "arsnl", "arsnal", "gunners", "afc", "ars"],
    "Aston Villa": ["aston villa", "villa", "aston", "avfc", "vilians", "astnvilla"],
    "AFC Bournemouth": ["bournemouth", "bmouth", "bournmouth", "cherries", "afcb", "bmth", "bourn"],
    "Brentford": ["brentford", "brentfrd", "bees", "brent", "brenford"],
    "Brighton & Hove Albion": ["brighton", "brightn", "seagulls", "bha", "brighton & hove", "bright"],
    "Chelsea": ["chelsea", "chelsa", "chelski", "blues", "cfc", "chels"],
    "Coventry City": ["coventry", "coventry city", "cov", "covntry", "sky blues", "coventrycty"],
    "Crystal Palace": ["crystal palace", "palace", "cpfc", "eagles", "crystal", "crystl palace"],
    "Everton": ["everton", "evrton", "toffees", "efc", "evertn", "evrtn"],
    "Fulham": ["fulham", "fulhm", "cottagers", "ffc", "fulm"],
    "Hull City": ["hull", "hull city", "tigers", "hullcity", "hullcty"],
    "Ipswich Town": ["ipswich", "ipswich town", "tractor boys", "itfc", "ipswch", "ipsw", "ipswich tn"],
    "Leeds United": ["leeds", "leeds united", "lufc", "peacocks", "leed", "leeds utd"],
    "Liverpool": ["liverpool", "lfc", "reds", "liv", "liverpl", "pool", "livrpool"],
    "Manchester City": ["man city", "manchester city", "city", "mcfc", "citizens", "mancity", "mn city"],
    "Manchester United": ["man utd", "manchester united", "united", "mufc", "red devils", "manutd", "man u", "mn utd"],
    "Newcastle United": ["newcastle", "newcastle united", "nufc", "magpies", "newcstle", "toon", "newc utd"],
    "Nottingham Forest": ["nottingham forest", "forest", "nffc", "notts forest", "nottm forest", "forrest", "nott forest"],
    "Sunderland": ["sunderland", "safc", "black cats", "sundrland", "sunderlnd", "sundland"],
    "Tottenham Hotspur": ["tottenham", "spurs", "tottenham hotspur", "thfc", "totenham", "hotspur", "totnham"]
}

# Blacklist of conversational non-prediction phrases
NOISE_PATTERNS = [
    r"^missed\s+these", r"^my\s+predictions", r"^predictions", r"^gw\s*\d+", r"^gameweek\s*\d+",
    r"^table", r"^good\s+luck", r"^great\s+video", r"^sub\s+count", r"^subscribers",
    r"^late\s+predictions", r"^scores", r"^results"
]


def compute_string_similarity(a: str, b: str) -> float:
    """Returns normalized SequenceMatcher similarity ratio between two lowercase strings (0.0 to 1.0)."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def match_team_fuzzy(word: str) -> Tuple[Optional[str], float]:
    """
    Compares an input word/phrase against all 20 clubs and known spelling variants.
    Returns (Best Canonical Team Name, Confidence Float 0.0 to 1.0).
    Requires word length >= 3 and strict confidence threshold >= 0.75.
    """
    w_clean = re.sub(r"[^\w\s&]", "", word).strip().lower()
    if not w_clean or len(w_clean) < 3:
        return None, 0.0

    # Strip conversational noise prefix e.g. "missed these: arsenal" -> "arsenal"
    for np in NOISE_PATTERNS:
        w_clean = re.sub(np, "", w_clean).strip()
    if not w_clean or len(w_clean) < 3:
        return None, 0.0

    best_team = None
    best_score = 0.0

    for club, variants in CLUB_VARIANTS.items():
        score = compute_string_similarity(w_clean, club.lower())
        if score > best_score:
            best_score = score
            best_team = club

        for v in variants:
            v_score = compute_string_similarity(w_clean, v)
            if w_clean == v:
                v_score = 1.0
            elif len(w_clean) >= 4 and len(v) >= 4:
                if w_clean.startswith(v) or v.startswith(w_clean):
                    v_score = max(v_score, 0.82)

            if v_score > best_score:
                best_score = v_score
                best_team = club

    if best_score >= 0.75:
        return best_team, best_score
    return None, 0.0


def detect_fuzzy_prediction_candidates(
    comment_text: str,
    fixtures: List[Dict[str, Any]],
    author: str,
    comment_id: str,
    published_at: str,
    existing_exact_pairs: List[Tuple[str, str]],
    existing_exact_preds: Dict[str, str],
    gw_number: int
) -> List[Dict[str, Any]]:
    """
    Scans lines that failed exact regex parsing and identifies strictly legitimate >= 75% candidates.
    Rejects conversational noise lines (e.g. 'Missed these').
    """
    if not isinstance(comment_text, str) or not comment_text.strip():
        return []

    lines = re.split(r'[\r\n;]+', comment_text)
    candidates = []
    seen_fixture_keys = set(existing_exact_pairs)

    # Tight score pattern: must have explicit separator e.g. 2-1, 2:1, 2 - 1, 2 to 1, 2v1
    score_regex = re.compile(r'(\b\d{1,2}\b)\s*(?:[\-\:\–\—\/]|to|v|\-)\s*(\b\d{1,2}\b)', re.IGNORECASE)

    for line in lines:
        line_clean = line.strip()
        if not line_clean or len(line_clean) < 4:
            continue

        # Skip pure noise lines
        is_noise = False
        for np in NOISE_PATTERNS:
            if re.search(np, line_clean, re.IGNORECASE) and not re.search(r'\b(?:vs|v|-)\b', line_clean):
                is_noise = True
                break
        if is_noise:
            continue

        score_match = score_regex.search(line_clean)
        if not score_match:
            continue

        s1 = int(score_match.group(1))
        s2 = int(score_match.group(2))
        
        # Valid football score range: 0 to 15
        if s1 > 15 or s2 > 15:
            continue

        start_idx, end_idx = score_match.span()
        left_text = line_clean[:start_idx].strip()
        right_text = line_clean[end_idx:].strip()

        # Clean noise prefixes from left text e.g. "Missed these - Arsenal"
        for np in NOISE_PATTERNS:
            left_text = re.sub(np, "", left_text, flags=re.IGNORECASE).strip(" :-–—")

        team1, conf1 = match_team_fuzzy(left_text)
        team2, conf2 = match_team_fuzzy(right_text)

        # If right text was empty or didn't match, check if left text had both teams e.g. "Arsnl vs Cov 3-0"
        if not team2 or conf2 < 0.75:
            tokens = re.split(r'\s+(?:vs\.?|v\.?|-|against)\s+', left_text, flags=re.IGNORECASE)
            if len(tokens) == 2:
                team1, conf1 = match_team_fuzzy(tokens[0])
                team2, conf2 = match_team_fuzzy(tokens[1])

        # Strict Requirement: Both teams must match canonical clubs with >= 0.75 individual confidence
        if not team1 or not team2 or team1 == team2 or conf1 < 0.75 or conf2 < 0.75:
            continue

        avg_conf = (conf1 + conf2) / 2.0
        conf_pct = int(round(avg_conf * 100))

        for f in fixtures:
            h, a = f["home"], f["away"]
            fix_id = f["id"]
            pair_key = (h, a)

            if pair_key in seen_fixture_keys:
                continue

            if (team1 == h and team2 == a) or (team1 == a and team2 == h):
                if team1 == h and team2 == a:
                    pred_h, pred_a = s1, s2
                else:
                    pred_h, pred_a = s2, s1

                if conf_pct >= 75:
                    cand_id = f"cand_gw{gw_number}_{re.sub(r'[^a-zA-Z0-9]', '', author)}_{fix_id}"
                    candidate_obj = {
                        "id": cand_id,
                        "gameweek": gw_number,
                        "author": author,
                        "comment_id": comment_id,
                        "published_at": published_at,
                        "raw_line": line_clean,
                        "full_comment": comment_text.strip(),
                        "other_predictions": existing_exact_preds,
                        "fixture_id": fix_id,
                        "home_team": h,
                        "away_team": a,
                        "pred_home": pred_h,
                        "pred_away": pred_a,
                        "confidence": conf_pct,
                        "detected_teams": f"{team1} vs {team2}",
                        "gameweek": gw_number,
                        "status": "pending"
                    }
                    candidates.append(candidate_obj)
                    seen_fixture_keys.add(pair_key)
                break

    return candidates
