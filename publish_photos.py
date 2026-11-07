#!/usr/bin/env python3
"""Turn a folder of phone photos into a web photo album.

Put photos in   inbox/<YYYY-MM-DD-name>/   (for example inbox/2026-11-08-remembrance-sunday/)
then double-click publish-photos.command  (or run: python3 publish_photos.py).

What it does for every photo: fixes rotation, shrinks it (1600 px, plus a small 600 px copy),
removes location/camera data, and saves it under photos/<folder>/.  It then lists the album in
data/events/<folder>.json and rebuilds the site.  Your originals stay in inbox/ (which is not
uploaded to GitHub).

Optional files inside the folder:
  info.txt      lines such as   title: Remembrance Sunday   /   intro: One sentence.   /   album: https://...
  captions.txt  one line per photo:   IMG_1234.jpeg: Fr. Savi greets the congregation
Photos whose name starts with an underscore (_IMG_1234.jpeg) are favourites: shown first, and the
first one becomes the big picture at the top of the page.

Only Python 3 and the tools already on a Mac (sips) are used.  Nothing to install.
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INBOX = ROOT / 'inbox'
EXTS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tif', '.tiff', '.webp'}
FULL, THUMB, QUALITY = 1600, 600, 80
WARN_COUNT, WARN_MB, STRONG_CHECK = 150, 40, 20


# ------------------------------------------------------------ image tools

def backend():
    if shutil.which('sips'):
        return 'sips'
    for exe in ('magick', 'convert'):
        if shutil.which(exe):
            return exe
    sys.exit('No image tool found (expected the Mac tool "sips").')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip() or 'command failed')


def resize(tool, src, dst, size):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if tool == 'sips':
        run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', str(QUALITY), '-Z', str(size), str(src), '--out', str(dst)])
    else:
        exe = [tool] if tool == 'convert' else [tool, 'convert']
        run(exe + [str(src), '-auto-orient', '-resize', f'{size}x{size}>', '-quality', str(QUALITY), str(dst)])


def exif_orientation(path):
    """EXIF orientation (1-8) of a JPEG, 1 if none."""
    data = path.read_bytes()
    i = 2
    while i + 4 < len(data) and data[i] == 0xFF:
        marker, length = data[i + 1], int.from_bytes(data[i + 2:i + 4], 'big')
        if marker == 0xE1 and data[i + 4:i + 10] == b'Exif\0\0':
            t = data[i + 10:i + 4 + length]
            le = t[:2] == b'II'
            rd = lambda o, n: int.from_bytes(t[o:o + n], 'little' if le else 'big')
            ifd = rd(4, 4)
            for k in range(rd(ifd, 2)):
                e = ifd + 2 + 12 * k
                if rd(e, 2) == 0x0112:
                    return rd(e + 8, 2)
            return 1
        if marker == 0xDA:
            break
        i += 2 + length
    return 1


def strip_metadata(path):
    """Remove EXIF/GPS/XMP/IPTC segments from a JPEG; keep the colour profile."""
    data = path.read_bytes()
    out, i = [data[:2]], 2
    while i + 4 <= len(data) and data[i] == 0xFF:
        marker, length = data[i + 1], int.from_bytes(data[i + 2:i + 4], 'big')
        if marker == 0xDA:
            out.append(data[i:])
            break
        seg = data[i:i + 2 + length]
        if marker in (0xE1, 0xED, 0xFE):          # APP1 (EXIF/XMP), APP13 (IPTC), comments
            pass
        else:
            out.append(seg)
        i += 2 + length
    path.write_bytes(b''.join(out))


def make_jpeg(tool, src, dst, size):
    resize(tool, src, dst, size)
    o = exif_orientation(dst)
    if tool == 'sips' and o in (3, 6, 8):         # sips leaves rotation to us
        run(['sips', '-r', {3: '180', 6: '90', 8: '270'}[o], str(dst)])
    strip_metadata(dst)


# ------------------------------------------------------------ helpers

def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def read_pairs(path, sep):
    out = {}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            if sep in line and not line.strip().startswith('#'):
                k, v = line.split(sep, 1)
                out[k.strip().lower() if sep == ':' and path.name == 'info.txt' else k.strip()] = v.strip()
    return out


def ask(question, assume_yes):
    if assume_yes:
        return True
    return input(question + ' ').strip().lower() in ('y', 'yes')


def publish(folder, assume_yes=False):
    m = re.match(r'(\d{4}-\d{2}-\d{2})[-_ ]*(.*)', folder.name)
    if not m:
        print(f'  Skipped "{folder.name}": the folder name must start with the date, e.g. 2026-11-08-remembrance-sunday')
        return False
    iso, rest = m.group(1), m.group(2)
    date.fromisoformat(iso)
    name = f'{iso}-{slug(rest)}'.rstrip('-')
    photos = sorted(p for p in folder.iterdir() if p.suffix.lower() in EXTS and not p.name.startswith('.'))
    if not photos:
        print(f'  Skipped "{folder.name}": no photos in it.')
        return False
    total_mb = sum(p.stat().st_size for p in photos) / 1e6
    print(f'\n{folder.name}: {len(photos)} photos ({total_mb:.0f} MB of originals)')

    if len(photos) > WARN_COUNT or total_mb > WARN_MB * 6:
        print(f'  That is a large album. Consider keeping only the best {WARN_COUNT} here and linking the rest with  album: <Google link>  in info.txt.')
    if len(photos) > STRONG_CHECK:
        print('  Large albums usually show many people, often children.')
        if not ask('  Have you checked every photo, and are you sure the parish has permission to publish them? (yes/no)', assume_yes):
            print('  Not published.'); return False
    elif not ask('  Do the photos show children or other people? If so, are you sure the parish has permission to publish them? (yes/no)', assume_yes):
        print('  Not published.'); return False

    info, caps = read_pairs(folder / 'info.txt', ':'), read_pairs(folder / 'captions.txt', ':')
    tool = backend()
    out_dir = ROOT / 'photos' / name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    entries, favs = [], []
    for n, src in enumerate(photos, 1):
        fav = src.name.startswith('_')
        stem = slug(src.stem.lstrip('_'))
        fn = f'{n:03d}-{stem}.jpg'
        try:
            make_jpeg(tool, src, out_dir / fn, FULL)
            make_jpeg(tool, src, out_dir / 'thumbs' / fn, THUMB)
        except RuntimeError as err:
            print(f'  ! could not convert {src.name}: {err}'); continue
        e = {'file': f'photos/{name}/{fn}', 'thumb': f'photos/{name}/thumbs/{fn}',
             'alt': caps.get(src.name) or caps.get(src.name.lstrip('_')) or 'Parish photograph'}
        cap = caps.get(src.name) or caps.get(src.name.lstrip('_'))
        if cap:
            e['caption'] = cap
        (favs if fav else entries).append(e)
        if n % 10 == 0:
            print(f'  ... {n}/{len(photos)}')
    allp = favs + entries
    if not allp:
        return False

    jpath = ROOT / 'data' / 'events' / f'{name}.json'
    old = json.loads(jpath.read_text(encoding='utf-8')) if jpath.exists() else {}
    title = info.get('title') or old.get('title') or rest.replace('-', ' ').replace('_', ' ').strip().title() or 'Parish photographs'
    d = date.fromisoformat(iso)
    ev = {
        'output': f'{name}.html', 'date': iso, 'title': title,
        'description': info.get('intro') or old.get('description') or f'Photographs: {title}, {d.day} {d.strftime("%B %Y")}.',
        'hero': {'file': allp[0]['file'], 'alt': title},
        'eyebrow': f'{d.strftime("%A")} {d.day} {d.strftime("%B %Y")}',
        'headline': title,
        'lead': info.get('intro') or old.get('lead', ''),
        'intro_heading': 'About this album',
        'intro': [info['intro']] if info.get('intro') else old.get('intro', []),
        'details': {},
        'sections': [],
        'gallery_heading': 'All Photographs',
        'gallery_subtitle': 'Select a photo to enlarge it.',
        'photos': allp,
    }
    if info.get('album') or old.get('album'):
        ev['album'] = old.get('album') or {'url': info['album'], 'label': 'Download Full-Resolution Photos', 'download': True}
        if info.get('album'):
            ev['album']['url'] = info['album']
    jpath.parent.mkdir(parents=True, exist_ok=True)
    jpath.write_text(json.dumps(ev, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    done = INBOX / '_done'
    done.mkdir(exist_ok=True)
    target = done / folder.name
    if target.exists():
        shutil.rmtree(target)
    shutil.move(str(folder), str(target))
    size_mb = sum(f.stat().st_size for f in out_dir.rglob('*') if f.is_file()) / 1e6
    print(f'  Published {len(allp)} photos ({size_mb:.0f} MB on the website) -> {name}.html')
    return True


def main():
    assume_yes = '--yes' in sys.argv
    INBOX.mkdir(exist_ok=True)
    folders = sorted(p for p in INBOX.iterdir() if p.is_dir() and not p.name.startswith(('_', '.')))
    if not folders:
        print('Nothing to do. Put photos in a folder such as  inbox/2026-11-08-remembrance-sunday/  and run this again.')
        return 0
    done = [f for f in folders if publish(f, assume_yes)]
    if done:
        sys.path.insert(0, str(ROOT))
        import build
        build.build()
        print('\nDone. Open photos.html in your browser to check, then commit and push in GitHub Desktop.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
