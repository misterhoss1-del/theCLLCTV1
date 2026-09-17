from __future__ import annotations

from .config import ICPConfig
from .store import Lead


def score_lead(lead: Lead, icp: ICPConfig) -> int:
    score = 0
    title = (lead.title or "").lower()
    headline = (lead.headline or "").lower()
    industry = (lead.industry or "").lower()

    if lead.title and any(t.lower() in title for t in icp.titles):
        score += 30

    if lead.title and any(t.lower() in title for t in icp.exclude_titles):
        return 0

    if lead.industry and any(i.lower() in industry for i in icp.exclude_industries):
        return 0

    if lead.industry and any(i.lower() in industry for i in icp.industries):
        score += 20

    if lead.company_size is not None:
        if icp.company_size_min <= lead.company_size <= icp.company_size_max:
            score += 15

    if icp.keywords and any(k.lower() in headline for k in icp.keywords):
        score += 15

    if lead.location and icp.locations and any(
        loc.lower() in lead.location.lower() for loc in icp.locations
    ):
        score += 10

    for rule in icp.scoring_rules:
        field_value = getattr(lead, rule.field, None)
        if field_value is None:
            continue
        if rule.range and isinstance(field_value, int):
            lo, hi = rule.range
            if lo <= field_value <= hi:
                score += rule.weight
        elif rule.match:
            value_str = str(field_value).lower()
            if any(m.lower() in value_str for m in rule.match):
                score += rule.weight

    return min(score, 100)


def classify(score: int, threshold: int) -> str:
    return "qualified" if score >= threshold else "disqualified"
