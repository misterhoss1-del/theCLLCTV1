# Checkout → Delivery → Nurture Flow

Runbook for: Stripe checkout → GHL automation → delivery email (Notion template
+ Google Drive folder) → nurture tagging with Core→Full OS upsell path.

Placeholder products used throughout (swap in real names/prices/IDs when known):

| Placeholder    | Tier      | Notes                                   |
|----------------|-----------|------------------------------------------|
| `core`         | Core      | Entry tier, eligible for Full OS upsell |
| `full-os`      | Full OS   | Top tier, no upsell needed               |
| `addon-x`      | Add-on    | Sold alongside either tier                |

Replace the `PRICE_ID` / `PRODUCT_ID` placeholders in
`server/src/config/productMap.js` once the 3 new Stripe products exist.

## 1. Stripe setup

1. Add the 3 new products to the existing Stripe catalog (Products → Add
   product). For each, set:
   - A clear `name` (used in receipts/emails).
   - `metadata.tier` = `core` / `full-os` / `addon` — lets downstream logic
     branch without hardcoding product IDs everywhere.
2. Use Stripe Checkout (hosted page or Payment Links) for all products,
   existing and new, so the flow is uniform.
3. Note the `price_...` IDs — they're the join key between Stripe and the
   product/tag map (see §4).

## 2. Getting the purchase event into GHL

Pick one path depending on whether checkout runs through GHL or standalone Stripe.

**Path A — GHL native Stripe integration (preferred, no code)**
- Connect the Stripe account under GHL → Payments → Integrations.
- Build the checkout as a GHL Order Form / Payment Link using the connected
  Stripe products.
- GHL fires an internal "Order Form Submitted" / "Product Purchased" trigger
  automatically — no webhook plumbing needed. Skip to §3.

**Path B — Standalone Stripe Checkout (e.g. checkout lives outside GHL)**
- Stripe checkout stays where it is today; a webhook relays the purchase into
  GHL. Use the scaffold in `server/`:
  - `checkout.session.completed` webhook → look up the purchased price ID in
    `productMap.js` → upsert the GHL contact, add tags, set custom fields
    (`notion_link`, `drive_link`) for the email template to merge in.
  - See `server/README.md` for setup/deploy.

## 3. GHL workflow: trigger → delivery email → tag

Build one GHL workflow, triggered by "Order Form Submitted" (Path A) or
"Contact Tag Added: `purchased:*`" (Path B, since the webhook adds the tag
before the workflow trigger fires):

1. **Trigger**: Payment received / order submitted (or tag-added, Path B).
2. **Action — Send email** ("Delivery" template): merge fields
   `{{contact.notion_link}}` and `{{contact.drive_link}}` so one template
   works for every product instead of one email per SKU.
3. **Action — Add tag**: `purchased:<tier>` (e.g. `purchased:core`).
4. **Action — Add to workflow**: enrolls contact into the nurture sequence
   from §5.

## 4. Delivery assets: Notion + Google Drive

- **Notion template link**: use the public "Duplicate" template link format
  (`https://notion.so/.../template?duplicate=true`) so the buyer gets their
  own editable copy, not shared access to your source.
- **Google Drive folder**: share as *Viewer*, "Anyone with the link." Note
  Drive's "Make a copy" affordance only exists on individual Docs/Sheets/Slides
  files, not folders — two options:
  - Put a Google Doc at the top of the folder with a "Click to make your own
    copy" button linking to each file's `/copy` URL
    (`https://docs.google.com/.../copy`), or
  - Use Drive's built-in "Make a copy of folder" via a shared template folder
    (works for the whole folder, but requires the buyer to be signed into a
    Google account — call this out in the delivery email).

Store both links as GHL custom fields per product/tier so the same delivery
email template can merge the right pair in.

## 5. Nurture sequence + Core → Full OS upsell

- Everyone tagged `purchased:core` (and NOT already `purchased:full-os`)
  enters a "Core Nurture" sequence:
  1. Day 0: delivery email (§3) — already sent by the trigger workflow.
  2. Day 3–7: value/onboarding touches (use GHL nurture email defaults).
  3. Day 10+: Full OS upsell email/SMS — gated by a workflow "if/else" that
     checks `purchased:full-os` is absent, so buyers who already own Full OS
     never see the upsell.
- Everyone tagged `purchased:full-os` enters a "Full OS Nurture" sequence
  with no upsell step (retention/onboarding only).
- Add-on buyers (`purchased:addon-x`) get tagged but don't need a dedicated
  sequence unless requested — they ride whichever tier sequence they're
  already in.

## 6. Product → tag/sequence map (placeholders)

| Stripe price ID   | Tier    | Tag added         | Sequence entered        | Upsell? |
|--------------------|---------|--------------------|--------------------------|---------|
| `price_CORE_ID`    | core    | `purchased:core`   | Core Nurture             | Yes → Full OS |
| `price_FULLOS_ID`  | full-os | `purchased:full-os`| Full OS Nurture          | No |
| `price_ADDONX_ID`  | addon   | `purchased:addon-x`| (rides existing tier)    | No |

Update this table and `server/src/config/productMap.js` together once real
Stripe price IDs, GHL tag names, and workflow/sequence IDs are known.

## 7. Testing checklist

- [ ] Stripe test-mode purchase for each of the 3 new products completes
      checkout successfully.
- [ ] GHL contact is created/updated with the correct tag within a few
      seconds of purchase.
- [ ] Delivery email arrives with correct Notion + Drive links merged in
      (no `{{contact.notion_link}}` left unresolved).
- [ ] Core buyer is enrolled in the Core Nurture sequence and receives the
      Full OS upsell step after the configured delay.
- [ ] Full OS buyer does **not** receive the upsell step.
- [ ] Google Drive folder permission is confirmed view-only (buyer cannot
      edit the source files).
