#!/usr/bin/env python3
"""Rebuild search-index.json section entries for the guide pages.

Keeps the existing 13 page-level entries untouched (they carry curated
labels/descriptions). Drops any previous section entries (url contains '#')
and regenerates them from the current HTML, one entry per .accordion section,
so search results deep-link to the exact section. Safe to re-run any time a
guide page changes.
"""
import json, re, html as htmllib, pathlib

REPO = pathlib.Path(__file__).parent
GUIDE_PAGES = ["beginner.html", "level-2.html", "prompting.html",
               "workflows.html", "claude-code-2.html", "claude-design.html",
               "claude-everywhere.html"]

def strip_tags(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()

idx = json.loads((REPO / "search-index.json").read_text())
idx = [e for e in idx if "#" not in e["url"]]
page_labels = {e["url"]: e["label"] for e in idx}

sections = []
for page in GUIDE_PAGES:
    src = (REPO / page).read_text()
    label = page_labels.get(page, page)
    # each section runs from its wrapper div to the next one (or a page-end marker)
    parts = re.split(r'<div class="accordion" id="([a-z0-9-]+)">', src)
    for i in range(1, len(parts), 2):
        slug, body = parts[i], parts[i + 1]
        tm = re.search(r'<h2 class="accordion-title">(.*?)</h2>', body, re.S)
        title = strip_tags(tm.group(1)) if tm else slug
        sm = re.search(r'<div class="accordion-subtitle">(.*?)</div>', body, re.S)
        desc = strip_tags(sm.group(1)) if sm else ""
        lm = re.search(r'<div class="accordion-label">(.*?)</div>', body, re.S)
        step = strip_tags(lm.group(1)) if lm else ""
        headings = [strip_tags(h) for h in re.findall(r"<h3[^>]*>(.*?)</h3>", body, re.S)]
        sections.append({
            "url": f"{page}#{slug}",
            "label": f"{label} · {step}" if step else label,
            "title": title,
            "desc": desc,
            "headings": headings,
            "text": strip_tags(body).lower(),
        })

(REPO / "search-index.json").write_text(
    json.dumps(idx + sections, ensure_ascii=False, indent=1))
print(f"pages kept: {len(idx)}, section entries written: {len(sections)}")
