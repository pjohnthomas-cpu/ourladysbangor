# Editing the parish website

The pages `index.html`, `photos.html` and every photo-album page are **built** from the files in
`data/` and `templates/`. Do not edit them by hand: the next build overwrites them.

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

## Each week: photos

1. Make a folder inside `inbox/` named with the date and a few words, for example
   `inbox/2026-11-08-remembrance-sunday/`, and drop the photos from your iPhone into it
   (AirDrop, or Photos > File > Export). HEIC files are fine.
2. Optional, inside that folder:
   - `info.txt` with lines like `title: Remembrance Sunday`, `intro: One sentence about the day.`
     and `album: https://...` (a Google link to the full-size originals).
   - `captions.txt` with lines like `IMG_1234.jpeg: Fr. Savi greets the congregation`.
   - Put an underscore in front of a photo's name (`_IMG_1234.jpeg`) to make it a favourite:
     favourites come first and the first one is the big picture at the top.
3. Double-click `publish-photos.command`. It asks you to confirm you have permission to publish
   photos of people (especially children), shrinks the photos, removes location data, adds the
   album to the site and rebuilds it. Your originals stay in `inbox/_done/` and are never uploaded.
4. Open `photos.html` and the new album page in a browser and check them.
5. Commit and push in GitHub Desktop.

Albums are listed newest first on `photos.html`, and the three newest appear on the home page.
To change an album later (title, intro, captions, remove a photo) edit `data/events/<name>.json`
and run `python3 build.py`. Large events such as a bishop's visit: keep the best 100-150 photos
here and link the rest with `album:` in `info.txt`; the script warns you when an album is large.
To add chapters with headings and text to an album, see `data/events/family-eucharist-2026-05-03.json`.

## Small rules for the data files

- Keep the quotation marks, commas and brackets exactly as in the existing entries.
- In notice text, `*word*` makes italics and an email address becomes a link automatically.
- `{next_edition}` and `{deadline}` in a notice are filled in from `site.json`.
- Badge styles in the calendar: `feast`, `none`, `lent`, `holy`, `easter`.
- Never put bank details, children's names (captions and intros too) or other private details on the site.

## What is where

- `publish_photos.py` and `publish-photos.command`: the weekly photo script.
- `data/events/`: one file per photo album (the old event pages are here too, at the same web addresses).
- `templates/`: page sections that rarely change (header, music, gallery, contact, footer).
- `assets/site.css` and `assets/site.js`: look and behaviour.
- `build.py`: the build script (Python 3 only, nothing to install).
