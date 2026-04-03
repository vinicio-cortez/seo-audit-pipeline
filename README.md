# SEO Audit Pipeline

Automated SEO audit tool that processes Screaming Frog CSV exports and generates structured JSON findings.

## What It Does

- Takes a Screaming Frog CSV export
- Extracts top 5–8 SEO issues (missing titles, missing meta descriptions, broken links, etc.)
- Assigns severity (high/medium/low)
- Outputs clean JSON with findings, URL counts, and recommendations

## Tools Used

- Python 3
- Screaming Frog SEO Spider (free version works)
- CSV processing

## How to Use

1. Export CSV from Screaming Frog
2. Run `python seo_audit_processor.py`
3. Get JSON output with prioritized findings

## Sample Output

```json
{
  "findings": [
    {
      "title": "Missing Title",
      "severity": "high",
      "url_count": 31
    }
  ]
}
