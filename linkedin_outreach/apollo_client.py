from __future__ import annotations

from typing import Any

import requests

from .config import ICPConfig, apollo_api_key

BASE_URL = "https://api.apollo.io/v1"


class ApolloClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or apollo_api_key()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
            }
        )

    def search_people(self, icp: ICPConfig, page: int = 1, per_page: int = 25) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "person_titles": icp.titles,
            "organization_num_employees_ranges": [
                f"{icp.company_size_min},{icp.company_size_max}"
            ],
        }
        if icp.industries:
            payload["organization_industry_tag_ids"] = icp.industries
        if icp.locations:
            payload["person_locations"] = icp.locations
        if icp.keywords:
            payload["q_keywords"] = " ".join(icp.keywords)

        resp = self.session.post(f"{BASE_URL}/mixed_people/search", json=payload)
        resp.raise_for_status()
        return resp.json()

    def search_all(self, icp: ICPConfig) -> list[dict[str, Any]]:
        people: list[dict[str, Any]] = []
        page = 1
        per_page = 25
        while len(people) < icp.max_results:
            data = self.search_people(icp, page=page, per_page=per_page)
            batch = data.get("people", [])
            if not batch:
                break
            people.extend(batch)
            pagination = data.get("pagination", {})
            if page >= pagination.get("total_pages", page):
                break
            page += 1
        return people[: icp.max_results]

    def enrich_person(self, linkedin_url: str | None = None, email: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url
        if email:
            payload["email"] = email
        resp = self.session.post(f"{BASE_URL}/people/match", json=payload)
        resp.raise_for_status()
        return resp.json()
