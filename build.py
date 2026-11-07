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
    'head', 'header', 'hero', 'announcement', 'gallery', 'recent_photos',
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


# ---------------------------------------------------------------- photo pages

SITE_URL = 'https://www.ourladysbangor.org/'


def inline(text):
    """Plain text -> HTML for photo pages: **bold**, *italic*, line breaks, email links."""
    text = esc(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+', lambda m: f'<a href="mailto:{m.group(0)}">{m.group(0)}</a>', text)
    return text.replace('\n', '<br>')


def attr(text):
    return html.escape(text, quote=True)


def long_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B %Y')}"


def image_size(path):
    """(width, height) of a JPEG or PNG without any library; None if unreadable."""
    try:
        with open(path, 'rb') as f:
            head = f.read(26)
            if head[:8] == b'\x89PNG\r\n\x1a\n':
                return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')
            if head[:2] != b'\xff\xd8':
                return None
            f.seek(2)
            while True:
                b = f.read(1)
                while b and b != b'\xff':
                    b = f.read(1)
                while b == b'\xff':
                    b = f.read(1)
                if not b:
                    return None
                marker = b[0]
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    continue
                length = int.from_bytes(f.read(2), 'big')
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    seg = f.read(5)
                    return int.from_bytes(seg[3:5], 'big'), int.from_bytes(seg[1:3], 'big')
                f.seek(length - 2, 1)
    except OSError:
        return None


def figure(p, caption_text):
    """One <figure>. Orientation comes from the real image size."""
    shown = p.get('thumb') or p['file']      # grid shows the small copy, the lightbox the full one
    size = image_size(ROOT / shown)
    cls, dims = [], ''
    if size:
        w, h = size
        cls.append('portrait' if h > w else 'landscape')
        dims = f' width="{w}" height="{h}"'
    if p.get('wide'):
        cls.append('wide')
    cap = f'<figcaption>{inline(caption_text)}</figcaption>' if caption_text else ''
    c = f' class="{" ".join(cls)}"' if cls else ''
    f, t = attr(p['file']), attr(shown)
    return (f'<figure{c}><a href="{f}"><img loading="lazy"{dims} src="{t}" '
            f'alt="{attr(p.get("alt") or p.get("caption") or "Parish photograph")}"></a>{cap}</figure>')


def load_events():
    events = []
    for path in sorted((DATA / 'events').glob('*.json')):
        with open(path, encoding='utf-8') as f:
            e = json.load(f)
        e.setdefault('output', path.stem + '.html')
        e['_name'] = path.name
        events.append(e)
    events.sort(key=lambda e: e['date'], reverse=True)
    return events


def photo_count(e):
    return len(e.get('photos') or []) or sum(len(s['photos']) for s in e.get('sections', []))


def cover(e):
    return e['hero']['file'] if e.get('hero') else (e['photos'][0]['file'] if e.get('photos') else e['sections'][0]['photos'][0]['file'])


def event_page(e, top, bottom, main_tpl):
    chapters = ''
    if e.get('sections'):
        blocks = []
        for s in e['sections']:
            left = ''
            if s.get('kicker'):
                left += f'          <p class="chapter-kicker">{inline(s["kicker"])}</p>\n'
            if s.get('heading'):
                left += f'          <h3>{inline(s["heading"])}</h3>\n'
            for t in s.get('text', []):
                left += f'          <p>{inline(t)}</p>\n'
            if s.get('quote'):
                left += (f'          <blockquote>&ldquo;{inline(s["quote"]["text"])}&rdquo;'
                         f'<cite>{inline(s["quote"].get("cite", ""))}</cite></blockquote>\n')
            figs = '\n'.join('          ' + figure(p, p.get('caption')) for p in s['photos'])
            blocks.append(f'      <div class="chapter">\n        <div>\n{left}        </div>\n'
                          f'        <div class="photo-grid{" few-" + str(len(s["photos"])) if len(s["photos"]) < 3 else ""}">\n{figs}\n        </div>\n      </div>')
        chapters = ('\n  <div class="chapter-band">\n    <section class="section">\n'
                    + '\n\n'.join(blocks) + '\n    </section>\n  </div>\n')
    gallery = ''
    if e.get('photos'):
        figs = '\n'.join('        ' + figure(p, p.get('caption') or f'{i:02d}') for i, p in enumerate(e['photos'], 1))
        gallery = ('\n  <section class="full-gallery" id="gallery">\n    <div class="section">\n      <div class="divider"></div>\n'
                   f'      <h2 class="section-title">{inline(e.get("gallery_heading", "All Photographs"))}</h2>\n'
                   f'      <p class="section-subtitle">{inline(e.get("gallery_subtitle", "All photographs in sequence."))}</p>\n'
                   f'      <div class="mosaic" aria-label="Complete photo gallery">\n{figs}\n      </div>\n    </div>\n  </section>\n')
    album, panel_bits = e.get('album'), ''
    details = e.get('details') or {}
    if details:
        panel_bits += '<p>' + '<br>\n        '.join(f'<strong>{inline(k)}:</strong> {inline(v)}' for k, v in details.items()) + '</p>\n'
    if album and album.get('text'):
        panel_bits += f'        <p>{inline(album["text"])}</p>\n'
    if album:
        icon = '&#8659; ' if album.get('download') else ''
        label = inline(album.get('label') or 'View Full Album')
        panel_bits += (f'        <div style="margin-top:16px;"><a class="button secondary" href="{attr(album["url"])}" '
                       f'target="_blank" rel="noopener">{icon}{label}</a></div>\n')
    note_panel = ''
    if panel_bits:
        note_panel = ('      <aside class="note-panel" aria-label="Photo details">\n        <h2>About This Set</h2>\n        '
                      + panel_bits + '      </aside>')
    album_button = ''
    if album:
        icon = '&#8659; ' if album.get('download') else ''
        album_button = (f'        <a class="button" href="{attr(album["url"])}" target="_blank" rel="noopener">'
                        f'{icon}{inline(album.get("label") or "View Full Album")}</a>\n')
    nav = ['      <a href="index.html">Home</a>', '      <a href="#essay">About</a>']
    if e.get('photos'):
        nav.append('      <a href="#gallery">All Photos</a>')
    nav += ['      <a href="photos.html">More Albums</a>', '      <a href="#contact">Parish Details</a>']
    url = SITE_URL + e['output']
    ogimg = SITE_URL + cover(e)
    desc = e.get('description') or e.get('lead', '')
    vals = {
        'page_title': esc(f'{e["title"]} | {long_date(e["date"])} | Our Lady & St. James, Bangor'),
        'description': attr(desc), 'canonical': attr(url), 'og_title': attr(e['title']), 'og_image': attr(ogimg),
        'nav_links': '\n'.join(nav),
        'headline': inline(e.get('headline', e['title'])), 'eyebrow': inline(e.get('eyebrow') or long_date(e['date'])),
        'lead': inline(e.get('lead', '')),
        'hero_file': attr(cover(e)), 'hero_alt': attr((e.get('hero') or {}).get('alt', e['title'])),
        'intro_heading': ('<h2 class="section-title">' + inline(e['intro_heading']) + '</h2>') if e.get('intro_heading') else '',
        'intro_paras': '\n'.join(f'        <p>{inline(p)}</p>' for p in e.get('intro', [])),
        'note_panel': note_panel, 'chapters': chapters, 'gallery': gallery, 'album_button': album_button,
    }
    return fill_template(top + main_tpl + bottom, vals)


def fill_template(text, values):
    def fill(m):
        key = m.group(1)
        if key not in values:
            sys.exit(f'build.py: template placeholder {{{{{key}}}}} has no value')
        return values[key]
    return re.sub(r'\{\{(\w+)\}\}', fill, text)


def album_cards(events, css_class=None):
    out = []
    for e in events:
        out.append(f'      <a class="album-card" href="{attr(e["output"])}"><img loading="lazy" src="{attr(cover(e))}" alt="">'
                   f'<div><h3>{inline(e["title"])}</h3><p>{long_date(e["date"])} &middot; {photo_count(e)} photos</p></div></a>')
    return '\n'.join(out)


def recent_cards(events, n=3):
    out = []
    for e in events[:n]:
        out.append(f'      <a href="{attr(e["output"])}"><img loading="lazy" src="{attr(cover(e))}" alt="">'
                   f'<div><h3>{inline(e["title"])}</h3><p>{long_date(e["date"])} &middot; {photo_count(e)} photos</p></div></a>')
    return '\n'.join(out)


def build_photo_pages(events):
    top = (TEMPLATES / 'photo_top.html').read_text(encoding='utf-8')
    bottom = (TEMPLATES / 'photo_bottom.html').read_text(encoding='utf-8')
    main = (TEMPLATES / 'event_main.html').read_text(encoding='utf-8')
    for e in events:
        (ROOT / e['output']).write_text(event_page(e, top, bottom, main), encoding='utf-8')
    albums = fill_template(top + (TEMPLATES / 'albums_main.html').read_text(encoding='utf-8') + bottom, {
        'page_title': 'Parish Photo Albums | Our Lady &amp; St. James, Bangor',
        'description': 'Photographs from Our Lady &amp; St. James, Bangor and St. David &amp; St. Helen, Caernarfon.',
        'canonical': SITE_URL + 'photos.html', 'og_title': 'Parish Photo Albums', 'og_image': attr(SITE_URL + cover(events[0])) if events else '',
        'nav_links': '      <a href="index.html">Home</a>\n      <a href="#contact">Parish Details</a>'.replace('      <a href="#contact">Parish Details</a>', '      <a href="index.html#contact">Contact</a>'),
        'album_cards': album_cards(events),
    })
    (ROOT / 'photos.html').write_text(albums, encoding='utf-8')


# ---------------------------------------------------------------- build

def build():
    site = load('site.json')
    masses = load('masses.json')
    cal = load('calendar.json')
    notices = load('notices.json')
    forms = load('forms.json')
    nl = site['newsletter']
    events = load_events()

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
        'recent_cards': recent_cards(events),
    }

    parts = []
    for name in SECTIONS:
        parts.append((TEMPLATES / f'{name}.html').read_text(encoding='utf-8'))
    page = ''.join(parts) + '<script src="assets/site.js"></script>\n</body>\n</html>\n'

    page = fill_template(page, values)
    (ROOT / 'index.html').write_text(page, encoding='utf-8')
    build_photo_pages(events)
    print(f'Built index.html  ({len(cal["entries"])} calendar days, {len(notices["notices"])} notices, {len(forms["forms"])} forms)')
    print(f'Built photos.html and {len(events)} photo pages: ' + ', '.join(e['output'] for e in events))


if __name__ == '__main__':
    build()
