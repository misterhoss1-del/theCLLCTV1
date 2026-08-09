const express = require("express");
const Stripe = require("stripe");
const productMap = require("../config/productMap");
const { upsertContactWithDelivery } = require("../lib/ghl");

const router = express.Router();
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

// Needs the raw body to verify the Stripe signature, so this route is
// mounted with express.raw() in index.js rather than the JSON body parser.
router.post("/", async (req, res) => {
  let event;
  try {
    event = stripe.webhooks.constructEvent(
      req.body,
      req.headers["stripe-signature"],
      process.env.STRIPE_WEBHOOK_SECRET
    );
  } catch (err) {
    console.error("Stripe signature verification failed:", err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  if (event.type !== "checkout.session.completed") {
    return res.json({ received: true, skipped: event.type });
  }

  try {
    const session = event.data.object;
    const email = session.customer_details?.email;
    if (!email) {
      console.error("No customer email on session", session.id);
      return res.status(200).json({ received: true, error: "missing_email" });
    }

    const lineItems = await stripe.checkout.sessions.listLineItems(session.id, {
      expand: ["data.price"],
    });

    for (const item of lineItems.data) {
      const config = productMap[item.price.id];
      if (!config) {
        console.warn(`No product map entry for price ${item.price.id}, skipping`);
        continue;
      }
      await upsertContactWithDelivery({ email, ...config });
    }

    return res.json({ received: true });
  } catch (err) {
    console.error("Failed to process checkout.session.completed:", err);
    // Return 500 so Stripe retries the webhook.
    return res.status(500).json({ received: false });
  }
});

module.exports = router;
