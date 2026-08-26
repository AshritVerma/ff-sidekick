# Gumroad: the offline standalone board

`ff-sidekick-standalone.html` is a single self-contained file (all player data,
images, and fonts embedded) that opens with no internet and no server — handy at
a draft party with bad Wi-Fi. It is a nice paid artifact and a season-pass perk.

## Product setup
1. Create a Gumroad product: **FF Sidekick — Offline Draft Board**.
2. Price: **$2.99** one-time.
3. Upload the current `ff-sidekick-standalone.html` as the file. (Refresh the
   upload whenever the daily data pipeline produces a newer build you care about.)
4. Add a short description + one screenshot (reuse `store/screenshots/`).
5. Copy the product URL.

## Bundle it free with the season pass
Season-pass buyers should get the offline file at no extra cost:
- Simplest: in the ExtensionPay/Stripe post-purchase confirmation (or the popup's
  "Season pass active" state), link to a Gumroad **discount code** that makes the
  offline product free (create a 100%-off code in Gumroad).
- Or email the Gumroad free link to customers when you do the weekly
  customer-tag sync (see marketing/CUSTOMERS.md).

## Link it from the board (optional)
- Put the Gumroad URL in the README "Offline copy" section (done — update the
  placeholder link once the product is live).
- Optionally add a small "Get the offline copy" link in the board footer later.

## Note
The standalone file is also downloadable free from the repo for developers. The
Gumroad listing is for non-technical users who want a one-click purchase and to
support the project; keep the pricing framing honest ("also free on GitHub").
