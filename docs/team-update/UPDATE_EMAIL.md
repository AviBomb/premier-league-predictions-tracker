**To:** Irish Guy Predictions team
**Subject:** Irish Guy Predictions: redesigned site and new features (ready for review)

Hi team,

Here's a summary of everything that changed between the original site and the new version. Every item has a one-line explanation and a screenshot. The new version runs locally and has been fully tested, but it isn't live yet, so nothing has changed for users so far.

**At a glance**

- Both pages, the public dashboard and the admin portal, have a new professional design for desktop and mobile.
- The dashboard page is **37× smaller** (5.7 MB down to 152 KB), so it opens much faster, especially on phones.
- **Scoring is unchanged.** After recalculating every finished gameweek, all 888 predictors kept the same standings.
- There are new features for predictors (AI predictions, Premier League table, profiles, sharing, installable app) and for admins (bulk actions, undo, manual entries, spam checks, activity log, CSV downloads).

---

## 1. The new look

**Dashboard (desktop).** A cleaner, modern layout with a clear header, a deadline countdown, summary cards and a tidier gameweek bar.

| Before | After |
|---|---|
| ![Original dashboard, desktop](img/01-before-dashboard-desktop.png) | ![New dashboard, desktop](img/01-after-dashboard-desktop.png) |

**Dashboard (mobile).** A compact header and a bottom navigation bar: Standings, Matches, PL table, Live GW and Admin.

| Before | After |
|---|---|
| ![Original dashboard, mobile](img/02-before-dashboard-mobile.png) | ![New dashboard, mobile](img/02-after-dashboard-mobile.png) |

**Admin portal.** It has the same tools as before, with clearer tabs, grouped review cards and bulk actions.

| Before | After |
|---|---|
| ![Original admin portal](img/03-before-admin-typo-review.png) | ![New admin portal](img/03-after-admin-typo-review.png) |

---

## 2. What's new for predictors (public dashboard)

**Light and dark themes.** The site follows the phone or laptop setting automatically, and the sun/moon button switches between them.
![Light theme](img/04-light-theme.png)

**Header buttons.** Support opens an email to avi.bomb@gmail.com. Share sends a link to the exact view on screen. There's also the theme switch and a link to Admin.
![Header with Support, Share, theme and Admin](img/10-header-support-share-theme.png)

**Mobile fixtures.** Matches are now compact rows grouped by day, so results can be read without lots of scrolling. Tap a match to see the goal scorers.
![Mobile fixtures](img/05-mobile-fixtures.png)

**Desktop match centre.** It keeps the familiar card layout from the original desktop view and adds a crowd-picks line. This shows the home/draw/away split of everyone's predictions and the most popular scoreline. Kickoff times now show in each visitor's local time.
![Desktop match centre with crowd picks](img/06-desktop-match-centre-crowd-picks.png)

**Premier League table.** This is the live league table, with each club's last five results and a new **Next** column showing the next opponent's badge and whether it's a home (H) or away (A) game.
![Premier League table with next opponent](img/07-premier-league-table-next-opponent.png)

The same table on mobile:

![Premier League table on mobile](img/07b-mobile-league-table.png)

**AI predictions.** This is a new tab with the AI's predicted scoreline for every match in the next gameweek, plus win/draw/loss chances and expected goals. It uses a statistical goal model trained on this season's results and FPL team strengths.
![AI predictions](img/08-ai-predictions.png)

**Beat the AI.** A banner above the standings shows how the AI would rank if it had entered, currently #123 of 888, so predictors can see whether they're beating it.
![Standings with Beat the AI, rank movement and gameweek wins](img/12-standings-rank-movement.png)

**Rank movement and gameweek wins.** Green and red arrows show how many places each predictor moved since the last gameweek. A trophy marks gameweek winners. Both are visible in the screenshot above.

**Deadline countdown.** A live countdown to the next gameweek's first kickoff, shown in the visitor's local time.
![Deadline countdown](img/11-deadline-countdown.png)

**Faster standings.** The standings show 50 predictors at a time with a **Show 50 more** button. Search still covers all 888.
![Show more](img/13-standings-show-more.png)

