require("dotenv").config();
const express = require("express");
const stripeWebhook = require("./routes/stripeWebhook");

const app = express();

// Mounted before express.json() because Stripe signature verification
// needs the raw request body, not the parsed one.
app.use("/webhooks/stripe", express.raw({ type: "application/json" }), stripeWebhook);

app.use(express.json());

app.get("/health", (req, res) => res.json({ ok: true }));

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Listening on port ${port}`));
