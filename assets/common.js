/*
 * Shared by dashboard.html (via templates/dashboard.html) and admin.html.
 * Loaded synchronously in <head> so the theme is applied before the first paint.
 */

// ---------- Theme: follows the device setting until the visitor picks one ----------
(function () {
    var root = document.documentElement;
    var media = window.matchMedia('(prefers-color-scheme: light)');
    function stored() { try { return localStorage.getItem('pl_theme'); } catch (e) { return null; } }
    function setTheme(theme) {
        root.setAttribute('data-theme', theme);
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', theme === 'light' ? '#f6f5f8' : '#0c0a10');
    }
    function apply() { setTheme(stored() || (media.matches ? 'light' : 'dark')); }
    apply();
    media.addEventListener('change', apply);
    window.plToggleTheme = function () {
        var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        try {
            if (next === (media.matches ? 'light' : 'dark')) localStorage.removeItem('pl_theme');
            else localStorage.setItem('pl_theme', next);
        } catch (e) { /* storage blocked: theme still switches for this visit */ }
        setTheme(next);
    };
})();

// ---------- Clubs & goals ----------
const FALLBACK_BADGE = 'https://resources.premierleague.com/premierleague/badges/70/t3.png';
const PL_BADGES = {
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
};

function getTeamLogoJS(name) {
    if (!name) return FALLBACK_BADGE;
    const clean = name.trim();
    if (PL_BADGES[clean]) return PL_BADGES[clean];
    for (const k in PL_BADGES) {
        if (clean.toLowerCase().includes(k.toLowerCase()) || k.toLowerCase().includes(clean.toLowerCase())) {
            return PL_BADGES[k];
        }
    }
    return FALLBACK_BADGE;
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatGoalsJS(goals, summaryFallback) {
    if (goals && Array.isArray(goals) && goals.length > 0) {
        return goals.map(g => {
            const min = g.minute ? `<b>${escapeHtml(g.minute)}</b>` : '';
            const scorer = g.scorer ? escapeHtml(g.scorer) : 'Goal';
            const isOg = g.type === 'OG' || g.type === 'O';
            const isPen = g.type === 'P' || g.type === 'PEN';
            const assist = (!isOg && g.assist) ? ` <span class="goal-assist">(assist: ${escapeHtml(g.assist)})</span>` : '';
            const type = isOg ? ' <span class="goal-tag goal-og">OG</span>' : (isPen ? ' <span class="goal-tag goal-pen">P</span>' : '');
            return `${scorer} ${min}${type}${assist}`;
        }).join('<span class="goal-sep">&bull;</span> ');
    }
    return escapeHtml(summaryFallback || '');
}

// ---------- Pop-ups: keep keyboard focus inside the open one, restore it on close ----------
const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex="-1"])';
const focusTraps = [];

function focusableIn(container) {
    return [...container.querySelectorAll(FOCUSABLE)].filter(el => !el.hidden && el.offsetParent !== null);
}

function trapFocus(container, onEscape) {
    releaseFocus(container);
    const trap = { container, previous: document.activeElement };
    trap.handler = event => {
        if (focusTraps.at(-1) !== trap) return; // only the top-most pop-up handles keys
        if (event.key === 'Escape' && onEscape) {
            event.preventDefault();
            event.stopImmediatePropagation();
            onEscape();
            return;
        }
        if (event.key !== 'Tab') return;
        const items = focusableIn(container);
        if (!items.length) {
            event.preventDefault();
            return;
        }
        const first = items[0];
        const last = items.at(-1);
        if (!container.contains(document.activeElement)) {
            event.preventDefault();
            first.focus();
        } else if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    };
    document.addEventListener('keydown', trap.handler, true);
    focusTraps.push(trap);
    requestAnimationFrame(() => (focusableIn(container)[0] || container).focus());
}

function releaseFocus(container) {
    const index = focusTraps.findIndex(t => t.container === container);
    if (index < 0) return;
    const [trap] = focusTraps.splice(index, 1);
    document.removeEventListener('keydown', trap.handler, true);
    if (trap.previous && document.contains(trap.previous) && typeof trap.previous.focus === 'function') trap.previous.focus();
}

// ---------- CSV downloads ----------
// Spreadsheet apps run cells that start with = + - @ as formulas; YouTube-style @handles are left as they are.
function csvCell(value) {
    if (typeof value === 'number') return String(value);
    let text = value === null || value === undefined ? '' : String(value);
    const risky = /^[=+\-\t\r]/.test(text) || (/^@/.test(text) && !/^@[\w.\-]*$/.test(text));
    if (risky) text = `'${text}`;
    return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function downloadCsv(filename, header, rows) {
    const lines = [header, ...rows].map(row => row.map(csvCell).join(','));
    const blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = Object.assign(document.createElement('a'), { href: url, download: filename });
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ---------- Sharing ----------
async function shareCurrentPage(title) {
    const url = window.location.href;
    if (navigator.share) {
        try {
            await navigator.share({ title, url });
            return 'shared';
        } catch (e) {
            if (e && e.name === 'AbortError') return 'cancelled';
        }
    }
    try {
        await navigator.clipboard.writeText(url);
        return 'copied';
    } catch (e) {
        window.prompt('Copy this link:', url);
        return 'prompted';
    }
}
