# FF Sidekick launch playbook

Draft season is the entire acquisition window (roughly now through the week
before NFL kickoff). Ship rough and fast; the Web Store review clock is the
bottleneck, so submit first.

## Order of operations
1. Submit the extension to the Chrome Web Store (review takes days).
2. While it reviews: record the demo GIF (marketing/ASSETS.md), set up Kit +
   ExtensionPay/Stripe (marketing/CUSTOMERS.md), and confirm the board on Pages.
3. When the listing is approved: swap `STORE_URL` in `index.html` for the real
   Web Store URL, then post to Reddit and (optionally) Show HN.

## 1. Chrome Web Store submission
- Developer account: one-time $5 registration.
- Package: zip the `extension/` folder contents (manifest at the zip root).
- Fields: copy from `store/LISTING.md`.
- Privacy: fill the data-collection disclosures exactly as in `store/LISTING.md`
  (financial/payment via Stripe, email on site, cookieless analytics). Do NOT
  claim "collects no data" — that is no longer true and Google checks.
- Assets: 128px icon (included), at least one 1280x800 screenshot (included),
  demo video/GIF once recorded.
- Justify `extensionpay.com` host permission: "process the season-pass purchase
  and verify license status."

## 2. Reddit (biggest fantasy channel)
r/fantasyfootball is strict about self-promo — post only in the pinned
tools/apps/self-promo thread, in creator voice, not ad copy.

Draft post:
> **I built a free draft board that live-syncs with your ESPN draft**
>
> Every pick in your ESPN room (real or mock) auto-crosses players off a fast
> research board — true averages, byes, SoS, depth charts, news. No server, no
> login, picks stay in your browser.
>
> Your first draft is free (try it in a mock). If you like it there's a $9.99
> season pass for unlimited drafts — figured I'd be upfront about that. Open
> source, feedback very welcome.
>
> Board: <UTM link>  ·  Extension: <UTM link>  ·  Code: github.com/AshritVerma/ff-sidekick

Lead with the free board + free first draft; let the pass be discovered in the
product. Also consider r/fantasyfootballadvice and r/DynastyFF where allowed.

## 3. Show HN (optional, for credibility/backlinks)
> **Show HN: A fantasy draft assistant with no backend — Chrome extension +
> static page**
>
> Replaced a paid draft assistant and a local Python helper with extension
> messaging and a static GitHub Pages board. Picks are scraped in the ESPN tab
> and handed to the board via chrome.runtime; data refresh is a GitHub Action.
> Monetized with ExtensionPay/Stripe. Notes on the architecture inside.

## UTM tagging (so channels are measurable in Plausible)
Append to every link you post:
- Reddit: `?utm_source=reddit&utm_medium=social&utm_campaign=launch2026`
- Show HN: `?utm_source=hn&utm_medium=social&utm_campaign=launch2026`
- Web Store listing link back to board: `?utm_source=webstore&utm_medium=referral&utm_campaign=launch2026`
- Gumroad: `?utm_source=gumroad&utm_medium=referral&utm_campaign=launch2026`

Plausible shows source/medium/campaign automatically, alongside the custom
funnel events already wired in the board (`email_unlock`, `get_extension_click`,
`live_draft_on`, `paywall_shown`, `pricing_click`).

## Don't bother (for a 10-day window)
- Paid ads and brand-new zero-follower social accounts won't move volume in time.
- Custom domain can wait; the Pages URL is fine for v1.
