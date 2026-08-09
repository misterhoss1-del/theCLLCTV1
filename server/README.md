# Checkout webhook (Path B)

Only needed if Stripe Checkout runs **outside** GHL's native Stripe
integration. If checkout is a GHL Order Form/Payment Link, skip this — see
Path A in `../docs/checkout-to-nurture-flow.md`.

Relays `checkout.session.completed` from Stripe into GHL: upserts the buyer
as a contact, adds the tier's tag (`purchased:core` / `purchased:full-os` /
`purchased:addon-x`), and sets `notion_link` / `drive_link` custom fields so
the GHL delivery email template can merge them in.

## Setup

```bash
cd server
npm install
cp .env.example .env   # fill in Stripe + GHL credentials
```

Fill in real Stripe price IDs and delivery links in
`src/config/productMap.js` (currently placeholders — see
`../docs/checkout-to-nurture-flow.md` section 6).

## Run

```bash
npm start
```

Point a Stripe webhook (test mode: `stripe listen --forward-to
localhost:3000/webhooks/stripe`) at `/webhooks/stripe`, subscribed to
`checkout.session.completed`.

In GHL, build the workflow trigger off "Contact Tag Added: `purchased:*`"
(this route adds the tag before the workflow needs to fire) — see
`../docs/checkout-to-nurture-flow.md` section 3.
