"""
Premier League YouTube Predictions Tracker & Real-Time Engine (2026-2027 Season)
Orchestrates:
1. Real-time fixture loading from Premier League API (with config fallback)
2. Live YouTube comment scraping via YouTube Data API v3 (auto-updating local list on each call)
3. Noise-filtered Typo / Spelling mistake detection with candidate queue
4. Applying Admin-approved spelling corrections and updating points
5. Multi-week cumulative state persistence
6. Live public Dashboard (dashboard.html & index.html) + Secure Admin Portal (admin.html)
"""
import os
import sys
import json
import shutil
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.fixture_service import fetch_gameweek_fixtures
from src.scraper import scrape_youtube_comments
from src.scoring_engine import audit_and_score_gameweek
from src.leaderboard_manager import save_gameweek_csv, update_cumulative_leaderboard
from src.dashboard_generator import generate_live_dashboard

CONFIG_PATH = "config/gameweek_config.json"
APPROVALS_PATH = "data/admin_approvals.json"
PENDING_APPROVALS_PATH = "data/pending_approvals.json"
API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
LOCAL_DATA_FALLBACK = "data/sample_comments.csv"


def load_gameweek_configuration(target_gw: Optional[int] = None) -> Tuple[int, List[str], List[Dict[str, Any]], bool]:
    """Reads active gameweek, fixtures, and target URLs from config/gameweek_config.json."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                cfg = json.load(f)
                active_gw = target_gw if target_gw is not None else cfg.get("active_gameweek", 1)
                
                registered_vids = cfg.get("registered_videos", {})
                gw_key = str(active_gw)
                
                if gw_key in registered_vids and registered_vids[gw_key]:
                    video_urls = [registered_vids[gw_key]]
                else:
                    gw_info = cfg.get("gameweeks", {}).get(gw_key, {})
                    video_url = gw_info.get("video_url")
                    if video_url:
                        video_urls = [video_url]
                    else:
                        video_urls = []

                gw_info = cfg.get("gameweeks", {}).get(gw_key, {})
                fixtures = gw_info.get("fixtures", [])
                use_live = gw_info.get("use_live_fpl_api", True)
                return active_gw, video_urls, fixtures, use_live
        except Exception as e:
            print(f"[!] Warning reading {CONFIG_PATH}: {e}")

    return 1, [], [], True


def load_admin_approvals() -> Dict[str, Any]:
    """Loads persisted Admin approvals for spelling & typo matches."""
    if os.path.exists(APPROVALS_PATH):
        try:
            with open(APPROVALS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Warning reading {APPROVALS_PATH}: {e}")
    return {}


def save_pending_approvals(candidates: List[Dict[str, Any]], current_gw: int):
    """Saves detected typo candidates for Admin Review Queue across gameweeks."""
    os.makedirs(os.path.dirname(PENDING_APPROVALS_PATH), exist_ok=True)
    all_cands = []
    if os.path.exists(PENDING_APPROVALS_PATH):
        try:
            with open(PENDING_APPROVALS_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
                all_cands = [c for c in existing if c.get("gameweek") != current_gw]
        except Exception:
            all_cands = []
    all_cands.extend(candidates)
    with open(PENDING_APPROVALS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_cands, f, indent=2, ensure_ascii=False)


ALL_GW_DATA_PATH = "data/all_gameweeks_data.json"


def load_all_gameweeks_cache() -> Dict[str, Any]:
    if os.path.exists(ALL_GW_DATA_PATH):
        try:
            with open(ALL_GW_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_all_gameweeks_cache(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(ALL_GW_DATA_PATH), exist_ok=True)
    with open(ALL_GW_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def process_gameweek_data(gw_num: int, use_live_api: bool, admin_approvals: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Processes scraping, fixtures, and prediction scoring for a given gameweek number."""
    active_gw_conf, video_urls, custom_fixtures, use_live_fpl = load_gameweek_configuration(target_gw=gw_num)

    # By default, always pull live fixtures and match scores from Official Premier League API
    fixtures = []
    if use_live_fpl:
        fixtures = fetch_gameweek_fixtures(gw_num, use_live_api=True)
    
    if not fixtures:
        if custom_fixtures:
            fixtures = custom_fixtures
        else:
            fixtures = fetch_gameweek_fixtures(gw_num, use_live_api=False)

    # Sync live fixtures back to config/gameweek_config.json
    if fixtures and os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                cfg = json.load(f)
            if "gameweeks" not in cfg:
                cfg["gameweeks"] = {}
            if str(gw_num) not in cfg["gameweeks"]:
                cfg["gameweeks"][str(gw_num)] = {"use_live_fpl_api": True, "video_url": "", "fixtures": []}
            cfg["gameweeks"][str(gw_num)]["fixtures"] = fixtures
            cfg["gameweeks"][str(gw_num)]["use_live_fpl_api"] = True
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    comments = []
    gw_fallback_file = f"data/sample_comments_gw{gw_num}.csv" if gw_num > 1 else LOCAL_DATA_FALLBACK

    if use_live_api and API_KEY and not API_KEY.startswith("YOUR_") and video_urls and any(video_urls):
        try:
            valid_urls = [u for u in video_urls if u and "youtube.com" in u]
            if valid_urls:
                comments = scrape_youtube_comments(API_KEY, valid_urls)
                if comments:
                    os.makedirs("data", exist_ok=True)
                    df_cache = pd.DataFrame(comments)
                    df_cache.to_csv(gw_fallback_file, index=False, encoding="utf-8")
        except Exception as e:
            print(f"[!] Live API query note for GW {gw_num}: {e}. Using local cache...")

    if not comments:
        if os.path.exists(gw_fallback_file):
            df = pd.read_csv(gw_fallback_file)
            comments = df.to_dict(orient="records")
        elif os.path.exists(LOCAL_DATA_FALLBACK):
            df = pd.read_csv(LOCAL_DATA_FALLBACK)
            comments = df.to_dict(orient="records")
        else:
            comments = []

    if not comments:
        return [], {}, [], fixtures

    audited_records, valid_entries, fuzzy_candidates = audit_and_score_gameweek(
        comments, fixtures, gw_num, admin_approvals=admin_approvals
    )

    save_pending_approvals(fuzzy_candidates, gw_num)
    save_gameweek_csv(audited_records, fixtures, gw_num)
    update_cumulative_leaderboard(gw_num, valid_entries)

    return audited_records, valid_entries, fuzzy_candidates, fixtures


