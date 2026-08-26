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

### 2. (Optional) Install the extension for live draft sync
To watch picks land on the board during a real or mock ESPN draft:

1. Install **FF Sidekick** from the Chrome Web Store. _(Until the listing is
   live, load it unpacked — see [Developing the extension](#developing-the-extension).)_
2. Open your ESPN draft room (`fantasy.espn.com`) in one tab.
3. On the board, flip the **Live Draft** switch.

Picks stream in automatically. Drafted players get struck through, rosters fill
in, and the board marks where your next pick lands.

### Offline copy
Download **`ff-sidekick-standalone.html`** from this repo — it's a single file
with all data, images, and fonts embedded. Double-click to open; no server, no
network. (Live draft sync needs the hosted board + extension.)

### Privacy
The extension reads only the ESPN draft-room pick feed and stores picks in your
own browser. It has no backend and sends nothing anywhere. See
[store/PRIVACY.md](store/PRIVACY.md).

---

## For developers

### Layout
| Path | What it is |
| --- | --- |
| `index.html` | The board (static HTML/CSS/JS, no framework). Fetches `data.json`. |
| `data.json` | Player snapshot: top-300 PPR, schedule, matchups, coaches, news. |
| `ff-sidekick-standalone.html` | Single-file offline build (data + images + font embedded). |
| `extension/` | MV3 Chrome extension (draft companion). |
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

### Deploying
- **Board:** GitHub Pages serves this repo root. Push to `main`.
- **Extension:** package `extension/` and submit to the Chrome Web Store — see
  [store/LISTING.md](store/LISTING.md). After approval, update the `STORE_URL`
  constant in `index.html` so the install banner points at the listing.
