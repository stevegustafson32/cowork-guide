#!/usr/bin/env python3
"""Lint the site before a push.

Catches the drift that reading cannot: product names the app no longer
uses, guide counts that disagree with the path, links to anchors that are
gone, and a search index older than the pages it describes.

    python3 check-stale.py

Exits 1 when anything FAILs. WARN lines are for a human to judge.
"""

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

from site_data import EXTRA_PAGES, GUIDES, NUMBER_WORDS

ROOT = Path(__file__).parent
SITE_URL = "https://stevesaiguide.com/"
HOME_PAGE = "index.html"
INDEX_FILE = "search-index.json"
SITEMAP_FILE = "sitemap.xml"
SEARCH_SCRIPT = "search.js"
INDEX_BUILDER = "build-search-index.py"
INDEX_FIELDS = {"url", "label", "kind", "title", "desc", "headings", "text"}
WRITING_GUIDE = "claude-writing.html"  # teaches the banned list, so it names it

FAIL, WARN = "FAIL", "WARN"

NAV_BLOCK_RE = re.compile(
    r"<!-- SAG-NAV:START.*?<!-- SAG-NAV:END -->"
    r"|<!-- SAG-CHANGELOG -->.*?<!-- /SAG-CHANGELOG -->", re.S)
NON_TEXT_RE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]*>")

# Names and versions the product has moved past. A hit is a FAIL unless the
# same line matches an entry in STALE_ALLOWED.
STALE_RULES = {
    "Cowork named as a separate product": re.compile(r"\bCowork\b"),
    "old settings name": re.compile(r"Global instructions"),
    "superseded model: Opus 5": re.compile(r"\bOpus 5(?![.\d])"),
    "superseded model: Sonnet 5": re.compile(r"\bSonnet 5(?![.\d])"),
    "superseded model: Fable 5": re.compile(r"\bFable 5(?![.\d])"),
    "old github.io address": re.compile(r"github\.io/cowork-guide"),
    "double-encoded characters": re.compile(r"[\u0080-\u009f]"),
}

# Lines where a stale-looking string is right: titles of other people's
# work and dated history. Adding a line here is a decision, not a fix.
STALE_ALLOWED = [
    re.compile(r"Introducing Cowork"),
    re.compile(r"Get Started with Cowork"),
    re.compile(r"called Cowork"),            # dated history: the mode's old name
    re.compile(r"Cowork OS setup prompt"),   # Paul J Lipsky's name for his method
    re.compile(r"Claude Cowork Guide: 50\+ Tested Tips"),
    re.compile(r"Anthropic's Opus 5 guidance"),  # cites the guidance as published
    re.compile(r"Claude Cowork Plugins: What They Are"),
    re.compile(r"Chat / Cowork"),            # the switch on the earlier app
    re.compile(r"SAG-ROLLOUT"),              # generated rollout notice
]

