import csv

from linkedin_outreach.csv_import import import_csv
from linkedin_outreach.store import LeadStore

HEADER = [
    "First Name", "Last Name", "Title", "Company", "Company Name for Emails",
    "Email", "Phone", "Departments", "", "Corporate Phone", "# Employees",
    "Industry", "Keywords", "Person Linkedin Url", "Website",
    "Company Linkedin Url", "Facebook Url", "Twitter Url", "City", "State",
    "Country", "Company Address", "Company City", "Company State",
    "Company Country", "Company Phone", "SEO Description", "Technologies",
    "Annual Revenue",
]


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for row in rows:
            writer.writerow([row.get(h, "") for h in HEADER])


def test_import_maps_fields_and_dedupes_by_linkedin_url(tmp_path):
    csv_path = tmp_path / "leads.csv"
    write_csv(csv_path, [
        {
            "First Name": "Dana", "Last Name": "Reyes", "Title": "Owner",
            "Company": "Glow Med Spa", "Email": "dana@glowmedspa.com",
            "# Employees": "12", "Industry": "Medical Practice",
            "Person Linkedin Url": "http://www.linkedin.com/in/danareyes/",
            "City": "Austin", "State": "Texas", "Annual Revenue": "1400000",
        },
        {
            # re-import of the same lead (trailing slash differs) should upsert, not duplicate
            "First Name": "Dana", "Last Name": "Reyes", "Title": "Owner",
            "Company": "Glow Med Spa", "Email": "dana@glowmedspa.com",
            "# Employees": "12", "Industry": "Medical Practice",
            "Person Linkedin Url": "http://www.linkedin.com/in/danareyes",
            "City": "Austin", "State": "Texas", "Annual Revenue": "1400000",
        },
        {"Company": "No Name Co", "Title": "CEO"},  # no first name but has company -> kept
        {},  # fully blank row -> skipped
    ])

    store = LeadStore(str(tmp_path / "leads.db"))
    count = import_csv(store, str(csv_path))

    assert count == 3
    lead = store.get("http://www.linkedin.com/in/danareyes")
    assert lead.first_name == "Dana"
    assert lead.company == "Glow Med Spa"
    assert lead.company_size == 12
    assert lead.annual_revenue == 1400000
    assert lead.location == "Austin, Texas"
