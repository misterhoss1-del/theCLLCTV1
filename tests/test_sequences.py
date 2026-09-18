import pytest

from linkedin_outreach.config import SequenceConfig, SequenceStep
from linkedin_outreach.sequences import PersonalizationError, render_sequence, render_step
from linkedin_outreach.store import Lead


def test_render_step_fills_known_tokens():
    step = SequenceStep(name="intro", offset_days=0, template="Hi {first_name} at {company}")
    lead = Lead(id="1", first_name="Jordan", company="Acme")
    assert render_step(step, lead) == "Hi Jordan at Acme"


def test_render_step_falls_back_for_missing_fields():
    step = SequenceStep(name="intro", offset_days=0, template="Hi {first_name}, re: {title}")
    lead = Lead(id="1", first_name=None, title=None)
    assert render_step(step, lead) == "Hi there, re: your role"


def test_render_step_rejects_unknown_token():
    step = SequenceStep(name="intro", offset_days=0, template="Hi {nickname}")
    lead = Lead(id="1", first_name="Jordan")
    with pytest.raises(PersonalizationError):
        render_step(step, lead)


def test_render_sequence_produces_one_message_per_step():
    sequence = SequenceConfig(
        name="seq",
        steps=[
            SequenceStep(name="a", offset_days=0, template="Hi {first_name}"),
            SequenceStep(name="b", offset_days=3, template="Following up, {first_name}"),
        ],
    )
    lead = Lead(id="1", first_name="Jordan")
    messages = render_sequence(lead, sequence)
    assert [m.step_name for m in messages] == ["a", "b"]
    assert [m.offset_days for m in messages] == [0, 3]
    assert messages[0].body == "Hi Jordan"
