// Maps Stripe price IDs to the GHL tag/delivery-link config for that product.
// Replace the placeholder keys and values once the 3 new products exist in
// Stripe and the Notion/Drive links + GHL tag names are finalized.
// See docs/checkout-to-nurture-flow.md section 6 for the source-of-truth table.

module.exports = {
  price_CORE_ID: {
    tier: "core",
    tag: "purchased:core",
    notionLink: "https://notion.so/REPLACE_CORE_TEMPLATE?duplicate=true",
    driveLink: "https://drive.google.com/drive/folders/REPLACE_CORE_FOLDER",
  },
  price_FULLOS_ID: {
    tier: "full-os",
    tag: "purchased:full-os",
    notionLink: "https://notion.so/REPLACE_FULLOS_TEMPLATE?duplicate=true",
    driveLink: "https://drive.google.com/drive/folders/REPLACE_FULLOS_FOLDER",
  },
  price_ADDONX_ID: {
    tier: "addon",
    tag: "purchased:addon-x",
    notionLink: "https://notion.so/REPLACE_ADDONX_TEMPLATE?duplicate=true",
    driveLink: "https://drive.google.com/drive/folders/REPLACE_ADDONX_FOLDER",
  },
};