GUIDE_COUNT_RE = re.compile(
    r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\s+guides\b", re.I)
RAMP_CARD_RE = re.compile(
    r'<a href="([^"]+)" class="ramp-card[^"]*">(.*?)</a>', re.S)
SECTION_COUNT_RE = re.compile(r"<span>(\d+) sections</span>")
ACCORDION_RE = re.compile(r'<div class="accordion" id=')
ID_RE = re.compile(r'\bid="([^"]+)"')
HREF_RE = re.compile(r'\bhref="([^"]+)"')
OG_IMAGE_RE = re.compile(r'<meta property="og:image" content="([^"]+)"')
SITEMAP_LOC_RE = re.compile(r"<loc>([^<]+)</loc>")

FREE_RE = re.compile(r"\bfree\b", re.I)
BANNED_WORDS_RE = re.compile(
    r"\b(delve|leverage|utilize|facilitate|robust|seamless|paramount|"
    r"multifaceted|holistic|ever-evolving|pivotal|crucial|furthermore|"
    r"moreover|additionally)\b", re.I)


class Finding(NamedTuple):
    level: str
    where: str
    message: str


def site_pages():
    return [g.file for g in GUIDES] + EXTRA_PAGES


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def blank(match):
    """Replace a block with its own newlines so line numbers survive."""
    return "\n" * match.group(0).count("\n")


def authored_lines(src):
    """The hand-written source, line by line, generated nav blanked out."""
    return NAV_BLOCK_RE.sub(blank, src).split("\n")


def visible_lines(src):
    """Reader-visible text per line: no nav, scripts, styles or tags."""
    text = NON_TEXT_RE.sub(blank, NAV_BLOCK_RE.sub(blank, src))
    return [TAG_RE.sub(" ", line) for line in text.split("\n")]


def excerpt(line, match):
    start = max(0, match.start() - 30)
    return line[start:match.end() + 30].strip()


def check_stale_strings(page, src):
    findings = []
    for number, line in enumerate(authored_lines(src), 1):
        if any(allowed.search(line) for allowed in STALE_ALLOWED):
            continue
        for label, pattern in STALE_RULES.items():
            match = pattern.search(line)
            if match:
                findings.append(Finding(
                    FAIL, f"{page}:{number}", f"{label}: …{excerpt(line, match)}…"))
    return findings


def stated_count(text):
    lowered = text.lower()
    return NUMBER_WORDS.index(lowered) if lowered in NUMBER_WORDS else int(text)


def check_guide_counts(name, src):
    findings = []
    for number, line in enumerate(src.split("\n"), 1):
        for match in GUIDE_COUNT_RE.finditer(line):
            if stated_count(match.group(1)) != len(GUIDES):
                findings.append(Finding(
                    FAIL, f"{name}:{number}",
                    f'says "{match.group(0)}"; the path has {len(GUIDES)}'))
    return findings


def check_ramp_cards(home_src):
    """Homepage cards: one per guide, in path order, true section counts."""
    findings = []
    cards = [card for card in RAMP_CARD_RE.findall(home_src) if is_local(card[0])]
    order = [href for href, _body in cards]
    if order != [g.file for g in GUIDES]:
        findings.append(Finding(
            FAIL, HOME_PAGE, f"ramp cards {order} do not match the path order"))
    for href, body in cards:
        stated = SECTION_COUNT_RE.search(body)
        actual = len(ACCORDION_RE.findall(read(href))) if (ROOT / href).exists() else 0
        if stated and int(stated.group(1)) != actual:
            findings.append(Finding(
                FAIL, HOME_PAGE,
                f"card for {href} says {stated.group(1)} sections; the page has {actual}"))
    return findings


def link_problem(href, page, ids_by_page):
    """Why a local link is broken, or an empty string when it resolves."""
    target, _, anchor = href.partition("#")
    target = target or page
    problem = ""
    if not (ROOT / target).exists():
        problem = f"links to missing file {target}"
    elif anchor and target in ids_by_page and anchor not in ids_by_page[target]:
        problem = f"links to missing anchor {target}#{anchor}"
    return problem


def is_local(href):
    external = re.match(r"[a-z][a-z0-9+.-]*:|//", href, re.I)
    return not external and not href.startswith("/") and href != "#"


def check_links(page, src, ids_by_page):
    findings = []
    for number, line in enumerate(src.split("\n"), 1):
        for href in HREF_RE.findall(line):
            problem = link_problem(href, page, ids_by_page) if is_local(href) else ""
            if problem:
                findings.append(Finding(FAIL, f"{page}:{number}", problem))
    return findings


def check_og_image(page, src):
    findings = []
    match = OG_IMAGE_RE.search(src)
    if not match:
        findings.append(Finding(FAIL, page, "no og:image tag"))
    elif not (ROOT / match.group(1).replace(SITE_URL, "")).exists():
        findings.append(Finding(FAIL, page, f"og:image file is missing: {match.group(1)}"))
    return findings


def check_sitemap():
    listed = {loc.replace(SITE_URL, "") or HOME_PAGE
              for loc in SITEMAP_LOC_RE.findall(read(SITEMAP_FILE))}
    expected = set(site_pages())
    findings = [Finding(FAIL, SITEMAP_FILE, f"missing {page}")
                for page in sorted(expected - listed)]
    findings += [Finding(FAIL, SITEMAP_FILE, f"lists unknown page {page}")
                 for page in sorted(listed - expected)]
    return findings


def check_search_index():
    spec = importlib.util.spec_from_file_location("index_builder", ROOT / INDEX_BUILDER)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    findings = []
    if builder.render_index() != read(INDEX_FILE):
        findings.append(Finding(
            FAIL, INDEX_FILE, f"out of date; run python3 {INDEX_BUILDER}"))
    entries = json.loads(read(INDEX_FILE))
    malformed = [e for e in entries if not isinstance(e, dict) or not INDEX_FIELDS <= set(e)]
    if malformed:
        findings.append(Finding(
            FAIL, INDEX_FILE, f"{len(malformed)} entries are missing fields search.js reads"))
    indexed = {e["url"] for e in entries if isinstance(e, dict) and "url" in e}
    findings += [Finding(FAIL, INDEX_FILE, f"no entry for {page}")
                 for page in site_pages() if page not in indexed]
    return findings


def check_copy_words(page, src):
    findings = []
    for number, line in enumerate(visible_lines(src), 1):
        match = FREE_RE.search(line)
        if match:
            findings.append(Finding(
                WARN, f"{page}:{number}", f'"free": …{excerpt(line, match)}…'))
        match = BANNED_WORDS_RE.search(line)
        if match and page != WRITING_GUIDE:
            findings.append(Finding(
                WARN, f"{page}:{number}", f"banned word: …{excerpt(line, match)}…"))
    return findings


def check_inbound_links(sources):
    """Pages nothing else links to outside the generated nav."""
    linked = set()
    for page, src in sources.items():
        hrefs = HREF_RE.findall(NAV_BLOCK_RE.sub("", src))
        linked |= {h.partition("#")[0] for h in hrefs if h.partition("#")[0] != page}
    orphans = [p for p in site_pages() if p not in linked and p != HOME_PAGE]
    return [Finding(WARN, page, "no page links here outside the nav") for page in orphans]


def collect():
    sources = {page: read(page) for page in site_pages()}
    ids_by_page = {page: set(ID_RE.findall(src)) for page, src in sources.items()}
    findings = []
    for page, src in sources.items():
        findings += check_stale_strings(page, src)
        findings += check_guide_counts(page, src)
        findings += check_links(page, src, ids_by_page)
        findings += check_og_image(page, src)
        findings += check_copy_words(page, src)
    for name in (SEARCH_SCRIPT, INDEX_FILE):
        findings += check_guide_counts(name, read(name))
    findings += check_ramp_cards(sources[HOME_PAGE])
    findings += check_sitemap()
    findings += check_search_index()
    findings += check_inbound_links(sources)
    return findings


def main():
    findings = collect()
    for level in (FAIL, WARN):
        for finding in (f for f in findings if f.level == level):
            print(f"{finding.level}  {finding.where:<38} {finding.message}")
    fails = sum(1 for f in findings if f.level == FAIL)
    warns = len(findings) - fails
    print(f"\n{fails} failing, {warns} to review.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
