# Editing the parish website

The page `index.html` is **built** from the files in `data/` and `templates/`.
Do not edit `index.html` by hand: the next build overwrites it.

## Each month

1. Put the new newsletter PDF in this folder (for example `theflamedecember26.pdf`).
2. Edit the files in `data/`:
   - `site.json`: month name, newsletter file name, summary, next edition and deadline.
   - `calendar.json`: one entry per day. Weekday names are worked out from the date.
   - `masses.json`: weekly Mass and confession times, and the red alert line.
   - `notices.json`: one entry per notice card.
   - `forms.json`: forms and the PDF each links to.
   - `../announcement.json`: the "Important Announcement" box (set `"hidden": true` to hide it).
3. Open Terminal in this folder and run: `python3 build.py`
4. Open `index.html` in a browser and check it.
5. Commit and push in GitHub Desktop.

## Small rules for the data files

- Keep the quotation marks, commas and brackets exactly as in the existing entries.
- In notice text, `*word*` makes italics and an email address becomes a link automatically.
- `{next_edition}` and `{deadline}` in a notice are filled in from `site.json`.
- Badge styles in the calendar: `feast`, `none`, `lent`, `holy`, `easter`.
- Never put bank details, children's names or other private details on the site.

## What is where

- `templates/`: page sections that rarely change (header, music, gallery, contact, footer).
- `assets/site.css` and `assets/site.js`: look and behaviour.
- `build.py`: the build script (Python 3 only, nothing to install).
