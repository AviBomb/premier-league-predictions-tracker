"""
NLP Parser and Multi-Pattern Prediction Extraction Engine
Isolates fixture predictions from banter, alternative delimiters, and reversed ordering.
"""
import re
from typing import List, Dict, Any, Tuple
from src.team_aliases import parse_team, SORTED_ALIASES


"""
NLP Parser and Multi-Pattern Prediction Extraction Engine
Isolates fixture predictions from banter, alternative delimiters, and reversed ordering.
Supports multi-match single-line comments, numbered predictions, and custom delimiters.
"""
import re
from typing import List, Dict, Any, Tuple
from src.team_aliases import parse_team, SORTED_ALIASES, load_all_aliases, build_alias_lookup


def extract_predictions_from_comment(text: str) -> List[Dict[str, Any]]:
    """
    Extracts structured fixture predictions from noisy comment text.
    Handles delimiters (-, vs, v, :, /, to, spaces), multi-lines, single-line concatenated predictions, and banter.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    # Normalize unicode quotation marks, apostrophes, dashes, and whitespace
    clean_text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    clean_text = clean_text.replace("–", "-").replace("—", "-").replace("−", "-")
    clean_text = clean_text.replace("\u00a0", " ")

    alias_to_canonical, sorted_aliases = build_alias_lookup()
    alias_pattern = "|".join(re.escape(a) for a in sorted_aliases)

    lines = re.split(r'[\r\n;]+', clean_text)

    # Multi-pattern definitions for football predictions
    patterns = [
        # Pattern 0: [Team A] [Score A] [Delim] [Score B] [Team B]
        # e.g., "Aston Villa 2 - 1 Liverpool", "Palace 1-1 Man City", "Villa 2-2 Liverpool"
        (0, re.compile(
            rf'(?:^|\b|\d+\.?\s*)({alias_pattern})\s*[:\-\/v\.]*\s*(\d{{1,2}})\s*(?:[\-\:\/]|to|\s+)\s*(\d{{1,2}})\s*[:\-\/v\.]*\s*({alias_pattern})(?:\b|$)',
            re.IGNORECASE
        )),
        # Pattern 1: [Team A] [Score A] [Delim] [Team B] [Score B]
        # e.g., "Man United 2 Forest 1", "Arsenal 3 Burnley 0"
        (1, re.compile(
            rf'(?:^|\b|\d+\.?\s*)({alias_pattern})\s*[:\-\/v\.]*\s*(\d{{1,2}})\s*[:\-\/v\.]*\s*({alias_pattern})\s*[:\-\/v\.]*\s*(\d{{1,2}})(?:\b|$)',
            re.IGNORECASE
        )),
        # Pattern 2: [Score A] [Delim] [Score B] [Team A] vs [Team B]
        # e.g., "2-1 Arsenal vs Chelsea", "1-0 Villa v Liverpool"
        (2, re.compile(
            rf'(?:^|\b)(\d{{1,2}})\s*(?:[\-\:\/]|to|\s+)\s*(\d{{1,2}})\s+({alias_pattern})\s*(?:vs\.?|v\.?|\-|\s+)\s*({alias_pattern})(?:\b|$)',
            re.IGNORECASE
        )),
        # Pattern 3: [Score A] [Team A] [Team B] [Score B]
        # e.g., "1 Aston Villa Liverpool 2"
        (3, re.compile(
            rf'(?:^|\b)(\d{{1,2}})\s+({alias_pattern})\s*[:\-\/v\.]*\s*({alias_pattern})\s+(\d{{1,2}})(?:\b|$)',
            re.IGNORECASE
        )),
        # Pattern 4: [Team A] vs [Team B] -> [Score A] - [Score B]
        # e.g., "Arsenal vs Burnley -> 2-0", "Chelsea v Spurs: 1-1", "Palace - City: 2 - 1"
        (4, re.compile(
            rf'({alias_pattern})\s*(?:vs\.?|v\.?|\-)\s*({alias_pattern})\s*(?:[\-\:\>\s]+)\s*(\d{{1,2}})\s*[\-\:\s]\s*(\d{{1,2}})(?:\b|$)',
            re.IGNORECASE
        ))
    ]

    preds = []
    found_pairs = set()

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        candidate_matches = []

        for p_idx, pat in patterns:
            for match in pat.finditer(line_str):
                groups = match.groups()
                if p_idx == 2:  # [s1, s2, t1_raw, t2_raw]
                    s1, s2, t1_raw, t2_raw = groups
                elif p_idx == 3:  # [s1, t1_raw, t2_raw, s2]
                    s1, t1_raw, t2_raw, s2 = groups
                elif p_idx == 4:  # [t1_raw, t2_raw, s1, s2]
                    t1_raw, t2_raw, s1, s2 = groups
                elif p_idx == 1:  # [t1_raw, s1, t2_raw, s2]
                    t1_raw, s1, t2_raw, s2 = groups
                else:  # p_idx == 0: [t1_raw, s1, s2, t2_raw]
                    t1_raw, s1, s2, t2_raw = groups

                t1, t2 = parse_team(t1_raw), parse_team(t2_raw)
                try:
                    score1, score2 = int(s1), int(s2)
                except (ValueError, TypeError):
                    continue

                if t1 and t2 and t1 != t2 and 0 <= score1 <= 20 and 0 <= score2 <= 20:
                    candidate_matches.append({
                        "start": match.start(),
                        "end": match.end(),
                        "length": match.end() - match.start(),
                        "p_idx": p_idx,
                        "team_a": t1,
                        "team_b": t2,
                        "score_a": score1,
                        "score_b": score2
                    })

        # Sort candidate matches by starting index, then longer match length, then pattern priority
        candidate_matches.sort(key=lambda m: (m["start"], -m["length"], m["p_idx"]))

        current_end_pos = 0
        for cand in candidate_matches:
            # Prevent overlapping match spans
            if cand["start"] >= current_end_pos:
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
