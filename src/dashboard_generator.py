"""
Premier League Live Dashboard Generator (2026-2027 Season)
Multi-Gameweek Interactive Dashboard:
1. Dynamic Tab Switcher for Season Leaderboard and each individual Gameweek (GW1, etc.)
2. Live Match Center Ticker per Gameweek with GMT kickoffs and FT/UPCOMING statuses
3. Submissions Table per Gameweek with search, status filters, sorting, and inspector modal
4. Cumulative Season Leaderboard without unnecessary inspect button
5. Detailed Predictor Inspector with preserved raw comments, timing audit, and edit diffs
6. Fullscreen blurred loading overlay with spinner for seamless transitions
"""
import os
import json
import pandas as pd
from typing import List, Dict, Any


def generate_live_dashboard(
    active_gw: int,
    all_gameweeks_data: Dict[str, Any],
    df_leaderboard: pd.DataFrame,
    output_path: str = "dashboard.html"
) -> str:
    leaderboard_json = df_leaderboard.to_json(orient="records") if not df_leaderboard.empty else "[]"
    all_gw_json = json.dumps(all_gameweeks_data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Irish Guy Premier League Predictions | Live Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --pl-purple: #38003c;
            --pl-dark: #1b0022;
            --pl-bg: #0e0014;
            --pl-card: rgba(43, 6, 49, 0.75);
            --pl-card-hover: rgba(65, 12, 74, 0.9);
            --pl-border: rgba(255, 255, 255, 0.12);
            --pl-green: #00ff87;
            --pl-green-glow: rgba(0, 255, 135, 0.3);
            --pl-pink: #e90052;
            --pl-pink-glow: rgba(233, 0, 82, 0.3);
            --pl-cyan: #04f5ff;
            --pl-gold: #ffb800;
            --text-main: #ffffff;
            --text-muted: #bda8c4;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }}
        body {{ background: radial-gradient(circle at top right, #2f0236 0%, var(--pl-bg) 65%); color: var(--text-main); padding: 28px 20px; min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}

        /* Header */
        .pl-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 18px; border-bottom: 1px solid var(--pl-border); flex-wrap: wrap; gap: 16px; }}
        .pl-logo-area {{ display: flex; align-items: center; gap: 14px; }}
        .pl-lion-icon {{ width: 46px; height: 46px; background: linear-gradient(135deg, var(--pl-green), var(--pl-cyan)); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; font-weight: 900; color: #000; box-shadow: 0 0 20px var(--pl-green-glow); }}
        h1 {{ font-size: 2.1rem; font-weight: 900; letter-spacing: -0.5px; background: linear-gradient(135deg, #ffffff, var(--pl-green)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ color: var(--text-muted); font-size: 0.92rem; }}
        
        .header-actions {{ display: flex; align-items: center; gap: 12px; }}
        .gw-select-pill {{ background: rgba(255, 255, 255, 0.08); border: 1px solid var(--pl-border); color: #fff; padding: 8px 14px; border-radius: 99px; font-weight: 700; font-size: 0.88rem; outline: none; cursor: pointer; }}
        .gw-select-pill:focus {{ border-color: var(--pl-green); }}
        .gw-select-pill option {{ background: #1b0022; color: #fff; }}
        .pl-badge {{ background: linear-gradient(135deg, var(--pl-pink), var(--pl-purple)); color: #fff; padding: 8px 16px; border-radius: 99px; font-weight: 700; font-size: 0.88rem; border: 1px solid rgba(255,255,255,0.2); box-shadow: 0 4px 15px var(--pl-pink-glow); }}
        .btn-admin-portal {{ background: rgba(255, 255, 255, 0.08); border: 1px solid var(--pl-border); color: #fff; padding: 8px 16px; border-radius: 99px; font-weight: 700; font-size: 0.88rem; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s ease; }}
        .btn-admin-portal:hover {{ background: linear-gradient(135deg, var(--pl-green), var(--pl-cyan)); color: #000; border-color: transparent; box-shadow: 0 4px 15px var(--pl-green-glow); transform: translateY(-2px); }}

        /* Navigation Tabs for Leaderboard and Individual Gameweeks */
        .nav-tabs-bar {{ display: flex; gap: 10px; margin-bottom: 24px; flex-wrap: wrap; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 16px; border: 1px solid var(--pl-border); }}
        .nav-tab-btn {{ background: transparent; border: 1px solid transparent; color: var(--text-muted); padding: 10px 20px; border-radius: 12px; font-size: 0.95rem; font-weight: 700; cursor: pointer; transition: 0.2s ease; display: flex; align-items: center; gap: 8px; }}
        .nav-tab-btn:hover {{ background: var(--pl-card); color: #fff; }}
        .nav-tab-btn.active {{ background: linear-gradient(135deg, var(--pl-green), var(--pl-cyan)); color: #000; font-weight: 800; border-color: transparent; box-shadow: 0 4px 16px var(--pl-green-glow); }}
        .nav-tab-btn .tab-counter {{ background: rgba(0,0,0,0.25); padding: 2px 7px; border-radius: 99px; font-size: 0.75rem; }}

        /* Live Match Center Ticker */
        .fixture-ticker-section {{ margin-bottom: 28px; }}
        .section-title {{ font-size: 1.05rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: var(--pl-green); margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }}
        .fixture-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 12px; }}
        .fixture-card {{ background: var(--pl-card); border: 1px solid var(--pl-border); border-radius: 14px; padding: 14px 16px; backdrop-filter: blur(10px); transition: transform 0.2s ease, border-color 0.2s ease; }}
        .fixture-card:hover {{ transform: translateY(-3px); border-color: var(--pl-green); }}
        .fix-header {{ display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 8px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }}
        .fix-team-row {{ display: flex; justify-content: space-between; align-items: center; margin: 4px 0; font-size: 0.95rem; font-weight: 700; }}
        .fix-score {{ font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; color: var(--pl-green); font-weight: 900; }}
        .fix-score-pending {{ font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: var(--pl-gold); font-weight: 700; }}
        .fix-status-ft {{ background: rgba(0, 255, 135, 0.15); color: var(--pl-green); padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 800; }}
        .fix-status-upcoming {{ background: rgba(255, 184, 0, 0.15); color: var(--pl-gold); padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 800; border: 1px solid rgba(255, 184, 0, 0.3); }}

        /* Top Metric Cards */
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 26px; }}
        .stat-card {{ background: var(--pl-card); border: 1px solid var(--pl-border); padding: 20px; border-radius: 16px; backdrop-filter: blur(10px); position: relative; overflow: hidden; }}
        .stat-card::after {{ content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: var(--pl-green); }}
        .stat-val {{ font-size: 2.2rem; font-weight: 900; color: var(--pl-green); margin-top: 4px; font-family: 'JetBrains Mono', monospace; }}
        .stat-lbl {{ font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); }}

        /* Controls: Filters, Sort, Search */
        .controls-panel {{ display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }}
        .table-view-heading {{ font-size: 1.2rem; font-weight: 800; display: flex; align-items: center; gap: 8px; color: #fff; }}
        .filters-group {{ display: flex; gap: 10px; align-items: center; flex: 1; max-width: 650px; justify-content: flex-end; }}
        .search-input {{ padding: 11px 16px; background: var(--pl-card); border: 1px solid var(--pl-border); border-radius: 12px; color: #fff; font-size: 0.92rem; outline: none; flex: 1; min-width: 200px; }}
        .search-input:focus {{ border-color: var(--pl-green); }}
        .filter-select {{ padding: 11px 14px; background: var(--pl-card); border: 1px solid var(--pl-border); border-radius: 12px; color: #fff; font-size: 0.9rem; font-weight: 600; outline: none; cursor: pointer; }}

        /* Tables */
        .table-card {{ background: var(--pl-card); border: 1px solid var(--pl-border); border-radius: 18px; overflow: hidden; backdrop-filter: blur(12px); box-shadow: 0 10px 30px rgba(0,0,0,0.4); }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th, td {{ padding: 14px 18px; border-bottom: 1px solid var(--pl-border); }}
        th {{ background: rgba(0,0,0,0.4); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); font-weight: 800; cursor: pointer; user-select: none; }}
        th:hover {{ color: var(--pl-green); }}
        tbody tr {{ transition: background 0.15s ease; }}
        tbody tr:hover {{ background: var(--pl-card-hover); }}

        /* Status & Badges */
        .team-badge {{ width: 26px; height: 26px; object-fit: contain; vertical-align: middle; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); flex-shrink: 0; }}
        .team-badge-sm {{ width: 20px; height: 20px; object-fit: contain; vertical-align: middle; flex-shrink: 0; }}
        .team-badge-md {{ width: 28px; height: 28px; object-fit: contain; vertical-align: middle; flex-shrink: 0; }}
        .fix-team-name {{ display: inline-flex; align-items: center; gap: 10px; font-size: 0.95rem; font-weight: 700; }}
        .fix-scorers-box {{ margin-top: 10px; padding-top: 10px; border-top: 1px dashed rgba(255,255,255,0.12); font-size: 0.78rem; font-family: 'JetBrains Mono', monospace; line-height: 1.45; }}
        .scorer-line {{ display: flex; align-items: flex-start; gap: 6px; margin-top: 4px; color: #ffe082; word-break: break-word; }}
        .scorer-ball {{ font-size: 0.75rem; flex-shrink: 0; margin-top: 1px; }}

        .rank-badge {{ display: inline-flex; align-items: center; justify-content: center; width: 34px; height: 34px; border-radius: 8px; font-weight: 800; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; }}
        .rank-1 {{ background: linear-gradient(135deg, #ffd700, #ffae00); color: #000; box-shadow: 0 0 12px rgba(255,215,0,0.4); }}
        .rank-2 {{ background: linear-gradient(135deg, #e2e8f0, #94a3b8); color: #000; }}
        .rank-3 {{ background: linear-gradient(135deg, #f59e0b, #b45309); color: #fff; }}
        .rank-other {{ color: var(--text-muted); }}

        .pill {{ padding: 5px 12px; border-radius: 99px; font-size: 0.76rem; font-weight: 800; display: inline-flex; align-items: center; gap: 5px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .pill-valid {{ background: rgba(0, 255, 135, 0.15); color: var(--pl-green); border: 1px solid rgba(0, 255, 135, 0.35); }}
        .pill-partial {{ background: rgba(255, 184, 0, 0.18); color: #ffd166; border: 1px solid rgba(255, 184, 0, 0.45); }}
        .pill-disqualified {{ background: rgba(233, 0, 82, 0.2); color: #ff6b8b; border: 1px solid rgba(233, 0, 82, 0.4); }}
        .pill-late {{ background: rgba(255, 184, 0, 0.2); color: #ffd166; border: 1px solid rgba(255, 184, 0, 0.4); }}
        .pill-exact {{ background: rgba(255, 184, 0, 0.2); color: var(--pl-gold); font-weight: 800; font-family: 'JetBrains Mono', monospace; border-radius: 8px; }}

        /* Modal */
        .modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 999; backdrop-filter: blur(14px); align-items: center; justify-content: center; padding: 20px; }}
        .modal.active {{ display: flex; }}
        .modal-box {{ background: #1a0122; border: 1px solid var(--pl-border); border-radius: 20px; width: 92%; max-width: 780px; max-height: 90vh; overflow-y: auto; padding: 28px; box-shadow: 0 20px 60px rgba(0,0,0,0.85); }}
        .modal-top {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 1px solid var(--pl-border); padding-bottom: 16px; }}
        .close-btn {{ background: none; border: none; color: var(--text-muted); font-size: 1.8rem; cursor: pointer; }}
        .close-btn:hover {{ color: #fff; }}

        /* Timing & History Box */
        .timing-audit-box {{ background: rgba(0,0,0,0.45); border: 1px solid var(--pl-border); border-radius: 14px; padding: 14px 18px; margin-bottom: 18px; }}
        .timing-row {{ display: flex; justify-content: space-between; align-items: center; font-size: 0.88rem; margin: 4px 0; }}
        .timing-lbl {{ color: var(--text-muted); font-weight: 600; }}
        .timing-val {{ font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #ffffff; }}

        /* Edit History Timeline & Diff Box */
        .edit-history-box {{ background: rgba(0,0,0,0.35); border: 1px solid rgba(233, 0, 82, 0.35); border-radius: 14px; padding: 16px; margin-bottom: 18px; }}
        .version-block {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px; margin-top: 10px; }}
        .version-header {{ display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; font-weight: 800; text-transform: uppercase; margin-bottom: 6px; }}
        .diff-container {{ background: rgba(0,0,0,0.5); border: 1px solid var(--pl-border); border-radius: 10px; padding: 12px; margin-top: 10px; font-family: 'JetBrains Mono', monospace; font-size: 0.86rem; line-height: 1.6; }}
        .diff-line {{ padding: 2px 0; }}
        .diff-add {{ background: rgba(0, 255, 135, 0.15); color: #00ff87; border-left: 3px solid #00ff87; padding-left: 8px; font-weight: 700; }}
        .diff-del {{ background: rgba(233, 0, 82, 0.15); color: #ff6b8b; border-left: 3px solid #ff6b8b; padding-left: 8px; text-decoration: line-through; }}

        .raw-comment-box {{ background: rgba(0,0,0,0.3); border: 1px solid var(--pl-border); border-radius: 12px; padding: 14px; margin-bottom: 18px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; line-height: 1.5; color: #ffe082; white-space: pre-wrap; }}

        .fix-audit-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: rgba(255,255,255,0.03); border-radius: 12px; margin-bottom: 8px; font-size: 0.92rem; border-left: 3px solid transparent; }}
        .fix-audit-row.exact {{ border-left-color: var(--pl-gold); background: rgba(255, 184, 0, 0.05); }}
        .fix-audit-row.outcome {{ border-left-color: var(--pl-green); background: rgba(0, 255, 135, 0.05); }}
        .fix-audit-row.pending {{ border-left-color: var(--pl-gold); background: rgba(255, 184, 0, 0.03); }}
        .fix-audit-row.voided {{ border-left-color: var(--pl-pink); background: rgba(233, 0, 82, 0.04); }}
        .fix-audit-row.miss {{ border-left-color: rgba(255,255,255,0.2); }}

        /* View Switcher Controls */
        .view-mode-toggle {{ display: inline-flex; background: rgba(0,0,0,0.4); border: 1px solid var(--pl-border); border-radius: 12px; padding: 3px; gap: 4px; }}
        .view-toggle-btn {{ background: transparent; border: none; color: var(--text-muted); padding: 7px 14px; border-radius: 9px; font-weight: 800; font-size: 0.82rem; cursor: pointer; transition: all 0.2s ease; }}
        .view-toggle-btn.active {{ background: linear-gradient(135deg, var(--pl-green), var(--pl-cyan)); color: #000; box-shadow: 0 2px 10px var(--pl-green-glow); }}

        /* Mobile & Tablet Cards View Grid */
        .cards-view-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr)); gap: 14px; margin-top: 14px; }}
        .mobile-card {{ background: var(--pl-card); border: 1px solid var(--pl-border); border-radius: 16px; padding: 18px; backdrop-filter: blur(12px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); transition: all 0.2s ease; position: relative; overflow: hidden; }}
        .mobile-card:hover {{ border-color: var(--pl-green); transform: translateY(-2px); }}
        .mobile-card-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px; gap: 10px; }}
        .mobile-card-user {{ font-size: 1.05rem; font-weight: 800; color: #fff; word-break: break-all; }}
        .mobile-card-pts-big {{ font-size: 1.6rem; font-weight: 900; color: var(--pl-green); font-family: 'JetBrains Mono', monospace; line-height: 1; text-align: right; flex-shrink: 0; }}
        .mobile-card-stats {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 10px; font-size: 0.84rem; background: rgba(0,0,0,0.3); padding: 10px 12px; border-radius: 10px; }}
        .mobile-card-stat-item {{ display: flex; flex-direction: column; gap: 2px; }}
        .mobile-card-lbl {{ font-size: 0.72rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase; }}
        .mobile-card-val {{ font-weight: 800; font-family: 'JetBrains Mono', monospace; }}
        .mobile-card-inspect-btn {{ width: 100%; margin-top: 12px; padding: 10px; background: rgba(0, 255, 135, 0.15); border: 1px solid rgba(0, 255, 135, 0.35); color: var(--pl-green); border-radius: 10px; font-weight: 800; font-size: 0.86rem; cursor: pointer; transition: 0.2s; text-align: center; }}
        .mobile-card-inspect-btn:hover {{ background: var(--pl-green); color: #000; }}

        /* Media Queries for Tablet & Mobile Responsiveness */
        @media (max-width: 1024px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .controls-panel {{ flex-direction: column; align-items: stretch; gap: 14px; }}
            .filters-group {{ width: 100%; max-width: 100%; justify-content: flex-start; flex-wrap: wrap; }}
            .search-input {{ min-width: 100%; }}
        }}

        @media (max-width: 768px) {{
            body {{ padding: 16px 10px; }}
            .pl-header {{ flex-direction: column; align-items: flex-start; gap: 14px; }}
            .pl-logo-area {{ width: 100%; }}
            h1 {{ font-size: 1.55rem; }}
            .subtitle {{ font-size: 0.82rem; }}
            .header-actions {{ width: 100%; justify-content: space-between; flex-wrap: wrap; gap: 8px; }}
            .gw-select-pill, .pl-badge, .btn-admin-portal {{ flex: 1 1 auto; text-align: center; justify-content: center; font-size: 0.82rem; padding: 9px 12px; }}
            .irish-guy-banner {{ flex-direction: column; align-items: flex-start; padding: 14px 16px; gap: 12px; }}
            .irish-guy-banner > div {{ width: 100%; }}
            .irish-guy-banner a {{ width: 100%; justify-content: center; }}
            .nav-tabs-bar {{ overflow-x: auto; flex-wrap: nowrap; padding: 6px; -webkit-overflow-scrolling: touch; }}
            .nav-tab-btn {{ white-space: nowrap; flex-shrink: 0; padding: 8px 14px; font-size: 0.86rem; }}
            .fixture-grid {{ grid-template-columns: 1fr; }}
            .table-card {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
            th, td {{ padding: 10px 12px; font-size: 0.85rem; }}
            .rank-badge {{ width: 28px; height: 28px; font-size: 0.82rem; }}
            .cards-view-grid {{ grid-template-columns: 1fr; }}
        }}

        @media (max-width: 480px) {{
            .stats-grid {{ grid-template-columns: 1fr; gap: 10px; }}
            .stat-card {{ padding: 14px; }}
            .stat-val {{ font-size: 1.7rem; }}
            .modal-box {{ padding: 18px 14px; width: 96%; max-height: 94vh; border-radius: 16px; }}
            .fix-audit-row {{ flex-direction: column; align-items: flex-start; gap: 8px; }}
        }}

        /* Fullscreen Blur Loading Overlay */
        .loading-overlay {{ position: fixed; inset: 0; background: rgba(9, 0, 13, 0.85); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); z-index: 9999; display: none; align-items: center; justify-content: center; animation: fadeIn 0.2s ease; }}
        .loading-box {{ background: var(--pl-card); border: 1px solid var(--pl-border); border-radius: 24px; padding: 36px 44px; text-align: center; max-width: 440px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.8), 0 0 30px var(--pl-green-glow); }}
        .pl-spinner-large {{ width: 56px; height: 56px; border: 4px solid rgba(0, 255, 135, 0.2); border-top-color: var(--pl-green); border-right-color: var(--pl-cyan); border-radius: 50%; margin: 0 auto 20px; animation: spin 0.8s linear infinite; }}
        .loading-title {{ font-size: 1.3rem; font-weight: 900; color: #ffffff; margin-bottom: 8px; }}
        .loading-subtitle {{ font-size: 0.88rem; color: var(--text-muted); line-height: 1.45; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    </style>
</head>
<body>
    <!-- Global Fullscreen Blurred Loading Overlay -->
    <div id="global-loading-overlay" class="loading-overlay">
        <div class="loading-box">
            <div class="pl-spinner-large"></div>
            <div class="loading-title" id="loading-title">Updating Live Standings</div>
            <div class="loading-subtitle" id="loading-subtitle">Please wait while the real-time scoring engine calculates results...</div>
        </div>
    </div>

    <div class="container">
        <!-- Header -->
        <div class="pl-header">
            <div class="pl-logo-area">
                <div class="pl-lion-icon" style="background: linear-gradient(135deg, #00f076, #00b0ff); box-shadow: 0 0 20px rgba(0, 240, 118, 0.4);">☘️</div>
                <div>
                    <h1>The Irish Guy Premier League Predictions</h1>
                    <p class="subtitle">Official Prediction League &amp; Live NLP Tracker for <a href="https://www.youtube.com/@theirishguy2494" target="_blank" style="color: var(--pl-green); text-decoration: none; font-weight: 700;">@theirishguy2494</a> &amp; <a href="https://www.youtube.com/@TheIrishGuyExtra" target="_blank" style="color: var(--pl-cyan); text-decoration: none; font-weight: 700;">@TheIrishGuyExtra</a></p>
                </div>
            </div>
            <div class="header-actions">
                <select id="gw-quick-select" class="gw-select-pill" onchange="onGwDropdownChange(this.value)">
                </select>
                <div class="pl-badge" id="header-scope-badge">Gameweek {active_gw} Live Hub</div>
                <a href="admin.html" class="btn-admin-portal" title="Admin Score & Video Management">⚙️ Admin Portal</a>
            </div>
        </div>

        <!-- The Irish Guy Channel Hub Banner -->
        <div class="irish-guy-banner" style="background: linear-gradient(135deg, rgba(0, 50, 25, 0.85), rgba(27, 0, 34, 0.95)); border: 1px solid rgba(0, 255, 135, 0.4); border-radius: 18px; padding: 18px 24px; margin-bottom: 24px; backdrop-filter: blur(12px); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 0 20px rgba(0,255,135,0.08);">
            <div style="display: flex; align-items: center; gap: 16px;">
                <div style="width: 52px; height: 52px; background: radial-gradient(circle, #00ff87 0%, #004d25 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; border: 2px solid #00ff87; box-shadow: 0 0 18px rgba(0, 255, 135, 0.4);">
                    ☘️
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                        <span style="font-size: 1.25rem; font-weight: 900; color: #fff;">The Irish Guy Predictions League</span>
                        <span style="background: linear-gradient(135deg, #00ff87, #04f5ff); color: #000; padding: 3px 10px; border-radius: 99px; font-weight: 800; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">Official YouTube Hub</span>
                    </div>
                    <p style="font-size: 0.88rem; color: #bda8c4; margin-top: 4px;">
                        Built exclusively for <b>The Irish Guy</b> YouTube Community! Predict match scores in YouTube comments on his channels to compete on the live leaderboard.
                    </p>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <a href="https://www.youtube.com/@theirishguy2494" target="_blank" style="background: #ff0000; color: #fff; padding: 9px 16px; border-radius: 12px; font-weight: 800; font-size: 0.86rem; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; transition: all 0.2s ease; box-shadow: 0 4px 15px rgba(255,0,0,0.3);">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.016 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                    The Irish Guy (@theirishguy2494)
                </a>
                <a href="https://www.youtube.com/@TheIrishGuyExtra" target="_blank" style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.2); color: #fff; padding: 9px 16px; border-radius: 12px; font-weight: 800; font-size: 0.86rem; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; transition: all 0.2s ease;">
                    ⚡ @TheIrishGuyExtra
                </a>
            </div>
        </div>

        <!-- Navigation Tabs for Leaderboard and Individual Gameweeks -->
        <div class="nav-tabs-bar" id="nav-tabs-container">
            <button class="nav-tab-btn active" id="tab-btn-leaderboard" onclick="switchMainTab('leaderboard')">
                🏆 Cumulative Season Leaderboard
            </button>
        </div>

        <!-- Official Fixtures & Match Center -->
        <div class="fixture-ticker-section">
            <div class="section-title">
                <span>🏟️</span> <span id="fixture-center-title">Gameweek {active_gw} Fixture Center (GMT / UK Time)</span>
            </div>
            <div class="fixture-grid" id="fixture-grid"></div>
        </div>

        <!-- Top Metrics Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-lbl" id="stat-1-lbl">Ranked Predictors</div>
                <div class="stat-val" id="stat-1-val">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-lbl" id="stat-2-lbl">Gameweek Top Score</div>
                <div class="stat-val" id="stat-2-val">0 pts</div>
            </div>
            <div class="stat-card">
                <div class="stat-lbl" id="stat-3-lbl">Total Exact Scores (3pts)</div>
                <div class="stat-val" id="stat-3-val" style="color: var(--pl-gold);">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-lbl" id="stat-4-lbl">Integrity Compliance Rate</div>
                <div class="stat-val" id="stat-4-val">0%</div>
            </div>
        </div>

        <!-- Controls: Filters, Sort, Search -->
        <div class="controls-panel">
            <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
                <div class="table-view-heading" id="table-view-heading">
                    🏆 Cumulative Season Standings
                </div>
                <div class="view-mode-toggle">
                    <button class="view-toggle-btn active" id="btn-view-cards" onclick="toggleViewMode('cards')">📱 Mobile Cards</button>
                    <button class="view-toggle-btn" id="btn-view-table" onclick="toggleViewMode('table')">📊 Table View</button>
                </div>
            </div>
            <div class="filters-group">
                <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search predictor username..." onkeyup="filterAndSort()">
                <select id="statusFilter" class="filter-select" onchange="filterAndSort()" style="display: none;">
                    <option value="ALL">All Statuses</option>
                    <option value="Valid">Valid & Valid* (Active)</option>
                    <option value="Disqualified">Disqualified (Edited)</option>
                    <option value="Late">Late (All Concluded)</option>
                </select>
                <select id="sortSelect" class="filter-select" onchange="filterAndSort()">
                    <option value="points_desc">Points: High to Low</option>
                    <option value="exacts_desc">Exact Scores (3pts)</option>
                    <option value="outcomes_desc">Outcomes (1pt)</option>
                    <option value="matches_desc">Matches Predicted</option>
                </select>
            </div>
        </div>

        <!-- Leaderboard Table -->
        <div class="table-card" id="leaderboard-panel">
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Predictor</th>
                        <th>GWs Played</th>
                        <th>Matches</th>
                        <th>Exact (3pts)</th>
                        <th>Outcome (1pt)</th>
                        <th>Season Points</th>
                    </tr>
                </thead>
                <tbody id="leaderboard-body"></tbody>
            </table>
        </div>

        <!-- GW Audit Table -->
        <div class="table-card" id="audit-panel" style="display: none;">
            <table>
                <thead>
                    <tr>
                        <th>Predictor</th>
                        <th>Submission Time (GMT)</th>
                        <th>Integrity Status</th>
                        <th>Matches</th>
                        <th>Exacts (3pts)</th>
                        <th>Outcomes (1pt)</th>
                        <th>GW Points</th>
                        <th>Inspect</th>
                    </tr>
                </thead>
                <tbody id="audit-body"></tbody>
            </table>
        </div>

        <!-- Mobile & Tablet Cards View Container -->
        <div class="cards-view-grid" id="cards-view-panel" style="display: none;"></div>

        <!-- Footer -->
        <footer style="margin-top: 40px; padding: 24px 0; border-top: 1px solid var(--pl-border); text-align: center; color: var(--text-muted); font-size: 0.88rem;">
            <p>☘️ Built for <b>The Irish Guy</b> Premier League Prediction Community (<a href="https://www.youtube.com/@theirishguy2494" target="_blank" style="color: #00ff87; text-decoration: none; font-weight: 700;">@theirishguy2494</a> &amp; <a href="https://www.youtube.com/@TheIrishGuyExtra" target="_blank" style="color: #04f5ff; text-decoration: none; font-weight: 700;">@TheIrishGuyExtra</a>) &bull; Premier League 2026/27 Live Score Tracker</p>
        </footer>
    </div>

    <!-- Inspector Modal -->
    <div class="modal" id="modal">
        <div class="modal-box">
            <div class="modal-top">
                <div>
                    <h2 id="modal-author" style="font-size: 1.4rem; font-weight: 800; color: #ffffff;">Predictor Inspection</h2>
                    <div id="modal-status-container" style="margin-top: 8px;"></div>
                </div>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>

            <!-- Submission Timing Audit Box -->
            <div class="timing-audit-box">
                <div class="timing-row">
                    <span class="timing-lbl">🕒 Submission Time (GMT):</span>
                    <span class="timing-val" id="modal-submit-time">-</span>
                </div>
                <div class="timing-row" id="modal-edit-row" style="display: none;">
                    <span class="timing-lbl">✏️ Last Edited Time (GMT):</span>
                    <span class="timing-val" id="modal-edit-time" style="color: var(--pl-pink);">-</span>
                </div>
                <div class="timing-row" id="modal-lateness-row" style="display: none;">
                    <span class="timing-lbl">⚠️ Lateness Note:</span>
                    <span class="timing-val" id="modal-lateness-val" style="color: var(--pl-gold);">-</span>
                </div>
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.08); font-size: 0.82rem; color: var(--text-muted); line-height: 1.4;" id="modal-timing-summary">
                </div>
            </div>

            <!-- Edit History Section (For Edited Comments) -->
            <div class="edit-history-box" id="modal-edit-history-section" style="display: none;">
                <div style="font-size: 0.86rem; font-weight: 800; color: var(--pl-pink); text-transform: uppercase; letter-spacing: 0.8px;">
                    ✏️ YouTube Comment Edit History & Modification Audit:
                </div>
                <div id="modal-edit-diff-desc" style="font-size: 0.8rem; color: var(--text-muted); margin-top: 3px;"></div>
                
                <!-- Highlighted Visual Diff (When true historical text is available) -->
                <div class="diff-container" id="modal-diff-view" style="display: none;"></div>

                <!-- Step-by-Step Revisions Timeline -->
                <div id="modal-revisions-timeline"></div>
            </div>

            <!-- Raw User Comment Block (For Unedited Comments) -->
            <div id="modal-single-comment-section">
                <div style="margin-bottom: 8px; font-size: 0.78rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px;">
                    💬 Submitted YouTube Comment:
                </div>
                <div class="raw-comment-box" id="modal-raw-comment"></div>
            </div>

            <!-- Fixtures Breakdown List -->
            <div style="margin-bottom: 8px; font-size: 0.78rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px;">
                ⚽ Fixture Predictions & Points Breakdown:
            </div>
            <div id="modal-fixtures-list"></div>
        </div>
    </div>

    <script>
        const PL_BADGES = {{
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
        }};

        function getTeamLogoJS(name) {{
            if (!name) return "https://resources.premierleague.com/premierleague/badges/70/t3.png";
            const clean = name.trim();
            if (PL_BADGES[clean]) return PL_BADGES[clean];
            for (let k in PL_BADGES) {{
                if (clean.toLowerCase().includes(k.toLowerCase()) || k.toLowerCase().includes(clean.toLowerCase())) {{
                    return PL_BADGES[k];
                }}
            }}
            return "https://resources.premierleague.com/premierleague/badges/70/t3.png";
        }}

        function formatGoalsJS(goals, summaryFallback) {{
            if (goals && Array.isArray(goals) && goals.length > 0) {{
                return goals.map(g => {{
                    const min = g.minute ? `<b>${{escapeHtml(g.minute)}}</b>` : '';
                    const scorer = g.scorer ? escapeHtml(g.scorer) : 'Goal';
                    const isOg = g.type === 'OG' || g.type === 'O';
                    const isPen = g.type === 'P' || g.type === 'PEN';
                    const assist = (!isOg && g.assist) ? ` <span style="color: var(--text-muted); font-size: 0.74rem;">(assist: ${{escapeHtml(g.assist)}})</span>` : '';
                    const type = isOg ? ' <span style="color:#ff6b8b; font-size:0.72rem; font-weight:800; background:rgba(233,0,82,0.18); border:1px solid rgba(233,0,82,0.35); padding:1px 5px; border-radius:4px;">(OG)</span>' : (isPen ? ' <span style="color:var(--pl-gold); font-size:0.72rem; font-weight:800; background:rgba(255,184,0,0.18); border:1px solid rgba(255,184,0,0.35); padding:1px 5px; border-radius:4px;">(P)</span>' : '');
                    return `${{scorer}} ${{min}}${{type}}${{assist}}`;
                }}).join('<span style="color: var(--text-muted); margin: 0 4px;">&bull;</span> ');
            }}
            return escapeHtml(summaryFallback || '');
        }}

        const ALL_GAMEWEEKS = {all_gw_json};
        const rawLeaderboard = {leaderboard_json};
        let activeGameweekScope = {active_gw};
        let currentTab = 'leaderboard'; // 'leaderboard' or 'gw_1', etc.
        let currentDisplayMode = window.innerWidth <= 768 ? 'cards' : 'table';
        window.userManuallySetView = false;

        function toggleViewMode(mode) {{
            window.userManuallySetView = true;
            currentDisplayMode = mode;
            filterAndSort();
        }}

        window.addEventListener('resize', () => {{
            if (!window.userManuallySetView) {{
                const isSmall = window.innerWidth <= 768;
                const newMode = isSmall ? 'cards' : 'table';
                if (newMode !== currentDisplayMode) {{
                    currentDisplayMode = newMode;
                    filterAndSort();
                }}
            }}
        }});

        function showLoadingOverlay(title = "Updating Live Standings", subtitle = "Please wait while the system processes results...") {{
            document.getElementById('loading-title').innerText = title;
            document.getElementById('loading-subtitle').innerText = subtitle;
            document.getElementById('global-loading-overlay').style.display = 'flex';
        }}

        function hideLoadingOverlay() {{
            document.getElementById('global-loading-overlay').style.display = 'none';
        }}

        // Initialize Navigation Tabs
        function initNavigationTabs() {{
            const navContainer = document.getElementById('nav-tabs-container');
            const dropdown = document.getElementById('gw-quick-select');
            
            let dropdownHtml = '<option value="leaderboard">🏆 Season Leaderboard</option>';
            
            const gwKeys = Object.keys(ALL_GAMEWEEKS).sort((a, b) => parseInt(a) - parseInt(b));
            
            gwKeys.forEach(gwKey => {{
                const gwNum = parseInt(gwKey);
                const gwData = ALL_GAMEWEEKS[gwKey];
                const predCount = (gwData.audited_records || []).length;
                
                // Add nav button
                const btn = document.createElement('button');
                btn.className = 'nav-tab-btn';
                btn.id = `tab-btn-gw-${{gwNum}}`;
                btn.innerHTML = `⚽ Gameweek ${{gwNum}} <span class="tab-counter">${{predCount}}</span>`;
                btn.onclick = () => switchMainTab(`gw_${{gwNum}}`);
                navContainer.appendChild(btn);

                // Add dropdown option
                dropdownHtml += `<option value="gw_${{gwNum}}">Gameweek ${{gwNum}} (${{predCount}} Predictions)</option>`;
            }});

            dropdown.innerHTML = dropdownHtml;
        }}

        function onGwDropdownChange(val) {{
            switchMainTab(val);
        }}

        function switchMainTab(tabKey) {{
            showLoadingOverlay("Switching View", "Loading predictions and match center...");
            setTimeout(() => {{
                currentTab = tabKey;
                
                // Update Tab Button Styles
                document.querySelectorAll('.nav-tab-btn').forEach(btn => btn.classList.remove('active'));
                if (tabKey === 'leaderboard') {{
                    document.getElementById('tab-btn-leaderboard')?.classList.add('active');
                    document.getElementById('gw-quick-select').value = 'leaderboard';
                }} else {{
                    const gwNum = tabKey.replace('gw_', '');
                    document.getElementById(`tab-btn-gw-${{gwNum}}`)?.classList.add('active');
                    document.getElementById('gw-quick-select').value = tabKey;
                    activeGameweekScope = parseInt(gwNum);
                }}

                // Toggle table panels & filter inputs
                const isLeaderboard = currentTab === 'leaderboard';
                document.getElementById('leaderboard-panel').style.display = isLeaderboard ? 'block' : 'none';
                document.getElementById('audit-panel').style.display = isLeaderboard ? 'none' : 'block';
                document.getElementById('statusFilter').style.display = isLeaderboard ? 'none' : 'inline-block';
                
                if (isLeaderboard) {{
                    document.getElementById('header-scope-badge').innerText = 'Season Standings';
                    document.getElementById('table-view-heading').innerHTML = '🏆 Cumulative Season Standings';
                    renderFixtures(activeGameweekScope);
                    renderSeasonMetrics();
                }} else {{
                    const gwNum = currentTab.replace('gw_', '');
                    document.getElementById('header-scope-badge').innerText = `Gameweek ${{gwNum}} Live Hub`;
                    document.getElementById('table-view-heading').innerHTML = `📋 Gameweek ${{gwNum}} Audited Submissions`;
                    renderFixtures(parseInt(gwNum));
                    renderGameweekMetrics(parseInt(gwNum));
                }}

                filterAndSort();
                hideLoadingOverlay();
            }}, 150);
        }}

        function renderFixtures(gwNum) {{
            const gwKey = String(gwNum);
            const gwData = ALL_GAMEWEEKS[gwKey] || {{ fixtures: [] }};
            const fixtures = gwData.fixtures || [];
            
            document.getElementById('fixture-center-title').innerText = `Gameweek ${{gwNum}} Match Results & Live Center (GMT / UK Time)`;

            const grid = document.getElementById('fixture-grid');
            if (fixtures.length === 0) {{
                grid.innerHTML = '<div style="color: var(--text-muted); padding: 12px;">No fixtures scheduled for this Gameweek.</div>';
                return;
            }}

            grid.innerHTML = fixtures.map(f => {{
                const hasScore = f.home_act !== null && f.away_act !== null && f.home_act !== undefined && f.away_act !== undefined;
                const d = new Date(f.kickoff);
                const timeStr = isNaN(d.getTime()) ? (f.kickoff || 'TBD') : d.toUTCString().replace(':00 GMT', ' GMT').replace(' 2026', '');
                
                const homeLogo = f.home_logo || getTeamLogoJS(f.home);
                const awayLogo = f.away_logo || getTeamLogoJS(f.away);
                const homeGoalsStr = formatGoalsJS(f.home_goals, f.home_goals_summary);
                const awayGoalsStr = formatGoalsJS(f.away_goals, f.away_goals_summary);
                const hasScorers = homeGoalsStr || awayGoalsStr;

                return `
                    <div class="fixture-card">
                        <div class="fix-header">
                            <span>${{timeStr}}</span>
                            <span class="${{hasScore ? 'fix-status-ft' : 'fix-status-upcoming'}}">${{hasScore ? 'FT' : 'UPCOMING'}}</span>
                        </div>
                        <div class="fix-team-row">
                            <span class="fix-team-name">
                                <img class="team-badge" src="${{homeLogo}}" alt="${{escapeHtml(f.home)}}" onerror="this.src='https://resources.premierleague.com/premierleague/badges/70/t3.png'">
                                <span>${{escapeHtml(f.home)}}</span>
                            </span>
                            <span class="${{hasScore ? 'fix-score' : 'fix-score-pending'}}">${{hasScore ? f.home_act : '-'}}</span>
                        </div>
                        <div class="fix-team-row">
                            <span class="fix-team-name">
                                <img class="team-badge" src="${{awayLogo}}" alt="${{escapeHtml(f.away)}}" onerror="this.src='https://resources.premierleague.com/premierleague/badges/70/t3.png'">
                                <span>${{escapeHtml(f.away)}}</span>
                            </span>
                            <span class="${{hasScore ? 'fix-score' : 'fix-score-pending'}}">${{hasScore ? f.away_act : '-'}}</span>
                        </div>
                        ${{hasScorers ? `
                            <div class="fix-scorers-box">
                                ${{homeGoalsStr ? `
                                    <div class="scorer-line">
                                        <span class="scorer-ball">⚽</span>
                                        <div><b>${{escapeHtml(f.home)}}:</b> ${{homeGoalsStr}}</div>
                                    </div>
                                ` : ''}}
                                ${{awayGoalsStr ? `
                                    <div class="scorer-line">
                                        <span class="scorer-ball">⚽</span>
                                        <div><b>${{escapeHtml(f.away)}}:</b> ${{awayGoalsStr}}</div>
                                    </div>
                                ` : ''}}
                            </div>
                        ` : ''}}
                    </div>
                `;
            }}).join('');
        }}

        function renderSeasonMetrics() {{
            document.getElementById('stat-1-lbl').innerText = 'Ranked Season Predictors';
            document.getElementById('stat-1-val').innerText = rawLeaderboard.length;

            const topPts = rawLeaderboard.length > 0 ? rawLeaderboard[0].Total_Season_Points : 0;
            document.getElementById('stat-2-lbl').innerText = 'Highest Season Total';
            document.getElementById('stat-2-val').innerText = topPts + ' pts';

            const totalExacts = rawLeaderboard.reduce((acc, r) => acc + (r['Total_Exact_Scores (3pts)'] || 0), 0);
            document.getElementById('stat-3-lbl').innerText = 'Total Season Exacts (3pts)';
            document.getElementById('stat-3-val').innerText = totalExacts;

            const totalGws = Object.keys(ALL_GAMEWEEKS).length;
            document.getElementById('stat-4-lbl').innerText = 'Completed Gameweeks';
            document.getElementById('stat-4-val').innerText = `${{totalGws}} / 38`;
        }}

        function renderGameweekMetrics(gwNum) {{
            const gwKey = String(gwNum);
            const gwData = ALL_GAMEWEEKS[gwKey] || {{ audited_records: [] }};
            const audits = gwData.audited_records || [];

            document.getElementById('stat-1-lbl').innerText = `GW ${{gwNum}} Predictors`;
            document.getElementById('stat-1-val').innerText = audits.length;

            if (audits.length > 0) {{
                const topGW = Math.max(...audits.map(r => r.total_points || 0));
                const exactCount = audits.reduce((sum, r) => sum + (r.exact_scores || 0), 0);
                const validCount = audits.filter(r => (r.status || '').startsWith("Valid")).length;
                
                document.getElementById('stat-2-lbl').innerText = `GW ${{gwNum}} Top Live Score`;
                document.getElementById('stat-2-val').innerText = topGW + " pts";
                
                document.getElementById('stat-3-lbl').innerText = `GW ${{gwNum}} Exacts (3pts)`;
                document.getElementById('stat-3-val').innerText = exactCount;
                
                document.getElementById('stat-4-lbl').innerText = `GW ${{gwNum}} Compliance Rate`;
                document.getElementById('stat-4-val').innerText = Math.round((validCount / audits.length) * 100) + "%";
            }} else {{
                document.getElementById('stat-2-val').innerText = "0 pts";
                document.getElementById('stat-3-val').innerText = "0";
                document.getElementById('stat-4-val').innerText = "0%";
            }}
        }}

        function filterAndSort() {{
            const q = document.getElementById('searchInput').value.toLowerCase();
            const statusF = document.getElementById('statusFilter').value;
            const sortF = document.getElementById('sortSelect').value;

            // Sync View Mode Toggle Button Styles
            const btnCards = document.getElementById('btn-view-cards');
            const btnTable = document.getElementById('btn-view-table');
            if (btnCards) btnCards.className = 'view-toggle-btn' + (currentDisplayMode === 'cards' ? ' active' : '');
            if (btnTable) btnTable.className = 'view-toggle-btn' + (currentDisplayMode === 'table' ? ' active' : '');

            if (currentTab === 'leaderboard') {{
                let data = [...rawLeaderboard].filter(r => (r.Author || '').toLowerCase().includes(q));
                if (sortF === 'exacts_desc') data.sort((a,b) => (b['Total_Exact_Scores (3pts)']||0) - (a['Total_Exact_Scores (3pts)']||0));
                else if (sortF === 'outcomes_desc') data.sort((a,b) => (b['Total_Outcome_Scores (1pt)']||0) - (a['Total_Outcome_Scores (1pt)']||0));
                else if (sortF === 'matches_desc') data.sort((a,b) => (b.Total_Matches_Predicted||0) - (a.Total_Matches_Predicted||0));
                else data.sort((a,b) => (b.Total_Season_Points||0) - (a.Total_Season_Points||0));

                if (currentDisplayMode === 'cards') {{
                    document.getElementById('leaderboard-panel').style.display = 'none';
                    document.getElementById('audit-panel').style.display = 'none';
                    const cardsPanel = document.getElementById('cards-view-panel');
                    cardsPanel.style.display = 'grid';

                    if (data.length === 0) {{
                        cardsPanel.innerHTML = '<div style="color: var(--text-muted); padding: 18px;">No predictors found matching query.</div>';
                        return;
                    }}

                    cardsPanel.innerHTML = data.map((r, idx) => {{
                        let badgeClass = idx === 0 ? 'rank-1' : (idx === 1 ? 'rank-2' : (idx === 2 ? 'rank-3' : 'rank-other'));
                        return `
                            <div class="mobile-card">
                                <div class="mobile-card-top">
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <span class="rank-badge ${{badgeClass}}">#${{r.Rank}}</span>
                                        <div class="mobile-card-user">${{escapeHtml(r.Author)}}</div>
                                    </div>
                                    <div class="mobile-card-pts-big">${{r.Total_Season_Points}} <span style="font-size: 0.82rem; color: var(--text-muted);">pts</span></div>
                                </div>
                                <div class="mobile-card-stats">
                                    <div class="mobile-card-stat-item">
                                        <span class="mobile-card-lbl">GWs Played</span>
                                        <span class="mobile-card-val">${{r.Gameweeks_Played}}</span>
                                    </div>
                                    <div class="mobile-card-stat-item">
                                        <span class="mobile-card-lbl">Matches</span>
                                        <span class="mobile-card-val">${{r.Total_Matches_Predicted}}</span>
                                    </div>
                                    <div class="mobile-card-stat-item">
                                        <span class="mobile-card-lbl">Exact (3pts)</span>
                                        <span class="mobile-card-val" style="color: var(--pl-gold);">${{r['Total_Exact_Scores (3pts)']}}</span>
                                    </div>
                                    <div class="mobile-card-stat-item">
                                        <span class="mobile-card-lbl">Outcome (1pt)</span>
                                        <span class="mobile-card-val" style="color: var(--pl-green);">${{r['Total_Outcome_Scores (1pt)']}}</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    }}).join('');
                }} else {{
                    document.getElementById('cards-view-panel').style.display = 'none';
                    document.getElementById('leaderboard-panel').style.display = 'block';
                    document.getElementById('audit-panel').style.display = 'none';

                    const tbody = document.getElementById('leaderboard-body');
                    tbody.innerHTML = data.map((r, idx) => {{
                        let badgeClass = idx === 0 ? 'rank-1' : (idx === 1 ? 'rank-2' : (idx === 2 ? 'rank-3' : 'rank-other'));
                        return `
                            <tr>
                                <td><span class="rank-badge ${{badgeClass}}">#${{r.Rank}}</span></td>
                                <td><b>${{escapeHtml(r.Author)}}</b></td>
                                <td>${{r.Gameweeks_Played}}</td>
                                <td>${{r.Total_Matches_Predicted}}</td>
                                <td><span class="pill pill-exact">${{r['Total_Exact_Scores (3pts)']}}</span></td>
                                <td>${{r['Total_Outcome_Scores (1pt)']}}</td>
                                <td><b style="color: var(--pl-green); font-size: 1.15rem; font-family: 'JetBrains Mono', monospace;">${{r.Total_Season_Points}} pts</b></td>
                            </tr>
                        `;
                    }}).join('');
                }}
            }} else {{
                const gwNum = currentTab.replace('gw_', '');
                const gwData = ALL_GAMEWEEKS[String(gwNum)] || {{ audited_records: [] }};
                const audits = gwData.audited_records || [];

                let data = [...audits].filter(r => (r.author || '').toLowerCase().includes(q));
                if (statusF === 'Valid') data = data.filter(r => (r.status || '').startsWith('Valid'));
                else if (statusF === 'Disqualified') data = data.filter(r => (r.status || '').includes('Edited') || (r.status || '').includes('Disqualified'));
                else if (statusF === 'Late') data = data.filter(r => (r.status || '').includes('concluded') || (r.status || '').includes('Late Submission'));

                if (sortF === 'exacts_desc') data.sort((a,b) => (b.exact_scores||0) - (a.exact_scores||0));
                else if (sortF === 'outcomes_desc') data.sort((a,b) => (b.outcome_scores||0) - (a.outcome_scores||0));
                else if (sortF === 'matches_desc') data.sort((a,b) => (b.matches_found||0) - (a.matches_found||0));
                else data.sort((a,b) => (b.total_points||0) - (a.total_points||0));

                if (currentDisplayMode === 'cards') {{
                    document.getElementById('leaderboard-panel').style.display = 'none';
                    document.getElementById('audit-panel').style.display = 'none';
                    const cardsPanel = document.getElementById('cards-view-panel');
                    cardsPanel.style.display = 'grid';

                    if (data.length === 0) {{
                        cardsPanel.innerHTML = '<div style="color: var(--text-muted); padding: 18px;">No submissions found matching filter.</div>';
                        return;
                    }}

                    cardsPanel.innerHTML = data.map((r) => {{
                        let pillClass = 'pill-valid';
                        const st = r.status || '';
                        if (st.startsWith('Valid*')) pillClass = 'pill-partial';
                        else if (st.includes('Edited') || st.includes('Disqualified')) pillClass = 'pill-disqualified';
                        else if (st.includes('Late')) pillClass = 'pill-late';

                        return `
                            <div class="mobile-card" onclick="openModal('${{r.comment_id}}', ${{gwNum}})">
                                <div class="mobile-card-top">
                                    <div>
                                        <div class="mobile-card-user">${{escapeHtml(r.author)}}</div>
                                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 3px; font-family: 'JetBrains Mono', monospace;">${{escapeHtml(r.submission_gmt || 'N/A')}}</div>
                                    </div>
                                    <div class="mobile-card-pts-big">${{r.total_points}} <span style="font-size: 0.82rem; color: var(--text-muted);">pts</span></div>
                                </div>
                                <div style="margin-bottom: 10px;">
                                    <span class="pill ${{pillClass}}">${{escapeHtml(r.status)}}</span>
                                </div>
                                <div class="mobile-card-stats">
                                    <div class="mobile-card-stat-item">
                                        <span class="mobile-card-lbl">Matches</span>
                                        <span class="mobile-card-val">${{r.matches_found}}</span>
                                    </div>
                                    <div class="mobile-card-stat-item">
                                        <span class="mobile-card-lbl">Exacts (3pts)</span>
                                        <span class="mobile-card-val" style="color: var(--pl-gold);">${{r.exact_scores}}</span>
                                    </div>
                                    <div class="mobile-card-stat-item">
                                        <span class="mobile-card-lbl">Outcomes (1pt)</span>
                                        <span class="mobile-card-val" style="color: var(--pl-green);">${{r.outcome_scores}}</span>
                                    </div>
                                    <div class="mobile-card-stat-item">
                                        <span class="mobile-card-lbl">GW Total</span>
                                        <span class="mobile-card-val" style="color: var(--pl-green);">${{r.total_points}} pts</span>
                                    </div>
                                </div>
                                <button class="mobile-card-inspect-btn" onclick="event.stopPropagation(); openModal('${{r.comment_id}}', ${{gwNum}})">🔍 Inspect Submission Details &rarr;</button>
                            </div>
                        `;
                    }}).join('');
                }} else {{
                    document.getElementById('cards-view-panel').style.display = 'none';
                    document.getElementById('leaderboard-panel').style.display = 'none';
                    document.getElementById('audit-panel').style.display = 'block';

                    const tbody = document.getElementById('audit-body');
                    tbody.innerHTML = data.map((r) => {{
                        let pillClass = 'pill-valid';
                        const st = r.status || '';
                        if (st.startsWith('Valid*')) pillClass = 'pill-partial';
                        else if (st.includes('Edited') || st.includes('Disqualified')) pillClass = 'pill-disqualified';
                        else if (st.includes('Late')) pillClass = 'pill-late';

                        return `
                            <tr onclick="openModal('${{r.comment_id}}', ${{gwNum}})">
                                <td><b>${{escapeHtml(r.author)}}</b></td>
                                <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--text-muted);">${{escapeHtml(r.submission_gmt || 'N/A')}}</td>
                                <td><span class="pill ${{pillClass}}">${{escapeHtml(r.status)}}</span></td>
                                <td>${{r.matches_found}}</td>
                                <td><span class="pill pill-exact">${{r.exact_scores}}</span></td>
                                <td>${{r.outcome_scores}}</td>
                                <td><b style="color: var(--pl-green); font-size: 1.1rem; font-family: 'JetBrains Mono', monospace;">${{r.total_points}} pts</b></td>
                                <td><button class="pill pill-valid" style="cursor:pointer;" onclick="event.stopPropagation(); openModal('${{r.comment_id}}', ${{gwNum}})">Inspect &rarr;</button></td>
                            </tr>
                        `;
                    }}).join('');
                }}
            }}
        }}

        function openModal(commentId, gwNum) {{
            const gwKey = String(gwNum || activeGameweekScope);
            const gwData = ALL_GAMEWEEKS[gwKey] || {{ audited_records: [] }};
            const r = (gwData.audited_records || []).find(x => x.comment_id === commentId);
            if (!r) return;

            document.getElementById('modal-author').innerText = `${{r.author}} (Gameweek ${{gwKey}})`;
            
            let statusPillClass = 'pill-valid';
            const st = r.status || '';
            if (st.startsWith('Valid*')) statusPillClass = 'pill-partial';
            else if (st.includes('Edited') || st.includes('Disqualified')) statusPillClass = 'pill-disqualified';
            else if (st.includes('Late')) statusPillClass = 'pill-late';

            document.getElementById('modal-status-container').innerHTML = `
                <span class="pill ${{statusPillClass}}">${{r.status}} | Live Points: ${{r.total_points}} pts</span>
            `;

            // Populate Timing Analysis Box
            document.getElementById('modal-submit-time').innerText = r.submission_gmt || 'N/A';
            
            const editRow = document.getElementById('modal-edit-row');
            if (r.is_edited && r.updated_gmt) {{
                editRow.style.display = 'flex';
                document.getElementById('modal-edit-time').innerText = `${{r.updated_gmt}} ${{r.edit_delta_str ? '(' + r.edit_delta_str + ')' : ''}}`;
            }} else {{
                editRow.style.display = 'none';
            }}

            const latenessRow = document.getElementById('modal-lateness-row');
            if (r.lateness_str) {{
                latenessRow.style.display = 'flex';
                document.getElementById('modal-lateness-val').innerText = r.lateness_str;
            }} else {{
                latenessRow.style.display = 'none';
            }}

            document.getElementById('modal-timing-summary').innerText = r.timing_analysis || 'No timing flags recorded.';

            // Edit History Section
            const editHistorySection = document.getElementById('modal-edit-history-section');
            const singleCommentSection = document.getElementById('modal-single-comment-section');

            if (r.is_edited) {{
                editHistorySection.style.display = 'block';
                singleCommentSection.style.display = 'none';

                const diffDesc = document.getElementById('modal-edit-diff-desc');
                const diffView = document.getElementById('modal-diff-view');
                const timeline = document.getElementById('modal-revisions-timeline');

                if (r.has_recorded_diff && r.diff_html) {{
                    diffDesc.innerText = "Comparing original snapshot vs in-between edits vs final version. Additions highlighted in green (+ added), modifications/deletions in red (- removed).";
                    diffView.style.display = 'block';
                    diffView.innerHTML = r.diff_html;
                }} else {{
                    diffDesc.innerText = "YouTube does not expose intermediate text states. Comment modification was detected via the YouTube API updated_at timestamp changing after original publish time.";
                    diffView.style.display = 'none';
                }}

                if (r.revisions && r.revisions.length > 0) {{
                    timeline.innerHTML = r.revisions.map((rev, revIdx) => `
                        <div class="version-block">
                            <div class="version-header">
                                <span style="color: ${{revIdx === 0 ? 'var(--pl-green)' : 'var(--pl-pink)'}};">
                                    ${{revIdx + 1}}. ${{rev.label}}
                                </span>
                                <span style="font-family: 'JetBrains Mono', monospace; color: var(--text-muted);">${{rev.timestamp_gmt}}</span>
                            </div>
                            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #ffe082; white-space: pre-wrap; line-height: 1.4;">${{escapeHtml(rev.text)}}</div>
                        </div>
                    `).join('');
                }} else {{
                    timeline.innerHTML = `
                        <div class="version-block">
                            <div class="version-header">
                                <span style="color: var(--pl-pink);">Current Modified Version (Disqualified)</span>
                                <span style="font-family: 'JetBrains Mono', monospace; color: var(--text-muted);">${{r.updated_gmt || r.submission_gmt}}</span>
                            </div>
                            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #ffe082; white-space: pre-wrap; line-height: 1.4;">${{escapeHtml(r.raw_text || '')}}</div>
                        </div>
                    `;
                }}
            }} else {{
                editHistorySection.style.display = 'none';
                singleCommentSection.style.display = 'block';
                document.getElementById('modal-raw-comment').innerText = r.raw_text || 'No text';
            }}

            // Fixtures breakdown list
            const fixContainer = document.getElementById('modal-fixtures-list');
            const fixDict = r.fixtures || {{}};
            const fixKeys = Object.keys(fixDict);

            if (fixKeys.length === 0) {{
                fixContainer.innerHTML = '<div style="color: var(--text-muted);">No fixture matches found in comment.</div>';
            }} else {{
                fixContainer.innerHTML = fixKeys.map(k => {{
                    const item = fixDict[k];
                    let rowClass = 'miss';
                    let badge = '<span class="pill" style="background: rgba(255,255,255,0.1);">0 pts</span>';
                    
                    if (item.points === 3) {{
                        rowClass = 'exact';
                        badge = '<span class="pill pill-exact">3 pts (Exact)</span>';
                    }} else if (item.points === 1) {{
                        rowClass = 'outcome';
                        badge = '<span class="pill pill-valid">1 pt (Outcome)</span>';
                    }} else if (item.result && item.result.includes('Void*')) {{
                        rowClass = 'voided';
                        badge = '<span class="pill pill-late">0 pts (Void* Late)</span>';
                    }} else if (item.result && item.result.includes('Disqualified')) {{
                        rowClass = 'voided';
                        badge = '<span class="pill pill-disqualified">0 pts (Edited)</span>';
                    }} else if (item.pred !== 'N/A' && item.actual === 'TBD') {{
                        rowClass = 'pending';
                        badge = '<span class="pill" style="background: rgba(255, 184, 0, 0.15); color: var(--pl-gold);">Pending Kickoff</span>';
                    }}

                    const parts = k.split(' vs ');
                    const hName = parts[0] ? parts[0].trim() : k;
                    const aName = parts[1] ? parts[1].trim() : '';
                    const hLogo = getTeamLogoJS(hName);
                    const aLogo = getTeamLogoJS(aName);

                    return `
                        <div class="fix-audit-row ${{rowClass}}">
                            <div>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <img src="${{hLogo}}" class="team-badge-sm" alt="${{escapeHtml(hName)}}" onerror="this.src='https://resources.premierleague.com/premierleague/badges/70/t3.png'">
                                    <b>${{escapeHtml(hName)}}</b>
                                    <span style="color: var(--text-muted); font-size: 0.8rem;">vs</span>
                                    <b>${{escapeHtml(aName)}}</b>
                                    ${{aName ? `<img src="${{aLogo}}" class="team-badge-sm" alt="${{escapeHtml(aName)}}" onerror="this.src='https://resources.premierleague.com/premierleague/badges/70/t3.png'">` : ''}}
                                </div>
                                <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 4px;">
                                    ${{item.result || 'No Match'}}
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.88rem;">
                                    Pred: <b style="color: var(--pl-green);">${{item.pred}}</b> | Actual: <b>${{item.actual}}</b>
                                </div>
                                ${{badge}}
                            </div>
                        </div>
                    `;
                }}).join('');
            }}

            document.getElementById('modal').classList.add('active');
        }}

        function closeModal() {{
            document.getElementById('modal').classList.remove('active');
        }}

        function escapeHtml(text) {{
            if (!text) return '';
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }}

        window.onclick = function(event) {{
            const modal = document.getElementById('modal');
            if (event.target === modal) {{
                closeModal();
            }}
        }}

        // Run On Load
        initNavigationTabs();
        switchMainTab('leaderboard');
    </script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
