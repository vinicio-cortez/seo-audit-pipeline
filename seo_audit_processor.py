import csv
import json
import sys
import os
from collections import defaultdict

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
# Adjust these column names if SEO Minion uses different headers in its CSV
COLUMN_TITLE       = 'Title'           # Page title column
COLUMN_META        = 'Meta Description' # Meta description column
COLUMN_H1          = 'H1'              # H1 tag column
COLUMN_URL         = 'URL'             # URL column
COLUMN_STATUS      = 'Status Code'     # HTTP status code column
COLUMN_LCP         = 'LCP'             # LCP value column (if present)

TITLE_MIN = 30
TITLE_MAX = 60
META_MAX  = 160
LCP_MAX   = 5.0  # seconds

# ── MAIN PROCESSOR ────────────────────────────────────────────────────────────

def process_csv(file_path: str) -> list:
    findings = []

    with open(file_path, mode='r', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file)

        # Show detected columns on first run (helpful for debugging)
        headers = reader.fieldnames or []
        print(f"[INFO] Columns detected: {headers}")

        for row in reader:
            url   = row.get(COLUMN_URL, '').strip()
            title = row.get(COLUMN_TITLE, '').strip()
            meta  = row.get(COLUMN_META, '').strip()
            h1    = row.get(COLUMN_H1, '').strip()
            status_raw = row.get(COLUMN_STATUS, '').strip()
            lcp_raw    = row.get(COLUMN_LCP, '').strip()

            if not url:
                continue

            # Missing or too-short title
            if not title:
                findings.append({
                    'type': 'missing_title',
                    'url': url,
                    'severity': 'high',
                    'what': 'Título de página faltante',
                    'detail': f'La página no tiene título: {url}',
                    'why': '{{WHY_MISSING_TITLE}}',
                    'how': '{{HOW_MISSING_TITLE}}'
                })
            elif len(title) < TITLE_MIN:
                findings.append({
                    'type': 'short_title',
                    'url': url,
                    'severity': 'high',
                    'what': 'Título demasiado corto',
                    'detail': f'"{title}" ({len(title)} caracteres) — mínimo recomendado: {TITLE_MIN}',
                    'why': '{{WHY_SHORT_TITLE}}',
                    'how': '{{HOW_SHORT_TITLE}}'
                })
            elif len(title) > TITLE_MAX:
                findings.append({
                    'type': 'long_title',
                    'url': url,
                    'severity': 'medium',
                    'what': 'Título demasiado largo',
                    'detail': f'"{title[:50]}…" ({len(title)} caracteres) — máximo recomendado: {TITLE_MAX}',
                    'why': '{{WHY_LONG_TITLE}}',
                    'how': '{{HOW_LONG_TITLE}}'
                })

            # Missing or too-long meta description
            if not meta:
                findings.append({
                    'type': 'missing_meta',
                    'url': url,
                    'severity': 'high',
                    'what': 'Meta descripción faltante',
                    'detail': f'La página no tiene meta descripción: {url}',
                    'why': '{{WHY_MISSING_META}}',
                    'how': '{{HOW_MISSING_META}}'
                })
            elif len(meta) > META_MAX:
                findings.append({
                    'type': 'long_meta',
                    'url': url,
                    'severity': 'medium',
                    'what': 'Meta descripción demasiado larga',
                    'detail': f'{len(meta)} caracteres — máximo recomendado: {META_MAX}',
                    'why': '{{WHY_LONG_META}}',
                    'how': '{{HOW_LONG_META}}'
                })

            # Missing H1
            if not h1:
                findings.append({
                    'type': 'missing_h1',
                    'url': url,
                    'severity': 'medium',
                    'what': 'Etiqueta H1 faltante',
                    'detail': f'La página no tiene H1: {url}',
                    'why': '{{WHY_MISSING_H1}}',
                    'how': '{{HOW_MISSING_H1}}'
                })

            # Broken links / server errors
            if status_raw:
                try:
                    status = int(status_raw)
                    if status == 404:
                        findings.append({
                            'type': 'broken_link',
                            'url': url,
                            'severity': 'high',
                            'what': 'Enlace roto (404)',
                            'detail': f'URL devuelve 404: {url}',
                            'why': '{{WHY_BROKEN_LINK}}',
                            'how': '{{HOW_BROKEN_LINK}}'
                        })
                    elif status >= 500:
                        findings.append({
                            'type': 'server_error',
                            'url': url,
                            'severity': 'high',
                            'what': f'Error del servidor ({status})',
                            'detail': f'URL devuelve {status}: {url}',
                            'why': '{{WHY_SERVER_ERROR}}',
                            'how': '{{HOW_SERVER_ERROR}}'
                        })
                except ValueError:
                    pass

            # Slow LCP
            if lcp_raw:
                try:
                    lcp = float(lcp_raw)
                    if lcp > LCP_MAX:
                        findings.append({
                            'type': 'long_lcp',
                            'url': url,
                            'severity': 'high',
                            'what': 'Tiempo de carga lento (LCP)',
                            'detail': f'LCP: {lcp}s — estándar de Google: menos de 2.5s',
                            'why': '{{WHY_LONG_LCP}}',
                            'how': '{{HOW_LONG_LCP}}'
                        })
                except ValueError:
                    pass

    return findings


