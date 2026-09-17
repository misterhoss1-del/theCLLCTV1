from unittest.mock import MagicMock

from linkedin_outreach.hubspot_client import HubSpotClient
from linkedin_outreach.store import Lead


def test_upsert_contact_uses_real_hubspot_property_names():
    client = HubSpotClient(token="fake-token")
    client.session = MagicMock()
    client.session.post.return_value.json.return_value = {"results": [{"id": "123"}]}

    lead = Lead(
        id="1",
        email="dana@glowmedspa.com",
        first_name="Dana",
        last_name="Reyes",
        title="Owner",
        company="Glow Med Spa",
        industry="Medical Practice",
        linkedin_url="https://linkedin.com/in/danareyes",
        score=90,
        status="qualified",
    )

    client.upsert_contact(lead)

    payload = client.session.post.call_args.kwargs["json"]
    properties = payload["inputs"][0]["properties"]

    # hs_linkedin_url is HubSpot's real default property; a bare
    # "linkedin_url" doesn't exist and HubSpot rejects unknown properties.
    assert properties["hs_linkedin_url"] == "https://linkedin.com/in/danareyes"
    assert "linkedin_url" not in properties
    assert properties["linkedin_outreach_score"] == 90
    assert properties["linkedin_outreach_status"] == "qualified"