def run_pipeline(use_live_api: bool = True, target_gw: Optional[int] = None):
    print("=" * 88)
    print("  PREMIER LEAGUE PREDICTIONS TRACKER & LIVE SCORING ENGINE (2026-2027)")
    print("=" * 88)

    # 1. Load active Gameweek configuration
    gw_number, video_urls, custom_fixtures, use_live_fpl = load_gameweek_configuration()
    if target_gw is not None:
        gw_number = target_gw
    admin_approvals = load_admin_approvals()

    print(f"[*] Active Gameweek Scope: {gw_number}")

    # 2. Load all gameweeks data store
    all_gw_data = load_all_gameweeks_cache()

    # 3. Process all active gameweeks up to current gw_number
    for gw in range(1, gw_number + 1):
        audited, valids, candidates, fixtures = process_gameweek_data(gw, use_live_api, admin_approvals)
        if audited or fixtures:
            all_gw_data[str(gw)] = {
                "gw": gw,
                "fixtures": fixtures,
                "audited_records": audited
            }

    save_all_gameweeks_cache(all_gw_data)

    # 5. Build Cumulative Leaderboard across all available gameweeks
    # Load cumulative leaderboard
    lead_path = "exports/Cumulative_Leaderboard.csv"
    if os.path.exists(lead_path):
        df_leaderboard = pd.read_csv(lead_path)
    else:
        df_leaderboard = pd.DataFrame()

    # 6. Generate Premier League Themed Live Web Dashboard (dashboard.html & index.html)
    dashboard_path = generate_live_dashboard(
        active_gw=gw_number,
        all_gameweeks_data=all_gw_data,
        df_leaderboard=df_leaderboard,
        output_path="dashboard.html"
    )
    shutil.copy("dashboard.html", "index.html")

    print("\n" + "-" * 88)
    print("  EXTRACTED GAMEWEEK RESULTS & PREDICTION AUDIT SUMMARY")
    print("-" * 88)
    print(f"Processed Active Gameweek : GW {gw_number}")
    print(f"Valid Predictions (GW {gw_number}) : {len(audited)}")
    print(f"Total Completed Gameweeks : {len(all_gw_data)} ({', '.join(['GW ' + k for k in all_gw_data.keys()])})")
    print(f"Typo/Spelling Candidates : {len(candidates)} detected in active queue")

    # 7. Display Console Standings
    print("\n" + "=" * 88)
    print(f"TOP 10 CUMULATIVE LEADERBOARD (AFTER 2026/27 GAMEWEEK {gw_number})")
    print("=" * 88)
    if not df_leaderboard.empty:
        preview_cols = ["Rank", "Author", "Gameweeks_Played", "Total_Matches_Predicted", "Total_Exact_Scores (3pts)", "Total_Outcome_Scores (1pt)", "Total_Season_Points"]
        avail_cols = [c for c in preview_cols if c in df_leaderboard.columns]
        print(df_leaderboard[avail_cols].head(10).to_string(index=False))
    print("=" * 88)
    print(f"\n[+] Public Dashboard Ready : file:///{os.path.abspath(dashboard_path).replace(os.sep, '/')}")
    print(f"[+] Admin Control Portal   : file:///{os.path.abspath('admin.html').replace(os.sep, '/')}")


if __name__ == "__main__":
    run_pipeline(use_live_api=True)
