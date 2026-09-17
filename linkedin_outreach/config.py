from __future__ import annotations

import os
from dataclasses import dataclass, field

import yaml


@dataclass
class ScoringRule:
    field: str
    match: list[str] = field(default_factory=list)
    range: list[int] | None = None
    weight: int = 0


@dataclass
class ICPConfig:
    name: str
    titles: list[str]
    industries: list[str]
    company_size_min: int
    company_size_max: int
    keywords: list[str]
    locations: list[str]
    exclude_titles: list[str]
    scoring_rules: list[ScoringRule]
    qualified_threshold: int
    max_results: int


@dataclass
class SequenceStep:
    name: str
    offset_days: int
    template: str


@dataclass
class SequenceConfig:
    name: str
    steps: list[SequenceStep]


def load_icp_config(path: str) -> ICPConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    rules = [
        ScoringRule(
            field=r["field"],
            match=r.get("match", []),
            range=r.get("range"),
            weight=r["weight"],
        )
        for r in raw.get("scoring_rules", [])
    ]

    return ICPConfig(
        name=raw["name"],
        titles=raw.get("titles", []),
        industries=raw.get("industries", []),
        company_size_min=raw.get("company_size_min", 1),
        company_size_max=raw.get("company_size_max", 100000),
        keywords=raw.get("keywords", []),
        locations=raw.get("locations", []),
        exclude_titles=raw.get("exclude_titles", []),
        scoring_rules=rules,
        qualified_threshold=raw.get("qualified_threshold", 60),
        max_results=raw.get("max_results", 200),
    )


def load_sequence_config(path: str) -> SequenceConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    steps = [
        SequenceStep(
            name=s["name"],
            offset_days=s["offset_days"],
            template=s["template"],
        )
        for s in raw["steps"]
    ]
    return SequenceConfig(name=raw["name"], steps=steps)


def apollo_api_key() -> str:
    key = os.environ.get("APOLLO_API_KEY")
    if not key:
        raise RuntimeError("APOLLO_API_KEY is not set")
    return key


def hubspot_token() -> str:
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("HUBSPOT_ACCESS_TOKEN is not set")
    return token


def db_path() -> str:
    return os.environ.get("OUTREACH_DB_PATH", "outreach.db")
