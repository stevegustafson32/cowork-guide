"""Generated blocks other than the nav.

Date stamps, the rollout notice, the change log and the sitemap all derive
from site_data.py. A page opts in by carrying a marker pair:

    <!-- SAG-STAMP -->October 2026<!-- /SAG-STAMP -->
    <!-- SAG-ROLLOUT:line --><!-- /SAG-ROLLOUT -->
    <!-- SAG-CHANGELOG --><!-- /SAG-CHANGELOG -->

build-nav.py rewrites whatever sits between each pair on every run.
"""

import html
import re
from datetime import date
from urllib.parse import urlparse

from site_data import (AFTER_PATH, BASE_EDITION, CHANGELOG_PAGE, CHANGES,
                       EXTRAS, GUIDES, ROLLOUT, change_id)

SITE_URL = "https://stevesaiguide.com/"
HOME_PAGE = "index.html"
UPPER = "upper"
PENDING_NOTE = "Guide updates in progress."

# Sitemap priority: home, the two entry guides, other guides, the rest.
HOME_PRIORITY = "1.0"
ENTRY_GUIDES = ("prompting.html", "beginner.html")
ENTRY_PRIORITY = "0.9"
GUIDE_PRIORITY = "0.8"
PAGE_PRIORITY = {"About": "0.6", "Updates": "0.6", "Plugin": "0.5"}

GUIDE_TITLES = {g.file: g.title for g in GUIDES}


def fill(src, name, render):
    """Rewrite the inside of every SAG-<name> marker pair in a page."""
    pattern = re.compile(
        rf"(<!-- SAG-{name}(?::([a-z]+))? -->)(.*?)(<!-- /SAG-{name} -->)", re.S)
    return pattern.sub(
        lambda m: m.group(1) + render(m.group(2) or "") + m.group(4), src)


def site_date():
    """The day the site was last revised for any change."""
    applied = [c.applied for c in CHANGES if c.applied]
    return max(applied + [BASE_EDITION])


def page_date(page):
    """The day one page was last revised; home and the log track the whole site."""
    applied = [c.applied for c in CHANGES if c.applied and page in c.pages]
    latest = max(applied + [BASE_EDITION])
    return site_date() if page in (HOME_PAGE, CHANGELOG_PAGE) else latest


def month_label(iso):
    day = date.fromisoformat(iso)
    return f"{day:%B} {day.year}"


def day_label(iso):
    day = date.fromisoformat(iso)
    return f"{day:%B} {day.day}, {day.year}"


def stamp_renderer(page):
    label = month_label(page_date(page))
    return lambda variant: label.upper() if variant == UPPER else label


def render_rollout(variant):
    return ROLLOUT.get(variant, "")


def guide_links(change):
    links = [f'<a href="{page}">{GUIDE_TITLES[page]}</a>'
             for page in change.pages if page in GUIDE_TITLES]
    return "Updated in: " + ", ".join(links) + "." if change.applied and links else PENDING_NOTE


def render_change(change):
    host = urlparse(change.source).netloc.removeprefix("www.")
    return (
        f'<article class="change" id="{change_id(change)}">\n'
        f'  <div class="change-date">{day_label(change.date)}</div>\n'
        f'  <h2 class="change-title">{html.escape(change.title)}</h2>\n'
        f'  <p>{html.escape(change.body)}</p>\n'
        f'  <p class="change-meta"><a href="{change.source}" target="_blank" '
        f'rel="noopener">Source: {host}</a> &middot; {guide_links(change)}</p>\n'
        f'</article>'
    )


def render_changelog(_variant):
    newest_first = sorted(CHANGES, key=lambda c: c.date, reverse=True)
    return "\n" + "\n".join(render_change(c) for c in newest_first) + "\n"


def path_link(side, label, href, title):
    return (f'  <a class="{side}" href="{href}"><span class="pn-label">{label}</span>'
            f'<span class="pn-title">{title}</span></a>\n')


def path_nav_renderer(page):
    """Previous / all guides / next for one guide, from the path order."""
    files = [g.file for g in GUIDES]
    markup = ""
    if page in files:
        i = files.index(page)
        after = GUIDES[i + 1] if i + 1 < len(GUIDES) else AFTER_PATH
        after_title = getattr(after, "title", None) or after.label
        prev = (path_link("prev", "&larr; Previous", GUIDES[i - 1].file, GUIDES[i - 1].title)
                if i else '  <span class="pn-empty"></span>\n')
        markup = ('\n<nav class="path-nav" aria-label="Guide navigation">\n' + prev
                  + '  <a class="hub" href="/">All guides</a>\n'
                  + path_link("next", "Next &rarr;", after.file, after_title) + "</nav>\n")
    return lambda _variant: markup


def render_guide_list(_variant):
    """The homepage footer's list of guides."""
    rows = []
    for guide in GUIDES:
        badge = '<span class="nav-new">NEW</span>' if guide.is_new else ""
        rows.append(f'        <a href="{guide.file}">{guide.title}{badge}</a>')
    return "\n" + "\n".join(rows) + "\n        "


def apply_blocks(page, src):
    """Fill every generated block a page carries."""
    src = fill(src, "STAMP", stamp_renderer(page))
    src = fill(src, "ROLLOUT", render_rollout)
    src = fill(src, "PATHNAV", path_nav_renderer(page))
    src = fill(src, "GUIDELIST", render_guide_list)
    return fill(src, "CHANGELOG", render_changelog)


def sitemap_priority(page, kind):
    priority = PAGE_PRIORITY.get(kind, GUIDE_PRIORITY)
    if page == HOME_PAGE:
        priority = HOME_PRIORITY
    elif page in ENTRY_GUIDES:
        priority = ENTRY_PRIORITY
    return priority


def render_sitemap():
    pages = ([(HOME_PAGE, "Home")] + [(g.file, "Guide") for g in GUIDES]
             + [(p.file, p.kind) for p in EXTRAS if p.file != HOME_PAGE])
    rows = []
    for page, kind in pages:
        loc = SITE_URL + ("" if page == HOME_PAGE else page)
        rows.append(f"  <url><loc>{loc}</loc><lastmod>{page_date(page)}</lastmod>"
                    f"<priority>{sitemap_priority(page, kind)}</priority></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n")
