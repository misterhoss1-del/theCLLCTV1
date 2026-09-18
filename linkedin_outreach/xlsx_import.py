from __future__ import annotations

import hashlib

import openpyxl

from .store import Lead, LeadStore

_INDUSTRY_KEYWORDS = [
    (("plumb", "hvac", "electrician", "contractor", "handyman", "roofing",
      "landscap", "pest control", "cleaning service", "home service"),
     "Facilities Services"),
    (("construction", "builder", "remodel", "general contractor"), "Construction"),
    (("law firm", "attorney", "legal"), "Legal Services"),
    (("dental", "medical", "clinic", "physician", "urgent care"), "Medical Practice"),
    (("spa", "salon", "fitness", "gym", "wellness"), "Health, Wellness and Fitness"),
    (("accounting", "cpa", "bookkeep", "tax prep"), "Accounting"),
    (("real estate", "realtor", "property management"), "Real Estate"),
]


def _infer_industry(categories: str | None) -> str | None:
    if not categories:
        return None
    text = categories.lower()
    for keywords, industry in _INDUSTRY_KEYWORDS:
        if any(k in text for k in keywords):
            return industry
    return "Consumer Services"


def _clean(value) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _parse_int(value) -> int | None:
    value = _clean(value)
    if value is None:
        return None
    value = value.lstrip("<>").replace(",", "").strip()
    try:
        return int(float(value))
    except ValueError:
        return None


def _parse_money(value) -> int | None:
    value = _clean(value)
    if value is None:
        return None
    value = value.lstrip("<>").replace("$", "").replace(",", "").strip().upper()
    multiplier = 1
    if value.endswith("K"):
        multiplier, value = 1_000, value[:-1]
    elif value.endswith("M"):
        multiplier, value = 1_000_000, value[:-1]
    elif value.endswith("B"):
        multiplier, value = 1_000_000_000, value[:-1]
    value = value.strip()
    try:
        return int(float(value) * multiplier)
    except ValueError:
        return None


def _location(row: dict) -> str | None:
    city = _clean(row.get("City"))
    state = _clean(row.get("State"))
    parts = [p for p in (city, state) if p]
    return ", ".join(parts) if parts else None


def _lead_id(row: dict) -> str:
    email = _clean(row.get("Contact Email"))
    if email:
        return email.lower()
    key = "|".join(
        str(row.get(k, "")) for k in ("Business", "Contact First Name", "Contact Last Name")
    )
    return hashlib.sha1(key.encode()).hexdigest()


def import_xlsx(store: LeadStore, path: str, sheet: str | None = None) -> int:
    """Import leads from a local-business-list export (Business, Street,
    City, State, ..., Categories, Revenue, Employees, Founded, Contact
    First Name, Contact Last Name, Contact Role, Contact Email, ...).

    Only rows with a named contact are imported — a company record with no
    person attached isn't an outreach target. Industry is inferred from
    Categories since this export format doesn't carry an ICP-shaped
    industry field.
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = next(rows)

    count = 0
    for values in rows:
        row = dict(zip(header, values))
        if not _clean(row.get("Contact First Name")):
            continue
        lead = Lead(
            id=_lead_id(row),
            first_name=_clean(row.get("Contact First Name")),
            last_name=_clean(row.get("Contact Last Name")),
            title=_clean(row.get("Contact Role")),
            company=_clean(row.get("Business")),
            industry=_infer_industry(row.get("Categories")),
            company_size=_parse_int(row.get("Employees")),
            annual_revenue=_parse_money(row.get("Revenue")),
            founded_year=_parse_int(row.get("Founded")),
            location=_location(row),
            email=_clean(row.get("Contact Email")),
            headline=_clean(row.get("Description")),
        )
        store.upsert(lead)
        count += 1
    return count
