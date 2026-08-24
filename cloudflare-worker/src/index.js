/**
 * Cloud Sync Worker — Premier League Predictions Tracker
 *
 * Purpose: let admin.html (a static page on GitHub Pages) persist admin
 * decisions (typo approvals, corrected scores, configuration edits) straight
 * to the GitHub repo — WITHOUT any admin ever holding a GitHub token.
 *
 * How it stays secure:
 *  1. The GitHub token lives only as a Worker secret (`GITHUB_TOKEN`), set once
 *     by the site owner via `wrangler secret put GITHUB_TOKEN`. It never
 *     reaches the browser.
 *  2. Every request must include the caller's short-lived Google OAuth access
 *     token (Authorization: Bearer <token>). This Worker independently calls
 *     Google's userinfo endpoint to resolve the caller's verified email — it
 *     does not trust anything the browser claims about who is signed in.
 *  3. The resolved email is checked against the LIVE `authorized_users_sha256`
 *     / `authorized_users` lists inside config/gameweek_config.json on the
 *     `main` branch, so the admin allow-list has exactly one source of truth
 *     (the same file admin.html already manages).
 *  4. Only two hard-coded file paths can ever be written to
 *     (data/admin_approvals.json and config/gameweek_config.json) — this
 *     Worker cannot be used to write arbitrary files.
 */

const GITHUB_API = "https://api.github.com";

const ROUTES = {
  "/api/save-approvals": { path: "data/admin_approvals.json", label: "typo approvals" },
  "/api/save-config": { path: "config/gameweek_config.json", label: "gameweek configuration" },
};

function corsHeaders(env) {
  return {
    "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN || "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
  };
}

function jsonResponse(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...headers, "Content-Type": "application/json" },
  });
}

async function sha256Hex(text) {
  const data = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function githubHeaders(env, extra = {}) {
  return {
    Authorization: `Bearer ${env.GITHUB_TOKEN}`,
    "User-Agent": "pl-tracker-sync-worker",
    Accept: "application/vnd.github+json",
    ...extra,
  };
}

async function resolveGoogleEmail(request) {
  const authHeader = request.headers.get("Authorization") || "";
  const accessToken = authHeader.replace(/^Bearer\s+/i, "").trim();
  if (!accessToken) {
    return { error: "Missing Google access token" };
  }

  const res = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) {
    return { error: "Invalid or expired Google session — please sign in again" };
  }

  const info = await res.json();
  const email = (info.email || "").toLowerCase().trim();
  if (!email || info.email_verified === false) {
    return { error: "Unverified Google account" };
  }
  return { email };
}

async function loadAuthorizedEmailSets(env) {
  const res = await fetch(
    `${GITHUB_API}/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/config/gameweek_config.json?ref=${env.GITHUB_BRANCH}`,
    { headers: githubHeaders(env) }
  );
  if (!res.ok) {
    throw new Error("Could not load the authorized admin list from GitHub");
  }
  const file = await res.json();
  const decoded = decodeURIComponent(escape(atob(file.content.replace(/\n/g, ""))));
  const config = JSON.parse(decoded);
  const authObj = config.google_auth || {};
  const hashes = authObj.authorized_users_sha256 || [];
  const plain = (authObj.authorized_users || []).map((e) => String(e).toLowerCase().trim());
  return { hashes, plain };
}

async function verifyAdmin(request, env) {
  const { email, error } = await resolveGoogleEmail(request);
  if (error) return { ok: false, error };

  const { hashes, plain } = await loadAuthorizedEmailSets(env);
  const emailHash = await sha256Hex(email);
  const isAuthorized = hashes.includes(emailHash) || plain.includes(email);

  if (!isAuthorized) {
    return { ok: false, error: `${email} is not an authorized admin` };
  }
  return { ok: true, email };
}

async function commitJsonFile(env, path, contentObj, commitMessage) {
  const getRes = await fetch(
    `${GITHUB_API}/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/${path}?ref=${env.GITHUB_BRANCH}`,
    { headers: githubHeaders(env) }
  );

  let sha;
  if (getRes.ok) {
    const existing = await getRes.json();
    sha = existing.sha;
  }

  const contentStr = JSON.stringify(contentObj, null, 2);
  const contentB64 = btoa(unescape(encodeURIComponent(contentStr)));

  const putRes = await fetch(`${GITHUB_API}/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/${path}`, {
    method: "PUT",
    headers: githubHeaders(env, { "Content-Type": "application/json" }),
    body: JSON.stringify({
      message: commitMessage,
      content: contentB64,
      branch: env.GITHUB_BRANCH,
      ...(sha ? { sha } : {}),
    }),
  });

  if (!putRes.ok) {
    const errText = await putRes.text();
    throw new Error(`GitHub commit failed (${putRes.status}): ${errText}`);
  }
  return await putRes.json();
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const headers = corsHeaders(env);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers });
    }

    const route = ROUTES[url.pathname];
    if (!route) {
      return jsonResponse({ ok: false, error: "Unknown endpoint" }, 404, headers);
    }
    if (request.method !== "POST") {
      return jsonResponse({ ok: false, error: "Method not allowed" }, 405, headers);
    }

    try {
      const auth = await verifyAdmin(request, env);
      if (!auth.ok) {
        return jsonResponse({ ok: false, error: auth.error }, 403, headers);
      }

      const body = await request.json();
      await commitJsonFile(env, route.path, body, `admin: update ${route.label} via Admin Portal (${auth.email})`);

      return jsonResponse({ ok: true }, 200, headers);
    } catch (err) {
      return jsonResponse({ ok: false, error: err.message || "Unexpected error" }, 500, headers);
    }
  },
};
