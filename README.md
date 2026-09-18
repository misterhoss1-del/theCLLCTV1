# theCLLCTV1 — LinkedIn Outreach Lead Engine

A config-driven pipeline for building qualified LinkedIn outreach lists: source
prospects against an ICP, score them, generate personalized multi-touch
message copy, and sync qualified leads into HubSpot.

## Compliance boundary

LinkedIn's Terms of Service prohibit automated connection requests, DMs, and
profile scraping — accounts that do it get rate-limited, shadow-banned, or
permanently suspended. This system stops at generating the target list and
the message copy. **Sending happens manually, inside LinkedIn (or Sales
Navigator), by a person.** Nothing here logs into LinkedIn or automates
actions on it.

## Pipeline

```
prospect  →  score  →  sequence  →  sync
(Apollo)     (ICP)     (copy CSV)   (HubSpot)
```

1. **prospect** — searches Apollo.io for people matching an ICP config
   (titles, industry, company size, location, keywords) and stores them
   locally.
2. **score** — applies weighted ICP-fit rules to every new lead; leads at or
   above `qualified_threshold` move to `qualified`, the rest to
   `disqualified`.
3. **sequence** — renders a multi-touch message sequence (connection
   request → follow-ups → breakup) for every qualified lead and writes it to
   a CSV for manual sending. Leads move to `sequenced`.
4. **sync** — upserts sequenced leads with an email address into HubSpot as
   contacts (score, status, and LinkedIn URL included), and marks them
   `synced`.

Lead state lives in a local SQLite file (`outreach.db` by default) so the
pipeline can be re-run incrementally without re-processing leads.

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in APOLLO_API_KEY and HUBSPOT_ACCESS_TOKEN
```

- `APOLLO_API_KEY` — Apollo.io API key (Settings → API in Apollo).
- `HUBSPOT_ACCESS_TOKEN` — HubSpot private app access token with
  `crm.objects.contacts.write` scope.

### HubSpot custom properties (one-time, before the first `sync`)

`sync` writes two custom contact properties this integration owns —
HubSpot doesn't create them for you, and `batch/upsert` rejects the whole
request if either is missing. In HubSpot: **Settings → Properties →
Contact properties → Create property**, twice:

| Name (internal) | Label | Type |
|---|---|---|
| `linkedin_outreach_score` | LinkedIn Outreach Score | Number |
| `linkedin_outreach_status` | LinkedIn Outreach Status | Single-line text |

Everything else `sync` writes (`email`, `firstname`, `lastname`, `jobtitle`,
`company`, `industry`, `hs_linkedin_url`) is a HubSpot default property and
needs no setup.

## Usage

```bash
python -m linkedin_outreach.cli prospect --icp config/icp.plateaued-operator.yaml
python -m linkedin_outreach.cli import-csv --path leads.csv      # Apollo-style people export
python -m linkedin_outreach.cli import-xlsx --path companies.xlsx # local-business-list export
python -m linkedin_outreach.cli score --icp config/icp.plateaued-operator.yaml
python -m linkedin_outreach.cli sequence --sequence config/sequences.rei.yaml --out messages.csv
python -m linkedin_outreach.cli sync
python -m linkedin_outreach.cli status
```

`import-csv` expects an Apollo-style people export (First Name, Last Name,
Title, Company, Email, Person Linkedin Url, Industry, ...). `import-xlsx`
expects a local-business-list export (Business, Categories, Revenue,
Employees, Founded, Contact First/Last Name, Contact Role, Contact Email,
...) — the kind a Google-Maps/GMB scraper produces. It skips company rows
with no named contact (nobody to reach on LinkedIn) and infers an
ICP-shaped industry from Categories since this format doesn't carry one.

Copy `config/icp.example.yaml` and `config/sequences.example.yaml` to define
your own ICP and message sequences — nothing about targeting or copy is
hardcoded. `config/icp.plateaued-operator.yaml` and `config/sequences.rei.yaml`
are the live production pair, built for REI's actual offer and buyer — use
them as the reference for how deep a production config should go.

### ICP config

Defines who counts as a fit: target titles, excluded titles, industries,
company size range, keywords, locations, `max_results`, and
`qualified_threshold`. Add arbitrary `scoring_rules` entries to weight *any*
field on the lead record — including `annual_revenue` and `founded_year`,
which Apollo returns on the organization object when available, letting you
score on revenue stage and business age, not just headcount.

Some qualifying signals can't be scored from Apollo data at all — franchise
structure, timing triggers like "just churned an agency." Put those in the
config file as comments for the human reviewing the qualified list, the way
`icp.plateaued-operator.yaml` does; the pipeline can't act on them, but a
person screening the output can.

### Sequence config

Defines the touch cadence: each step has a name, an `offset_days` (days
after the connection request to send it), and a `template` using
`{first_name}`, `{last_name}`, `{title}`, `{company}`, `{industry}` tokens.

`sequences.rei.yaml` is written for the Trust Tax / infrastructure-not-marketing
positioning: connection request stays under LinkedIn's ~300-character note
limit, and price is deliberately never mentioned in cold copy — it's a
qualification filter for the sales call, not an opener, since naming it
early would pre-select for the price shoppers this ICP explicitly
disqualifies.

## Tests

```bash
pytest
```

Covers the scoring engine (ICP matching, exclusions, custom rules) and the
sequence renderer (token substitution, missing-field fallback, unknown-token
errors).
