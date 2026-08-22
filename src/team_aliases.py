"""
Canonical Team Matrix and Alias Reference for Premier League (20 Clubs)
Loads aliases dynamically from config/gameweek_config.json if present,
with built-in comprehensive fallback.
"""
import os
import json
import re
from typing import Dict, List, Tuple, Optional

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "gameweek_config.json")

BASE_TEAM_ALIASES: Dict[str, List[str]] = {
    "Arsenal": [
        "arsenal", "ars", "gunners", "gooners", "the gunners", "arsenal fc", "aresnal", "arc", "afc"
    ],
    "Aston Villa": [
        "aston villa", "villa", "avl", "aston v", "avfc", "villans", "the villans", "aston vill", "astnvilla"
    ],
    "AFC Bournemouth": [
        "afc bournemouth", "bournemouth", "bou", "cherries", "afcb", "the cherries", "bouremouth", "bournemonth", "bourmouth", "bmouth", "bmth", "bourn"
    ],
    "Brentford": [
        "brentford", "bre", "bees", "brentford fc", "the bees", "brent", "brenford"
    ],
    "Brighton & Hove Albion": [
        "brighton & hove albion", "brighton and hove albion", "brighton", "bha", "bhafc", "seagulls", "the seagulls", "albion", "bright", "brightn"
    ],
    "Chelsea": [
        "chelsea", "che", "blues", "the blues", "cfc", "chelsea fc", "chelsa", "chelski"
    ],
    "Coventry City": [
        "coventry city", "coventry", "cov", "ccfc", "sky blues", "the sky blues", "cov city", "covntry", "coventrycty"
    ],
    "Crystal Palace": [
        "crystal palace", "palace", "cry", "cpfc", "eagles", "the eagles", "crystal p", "cystal palace", "pallace", "crystal"
    ],
    "Everton": [
        "everton", "eve", "toffees", "the toffees", "efc", "everton fc", "evrton", "evertn"
    ],
    "Fulham": [
        "fulham", "ful", "cottagers", "the cottagers", "ffc", "fulham fc", "fullham", "fulhm"
    ],
    "Hull City": [
        "hull city", "hull", "hul", "tigers", "the tigers", "hcfc", "hull city tigers", "hullcity"
    ],
    "Ipswich Town": [
        "ipswich town", "ipswich", "ips", "tractor boys", "the tractor boys", "itfc", "ipswich t", "ipsw", "ipswich tn", "ipswitch", "ipswch"
    ],
    "Leeds United": [
        "leeds united", "leeds", "lee", "lufc", "whites", "the whites", "peacocks", "leed", "leeds utd"
    ],
    "Liverpool": [
        "liverpool", "liv", "reds", "the reds", "lfc", "liverpool fc", "pool", "livrpool", "liverpl"
    ],
    "Manchester City": [
        "manchester city", "man city", "mci", "mcfc", "citizens", "manchester c", "man c", "mancity", "m. city", "city", "mn city"
    ],
    "Manchester United": [
        "manchester united", "man united", "man utd", "mun", "mufc", "red devils", "manchester u", "manutd", "m. united", "man u", "united", "yanited", "mn utd"
    ],
    "Newcastle United": [
        "newcastle united", "newcastle", "new", "nufc", "magpies", "the toon", "toon", "new castle", "newcaslte", "newc utd"
    ],
    "Nottingham Forest": [
        "nottingham forest", "forest", "nfo", "nottm forest", "nffc", "nottingham", "tricky trees", "forrest", "nott forest", "n forest", "notts forest"
    ],
    "Sunderland": [
        "sunderland", "sun", "safc", "black cats", "the black cats", "sundrland", "sunderlnd"
    ],
    "Tottenham Hotspur": [
        "tottenham hotspur", "tottenham", "spurs", "tot", "thfc", "lilywhites", "the lilywhites", "spur", "hotspur", "totenham"
    ]
}


def load_all_aliases() -> Dict[str, List[str]]:
    aliases = dict(BASE_TEAM_ALIASES)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                custom_aliases = cfg.get("team_aliases", {})
                if custom_aliases:
                    for team, alias_list in custom_aliases.items():
                        aliases[team] = [a.lower().strip() for a in alias_list if a.strip()]
        except Exception:
            pass
    return aliases


TEAM_ALIASES = load_all_aliases()


def build_alias_lookup() -> Tuple[Dict[str, str], List[str]]:
    alias_to_canonical = {}
    for canonical, aliases in TEAM_ALIASES.items():
        for alias in aliases:
            alias_to_canonical[alias.strip().lower()] = canonical
    sorted_aliases = sorted(alias_to_canonical.keys(), key=len, reverse=True)
    return alias_to_canonical, sorted_aliases


ALIAS_LOOKUP, SORTED_ALIASES = build_alias_lookup()


def parse_team(raw_text: str) -> Optional[str]:
    """Matches raw substring against canonical team names."""
    clean = raw_text.strip().lower()
    if clean in ALIAS_LOOKUP:
        return ALIAS_LOOKUP[clean]
    for alias in SORTED_ALIASES:
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, clean):
            return ALIAS_LOOKUP[alias]
    return None
