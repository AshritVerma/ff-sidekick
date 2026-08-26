# Customer and lead tracking

FF Sidekick collects two audiences, in two systems, with no backend of our own.
This doc is the operating procedure for keeping them as one clean, segmented
list you can market future products to.

## The two sources

| Audience | Where it comes from | Where it lives | Tag |
| --- | --- | --- | --- |
| **Leads** | Email gate on the board (`index.html`) | Kit (ConvertKit) | `ff-sidekick-lead` |
| **Customers** | $9.99 season pass checkout | Stripe (via ExtensionPay) | `ff-sidekick-customer` |

- The board's email gate subscribes every visitor to a Kit form, tagged
  `ff-sidekick-lead` (see `KIT_TAG` in `index.html`).
- ExtensionPay runs the Stripe checkout; every payer's email + purchase date +
  license status is in the ExtensionPay dashboard, which is backed by your own
  Stripe account.

## One-time setup

1. **Kit (ConvertKit)**
   - Create a form named "FF Sidekick board".
   - Copy its form action URL into `KIT_FORM_ACTION` in `index.html`
     (e.g. `https://app.kit.com/forms/1234567/subscriptions`).
   - Create the tag `ff-sidekick-lead`.
2. **ExtensionPay + Stripe**
   - Register the extension at https://extensionpay.com with id `ff-sidekick`
     (must match `EXTPAY_ID` in `extension/background.js` and `extension/popup.js`).
   - Create a product: **FF Sidekick 2026 Season Pass**, **$9.99 one-time**.
   - Connect your Stripe account in the ExtensionPay dashboard.

## Weekly during draft season: merge customers into Kit

So leads and buyers are one segmented list you can email:

1. In Stripe (or the ExtensionPay dashboard) export payers: email + created date.
2. In Kit, bulk-import those emails and apply the tag `ff-sidekick-customer`.
   Kit dedupes by email, so existing leads simply gain the customer tag.
3. Now you can target:
   - `lead` AND NOT `customer` -> "still on the fence" upgrade nudges.
   - `customer` -> onboarding, next-season renewal, and future product launches.

Optional automation later: Stripe webhook -> Kit API to auto-tag on purchase.
Not needed for v1; the weekly manual export is enough at launch volume.

## What NOT to do

- Do not put payer emails in the repo or in any committed file.
- Do not email leads more than the gate promised ("one or two draft-season
  emails"). The list's long-term value for future products depends on it.
