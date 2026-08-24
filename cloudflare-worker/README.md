# Cloud Sync Worker

A tiny, free Cloudflare Worker that lets `admin.html` (a static page hosted on
GitHub Pages) save admin decisions — typo approvals, corrected scores,
configuration changes — straight to your GitHub repo, **without ever putting a
GitHub token in a browser**.

## Why this exists

`admin.html` has no server of its own (GitHub Pages only serves static
files), so *something* needs to hold a GitHub credential to commit changes on
an admin's behalf. Instead of every admin pasting their own Personal Access
Token into `localStorage` (the old approach), this Worker holds **one**
credential centrally, and every admin just signs in with their normal Google
account. The Worker re-verifies that Google session on every request before
touching GitHub.

```
Admin's browser (admin.html)
   │  POST /api/save-approvals
   │  Authorization: Bearer <google-access-token>
   ▼
Cloudflare Worker (this folder)
   │  1. Calls Google userinfo with that token → gets verified email
   │  2. Reads config/gameweek_config.json from GitHub → checks email is an admin
   │  3. Commits the update to GitHub using the Worker's own secret token
   ▼
GitHub repo → triggers GitHub Actions → recalculates scores → redeploys Pages
```

Nobody but you (the person who sets this up) ever sees the GitHub token.

## One-time setup (you only need to do this once)

### 1. Create a fine-scoped GitHub token

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
2. Click **Generate new token**.
3. Set **Resource owner** to your account and **Repository access** to
   "Only select repositories" → choose `premier-league-predictions-tracker`.
4. Under **Repository permissions**, set **Contents** to **Read and write**.
5. Generate the token and copy it (you'll paste it once in step 4 below — it
   is never committed to git).

### 2. Install the Cloudflare CLI (Wrangler)

```bash
cd cloudflare-worker
npm install
```

This installs `wrangler` locally as a dev dependency (no global install
needed). You'll need a free [Cloudflare account](https://dash.cloudflare.com/sign-up).

### 3. Log in to Cloudflare

```bash
npx wrangler login
```

This opens a browser window to authorize Wrangler against your free
Cloudflare account.

### 4. Store the GitHub token as a Worker secret

```bash
npx wrangler secret put GITHUB_TOKEN
```

Paste the token from step 1 when prompted. This value is encrypted and stored
by Cloudflare — it is **not** written to any file in this repo.

### 5. Review `wrangler.toml`

Double-check `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_BRANCH`, and
`ALLOWED_ORIGIN` match your repo and GitHub Pages URL. These are plain
(non-secret) config values, safe to commit.

### 6. Deploy

```bash
npm run deploy
```

Wrangler prints a URL like:

```
https://pl-tracker-sync.<your-subdomain>.workers.dev
```

### 7. Wire it up in the Admin Portal

1. Open `admin.html`, sign in, go to **Tab 2 → Authorized Google
   Administrators**.
2. Under **☁️ Cloud Sync (Secure — No Token Sharing Required)**, paste the
   Worker URL from step 6 and click **Save & Test**.
3. That's it — every admin who opens `admin.html` from now on (any device,
   any browser) automatically syncs through this Worker after signing in with
   an authorized Google account. Nobody needs to configure anything else.

## Updating the Worker later

If you edit `src/index.js` or `wrangler.toml`, redeploy with:

```bash
npm run deploy
```

## Local testing (optional)

```bash
npm run dev
```

This runs the Worker locally (usually at `http://127.0.0.1:8787`). You can
temporarily point the Admin Portal's "Cloud Sync Worker URL" field at that
local address to test before deploying.

## Cost

Cloudflare Workers' free tier includes 100,000 requests/day, which is far
more than an admin panel for a prediction league will ever need.
