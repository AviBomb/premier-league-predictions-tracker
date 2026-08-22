"""
NLP Parser and Multi-Pattern Prediction Extraction Engine
Isolates fixture predictions from banter, alternative delimiters, and reversed ordering.
"""
import re
from typing import List, Dict, Any, Tuple
from src.team_aliases import parse_team, SORTED_ALIASES


def extract_predictions_from_comment(text: str) -> List[Dict[str, Any]]:
    """
    Extracts structured fixture predictions from noisy comment text.
    Handles delimiters (-, vs, v, :, /, to, spaces), multi-lines, and banter.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    alias_pattern = "|".join(re.escape(a) for a in SORTED_ALIASES)
    lines = re.split(r'[\r\n;]+', text)

    patterns = [
        # Pattern 1: [Team A] [Score A] [Delim] [Score B] [Team B]
        # e.g., "Aston Villa 2 - 1 Liverpool", "Villa 2-2 Liverpool"
        re.compile(
            rf'(?:^|\b|\d+\.?\s*)({alias_pattern})\s*[:\-\/v\.]*\s*(\d{{1,2}})\s*(?:[\-\–\—\:\/]|to|\s+)\s*(\d{{1,2}})\s*[:\-\/v\.]*\s*({alias_pattern})(?:\b|$)',
            re.IGNORECASE
        ),
        # Pattern 2: [Team A] [Score A] [Delim] [Team B] [Score B]
        # e.g., "Man United 2 Forest 1", "Arsenal 3 Burnley 0"
        re.compile(
            rf'(?:^|\b|\d+\.?\s*)({alias_pattern})\s*[:\-\/v\.]*\s*(\d{{1,2}})\s*[:\-\/v\.]*\s*({alias_pattern})\s*[:\-\/v\.]*\s*(\d{{1,2}})(?:\b|$)',
            re.IGNORECASE
        ),
        # Pattern 3: [Score A] [Team A] [Team B] [Score B]
        # e.g., "1 Aston Villa Liverpool 2"
        re.compile(
            rf'(?:^|\b)(\d{{1,2}})\s+({alias_pattern})\s*[:\-\/v\.]*\s*({alias_pattern})\s+(\d{{1,2}})(?:\b|$)',
            re.IGNORECASE
        ),
        # Pattern 4: [Team A] vs [Team B] -> [Score A] - [Score B]
        # e.g., "Arsenal vs Burnley -> 2-0", "Chelsea v Spurs: 1-1"
        re.compile(
            rf'({alias_pattern})\s*(?:vs\.?|v\.?|\-)\s*({alias_pattern})\s*(?:[\-\:\>\–\—\s]+)\s*(\d{{1,2}})\s*[\-\:\–\—\s]\s*(\d{{1,2}})',
            re.IGNORECASE
        )
    ]

    preds = []
    found_pairs = set()

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        for p_idx, pat in enumerate(patterns):
            match = pat.search(line_str)
            if match:
                groups = match.groups()
                if p_idx == 2:  # P3 format
                    s1, t1_raw, t2_raw, s2 = groups
                elif p_idx == 3:  # P4 format
                    t1_raw, t2_raw, s1, s2 = groups
                else:  # P1 & P2 format
                    t1_raw, s1, s2_or_t2, t2_or_s2 = groups
                    if p_idx == 0:
                        s2, t2_raw = s2_or_t2, t2_or_s2
                    else:
                        t2_raw, s2 = s2_or_t2, t2_or_s2

                t1, t2 = parse_team(t1_raw), parse_team(t2_raw)
                if t1 and t2 and t1 != t2:
                    pair_key = tuple(sorted([t1, t2]))
                    if pair_key not in found_pairs:
                        found_pairs.add(pair_key)
                        preds.append({
                            "team_a": t1,
                            "team_b": t2,
                            "score_a": int(s1),
                            "score_b": int(s2)
                        })
                        break
    return preds
