# FF Sidekick

A fantasy football draft companion: a fast research board that turns your ESPN
draft into a live, sortable war room. Top-300 PPR values, true averages, bye
weeks, strength of schedule, depth charts, and aggregated player news — with
live pick tracking during your draft.

**Board:** https://ashritverma.github.io/ff-sidekick/

---

## For users

### 1. Open the board
Go to **https://ashritverma.github.io/ff-sidekick/**. That's the whole research
tool — search, sort, compare players, view depth charts and news. No install
needed for research.

<a id="install"></a>
### 2. (Optional) Install the extension for live draft sync
To watch picks land on the board during a real or mock ESPN draft:

1. Install **FF Sidekick** from the Chrome Web Store. _(Until the listing is
   live, load it unpacked — see [Developing the extension](#developing-the-extension).)_
2. Open your ESPN draft room (`fantasy.espn.com`) in one tab.
3. On the board, flip the **Live Draft** switch.

Picks stream in automatically. Drafted players get struck through, rosters fill
in, and the board marks where your next pick lands.

## Pricing
- The research **board is free** (email to open it).
- Your **first draft** — mock or real — **syncs free**. Try it in an ESPN mock draft.
- A one-time **$9.99 season pass** unlocks **unlimited drafts for the 2026
  season**. Upgrade from the FF Sidekick icon in your Chrome toolbar. (Other
  draft assistants charge ~$36/year.)

### Offline copy
Grab the single-file **offline board** (`ff-sidekick-standalone.html`): all data,
images, and fonts embedded, opens with no server or network — handy at a draft
party. It's downloadable free from this repo for the technically inclined, or as
a one-click **$2.99 download on Gumroad** _(link coming with launch)_. (Live
draft sync still needs the hosted board + extension.)

### Privacy
Draft picks are read only from the ESPN draft-room feed and stay in your own
browser. Payment is handled by Stripe (via ExtensionPay); the board asks for your
email and uses cookieless analytics. FF Sidekick is **not affiliated with ESPN**.
Full policy: [store/PRIVACY.md](store/PRIVACY.md).

---

## For developers

### Layout
| Path | What it is |
| --- | --- |
| `index.html` | The board (static HTML/CSS/JS, no framework). Fetches `data.json`. |
| `data.json` | Player snapshot: top-300 PPR, schedule, matchups, coaches, news. |
| `ff-sidekick-standalone.html` | Single-file offline build (data + images + font embedded). |
| `extension/` | MV3 Chrome extension (draft companion + season-pass gate). |
| `extension/ExtPay.js` | Vendored [ExtensionPay](https://extensionpay.com) client (Stripe checkout). |
| `extension/popup.html` / `popup.js` | Toolbar popup: pass status + $9.99 checkout. |
| `marketing/` | Launch playbook, asset checklist, customer/lead ops, Gumroad setup. |
| `fetch_espn.py` | Refresh ranks, projections, and per-player news. |
| `fetch_gamelogs.py` | Weekly PPR game logs and bye weeks. |
| `fetch_depth.py` | Head coaches, coordinators, and skill-position depth. |
| `build_standalone.py` | Bundle `index.html` + `data.json` + assets into the standalone. |
| `scripts/make_icons.py` | Generate the extension/site icons. |
| `.github/workflows/refresh.yml` | Daily data refresh (runs the fetch scripts, rebuilds, commits). |

### Refresh the data locally
```bash
pip install pillow
python3 fetch_espn.py          # ranks, projections, news (bakes news into data.json)
python3 fetch_gamelogs.py      # optional: weekly logs
python3 fetch_depth.py         # optional: depth charts
python3 build_standalone.py    # rebuild the offline file
```
In production this runs automatically via the daily GitHub Action.

### Run the board locally
```bash
python3 -m http.server 8000
# open http://localhost:8000/
```

### Developing the extension
1. `chrome://extensions` -> enable **Developer mode** -> **Load unpacked** ->
   select the `extension/` folder.
2. Open an ESPN draft room and the board (`http://localhost:8000/` is allowed by
   the extension's content-script matches).
3. Flip Live Draft on the board.

The extension stores picks in `chrome.storage.session`; `bridge.js` relays them
to the board via `window.postMessage`, so the page never needs the extension id.

### Configuration (fill before launch)
Placeholders that need real values, all clearly marked with `TODO`:
| Where | Constant | What to set |
| --- | --- | --- |
| `extension/background.js`, `extension/popup.js` | `EXTPAY_ID` | Your ExtensionPay extension id (register a $9.99 one-time product). |
| `index.html` | `KIT_FORM_ACTION` | Your Kit (ConvertKit) form action URL for the email gate. |
| `index.html` (head) | Plausible `data-domain` | The domain you register at plausible.io. |
| `index.html` | `STORE_URL` | Chrome Web Store listing URL, after approval. |
| `index.html` | `PRICING_URL` | Defaults to this README's `#pricing`; change if you make a pricing page. |

See [marketing/CUSTOMERS.md](marketing/CUSTOMERS.md) for the Kit + Stripe setup
and [marketing/LAUNCH.md](marketing/LAUNCH.md) for the full launch checklist.

### Deploying
- **Board:** GitHub Pages serves this repo root. Push to `main` and it is live in
  a minute or two, with no review. Keep as much logic here as possible — it is
  the only half of the product you can ship instantly.
- **Extension:** every store release is a zip upload against the same listing,
  and every one of them gets reviewed. Code-only changes from an established
  account usually clear in under a day; anything that adds a permission or
  widens a host pattern is treated close to a new submission and can take weeks,
  and it also **disables the extension for existing users** until each of them
  approves the new permission. Avoid touching the `permissions`,
  `host_permissions`, `content_scripts.matches` and `externally_connectable`
  blocks in [extension/manifest.json](extension/manifest.json) unless you have to.

#### First submission (manual, once)
The Web Store API can only update an item that already exists, so version one
has to go through the dashboard by hand:

```bash
scripts/package_extension.sh          # -> dist/ff-sidekick-extension-v2.1.0.zip
```

Upload that at the [developer dashboard](https://chrome.google.com/webstore/devconsole),
fill the listing from [store/LISTING.md](store/LISTING.md), and submit. Then set
the `STORE_URL` constant in `index.html` so the install banner points at the
listing, and add the five `CWS_*` secrets described in
[.github/workflows/publish-extension.yml](.github/workflows/publish-extension.yml).

#### Every release after that (automatic)
Any push to `main` that touches `extension/**` packages the extension and submits
it for review. Board-only pushes and the daily data-refresh commit are ignored on
purpose, since each store upload costs a review.

Versions are handled for you: `major.minor` comes from the manifest, so you bump
that by hand when a release deserves it, and the patch is the workflow run
number. That guarantees the strictly-increasing version the store demands without
a version-bump commit on every change, so the manifest in git reads `2.1.0` while
the published build is `2.1.<run>`. Each successful release is tagged `ext-v<version>`.

To build a zip without submitting it, run the workflow from the Actions tab with
**Submit for review** unchecked; it uploads as a draft you can inspect in the
dashboard. If the `CWS_*` secrets are missing the workflow still builds the zip
and attaches it as an artifact.
