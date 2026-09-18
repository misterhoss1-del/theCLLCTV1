from __future__ import annotations

import csv
from typing import Any

from .apollo_client import ApolloClient
from .config import ICPConfig, SequenceConfig
from .hubspot_client import HubSpotClient
from .scoring import classify, score_lead
from .sequences import render_sequence
from .store import Lead, LeadStore


def prospect(store: LeadStore, icp: ICPConfig, client: ApolloClient | None = None) -> int:
    client = client or ApolloClient()
    people = client.search_all(icp)
    count = 0
    for person in people:
        org = person.get("organization") or {}
        lead = Lead(
            id=person["id"],
            linkedin_url=person.get("linkedin_url"),
            first_name=person.get("first_name"),
            last_name=person.get("last_name"),
            title=person.get("title"),
            company=org.get("name"),
            industry=org.get("industry"),
            company_size=org.get("estimated_num_employees"),
            annual_revenue=org.get("annual_revenue"),
            founded_year=org.get("founded_year"),
            location=person.get("city"),
            email=person.get("email"),
            headline=person.get("headline"),
        )
        store.upsert(lead)
        count += 1
    return count


def score_all(store: LeadStore, icp: ICPConfig) -> dict[str, int]:
    results = {"qualified": 0, "disqualified": 0}
    for lead in store.list_by_status("new"):
        score = score_lead(lead, icp)
        status = classify(score, icp.qualified_threshold)
        store.set_score(lead.id, score, status)
        results[status] += 1
    return results


def generate_sequences(
    store: LeadStore, sequence: SequenceConfig, out_path: str
) -> int:
    qualified = store.list_by_status("qualified")
    rows: list[dict[str, Any]] = []
    for lead in qualified:
        for msg in render_sequence(lead, sequence):
            rows.append(
                {
                    "lead_id": lead.id,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "company": lead.company,
                    "linkedin_url": lead.linkedin_url,
                    "step": msg.step_name,
                    "send_on_day": msg.offset_days,
                    "message": msg.body,
                }
            )
        store.set_status(lead.id, "sequenced")

    if rows:
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    return len(qualified)


def sync_hubspot(store: LeadStore, client: HubSpotClient | None = None) -> dict[str, int]:
    client = client or HubSpotClient()
    results = {"synced": 0, "skipped_no_email": 0}
    for lead in store.list_by_status("sequenced"):
        if not lead.email:
            results["skipped_no_email"] += 1
            continue
        result = client.upsert_contact(lead)
        store.set_hubspot_id(lead.id, result["id"])
        store.set_status(lead.id, "synced")
        results["synced"] += 1
    return results
