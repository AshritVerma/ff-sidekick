FF Sidekick Draft Companion — Chrome extension
==============================================

Syncs your ESPN draft-room picks to the FF Sidekick board. No local server, no
Python, no cookies — the extension stores picks itself and the website reads
them back.

INSTALL (recommended: from the Chrome Web Store)
  Search the Chrome Web Store for "FF Sidekick" and click Add to Chrome.

INSTALL (unpacked, for development)
  1. Chrome -> chrome://extensions
  2. Turn on "Developer mode" (top right)
  3. Click "Load unpacked" and select this `extension` folder.

USE
  1. Open the FF Sidekick board:  https://ashritverma.github.io/ff-sidekick/
  2. Open your ESPN draft room (real or mock) in another tab. A dark badge
     appears bottom-right reading "FF Sidekick · N picks tracked".
  3. On the board, flip the Live Draft switch. Picks stream in.

HOW IT WORKS
  - content.js reads the ESPN draft room's pick feed.
  - background.js stores picks in chrome.storage.session (per draft).
  - bridge.js is injected into the board page and relays those picks to it via
    window.postMessage, so the site never needs the extension's id.

PRIVACY
  Picks stay on your machine. The extension sends nothing to any server. See
  store/PRIVACY.md in the repo.
