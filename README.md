# 🏆 Premier League Predictions Tracker & Live Analytics Engine

[![Auto-Update Premier League Predictions & Leaderboard](https://github.com/OWNER/REPO/actions/workflows/update_predictions.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/update_predictions.yml)
[![Live Dashboard](https://img.shields.io/badge/Live-Dashboard-00ff87?style=flat&logo=premierleague&logoColor=000)](https://OWNER.github.io/REPO/)

An enterprise-grade automated NLP and sports analytics system that scrapes public YouTube predictions comments, normalizes team aliases and scorelines, enforces deadlines and anti-spam integrity rules, calculates live gameweek standings, and hosts an interactive glassmorphic web dashboard & authenticated admin portal.

---

## 🌟 Key Features

* **Real-Time Live Scoring & Fixture Service**: Connects directly to the Official Premier League / FPL API to fetch live match scores, kickoff deadlines in GMT/UTC, and match statuses (FT/In-Progress/Upcoming).
* **Multi-Gameweek Archival**: Seamlessly tracks season-long cumulative leaderboards across Gameweek 1 through Gameweek 38.
* **Typo & Spelling Review Hub**: Integrated Admin Review portal with confidence scoring (Levenshtein & phonetic matching) allowing admins to batch-approve or reject borderline spelling variations.
* **Official PL Club Aliases Matrix**: Interactive customizable mapping table supporting 140+ nicknames and abbreviations across all 20 Premier League clubs.
* **Enterprise Google OAuth 2.0 Security**: Role-based access control allowing only authorized Google administrator emails to modify configurations and review queues.
* **Zero-Maintenance GitHub Actions CI/CD**: Automatically runs hourly during matchdays, updates predictions, recalculates leaderboards, and publishes live to **GitHub Pages**.

---

## 📁 Repository Structure

```text
pl_predictions_tracker/
├── .github/
│   └── workflows/
│       └── update_predictions.yml    # Hourly GitHub Actions cron & Pages deployer
├── config/
│   └── gameweek_config.json          # Active Gameweek, fixtures, and authorized admins
├── data/
│   ├── all_gameweeks_data.json       # Multi-Gameweek parsed store
│   ├── history_db.json               # Historical predictions state
│   ├── admin_approvals.json          # Human-in-the-loop decisions
│   └── pending_approvals.json        # Typo review candidates
├── exports/
│   ├── GW1_Parsed_Predictions.csv    # Match-by-match prediction audit sheet
│   └── Cumulative_Leaderboard.csv    # Season-long ranked standings
├── src/
│   ├── fixture_service.py            # Official Premier League / FPL live API integration
│   ├── team_aliases.py               # Canonical 20-club matrix & abbreviation resolver
│   ├── scraper.py                    # YouTube Data API v3 scraper
│   ├── nlp_parser.py                 # Multi-pattern regex & scoreline extractor
│   ├── scoring_engine.py             # Integrity audit & deadline calculator (3pts/1pt)
│   ├── leaderboard_manager.py        # Cumulative points aggregator & CSV generator
│   └── dashboard_generator.py        # HTML5 glassmorphic dashboard builder
├── admin.html                        # Authenticated enterprise admin management portal
├── dashboard.html                    # Public live predictions dashboard
├── index.html                        # Root landing page for GitHub Pages
├── server.py                         # Local Python development server & REST API
├── main.py                           # Master pipeline orchestrator
├── requirements.txt                  # Python dependencies
└── .env.example                      # Environment variables template
```

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the repository
```bash
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
cd <YOUR_REPO_NAME>
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and provide your API keys:
```bash
cp .env.example .env
```
```env
YOUTUBE_API_KEY=your_youtube_data_api_v3_key
GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
```

### 4. Run the Pipeline & Start Server
```bash
# Run prediction scraping & score calculation
python main.py

# Start local server on http://127.0.0.1:3000
python server.py
```
Open **[http://127.0.0.1:3000/dashboard.html](http://127.0.0.1:3000/dashboard.html)** for the Public Leaderboard, or **[http://127.0.0.1:3000/admin.html](http://127.0.0.1:3000/admin.html)** for the Admin Hub.

---

## 🌐 Deploying to GitHub (Step-by-Step Guide)

Follow these steps to push this project to GitHub and make it publicly accessible:

### Step 1: Create a New GitHub Repository
1. Go to [GitHub.com/new](https://github.com/new).
2. Name your repository (e.g. `premier-league-predictions-tracker`).
3. Choose **Public** and click **Create repository** (do not initialize with README or .gitignore).

### Step 2: Push Local Code to GitHub
Run the following commands in your project terminal:
```bash
# 1. Stage and commit all files
git add .
git commit -m "Initial release: Premier League Predictions Tracker & Live Dashboard"

# 2. Rename branch to main
git branch -M main

# 3. Add your remote repository (replace with your repo URL)
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git

# 4. Push code to GitHub
git push -u origin main
```

---

### Step 3: Enable GitHub Pages (Free Instant Hosting)
1. In your GitHub repository, navigate to **Settings** → **Pages** (in the left sidebar).
2. Under **Build and deployment** → **Source**, select:
   * **GitHub Actions** (recommended for automatic hourly scraping updates) OR
   * **Deploy from a branch** → Branch: `main` / Folder: `/ (root)` → Click **Save**.
3. Your live dashboard will be accessible at:
   `https://<YOUR_USERNAME>.github.io/<YOUR_REPO_NAME>/`

---

### Step 4: Add GitHub Secrets (For Automated Hourly Scraping)
To allow GitHub Actions to scrape YouTube comments and update match scores automatically:
1. In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret** and add:
   * `YOUTUBE_API_KEY`: Your YouTube Data API v3 Key.
   * `GOOGLE_CLIENT_ID`: Your Google OAuth 2.0 Client ID.
3. Done! The workflow `.github/workflows/update_predictions.yml` will now run automatically on an hourly cron and keep the live leaderboard updated without any manual intervention.

---

## 🔒 Enterprise Google Authentication Setup

To configure Google Sign-In for authorized administrators on `admin.html`:
1. Open [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Create an **OAuth 2.0 Client ID** (Web application).
3. Add Authorized JavaScript Origins:
   * Local: `http://127.0.0.1:3000` and `http://localhost:3000`
   * Production: `https://<YOUR_USERNAME>.github.io`
4. Add authorized admin emails directly in `admin.html` under the **👥 Authorized Google Users** tab or in `config/gameweek_config.json`.
