from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,
    linkedin_url TEXT,
    first_name TEXT,
    last_name TEXT,
    title TEXT,
    company TEXT,
    industry TEXT,
    company_size INTEGER,
    annual_revenue INTEGER,
    founded_year INTEGER,
    location TEXT,
    email TEXT,
    headline TEXT,
    score INTEGER DEFAULT 0,
    status TEXT DEFAULT 'new',
    sequence_step INTEGER DEFAULT 0,
    hubspot_contact_id TEXT,
    created_at TEXT,
    updated_at TEXT
);
"""


@dataclass
class Lead:
    id: str
    linkedin_url: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    company: str | None = None
    industry: str | None = None
    company_size: int | None = None
    annual_revenue: int | None = None
    founded_year: int | None = None
    location: str | None = None
    email: str | None = None
    headline: str | None = None
    score: int = 0
    status: str = "new"
    sequence_step: int = 0
    hubspot_contact_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LeadStore:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def upsert(self, lead: Lead) -> None:
        existing = self.get(lead.id)
        if existing:
            self.conn.execute(
                """
                UPDATE leads SET linkedin_url=?, first_name=?, last_name=?, title=?,
                    company=?, industry=?, company_size=?, annual_revenue=?, founded_year=?,
                    location=?, email=?, headline=?, updated_at=?
                WHERE id=?
                """,
                (
                    lead.linkedin_url, lead.first_name, lead.last_name, lead.title,
                    lead.company, lead.industry, lead.company_size, lead.annual_revenue,
                    lead.founded_year, lead.location, lead.email, lead.headline,
                    datetime.now(timezone.utc).isoformat(), lead.id,
                ),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO leads (id, linkedin_url, first_name, last_name, title, company,
                    industry, company_size, annual_revenue, founded_year, location, email,
                    headline, score, status, sequence_step, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    lead.id, lead.linkedin_url, lead.first_name, lead.last_name, lead.title,
                    lead.company, lead.industry, lead.company_size, lead.annual_revenue,
                    lead.founded_year, lead.location, lead.email, lead.headline, lead.score,
                    lead.status, lead.sequence_step, lead.created_at, lead.updated_at,
                ),
            )
        self.conn.commit()

    def get(self, lead_id: str) -> Lead | None:
        row = self.conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        return self._row_to_lead(row) if row else None

    def list_by_status(self, status: str) -> list[Lead]:
        rows = self.conn.execute("SELECT * FROM leads WHERE status=?", (status,)).fetchall()
        return [self._row_to_lead(r) for r in rows]

    def set_score(self, lead_id: str, score: int, status: str) -> None:
        self.conn.execute(
            "UPDATE leads SET score=?, status=?, updated_at=? WHERE id=?",
            (score, status, datetime.now(timezone.utc).isoformat(), lead_id),
        )
        self.conn.commit()

    def set_status(self, lead_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE leads SET status=?, updated_at=? WHERE id=?",
            (status, datetime.now(timezone.utc).isoformat(), lead_id),
        )
        self.conn.commit()

    def set_sequence_step(self, lead_id: str, step: int) -> None:
        self.conn.execute(
            "UPDATE leads SET sequence_step=?, updated_at=? WHERE id=?",
            (step, datetime.now(timezone.utc).isoformat(), lead_id),
        )
        self.conn.commit()

    def set_hubspot_id(self, lead_id: str, hubspot_contact_id: str) -> None:
        self.conn.execute(
            "UPDATE leads SET hubspot_contact_id=?, updated_at=? WHERE id=?",
            (hubspot_contact_id, datetime.now(timezone.utc).isoformat(), lead_id),
        )
        self.conn.commit()

    def funnel_counts(self) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT status, COUNT(*) as c FROM leads GROUP BY status"
        ).fetchall()
        return {r["status"]: r["c"] for r in rows}

    @staticmethod
    def _row_to_lead(row: sqlite3.Row) -> Lead:
        return Lead(**{k: row[k] for k in row.keys()})
