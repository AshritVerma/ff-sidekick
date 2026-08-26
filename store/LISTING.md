# Chrome Web Store listing — FF Sidekick Draft Companion

Copy/paste fields for the developer dashboard at
https://chrome.google.com/webstore/devconsole. Publishing is a manual step
(one-time $5 developer registration required).

## Name
FF Sidekick Draft Companion

## Summary (132 char max)
Live-sync your ESPN draft picks to the FF Sidekick research board. First draft free; season pass unlocks unlimited drafts.

## Category
Sports

## Description
FF Sidekick turns your ESPN fantasy football draft into a live research board.

Open your ESPN draft (real league or mock), open the FF Sidekick board, and
every pick appears on the board as it happens — with true averages, bye weeks,
strength of schedule, depth charts, and aggregated player news at a glance.

No local server. No Python. No copying cookies. Install the extension, open the
board, flip Live Draft, and go.

Pricing:
- Your FIRST draft (mock or real) syncs free — try it in an ESPN mock draft.
- A one-time $9.99 season pass unlocks unlimited drafts for the 2026 season.
  (For comparison, other draft assistants charge ~$36/year.)

How it works:
- The extension reads the pick feed already shown in your ESPN draft room.
- It stores those picks in your browser only.
- The FF Sidekick board reads them back to strike drafted players, build
  rosters, and mark where your next pick lands.

Privacy: draft picks never leave your machine. Payment is handled by Stripe via
ExtensionPay; the board asks for your email and uses privacy-friendly, cookieless
analytics. Full policy: https://ashritverma.github.io/ff-sidekick/store/PRIVACY.md

Not affiliated with, endorsed by, or connected to ESPN. "ESPN" is used only to
describe the draft rooms this tool works with.

## Privacy practices (dashboard answers)
- Single purpose: sync ESPN draft picks to the FF Sidekick board.
- Permission justification (storage): store the current draft's picks and the
  season-pass license state locally.
- Host permission justification (fantasy.espn.com): read the draft-room pick feed.
- Host permission justification (extensionpay.com): process the season-pass
  purchase and check license status.
- Data collected (must be disclosed):
  - Financial/payment info — collected by Stripe via ExtensionPay to process the
    $9.99 purchase.
  - Email address — collected on the website to send product updates.
  - Website analytics — cookieless Plausible on the board site only.
- Data use: NOT sold to third parties; NOT used for unrelated purposes; NOT used
  for creditworthiness/lending. Payment/email used only to run the service.
- Draft picks are processed locally and are NOT transmitted.

## Assets needed before submitting
- Icon 128x128: extension/icons/icon128.png (included)
- Screenshots 1280x800 or 640x400 (at least one): store/screenshots/ (one included)
- Demo GIF/video of picks syncing live: see marketing/ASSETS.md
- Small promo tile 440x280 (optional)

## Store URL after approval
Paste the published URL back into index.html (STORE_URL constant) and into the
README so the install banner points at the real listing.
