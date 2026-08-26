# Launch assets checklist

The single most important asset is a short demo of picks disappearing off the
board in real time. It is the Web Store hero, the Reddit post, and the site
header, all at once. Everything else is quick.

## Already in the repo
- Extension icons: `extension/icons/icon16.png`, `icon48.png`, `icon128.png`
- Store icon 512: `store/icon512.png`
- One board screenshot: `store/screenshots/board-players-1280x800.png`

## Still to produce

### 1. Demo GIF / video (highest priority)
Shows the magic moment: a player gets drafted in ESPN and instantly gets struck
through on the FF Sidekick board.

How to record (all local, no real league needed):
1. Load the extension unpacked (`chrome://extensions` -> Load unpacked -> `extension/`).
2. Open an **ESPN mock draft** room in one tab, the board (localhost or the
   Pages URL) in another, and flip **Live Draft** on the board.
3. Arrange the two tabs/windows side by side so a pick in ESPN and the strike-
   through on the board are both visible.
4. Record 15–30 seconds covering 3–4 picks with a screen recorder (macOS:
   `Cmd+Shift+5`). Convert to GIF (e.g. `ffmpeg -i demo.mov -vf "fps=12,scale=900:-1" demo.gif`)
   or keep the MP4 for the Web Store (video is allowed).
5. Save to `marketing/demo.gif` (and/or upload as the Web Store promo video).

### 2. Screenshots (1280x800), 2–4 total
- Players table (have one).
- A live draft in progress with drafted players struck through.
- The board/roster view.
- A player card with news/depth chart.

### 3. Promo tile 440x280 (optional but helps)
- Logo + "Live ESPN draft sync" + "First draft free".

## Copy (canonical source: store/LISTING.md)
- Name, summary, description, and pricing lines live in `store/LISTING.md`.
- Always include the disclaimer: **Not affiliated with, endorsed by, or
  connected to ESPN.** Use "ESPN" descriptively ("works with ESPN drafts"),
  never in the product name or logo.