**Predictor profiles.** Tap any name to see their season stats, a rank-over-time chart and every gameweek's points, with a link to their picks. Profiles have shareable links (for example `?user=@name`).
![Predictor profile](img/14-predictor-profile.png)

**Prediction inspector.** Redesigned to show the original YouTube comment, when it was posted relative to kickoff, and match-by-match points.
![Prediction inspector](img/15-prediction-inspector.png)

**Shareable links.** The address bar now remembers the selected gameweek and tab (for example `?view=gw_5&match=table`), so a shared link opens exactly that view. The browser's Back button steps through views too. On phones, the Share button opens the phone's share sheet.
![Mobile header with Share button](img/09-mobile-header-share.png)

**Installable app.** On a phone, "Add to Home Screen" installs the site like an app with its own icon. If the connection drops, it shows the last loaded standings.
![App icon](img/23-app-icon.png)

**Removed: the Latest Results tab.** Final scores are still shown on each gameweek's fixtures and in the PL table form guide.

**Accessibility.** Keyboard focus now stays inside open pop-ups, Escape closes them, and focus goes back to the button that opened them.

---

## 3. What's new for admins (admin portal)

**Approve all / Reject all per gameweek.** One click clears every pending typo in the selected gameweek. Each predictor's card also has its own Approve all / Reject all.
![Approve all and reject all](img/16-admin-approve-reject-all.png)

**Confirmation step.** Bulk actions show exactly how many predictions and predictors are affected before anything is applied.
![Bulk confirmation](img/17-admin-bulk-confirm.png)

**Undo last bulk action.** A mistaken bulk approve or reject can be reversed with one click.
![Undo bulk action](img/17b-admin-undo-bulk.png)

**More lenient typo review (50%).** Predictions are now sent for review from 50% match confidence, down from 75%. All finished gameweeks were recalculated with the new setting: the review queue grew from 320 to 342 items, and standings didn't change.

**Keyboard shortcuts.** In typo review, J/K moves between items, A approves and R rejects. The next pending item is selected automatically. There's a hint line in the admin screenshot in section 1.

**Manual prediction entry.** Admins can add or fix a prediction when a comment was deleted or too garbled to read. Each entry records a reason and which admin added it.
![Manual entry](img/18-admin-manual-entry.png)

**Duplicate and spam checks.** These flag accounts posting identical scorelines, the same copied comment text, or several comments from one account. The checks are information only and never change scores.
![Duplicate and spam checks](img/19-admin-duplicate-spam-checks.png)

**Pipeline and activity tab.** Shows when scoring last ran and what it did, with a **Run pipeline now** button, plus a log of every admin change.
![Pipeline status and activity log](img/20-admin-pipeline-activity.png)

**CSV downloads.** One-click downloads of the season leaderboard, the selected gameweek's predictions, typo decisions, the admin activity log and the spam flags. They open in Excel or Google Sheets.
![Downloads](img/21-admin-downloads.png)

**Safer admin list.** Admin emails are no longer stored in plain text in the public files, only as a secure hash with a masked label (for example `av***1@gmail.com`).
![Authorized users](img/22-admin-authorized-users.png)

---

## 4. Behind the scenes (no visual change)

- **Faster loading:** the dashboard only downloads each gameweek's data when someone opens it, instead of everything upfront.
- **Smarter updates:** the 30-minute update only re-checks gameweeks whose comments, approvals or scores changed, and only publishes when something actually changed.
- **More reliable data:** Premier League data requests retry on failure, and the last good copy is shown if the source is down.
- **Tighter security:** the sync service only accepts requests from the official site. The local test server no longer pushes changes to GitHub automatically (it needs a `--push` option) and only accepts requests from the local machine.
- **Automatic checks:** the update process runs automatic tests before every deploy.
- **Shared code:** code used by both pages lives in one shared file, so fixes apply everywhere at once.

---

## 5. What hasn't changed

- The scoring rules are the same: 3 points for an exact score and 1 for the right result.
- Predictors still enter by commenting on The Irish Guy's YouTube videos.
- The admin sign-in (Google) and the approval workflow work as before.

**Next step:** once the team is happy with this, we'll publish it to the live site. Reply with any feedback or anything you'd like changed first.

Thanks,
Avi
