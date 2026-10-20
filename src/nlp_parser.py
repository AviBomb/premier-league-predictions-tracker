"""
NLP Parser and Multi-Pattern Prediction Extraction Engine
Isolates fixture predictions from banter, alternative delimiters, and reversed ordering.
Supports multi-match single-line comments, numbered predictions, and custom delimiters.
"""
import re
import unicodedata
from typing import List, Dict, Any, Optional
from src.team_aliases import parse_team, build_alias_lookup

# Higher scores are almost always jokes ("Palace 50 City 15"); the admin queue decides those.
MAX_AUTO_GOALS = 9

NUM = r"(?<!\d)(\d{1,2})(?!\d)"
# Between the two numbers of a scoreline: "2-1", "2:1", "2--1", "2=1", "2x1", "2 vs 1", "2 to 1", "2 1".
SCORE_SEP = r"\s*(?:vs\.?|v(?![A-Za-z])|x(?![A-Za-z])|to(?![A-Za-z])|[\-:/=~]+|\s)\s*"
# Between a team and a number, or two teams: spaces, punctuation and the words vs / v / against.
JOIN = r"(?:\s|[,:\-/=~|()'.>]|vs\.?(?![A-Za-z])|v(?![A-Za-z])|against(?![A-Za-z]))*"
# "1 Aston Villa Liverpool 2" stays strict so list numbers ("3. Arsenal Chelsea 2-1") are not read as scores.
STRICT_JOIN = r"(?:\s|[:\-/.]|vs\.?(?![A-Za-z])|v(?![A-Za-z]))*"
# Regex group numbers of the two team names in patterns where they sit next to each other.
ADJACENT_TEAM_GROUPS = {2: (3, 4), 3: (2, 3), 4: (1, 2)}
TIMESTAMP_RE = re.compile(r"(?<![\d:])\d{1,2}:\d{2}(?::\d{2})?(?![\d:])")


def normalize_comment_text(text: str) -> str:
    """Unicode quotes/dashes/styled digits to ASCII, 'versus' to 'vs', video timestamps removed."""
    clean = unicodedata.normalize("NFKD", text)
    clean = "".join(ch for ch in clean if not unicodedata.combining(ch))
    clean = clean.replace("’", "'").replace("‘", "'").replace("`", "'")
    clean = clean.replace("–", "-").replace("—", "-").replace("−", "-")
    clean = clean.replace("\u00a0", " ")
    clean = re.sub(r"(?<![A-Za-z])versus(?![A-Za-z])", "vs", clean, flags=re.IGNORECASE)
    return TIMESTAMP_RE.sub(" ", clean)


def _merge_same_club(line: str, merge_re: "re.Pattern[str]", lookup: Dict[str, str]) -> str:
    """'Crystal Pallace' / 'Nottm Forrest' -> one team token. Mixed clubs ('Sunderland united') stay as typed."""
    out, last = [], 0
    for m in merge_re.finditer(line):
        if m.start(1) < last:
            continue
        club = lookup.get(m.group(1).lower())
        if club and club == lookup.get(m.group(2).lower()):
            out.append(line[last:m.end(1)])
            last = m.end(2)
    out.append(line[last:])
    return "".join(out)


