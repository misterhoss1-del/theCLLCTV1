const GHL_API_BASE = "https://services.leadconnectorhq.com";
const GHL_API_VERSION = "2021-07-28";

// Upserts a contact by email, adds the given tag, and sets the Notion/Drive
// delivery links as custom fields so the GHL email template can merge them
// (one template covers every product instead of one email per SKU).
async function upsertContactWithDelivery({ email, tag, notionLink, driveLink }) {
  const apiKey = process.env.GHL_API_KEY;
  const locationId = process.env.GHL_LOCATION_ID;

  if (!apiKey || !locationId) {
    throw new Error("GHL_API_KEY and GHL_LOCATION_ID must be set");
  }

  const response = await fetch(`${GHL_API_BASE}/contacts/upsert`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      Version: GHL_API_VERSION,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      locationId,
      email,
      tags: [tag],
      customFields: [
        { key: "notion_link", field_value: notionLink },
        { key: "drive_link", field_value: driveLink },
      ],
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`GHL upsert failed (${response.status}): ${body}`);
  }

  return response.json();
}

module.exports = { upsertContactWithDelivery };
