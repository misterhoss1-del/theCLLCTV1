from __future__ import annotations

from typing import Any

import requests

from .config import hubspot_token
from .store import Lead

BASE_URL = "https://api.hubapi.com"


class HubSpotClient:
    def __init__(self, token: str | None = None):
        self.token = token or hubspot_token()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
        )

    def upsert_contact(self, lead: Lead) -> dict[str, Any]:
        # linkedin_outreach_score and linkedin_outreach_status are custom
        # properties this integration owns, not HubSpot defaults — create
        # them once in Settings > Properties > Contact before the first
        # sync (see README). HubSpot's batch upsert rejects the whole
        # request if a property doesn't exist.
        if not lead.email:
            raise ValueError(f"lead {lead.id} has no email; cannot upsert to HubSpot")

        properties = {
            "email": lead.email,
            "firstname": lead.first_name,
            "lastname": lead.last_name,
            "jobtitle": lead.title,
            "company": lead.company,
            "industry": lead.industry,
            "linkedin_outreach_score": lead.score,
            "linkedin_outreach_status": lead.status,
            "hs_linkedin_url": lead.linkedin_url,
        }
        properties = {k: v for k, v in properties.items() if v is not None}

        payload = {
            "inputs": [
                {
                    "idProperty": "email",
                    "id": lead.email,
                    "properties": properties,
                }
            ]
        }
        resp = self.session.post(
            f"{BASE_URL}/crm/v3/objects/contacts/batch/upsert", json=payload
        )
        resp.raise_for_status()
        return resp.json()["results"][0]
