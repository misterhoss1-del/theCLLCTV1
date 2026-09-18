from __future__ import annotations

import string
from dataclasses import dataclass

from .config import SequenceConfig, SequenceStep
from .store import Lead


class PersonalizationError(ValueError):
    pass


class _SafeDict(dict):
    def __missing__(self, key):
        raise PersonalizationError(key)


def _tokens(lead: Lead) -> dict[str, str]:
    return {
        "first_name": lead.first_name or "there",
        "last_name": lead.last_name or "",
        "title": lead.title or "your role",
        "company": lead.company or "your company",
        "industry": lead.industry or "your industry",
    }


def render_step(step: SequenceStep, lead: Lead) -> str:
    tokens = _tokens(lead)
    formatter = string.Formatter()
    try:
        return formatter.vformat(step.template, (), _SafeDict(tokens))
    except PersonalizationError as e:
        raise PersonalizationError(
            f"template '{step.name}' references unknown token '{{{e.args[0]}}}'"
        ) from e


@dataclass
class RenderedMessage:
    lead_id: str
    step_name: str
    offset_days: int
    body: str


def render_sequence(lead: Lead, sequence: SequenceConfig) -> list[RenderedMessage]:
    return [
        RenderedMessage(
            lead_id=lead.id,
            step_name=step.name,
            offset_days=step.offset_days,
            body=render_step(step, lead),
        )
        for step in sequence.steps
    ]
