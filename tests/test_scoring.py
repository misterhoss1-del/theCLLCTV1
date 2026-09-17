from linkedin_outreach.config import ICPConfig
from linkedin_outreach.scoring import classify, score_lead
from linkedin_outreach.store import Lead


def make_icp(**overrides) -> ICPConfig:
    base = dict(
        name="test-icp",
        titles=["VP of Marketing", "CMO"],
        industries=["Computer Software"],
        company_size_min=50,
        company_size_max=1000,
        keywords=["growth"],
        locations=["United States"],
        exclude_titles=["Intern"],
        scoring_rules=[],
        qualified_threshold=60,
        max_results=200,
    )
    base.update(overrides)
    return ICPConfig(**base)


def test_full_match_scores_high():
    icp = make_icp()
    lead = Lead(
        id="1",
        title="VP of Marketing",
        industry="Computer Software",
        company_size=200,
        headline="scaling growth at a fast-growing startup",
        location="United States",
    )
    score = score_lead(lead, icp)
    assert score >= icp.qualified_threshold
    assert classify(score, icp.qualified_threshold) == "qualified"


def test_excluded_title_scores_zero():
    icp = make_icp()
    lead = Lead(id="2", title="Marketing Intern", industry="Computer Software")
    assert score_lead(lead, icp) == 0


def test_no_matches_is_disqualified():
    icp = make_icp()
    lead = Lead(id="3", title="Warehouse Associate", industry="Logistics")
    score = score_lead(lead, icp)
    assert classify(score, icp.qualified_threshold) == "disqualified"


def test_company_size_out_of_range_no_bonus():
    icp = make_icp()
    lead = Lead(id="4", title="CMO", industry="Computer Software", company_size=5)
    score = score_lead(lead, icp)
    assert score == 50


def test_custom_scoring_rule_adds_weight():
    from linkedin_outreach.config import ScoringRule

    icp = make_icp(
        scoring_rules=[ScoringRule(field="company_size", range=[50, 500], weight=10)]
    )
    lead = Lead(id="5", title="CMO", industry="Computer Software", company_size=200)
    score = score_lead(lead, icp)
    assert score == 30 + 20 + 15 + 10
