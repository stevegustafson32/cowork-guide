# cowork-guide

Source for [stevesaiguide.com](https://stevesaiguide.com): Steve's AI Guide, a set of guides to using Claude for knowledge work. Static HTML on GitHub Pages. A push to `main` is live in about two minutes.

## Before every push

```bash
python3 build-nav.py
python3 build-search-index.py
python3 check-stale.py
```

- `build-nav.py` writes the shared header into every page, between the `SAG-NAV` markers. Never edit that block by hand.
- `build-search-index.py` rebuilds `search-index.json` from the pages.
- `check-stale.py` fails on product names the app no longer uses, guide counts that disagree with the path, broken local links, and a search index older than the pages.

## Where things live

- `site_data.py` holds the guide order, the app list, and the dated log of product changes. Add or reorder a guide there, then run the three commands.
- Homepage guide cards in `index.html` are written by hand. The lint checks their order and section counts.

## Preview

```bash
python3 -m http.server 4170
```

Open `http://localhost:4170`. Root-relative links break when a page is opened as a file.
