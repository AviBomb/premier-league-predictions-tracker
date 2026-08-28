"""
Leaderboard and State Manager Module
Maintains multi-Gameweek database and exports CSV spreadsheets.
"""
import os
import json
import pandas as pd
from typing import List, Dict, Any


def save_gameweek_csv(audited_records: List[Dict[str, Any]], fixtures: List[Dict[str, Any]], gw: int, output_dir: str = "exports") -> str:
    """Exports granular match-by-match audit sheet for the target Gameweek."""
    os.makedirs(output_dir, exist_ok=True)
    flat_rows = []

    for r in audited_records:
        row = {
            "Comment_ID": r["comment_id"],
            "Author": r["author"],
            "Channel_URL": r["channel_url"],
            "Published_At": r["published_at"],
            "Is_Edited": r["is_edited"],
            "Status": r["status"],
            "Matches_Predicted": r["matches_found"],
            "Exact_Scores (3pts)": r["exact_scores"],
            "Outcome_Scores (1pt)": r["outcome_scores"],
            "Total_GW_Points": r["total_points"]
        }
        for f in fixtures:
            f_name = f"{f['home']} vs {f['away']}"
            f_data = r["fixtures"].get(f_name, {"pred": "N/A", "actual": "TBD", "points": 0})
            row[f"{f_name}_Pred"] = f_data["pred"]
            row[f"{f_name}_Actual"] = f_data["actual"]
            row[f"{f_name}_Pts"] = f_data["points"]
        flat_rows.append(row)

    df_gw = pd.DataFrame(flat_rows)
    filename = os.path.join(output_dir, f"GW{gw}_Parsed_Predictions.csv")
    df_gw.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"[+] Exported Granular Gameweek Sheet: {filename} ({len(df_gw)} records)")
    return filename


def rebuild_cumulative_leaderboard(
    db_path: str = "data/history_db.json",
    output_dir: str = "exports"
) -> pd.DataFrame:
    """Aggregates Season Stats across all Gameweeks in history_db.json and exports Cumulative_Leaderboard.csv."""
    os.makedirs(output_dir, exist_ok=True)
    history = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = {}

    season_totals = {}
    # Sort gameweek keys in chronological order (GW_1, GW_2, ...)
    sorted_gw_keys = sorted(
        history.keys(),
        key=lambda k: int(k.replace("GW_", "")) if k.replace("GW_", "").isdigit() else 0
    )

    for gw_key in sorted_gw_keys:
        users = history[gw_key]
        for author, data in users.items():
            if author not in season_totals:
                season_totals[author] = {
                    "Author": author,
                    "Channel_URL": data.get("channel_url", ""),
                    "Gameweeks_Played": 0,
                    "Total_Matches_Predicted": 0,
                    "Total_Exact_Scores (3pts)": 0,
                    "Total_Outcome_Scores (1pt)": 0,
                    "Total_Season_Points": 0
                }
            season_totals[author]["Gameweeks_Played"] += 1
            season_totals[author]["Total_Matches_Predicted"] += data.get("matches_found", 0)
            season_totals[author]["Total_Exact_Scores (3pts)"] += data.get("exact_scores", 0)
            season_totals[author]["Total_Outcome_Scores (1pt)"] += data.get("outcome_scores", 0)
            season_totals[author]["Total_Season_Points"] += data.get("total_points", 0)

    df_lead = pd.DataFrame(list(season_totals.values()))
    if not df_lead.empty:
        df_lead = df_lead.sort_values(
            by=["Total_Season_Points", "Total_Exact_Scores (3pts)", "Total_Outcome_Scores (1pt)"],
            ascending=[False, False, False]
        ).reset_index(drop=True)
        df_lead.insert(0, "Rank", df_lead.index + 1)

        lead_filename = os.path.join(output_dir, "Cumulative_Leaderboard.csv")
        df_lead.to_csv(lead_filename, index=False, encoding="utf-8-sig")
        print(f"[+] Exported Cumulative Season Leaderboard: {lead_filename} ({len(df_lead)} ranked users)")
        return df_lead

    return pd.DataFrame()


def update_cumulative_leaderboard(
    gw: int,
    valid_entries: Dict[str, Any],
    db_path: str = "data/history_db.json",
    output_dir: str = "exports"
) -> pd.DataFrame:
    """
    Updates multi-week JSON state and exports updated Cumulative_Leaderboard.csv
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    history = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = {}

    history[f"GW_{gw}"] = valid_entries

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    return rebuild_cumulative_leaderboard(db_path=db_path, output_dir=output_dir)