def build_report(findings: list, client_name: str, website: str, date: str) -> dict:
    # Count URLs per finding type
    url_counts = defaultdict(int)
    for f in findings:
        url_counts[f['type']] += 1

    # Deduplicate by type (keep one entry per type, with url_count)
    seen_types = {}
    for f in findings:
        t = f['type']
        if t not in seen_types:
            seen_types[t] = f

    # Sort: high severity first, then by url_count descending
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    sorted_findings = sorted(
        seen_types.values(),
        key=lambda x: (severity_order.get(x['severity'], 9), -url_counts[x['type']])
    )

    # Take top 5-8
    top_findings = sorted_findings[:8]

    high_count   = sum(1 for f in findings if f['severity'] == 'high')
    medium_count = sum(1 for f in findings if f['severity'] == 'medium')

    return {
        'client': {
            'name': client_name,
            'website': website,
            'date': date
        },
        'findings': [
            {
                'type': f['type'],
                'title': f['what'],
                'what': f['what'],
                'detail': f['detail'],
                'why': f['why'],
                'how': f['how'],
                'severity': f['severity'],
                'url_count': url_counts[f['type']]
            }
            for f in top_findings
        ],
        'summary': {
            'total_findings': len(seen_types),
            'total_instances': len(findings),
            'high_severity': high_count,
            'medium_severity': medium_count,
            'low_severity': 0
        },
        'tools_used': ['SEO Minion / SEO Checker', 'Google PageSpeed Insights']
    }


if __name__ == '__main__':
    # ── EDIT THESE ─────────────────────────────────────────────────────────────
    CSV_PATH    = r'/mnt/c/Users/Vin/Desktop/stuartrestaurant.com - Explore - 2xx status code - Success - 2026-04-01 - 19.31.16.csv'
    CLIENT_NAME = 'Stuart Restaurant'
    WEBSITE     = 'https://stuartrestaurant.com'
    DATE        = '1 de abril de 2026'
    OUTPUT_FILE = os.path.expanduser('~/stuart_seo_findings.json')
    # ───────────────────────────────────────────────────────────────────────────

    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] CSV not found at: {CSV_PATH}")
        print("Check the path and try again.")
        sys.exit(1)

    print(f"[INFO] Processing: {CSV_PATH}")
    findings = process_csv(CSV_PATH)
    print(f"[INFO] Total raw findings: {len(findings)}")

    report = build_report(findings, CLIENT_NAME, WEBSITE, DATE)
    print(f"[INFO] Unique finding types: {report['summary']['total_findings']}")
    print(f"[INFO] High severity: {report['summary']['high_severity']} instances")
    print(f"[INFO] Medium severity: {report['summary']['medium_severity']} instances")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] JSON saved to: {OUTPUT_FILE}")
    print("\n── JSON OUTPUT ──────────────────────────────")
    print(json.dumps(report, ensure_ascii=False, indent=2))
