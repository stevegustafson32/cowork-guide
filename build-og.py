#!/usr/bin/env python3
"""Render the share images (the cards shown when a page is linked).

One 1200x630 PNG per page in assets/, captured with headless Chrome from a
single template: the brand and title on the left, the guide's paper cover
(the same markup and cover.css the site uses) standing on the right. Run it
after adding a guide or changing a cover's wording:

    python3 build-og.py

Uses system fonts only (Georgia, Helvetica), so it needs no network.
"""

import html
import subprocess
import sys
import tempfile
from importlib import import_module
from pathlib import Path
from typing import NamedTuple

from site_data import COVERS, GUIDES

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH, HEIGHT = 1200, 630
SITE = "stevesaiguide.com"
ACCENT = "#d4956a"
STAMP = "October 2026"
COVERS_MODULE = import_module("build-covers")


class Card(NamedTuple):
    file: str
    kicker: str
    title_html: str
    tagline: str
    cover: str


GUIDE_KICKERS = {
    "prompting.html": "Core skill",
    "beginner.html": "Setup",
    "level-2.html": "Level up",
    "workflows.html": "Real work",
    "claude-code-2.html": "Action AI",
    "claude-design.html": "Look good",
    "claude-office.html": "In the file",
    "claude-writing.html": "Sound like you",
    "claude-everywhere.html": "On your phone",
    "claude-plugins.html": "Stay safe",
}

OTHER_CARDS = [
    Card("og-people.png", "People I learn from", "The <i>People</i>", "Who shaped these guides.", ""),
    Card("og-whats-changed.png", "Change log", "What <i>Changed</i>", "Every Claude change, dated and sourced.", ""),
]

HOME_FILE = "og-image.png"
HOME_TAGLINE = "The complete guide to Claude for knowledge work, from zero to power user."

PAGE_STYLE = """
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: 1200px; height: 630px; overflow: hidden; color: #f3ece2; position: relative;
         font-family: Helvetica, Arial, sans-serif;
         background: radial-gradient(900px 500px at 80% 110%, rgba(212,149,106,0.14), transparent 60%),
                     linear-gradient(180deg, #1a1410 0%, #0e0e0e 100%); }
  .left { position: absolute; left: 90px; top: 0; height: 630px; width: 640px;
          display: flex; flex-direction: column; justify-content: center; }
  .brand { display: flex; align-items: center; gap: 16px; font-weight: 700; font-size: 26px; margin-bottom: 44px; }
  .brand i { font-family: Georgia, serif; color: ACCENT; font-weight: 400; }
  .mark { width: 44px; height: 44px; border-radius: 50%; background: ACCENT; color: #17120e;
          display: flex; align-items: center; justify-content: center;
          font-family: Georgia, serif; font-style: italic; font-weight: 700; font-size: 24px; }
  .kicker { font-size: 18px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: ACCENT; margin-bottom: 18px; }
  .title { font-family: Georgia, serif; font-size: 72px; line-height: 1.02; letter-spacing: -1.5px; margin-bottom: 26px; }
  .title i { color: ACCENT; }
  .tagline { font-size: 28px; color: #a8a29e; line-height: 1.4; max-width: 560px; }
  .site { position: absolute; left: 90px; bottom: 54px; font-size: 20px; color: #a8a29e; letter-spacing: 0.04em; }
  .cover-slot { position: absolute; right: 100px; top: 75px; width: 360px; }
  .guide-cover { font-family: Helvetica, Arial, sans-serif; transform: perspective(1400px) rotateY(-11deg) rotateX(2deg); }
  .cover-title { font-family: Georgia, serif; font-size: 40px; }
  .cover-mark, .cover-bottom em { font-family: Georgia, serif; }
"""

BODY = """
<div class="left">
  <div class="brand"><span class="mark">S</span><span>Steve's <i>AI</i> Guide</span></div>
  <div class="kicker">{kicker}</div>
  <div class="title">{title}</div>
  <div class="tagline">{tagline}</div>
</div>
<div class="site">{site}</div>
<div class="cover-slot">{cover}</div>
"""


def guide_cards():
    cards = []
    for number, guide in enumerate(GUIDES, 1):
        cover = COVERS[guide.file]
        stem = guide.file.replace(".html", "")
        markup = COVERS_MODULE.cover_html(number, cover.title_html, cover.subtitle, STAMP)
        cards.append(Card(f"og-{stem}.png", f"Step {number} · {GUIDE_KICKERS[guide.file]}",
                          cover.title_html, cover.subtitle, markup))
    return cards


def page(body):
    cover_css = (ROOT / "cover.css").read_text(encoding="utf-8")
    style = cover_css + PAGE_STYLE.replace("ACCENT", ACCENT)
    markup = f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{style}</style></head><body>{body}</body></html>"
    return markup


def card_page(card):
    body = BODY.format(kicker=card.kicker, title=card.title_html,
                       tagline=html.escape(card.tagline), site=SITE, cover=card.cover)
    return page(body)


def home_page():
    cover = COVERS["prompting.html"]
    markup = COVERS_MODULE.cover_html(1, cover.title_html, cover.subtitle, STAMP)
    card = Card(HOME_FILE, "Ten guides, in order", "Claude for <i>knowledge work</i>", HOME_TAGLINE, markup)
    return card_page(card)


def render(markup, target):
    """Capture one page to a PNG with headless Chrome."""
    with tempfile.TemporaryDirectory() as work:
        source = Path(work) / "card.html"
        source.write_text(markup, encoding="utf-8")
        subprocess.run(
            [CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
             f"--window-size={WIDTH},{HEIGHT}", f"--screenshot={target}", source.as_uri()],
            check=True, capture_output=True, timeout=60)


def main():
    if not Path(CHROME).exists():
        raise SystemExit(f"Chrome not found at {CHROME}")
    for card in guide_cards() + OTHER_CARDS:
        render(card_page(card), ASSETS / card.file)
        print(f"  {card.file}")
    render(home_page(), ASSETS / HOME_FILE)
    print(f"  {HOME_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
