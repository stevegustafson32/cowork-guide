# cowork-guide

Source for [stevesaiguide.com](https://stevesaiguide.com): Steve's AI Guide, a set of guides to using Claude for knowledge work. Static HTML on GitHub Pages. A push to `main` is live in about two minutes.

## Before every push

```bash
python3 build-nav.py
python3 build-search-index.py
python3 check-stale.py
```

- `build-nav.py` writes the shared header into every page, between the `SAG-NAV` markers. Never edit that block by hand.
  It also stamps `?v=<hash>` on every shared stylesheet and script link (design-system.css, nav.css, cover.css, nav.js, search.js, sections.js, progress.js), so rerun it after editing any of those files; `check-stale.py` fails when a page's hash is behind the file.
- `progress.js` remembers the section a reader reached in each guide (localStorage, this browser only) and drives the "Continue" rows and hero button on the homepage, the reading line at the top of the viewport, and the "Resume" link in the path rail.
- `build-search-index.py` rebuilds `search-index.json` from the pages.
- `check-stale.py` fails on product names the app no longer uses, guide counts that disagree with the path, broken local links, and a search index older than the pages.

Every guide section ends with a "Checked <month>" stamp from `python3 build-stamps.py`, between `SAG-CHECKED` markers (never hand-edit). The month is the page's revision date; to mark one section as re-verified later, add `("page.html", "section-id"): "YYYY-MM-DD"` to `site_data.SECTION_CHECKS` and rerun. `check-stale.py` fails when a stamp is missing or behind the data.

After adding a guide or changing its cover line in `site_data.COVERS`, also run `python3 build-covers.py` (stamps the paper cover into each guide hero between the `SAG-COVER` markers; never edit that block by hand) and then `python3 build-og.py`, which draws the share images in `assets/` from the same cover.

## Where things live

- `site_data.py` holds the guide order, the app list, and the dated log of product changes. Add or reorder a guide there, then run the three commands.
- Homepage guide cards in `index.html` are written by hand. The lint checks their order and section counts.

## Preview

```bash
python3 -m http.server 4170
```

Open `http://localhost:4170`. Root-relative links break when a page is opened as a file.
