"""
Fuzzy Matcher and Typo Detection Engine
Identifies spelling mistakes, phonetic similarities, and alternative team spellings
with confidence scoring (50% to 100% confidence) for Admin Approval.
Strictly filters out conversational noise lines (e.g. 'Missed these', 'My predictions').
"""
import re
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional, Tuple

from src.nlp_parser import MAX_AUTO_GOALS, normalize_comment_text
from src.team_aliases import build_alias_lookup

# Minimum team-name similarity for a typo line to reach the admin review queue.
REVIEW_MIN_CONFIDENCE = 0.50
# Bar for trusting that the text after a score is a team before trying to split the text before it.
STRICT_TEAM_CONFIDENCE = 0.75

# Tight score pattern: must have explicit separator e.g. 2-1, 2:1, 2 - 1, 2 to 1, 2v1, 2x1, 1 vs 1
SCORE_REGEX = re.compile(r'(?<!\d)(\d{1,2})\s*(?:vs\.?|v|x|to|[\-:/=~]+)\s*(\d{1,2})(?!\d)', re.IGNORECASE)
# A scoreline inside a sentence: "Everton win 1-0", "(2-1 liverpool)"
PROSE_SCORE_REGEX = re.compile(r'(?<!\d)(\d{1,2})\s*(?:[\-:=~]|to|x)\s*(\d{1,2})(?!\d)', re.IGNORECASE)

ALL_CLUBS = [
    "Arsenal", "Aston Villa", "AFC Bournemouth", "Brentford", "Brighton & Hove Albion",
    "Chelsea", "Coventry City", "Crystal Palace", "Everton", "Fulham",
    "Hull City", "Ipswich Town", "Leeds United", "Liverpool", "Manchester City",
    "Manchester United", "Newcastle United", "Nottingham Forest", "Sunderland", "Tottenham Hotspur"
]