def extract_predictions_from_comment(text: str, fixtures: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Extracts structured fixture predictions from noisy comment text.
    Handles delimiters (-, vs, v, x, :, /, =, ~, to, commas, spaces), either score order,
    multi-lines, single-line concatenated predictions, and banter.
    When `fixtures` is given, only pairs that are real fixtures can claim text.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    clean_text = normalize_comment_text(text)
    fixture_pairs = {frozenset((f["home"], f["away"])) for f in fixtures} if fixtures else None

    alias_to_canonical, sorted_aliases = build_alias_lookup()
    alias_pattern = "|".join(re.escape(a) for a in sorted_aliases)
    # Letters may not touch a team name, except a stray "v" ("Arsenalv Leeds", "0-3 varsenal").
    team = rf"(?<![A-Za-z])v?({alias_pattern})(?:(?![A-Za-z])|(?=v(?![A-Za-z])))"
    merge_re = re.compile(rf"(?<![A-Za-z])({alias_pattern})(?=[\s.]+({alias_pattern})(?![A-Za-z]))", re.IGNORECASE)
    # A different club immediately before a match means the user stuck an extra word
    # on that club ("Sunderland united 0 Arsenal 2"). Leave it for the typo queue.
    prev_team_re = re.compile(rf"(?<![A-Za-z])({alias_pattern})\s+$", re.IGNORECASE)
    trailing_team_re = re.compile(rf"\s*{team}", re.IGNORECASE)

    lines = re.split(r'[\r\n;]+', clean_text)

    # (group order id, pattern). Group order: 0 = t1 s1 s2 t2, 1 = t1 s1 t2 s2, 2 = s1 s2 t1 t2, 3 = s1 t1 t2 s2, 4 = t1 t2 s1 s2
    patterns = [
        # "Aston Villa 2 - 1 Liverpool", "Everton 1 vs 3 Chelsea", "Arsenal 2x0 Coventry"
        (0, re.compile(rf"{team}{JOIN}{NUM}{SCORE_SEP}{NUM}{JOIN}{team}", re.IGNORECASE)),
        # "Man United 2 Forest 1", "Everton 2 vs Chelsea 2", "Arsenal 3, Coventry City 0", "liverpool-3,fulham-1"
        (1, re.compile(rf"{team}{JOIN}{NUM}{JOIN}{team}{JOIN}{NUM}", re.IGNORECASE)),
        # "2-1 Arsenal vs Chelsea", "1-0 Villa v Liverpool"
        (2, re.compile(rf"{NUM}{SCORE_SEP}{NUM}{JOIN}{team}{JOIN}{team}", re.IGNORECASE)),
        # "1 Aston Villa Liverpool 2"
        (3, re.compile(rf"{NUM}\s+{team}{STRICT_JOIN}{team}\s+{NUM}", re.IGNORECASE)),
        # "Everton Palace 1-1", "Arsenal vs Burnley -> 2-0", "Villa-Forest / 3-1", "EVE v CRY (0-0)", "Spurs v Newcastle1:3"
        (4, re.compile(rf"{team}{JOIN}{team}{JOIN}{NUM}{SCORE_SEP}{NUM}", re.IGNORECASE)),
    ]

    preds = []
    found_pairs = set()

    for line in lines:
        line_str = _merge_same_club(line.strip(), merge_re, alias_to_canonical)
        if not line_str:
            continue

        candidate_matches = []
        ambiguous = []

        for p_idx, pat in patterns:
            for match in pat.finditer(line_str):
                groups = match.groups()
                if p_idx == 2:
                    s1, s2, t1_raw, t2_raw = groups
                elif p_idx == 3:
                    s1, t1_raw, t2_raw, s2 = groups
                elif p_idx == 4:
                    t1_raw, t2_raw, s1, s2 = groups
                elif p_idx == 1:
                    t1_raw, s1, t2_raw, s2 = groups
                else:
                    t1_raw, s1, s2, t2_raw = groups

                t1, t2 = parse_team(t1_raw), parse_team(t2_raw)
                if not t1 or not t2 or t1 == t2:
                    continue
                # Side-by-side teams that are really one club name: "Leeds United 0-2", "Hull City 1-0".
                if p_idx in ADJACENT_TEAM_GROUPS:
                    g1, g2 = ADJACENT_TEAM_GROUPS[p_idx]
                    joined = re.sub(r"\s+", " ", line_str[match.start(g1):match.end(g2)]).lower()
                    if joined in alias_to_canonical:
                        continue
                if fixture_pairs is not None and frozenset((t1, t2)) not in fixture_pairs:
                    continue
                # "Liverpool vs Forest (2-1 liverpool)": which side the 2 belongs to is a guess. Admin decides.
                if p_idx == 4:
                    after = trailing_team_re.match(line_str, match.end())
                    if after and parse_team(after.group(1)) in (t1, t2):
                        ambiguous.append((frozenset((t1, t2)), match.start(), after.end()))
                        continue
                candidate_matches.append({
                    "start": match.start(),
                    "end": match.end(),
                    "length": match.end() - match.start(),
                    "p_idx": p_idx,
                    "team_a": t1,
                    "team_b": t2,
                    "score_a": int(s1),
                    "score_b": int(s2),
                })

        # Unless a longer reading covers it ("Leeds United 2-1 Man United" is not "Leeds, United 2-1 ...").
        ambiguous_pairs = {
            pair for pair, start, end in ambiguous
            if not any(frozenset((c["team_a"], c["team_b"])) == pair and c["start"] <= start and c["end"] >= end
                       for c in candidate_matches)
        }
        candidate_matches = [c for c in candidate_matches if frozenset((c["team_a"], c["team_b"])) not in ambiguous_pairs]
        # Sort candidate matches by starting index, then longer match length, then pattern priority
        candidate_matches.sort(key=lambda m: (m["start"], -m["length"], m["p_idx"]))

        current_end_pos = 0
        for cand in candidate_matches:
            # Prevent overlapping match spans
            if cand["start"] >= current_end_pos:
                gap = line_str[current_end_pos:cand["start"]]
                follows_accepted = current_end_pos > 0 and re.fullmatch(r"[\s.,;|/&+\-]*", gap) is not None
                # "Sunderland united 0 Arsenal 2": the club before this match has no score of its own.
                # "Chelsea Spurs 1-1 Villa" on the same line: Chelsea already closed the previous scoreline.
                if not follows_accepted:
                    prev = prev_team_re.search(line_str[:cand["start"]])
                    if prev:
                        prev_club = parse_team(prev.group(1))
                        if prev_club and prev_club != cand["team_a"]:
                            continue
                if cand["score_a"] > MAX_AUTO_GOALS or cand["score_b"] > MAX_AUTO_GOALS:
                    current_end_pos = cand["end"]
                    continue
                pair_key = tuple(sorted([cand["team_a"], cand["team_b"]]))
                if pair_key not in found_pairs:
                    found_pairs.add(pair_key)
                    preds.append({
                        "team_a": cand["team_a"],
                        "team_b": cand["team_b"],
                        "score_a": cand["score_a"],
                        "score_b": cand["score_b"]
                    })
                    current_end_pos = cand["end"]

    return preds
