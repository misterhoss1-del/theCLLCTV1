import openpyxl

from linkedin_outreach.store import LeadStore
from linkedin_outreach.xlsx_import import import_xlsx

HEADER = [
    "Business", "Street", "City", "State", "Postcode", "Country", "Phone",
    "Website", "Email", "Domain", "Categories", "Description", "Revenue",
    "Employees", "Founded", "Linkedin", "Contact First Name",
    "Contact Last Name", "Contact Role", "Contact Email",
]


def write_xlsx(path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(HEADER)
    for row in rows:
        ws.append([row.get(h, "") for h in HEADER])
    wb.save(path)


def test_import_skips_contactless_rows_and_maps_fields(tmp_path):
    xlsx_path = tmp_path / "companies.xlsx"
    write_xlsx(xlsx_path, [
        {
            "Business": "The Plumbing Doc", "City": "Bakersfield", "State": "CA",
            "Categories": "Plumber", "Description": "Family owned local plumber",
            "Revenue": "$390 K", "Employees": "4", "Founded": 2015,
            "Contact First Name": "Rick", "Contact Last Name": "Clemmons",
            "Contact Role": "Chief Executive Officer",
            "Contact Email": "rick@plumbingdoc.net",
        },
        {"Business": "No Contact Plumbing", "Categories": "Plumber"},  # no contact -> skipped
    ])

    store = LeadStore(str(tmp_path / "leads.db"))
    count = import_xlsx(store, str(xlsx_path))

    assert count == 1
    lead = store.get("rick@plumbingdoc.net")
    assert lead.first_name == "Rick"
    assert lead.last_name == "Clemmons"
    assert lead.title == "Chief Executive Officer"
    assert lead.company == "The Plumbing Doc"
    assert lead.industry == "Facilities Services"
    assert lead.company_size == 4
    assert lead.annual_revenue == 390_000
    assert lead.founded_year == 2015
    assert lead.location == "Bakersfield, CA"
    assert lead.headline == "Family owned local plumber"


def test_revenue_and_employee_range_strings_parse():
    from linkedin_outreach.xlsx_import import _parse_int, _parse_money

    assert _parse_money("$2.3 M") == 2_300_000
    assert _parse_money("<$5 M") == 5_000_000
    assert _parse_money("$166.6 B") == 166_600_000_000
    assert _parse_int("<25") == 25
    assert _parse_int("4,302") == 4302
    assert _parse_int(None) is None
