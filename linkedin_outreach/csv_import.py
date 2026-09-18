from __future__ import annotations

import csv
import hashlib

from .store import Lead, LeadStore


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _parse_int(value: str | None) -> int | None:
    value = _clean(value)
    if value is None:
        return None
    try:
        return int(float(value.replace(",", "")))
    except ValueError:
        return None


def _lead_id(row: dict[str, str]) -> str:
    linkedin_url = _clean(row.get("Person Linkedin Url"))
    if linkedin_url:
        return linkedin_url.rstrip("/")
    key = "|".join(
        row.get(k, "") for k in ("First Name", "Last Name", "Company", "Email")
    )
    return hashlib.sha1(key.encode()).hexdigest()


def _location(row: dict[str, str]) -> str | None:
    city = _clean(row.get("City"))
    region = _clean(row.get("State")) or _clean(row.get("Country"))
    parts = [p for p in (city, region) if p]
    return ", ".join(parts) if parts else None


def _headline(row: dict[str, str]) -> str | None:
    parts = [row.get("Title", ""), row.get("Keywords", ""), row.get("SEO Description", "")]
    text = " ".join(p for p in parts if p).strip()
    return text or None


def import_csv(store: LeadStore, path: str) -> int:
    """Import leads from an Apollo-style CSV export (First Name, Last Name,
    Title, Company, Email, # Employees, Industry, Person Linkedin Url,
    Annual Revenue, City/State/Country, ...). Missing columns are skipped
    silently; scoring already tolerates missing fields."""
    count = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not (_clean(row.get("First Name")) or _clean(row.get("Company"))):
                continue
            lead = Lead(
                id=_lead_id(row),
                linkedin_url=_clean(row.get("Person Linkedin Url")),
                first_name=_clean(row.get("First Name")),
                last_name=_clean(row.get("Last Name")),
                title=_clean(row.get("Title")),
                company=_clean(row.get("Company")),
                industry=_clean(row.get("Industry")),
                company_size=_parse_int(row.get("# Employees")),
                annual_revenue=_parse_int(row.get("Annual Revenue")),
                location=_location(row),
                email=_clean(row.get("Email")),
                headline=_headline(row),
            )
            store.upsert(lead)
            count += 1
    return count
