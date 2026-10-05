#!/usr/bin/env python3
"""Rebuild search-index.json from the current HTML.

One entry per page, then one per .accordion section on the guide pages, so
search results deep-link to the exact section. Nothing in the index is
written by hand: page titles and descriptions come from each page's own
<title> and meta description, labels from site_data.py.

    python3 build-search-index.py

Idempotent. Safe to re-run any time a page changes.
"""

import html as htmllib
import json
import re
from pathlib import Path

from site_data import EXTRAS, GUIDE_KIND, GUIDES, Page

ROOT = Path(__file__).parent
INDEX_FILE = ROOT / "search-index.json"

# A guide's sections carry its full text, so its page entry keeps an opening
# excerpt only. Pages without sections are indexed whole.
GUIDE_EXCERPT_CHARS = 2500

NAV_BLOCK_RE = re.compile(r"<!-- SAG-NAV:START.*?<!-- SAG-NAV:END -->", re.S)
NON_TEXT_RE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
SECTION_SPLIT_RE = re.compile(r'<div class="accordion" id="([a-z0-9-]+)">')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="(.*?)"', re.S)
BODY_RE = re.compile(r"<body[^>]*>(.*)</body>", re.S)
HEADING_RE = re.compile(r"<h[123][^>]*>(.*?)</h[123]>", re.S)
SUBHEADING_RE = re.compile(r"<h3[^>]*>(.*?)</h3>", re.S)
SECTION_FIELDS = {
    "title": re.compile(r'<h2 class="accordion-title">(.*?)</h2>', re.S),
    "desc": re.compile(r'<div class="accordion-subtitle">(.*?)</div>', re.S),
    "step": re.compile(r'<div class="accordion-label">(.*?)</div>', re.S),
}


def strip_tags(markup):
    text = NON_TEXT_RE.sub(" ", markup)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", htmllib.unescape(text)).strip()


def first_match(pattern, markup, fallback=""):
    found = pattern.search(markup)
    return strip_tags(found.group(1)) if found else fallback


def first_match_raw(pattern, markup):
    found = pattern.search(markup)
    return found.group(1) if found else ""


def site_pages():
    """Every indexed page: home first, then the path, then the rest."""
    guides = [Page(g.file, g.title, GUIDE_KIND) for g in GUIDES]
    return EXTRAS[:1] + guides + EXTRAS[1:]


def page_entry(page, src):
    body = NAV_BLOCK_RE.sub(" ", first_match_raw(BODY_RE, src))
    text = strip_tags(body).lower()
    if page.kind == GUIDE_KIND:
        text = text[:GUIDE_EXCERPT_CHARS]
    entry = {
        "url": page.file,
        "label": page.label,
        "kind": page.kind,
        "title": first_match(TITLE_RE, src, page.label),
        "desc": first_match(DESC_RE, src),
        "headings": [strip_tags(h) for h in HEADING_RE.findall(body)],
        "text": text,
    }
    return entry


def section_entries(page, src):
    """One entry per accordion; each runs from its wrapper div to the next."""
    parts = SECTION_SPLIT_RE.split(src)
    entries = []
    for i in range(1, len(parts), 2):
        slug, body = parts[i], parts[i + 1]
        step = first_match(SECTION_FIELDS["step"], body)
        entries.append({
            "url": f"{page.file}#{slug}",
            "label": f"{page.label} · {step}" if step else page.label,
            "kind": page.kind,
            "title": first_match(SECTION_FIELDS["title"], body, slug),
            "desc": first_match(SECTION_FIELDS["desc"], body),
            "headings": [strip_tags(h) for h in SUBHEADING_RE.findall(body)],
            "text": strip_tags(body).lower(),
        })
    return entries


def build_index():
    pages, sections = [], []
    for page in site_pages():
        src = (ROOT / page.file).read_text(encoding="utf-8")
        pages.append(page_entry(page, src))
        if page.kind == GUIDE_KIND:
            sections.extend(section_entries(page, src))
    return pages, sections


def render_index():
    """The exact text of search-index.json for the current pages."""
    pages, sections = build_index()
    return json.dumps(pages + sections, ensure_ascii=False, indent=1)


def main():
    pages, sections = build_index()
    INDEX_FILE.write_text(render_index(), encoding="utf-8")
    print(f"pages written: {len(pages)}, section entries written: {len(sections)}")


if __name__ == "__main__":
    main()