CLUB_VARIANTS = {
    "Arsenal": ["arsenal", "arsnl", "arsnal", "gunners", "afc", "ars", "aresnal", "arc"],
    "Aston Villa": ["aston villa", "villa", "aston", "avfc", "vilians", "astnvilla", "aston v", "a villa"],
    "AFC Bournemouth": ["bournemouth", "bmouth", "bournmouth", "b'mouth", "b’mouth", "cherries", "afcb", "bmth", "bourn", "bouremouth", "afc bmouth"],
    "Brentford": ["brentford", "brentfrd", "bees", "brent", "brenford"],
    "Brighton & Hove Albion": ["brighton", "brightn", "seagulls", "bha", "brighton & hove", "brighton and hove", "brighton hove albion", "bright", "bhafc"],
    "Chelsea": ["chelsea", "chelsa", "chelski", "blues", "cfc", "chels"],
    "Coventry City": ["coventry", "coventry city", "cov", "covntry", "sky blues", "coventrycty", "ccfc"],
    "Crystal Palace": ["crystal palace", "palace", "cpfc", "eagles", "crystal", "crystl palace", "c palace", "c.palace", "crystal p"],
    "Everton": ["everton", "evrton", "toffees", "efc", "evertn", "evrtn"],
    "Fulham": ["fulham", "fulhm", "cottagers", "ffc", "fulm", "fullham"],
    "Hull City": ["hull", "hull city", "tigers", "hullcity", "hullcty", "hcfc"],
    "Ipswich Town": ["ipswich", "ipswich town", "tractor boys", "itfc", "ipswch", "ipsw", "ipswich tn", "ipswitch"],
    "Leeds United": ["leeds", "leeds united", "lufc", "peacocks", "leed", "leeds utd"],
    "Liverpool": ["liverpool", "lfc", "reds", "liv", "liverpl", "pool", "livrpool"],
    "Manchester City": ["man city", "manchester city", "city", "mcfc", "citizens", "mancity", "mn city", "man c", "manc", "man. city"],
    "Manchester United": ["man utd", "manchester united", "united", "mufc", "red devils", "manutd", "man u", "mn utd", "manu", "man. united", "man. utd"],
    "Newcastle United": ["newcastle", "newcastle united", "newcastle utd", "nufc", "magpies", "newcstle", "toon", "newc utd"],
    "Nottingham Forest": ["nottingham forest", "forest", "nffc", "notts forest", "nottm forest", "forrest", "nott forest", "nott'm forest", "nottm", "nott'm", "n. forest", "n.forest", "nott. forest"],
    "Sunderland": ["sunderland", "safc", "black cats", "sundrland", "sunderlnd", "sundland"],
    "Tottenham Hotspur": ["tottenham", "spurs", "tottenham hotspur", "thfc", "totenham", "hotspur", "totnham", "spurs fc"]
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
    Requires word length >= 3 and confidence >= REVIEW_MIN_CONFIDENCE.
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

    if best_score >= REVIEW_MIN_CONFIDENCE:
        return best_team, best_score
    return None, 0.0


def _fixture_for(fixtures: List[Dict[str, Any]], team1: str, team2: str) -> Optional[Dict[str, Any]]:
    for f in fixtures:
        if {team1, team2} == {f["home"], f["away"]}:
            return f
    return None


def _queue(found: List[Dict[str, Any]], ctx: Dict[str, Any], fixture: Dict[str, Any],
           team1: str, scores: Tuple[int, int], conf_pct: int, raw_line: str, reason: str) -> None:
    """Adds one admin-review candidate unless that fixture is already parsed or queued for this comment."""
    h, a = fixture["home"], fixture["away"]
    if (h, a) in ctx["seen"]:
        return
    s1, s2 = scores
    pred_h, pred_a = (s1, s2) if team1 == h else (s2, s1)
    team2 = a if team1 == h else h
    if max(s1, s2) > MAX_AUTO_GOALS:
        reason, conf_pct = "unusual score", min(conf_pct, 50)
    fix_id = fixture["id"]
    found.append({
        "id": f"cand_gw{ctx['gw']}_{re.sub(r'[^a-zA-Z0-9]', '', ctx['author'])}_{fix_id}",
        "gameweek": ctx["gw"],
        "author": ctx["author"],
        "comment_id": ctx["comment_id"],
        "published_at": ctx["published_at"],
        "raw_line": raw_line,
        "full_comment": ctx["full_comment"],
        "other_predictions": ctx["other_predictions"],
        "fixture_id": fix_id,
        "home_team": h,
        "away_team": a,
        "pred_home": pred_h,
        "pred_away": pred_a,
        "confidence": conf_pct,
        "detected_teams": f"{team1} vs {team2}",
        "reason": reason,
        "status": "pending"
    })
    ctx["seen"].add((h, a))


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
    Scans lines that failed exact regex parsing and queues anything that looks like a prediction for admin review:
    typos, extra words on a team name, prose ("Everton win 1-0"), and unusual scores (10+ goals).
    Rejects conversational noise lines (e.g. 'Missed these'). Supports multiple fuzzy predictions per line.
    """
    if not isinstance(comment_text, str) or not comment_text.strip():
        return []

    lines = re.split(r'[\r\n;]+', normalize_comment_text(comment_text))
    candidates: List[Dict[str, Any]] = []
    ctx = {
        "gw": gw_number, "author": author, "comment_id": comment_id, "published_at": published_at,
        "full_comment": comment_text.strip(), "other_predictions": existing_exact_preds,
        "seen": set(existing_exact_pairs),
    }

    # Prose first: when both clubs are spelled correctly, "(3-1 everton)" decides who scored 3, not word order.
    _prose_candidates(lines, fixtures, ctx, candidates)
    _typo_candidates(lines, fixtures, ctx, candidates)
    _extra_word_candidates(lines, fixtures, ctx, candidates)
    _loose_candidates(lines, fixtures, ctx, candidates)
    return candidates


def _typo_candidates(lines: List[str], fixtures: List[Dict[str, Any]], ctx: Dict[str, Any], found: List[Dict[str, Any]]) -> None:
    """Misspelled team names around an explicit scoreline: '2-1', '2:1', '2 - 1', '2 to 1', '2v1', '2x1', '1 vs 1'."""
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

        score_matches = list(SCORE_REGEX.finditer(line_clean))
        if not score_matches:
            continue

        for i, score_match in enumerate(score_matches):
            s1 = int(score_match.group(1))
            s2 = int(score_match.group(2))

            start_idx, end_idx = score_match.span()
            # Context boundaries bounded by adjacent score matches or line ends
            prev_bound = score_matches[i - 1].end() if i > 0 else 0
            next_bound = score_matches[i + 1].start() if i + 1 < len(score_matches) else len(line_clean)

            left_text = line_clean[prev_bound:start_idx].strip(" ,;|.")
            right_text = line_clean[end_idx:next_bound].strip(" ,;|.")

            # Clean noise prefixes from left text e.g. "Missed these - Arsenal"
            for np in NOISE_PATTERNS:
                left_text = re.sub(np, "", left_text, flags=re.IGNORECASE).strip(" :-–—.")

            team1, conf1 = match_team_fuzzy(left_text)
            team2, conf2 = match_team_fuzzy(right_text)

            # If right text was empty or didn't match, check if left text had both teams e.g. "Arsnl vs Cov 3-0" or "Everton Palace 1-1"
            if not team2 or conf2 < STRICT_TEAM_CONFIDENCE:
                tokens = re.split(r'\s+(?:vs\.?|v\.?|-|against)\s+', left_text, flags=re.IGNORECASE)
                if len(tokens) == 2:
                    team1, conf1 = match_team_fuzzy(tokens[0])
                    team2, conf2 = match_team_fuzzy(tokens[1])
                else:
                    # Try splitting left_text by space at different word boundaries
                    words = left_text.split()
                    if len(words) >= 2:
                        best_pair_score = 0.0
                        for split_pos in range(1, len(words)):
                            t1_cand_text = " ".join(words[:split_pos])
                            t2_cand_text = " ".join(words[split_pos:])
                            cand_t1, cand_c1 = match_team_fuzzy(t1_cand_text)
                            cand_t2, cand_c2 = match_team_fuzzy(t2_cand_text)
                            if cand_t1 and cand_t2 and cand_t1 != cand_t2 and cand_c1 >= REVIEW_MIN_CONFIDENCE and cand_c2 >= REVIEW_MIN_CONFIDENCE:
                                avg = (cand_c1 + cand_c2) / 2.0
                                if avg > best_pair_score:
                                    best_pair_score = avg
                                    team1, conf1 = cand_t1, cand_c1
                                    team2, conf2 = cand_t2, cand_c2

            # Both teams must match canonical clubs with >= REVIEW_MIN_CONFIDENCE individual confidence
            if not team1 or not team2 or team1 == team2 or conf1 < REVIEW_MIN_CONFIDENCE or conf2 < REVIEW_MIN_CONFIDENCE:
                continue

            conf_pct = int(round((conf1 + conf2) / 2.0 * 100))
            fixture = _fixture_for(fixtures, team1, team2)
            if fixture and conf_pct >= REVIEW_MIN_CONFIDENCE * 100:
                raw_line = f"{left_text} {s1}-{s2} {right_text}".strip()
                _queue(found, ctx, fixture, team1, (s1, s2), conf_pct, raw_line, "typo")


def _extra_word_candidates(lines: List[str], fixtures: List[Dict[str, Any]], ctx: Dict[str, Any], found: List[Dict[str, Any]]) -> None:
    """A team, then a word that is not part of that club, then a score; on either team. Admin decides."""
    alias_to_canonical, sorted_aliases = build_alias_lookup()
    if not sorted_aliases:
        return
    alias_pattern = "|".join(re.escape(a) for a in sorted_aliases)
    extra = r"([A-Za-z][A-Za-z'.]*(?:\s+[A-Za-z][A-Za-z'.]*){0,2})"
    # "Sunderland united 0 Arsenal 2"
    lead = re.compile(
        rf"(?:^|\b|\d+\.?\s*)({alias_pattern})\s+{extra}\s+(\d{{1,2}})\s*(?:vs\.?|v(?![A-Za-z]))?\s*({alias_pattern})\s+(\d{{1,2}})(?:\b|$)",
        re.IGNORECASE,
    )
    # "Manchester city 2 Sunderland united 0", "Chelsea 2 Bournemouth AFC 1"
    trail = re.compile(
        rf"(?:^|\b|\d+\.?\s*)({alias_pattern})\s+(\d{{1,2}})\s*(?:vs\.?|v(?![A-Za-z]))?\s*({alias_pattern})\s+{extra}\s+(\d{{1,2}})(?:\b|$)",
        re.IGNORECASE,
    )
    skip_words = {"vs", "v", "against"}
    for line in lines:
        line_clean = line.strip()
        if len(line_clean) < 4:
            continue
        found_here = [(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(1)) for m in lead.finditer(line_clean)]
        found_here += [(m.group(1), m.group(4), m.group(2), m.group(3), m.group(5), m.group(3)) for m in trail.finditer(line_clean)]
        for t1_raw, extra_words, s1_raw, t2_raw, s2_raw, padded_raw in found_here:
            if any(word.lower().rstrip(".") in skip_words or len(word) < 2 for word in extra_words.split()):
                continue
            if f"{padded_raw} {extra_words}".strip().lower() in alias_to_canonical:
                continue
            team1 = alias_to_canonical.get(t1_raw.lower())
            team2 = alias_to_canonical.get(t2_raw.lower())
            if not team1 or not team2 or team1 == team2:
                continue
            s1, s2 = int(s1_raw), int(s2_raw)
            fixture = _fixture_for(fixtures, team1, team2)
            if fixture:
                _queue(found, ctx, fixture, team1, (s1, s2), 75, line_clean, "extra word")


def _team_options(words: List[str], from_end: bool) -> List[str]:
    picks = [words[-k:] if from_end else words[:k] for k in range(1, min(3, len(words)) + 1)]
    return [" ".join(p) for p in picks]


def _loose_candidates(lines: List[str], fixtures: List[Dict[str, Any]], ctx: Dict[str, Any], found: List[Dict[str, Any]]) -> None:
    """'Team N Team N' with a typo and no score separator: 'Fulham 1 Machester United 0', 'Crystal place 2- Manchester city 1'."""
    for line in lines:
        parts = re.split(r"(\d+)", line.strip())
        for i in range(1, len(parts) - 2, 2):
            n1, mid, n2 = parts[i], parts[i + 1], parts[i + 2]
            if len(n1) > 2 or len(n2) > 2:
                continue
            left_words = re.findall(r"[A-Za-z][A-Za-z'&.]*", parts[i - 1])
            right_words = re.findall(r"[A-Za-z][A-Za-z'&.]*", mid)
            if not left_words or not right_words:
                continue
            options = []
            for left in _team_options(left_words, from_end=True):
                t1, c1 = match_team_fuzzy(left)
                for right in _team_options(right_words, from_end=False):
                    t2, c2 = match_team_fuzzy(right)
                    if t1 and t2 and t1 != t2 and min(c1, c2) >= STRICT_TEAM_CONFIDENCE:
                        options.append(((c1 + c2) / 2.0, t1, t2))
            for avg, t1, t2 in sorted(options, reverse=True):
                fixture = _fixture_for(fixtures, t1, t2)
                if fixture:
                    _queue(found, ctx, fixture, t1, (int(n1), int(n2)), int(round(avg * 100)), line.strip(), "typo")
                    break


def _club_of(match: Optional["re.Match[str]"], alias_to_canonical: Dict[str, str]) -> Optional[str]:
    return alias_to_canonical.get(match.group(1).lower()) if match else None


def _prose_candidates(lines: List[str], fixtures: List[Dict[str, Any]], ctx: Dict[str, Any], found: List[Dict[str, Any]]) -> None:
    """Both clubs of one fixture and one scoreline in a sentence ('Everton vs Palace - Everton win 1-0'). Best guess, admin confirms."""
    alias_to_canonical, sorted_aliases = build_alias_lookup()
    if not sorted_aliases:
        return
    alias_pattern = "|".join(re.escape(a) for a in sorted_aliases)
    mention_re = re.compile(rf"(?<![A-Za-z])({alias_pattern})(?![A-Za-z])", re.IGNORECASE)
    after_re = re.compile(rf"[\s(),.:\-]*({alias_pattern})(?![A-Za-z])", re.IGNORECASE)
    before_re = re.compile(rf"(?<![A-Za-z])({alias_pattern})[\s(),.:\-]*$", re.IGNORECASE)
    win_re = re.compile(rf"(?<![A-Za-z])({alias_pattern})\s+(?:to\s+)?(?:wins?|victory)(?![A-Za-z])", re.IGNORECASE)
    for line in lines:
        line_clean = line.strip()
        scores = list(PROSE_SCORE_REGEX.finditer(line_clean))
        if len(scores) != 1:
            continue
        mentioned = []
        for m in mention_re.finditer(line_clean):
            club = alias_to_canonical.get(m.group(1).lower())
            if club and club not in mentioned:
                mentioned.append(club)
        matches = [f for f in fixtures if f["home"] in mentioned and f["away"] in mentioned]
        if len(matches) != 1:
            continue
        fixture = matches[0]
        pair = (fixture["home"], fixture["away"])
        score = scores[0]
        s1, s2 = int(score.group(1)), int(score.group(2))

        winner = _club_of(after_re.match(line_clean, score.end()), alias_to_canonical)
        if winner not in pair:
            winner = _club_of(win_re.search(line_clean), alias_to_canonical)
        before_score = {alias_to_canonical.get(m.group(1).lower()) for m in mention_re.finditer(line_clean[:score.start()])}
        if winner in pair:
            team1, ordered = winner, (max(s1, s2), min(s1, s2))
        elif set(pair) <= before_score:
            # "Bournemouth v Everton 14-1": scores follow the order the clubs were named.
            team1, ordered = min(pair, key=mentioned.index), (s1, s2)
        else:
            # "Hull 1-0 up against united": the club written right before the score owns the first number.
            first = _club_of(before_re.search(line_clean[:score.start()]), alias_to_canonical)
            team1 = first if first in pair else min(pair, key=mentioned.index)
            ordered = (s1, s2)
        _queue(found, ctx, fixture, team1, ordered, 60, line_clean, "prose")


