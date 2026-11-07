#!/usr/bin/env python3
"""Build index.html for ourladysbangor.org from the files in data/ and templates/.

Usage:   python3 build.py            (run from the repository folder)

Monthly content lives in data/*.json. Page layout lives in templates/*.html.
Only the Python standard library is used - nothing to install.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
TEMPLATES = ROOT / 'templates'

# Order in which the sections appear on the page.
SECTIONS = [
    'head', 'header', 'hero', 'announcement', 'gallery',
    'masses', 'bulletin', 'notices', 'forms', 'music', 'contact', 'footer',
]


def load(name):
    with open(DATA / name, encoding='utf-8') as f:
        return json.load(f)


def esc(text):
    """Escape plain text for HTML."""
    return html.escape(text, quote=False)


def rich(text, site):
    """Plain text -> HTML. *word* becomes italic; email addresses become links;
    {next_edition} and {deadline} are filled in from data/site.json."""
    nl = site['newsletter']
    text = text.replace('{next_edition}', nl['next_edition']).replace('{deadline}', nl['deadline'])
    text = esc(text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+', lambda m: f'<a href="mailto:{m.group(0)}">{m.group(0)}</a>', text)
    return text


def weekday_label(iso):
    d = date.fromisoformat(iso)
    return f"{d.strftime('%A')} {d.day} {d.strftime('%b')}"


# ---------------------------------------------------------------- sections

def mass_cards(masses):
    conf = ' · '.join(f"{c['day']} {c['time']}" for c in masses['confession'])
    out = []
    for church in masses['churches']:
        rows = [f'        <div class="mass-row"><span class="mass-day">{esc(r["day"])}</span>'
                f'<span class="mass-time">{esc(r["time"])}</span></div>' for r in church['rows']]
        if church.get('show_confession'):
            rows.append('        <div class="mass-row"><span class="mass-day">Confession</span>'
                        f'<span class="mass-time">{esc(conf)}</span></div>')
        out.append('      <div class="mass-card">\n'
                   f'        <h3>{esc(church["title"])}</h3>\n' + '\n'.join(rows) + '\n'
                   f'        <p class="mass-note">{esc(church["note"])}</p>\n      </div>')
    return '\n'.join(out)


def calendar_rows(cal):
    rows = []
    for e in cal['entries']:
        obs = ''
        if 'badge' in e:
            obs = f'<span class="badge badge-{e["badge"]["style"]}">{esc(e["badge"]["text"])}</span>'
        if e.get('observance'):
            obs = (obs + ' ' if obs else '') + esc(e['observance'])
        rows.append(f'        <tr><td>{weekday_label(e["date"])}</td><td>{obs}</td><td>{esc(e["details"])}</td></tr>')
    return '\n'.join(rows)


def notice_cards(notices, site):
    out = []
    for n in notices['notices']:
        cls = 'notice-card wide' if n.get('wide') else 'notice-card'
        out.append(f'      <div class="{cls}">\n'
                   f'        <h4>{rich(n["title"], site)}</h4>\n'
                   f'        <p>{rich(n["text"], site)}</p>\n      </div>')
    return '\n\n'.join(out)


def form_cards(forms):
    out = []
    for f in forms['forms']:
        out.append('      <div class="form-card">\n'
                   f'        <h4>{esc(f["title"])}</h4>\n'
                   f'        <p>{esc(f["text"])}</p>\n'
                   f'        <a class="form-download" href="{html.escape(f["file"])}" download>Download &darr;</a>\n'
                   '      </div>')
    return '\n\n'.join(out)


def confession_items(masses):
    return '\n'.join(f'          <li><strong>{esc(c["day"])}</strong> {esc(c["time"])}</li>' for c in masses['confession'])


# ---------------------------------------------------------------- build

def build():
    site = load('site.json')
    masses = load('masses.json')
    cal = load('calendar.json')
    notices = load('notices.json')
    forms = load('forms.json')
    nl = site['newsletter']

    values = {
        'masses_subtitle': esc(masses['subtitle']),
        'masses_alert': esc(masses['alert']),
        'mass_cards': mass_cards(masses),
        'calendar_title': esc(cal['title']),
        'calendar_subtitle': esc(cal['subtitle']),
        'calendar_month_heading': esc(cal['month_heading']),
        'calendar_rows': calendar_rows(cal),
        'newsletter_month': esc(nl['month']),
        'newsletter_month_name': esc(nl['month'].split()[0]),
        'newsletter_summary': esc(nl['summary']),
        'newsletter_next_edition': esc(nl['next_edition']),
        'newsletter_deadline': esc(nl['deadline']),
        'newsletter_email': esc(nl['email']),
        'newsletter_file': html.escape(nl['file']),
        'notices_subtitle': esc(notices['subtitle']),
        'notice_cards': notice_cards(notices, site),
        'forms_subtitle': esc(forms['subtitle']),
        'form_cards': form_cards(forms),
        'confession_items': confession_items(masses),
        'confession_by_arrangement': esc(masses['confession_by_arrangement']),
    }

    parts = []
    for name in SECTIONS:
        parts.append((TEMPLATES / f'{name}.html').read_text(encoding='utf-8'))
    page = ''.join(parts) + '<script src="assets/site.js"></script>\n</body>\n</html>\n'

    def fill(m):
        key = m.group(1)
        if key not in values:
            sys.exit(f'build.py: template placeholder {{{{{key}}}}} has no value')
        return values[key]

    page = re.sub(r'\{\{(\w+)\}\}', fill, page)
    (ROOT / 'index.html').write_text(page, encoding='utf-8')
    print(f'Built index.html  ({len(cal["entries"])} calendar days, {len(notices["notices"])} notices, {len(forms["forms"])} forms)')


if __name__ == '__main__':
    build()
