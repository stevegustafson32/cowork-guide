#!/usr/bin/env python3
"""Render the share images (the cards shown when a page is linked).

One 1200x630 PNG per page in assets/, drawn from a single HTML template
and captured with headless Chrome, so every card matches. Run it after
adding a guide or changing a card's wording:

    python3 build-og.py

Uses system fonts only (Georgia, Helvetica), so it needs no network.
"""

import html
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

from site_data import GUIDES

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH, HEIGHT = 1200, 630
SITE = "stevesaiguide.com"
BRAND = "Steve's AI Guide"

WARM, INDIGO, GREEN, BLUE, VIOLET = "#d4956a", "#7b8bd4", "#6ab88f", "#5b9bd5", "#9b7ed8"


class Card(NamedTuple):
    file: str
    kicker: str
    title: str
    tagline: str
    accent: str


# Per guide: the label after "STEP n", the tagline, the accent colour.
GUIDE_CARDS = {
    "prompting.html": ("og-prompting.png", "Core skill", "From search bar to strategic partner.", WARM),
    "beginner.html": ("og-beginner.png", "Setup", "Your first week, chatbot to partner.", WARM),
    "level-2.html": ("og-level-2.png", "Level up", "Techniques for power users.", INDIGO),
    "workflows.html": ("og-workflows.png", "Real work", "Eight workflows that actually work.", GREEN),
    "claude-code-2.html": ("og-claude-code-2.png", "Action AI", "Built for non-coders.", WARM),
    "claude-design.html": ("og-claude-design.png", "Look good", "Stunning decks. Skip Canva.", WARM),
    "claude-office.html": ("og-claude-office.png", "In the file", "Excel, PowerPoint & PDF as agents.", BLUE),
    "claude-writing.html": ("og-claude-writing.png", "Sound like you", "Sound like you, not like AI.", WARM),
    "claude-everywhere.html": ("og-claude-everywhere.png", "On your phone", "Mobile, web, and cloud.", WARM),
    "claude-plugins.html": ("og-claude-plugins.png", "Stay safe", "What to install, what to skip.", WARM),
}

OTHER_CARDS = [
    Card("og-people.png", "People I learn from", "The People", "Who shaped these guides.", VIOLET),
    Card("og-whats-changed.png", "Change log", "What Changed", "Every Claude change, dated and sourced.", VIOLET),
]

HOME_FILE = "og-image.png"
HOME_TAGLINE = "The complete guide to Claude for knowledge work, from zero to power user."

PAGE_STYLE = """
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: 1200px; height: 630px; overflow: hidden; color: #f3ece2;
         font-family: Helvetica, Arial, sans-serif;
         background: linear-gradient(180deg, color-mix(in srgb, ACCENT 16%, #141414) 0%, #0e0e0e 100%); }
  .mark { position: absolute; left: 90px; display: flex; align-items: center; justify-content: center;
          background: ACCENT; color: #17120e; font-family: Georgia, serif; font-weight: 700; }
  .brand { position: absolute; font-weight: 700; }
  .kicker { position: absolute; left: 90px; top: 250px; font-size: 24px; font-weight: 700;
            letter-spacing: 0.03em; text-transform: uppercase; color: ACCENT; }
  .title { position: absolute; left: 88px; top: 286px; font-family: Georgia, serif;
           font-size: 84px; font-weight: 700; letter-spacing: -0.5px; white-space: nowrap; }
  .tagline { position: absolute; left: 90px; font-size: 36px; color: #b4aca1; line-height: 1.35; }
  .rule { position: absolute; left: 92px; height: 5px; background: ACCENT; }
  .site { position: absolute; left: 90px; font-size: 26px; color: #b4aca1; }
"""

CARD_BODY = """
<div class="mark" style="top:120px;width:85px;height:85px;border-radius:20px;font-size:56px;">S</div>
<div class="brand" style="left:200px;top:134px;font-size:42px;">{brand}</div>
<div class="kicker">{kicker}</div>
<div class="title">{title}</div>
<div class="tagline" style="top:396px;">{tagline}</div>
<div class="rule" style="top:478px;width:161px;"></div>
<div class="site" style="top:508px;">{site}</div>
"""

HOME_BODY = """
<div class="mark" style="top:150px;width:97px;height:97px;border-radius:22px;font-size:62px;">S</div>
<div class="brand" style="left:220px;top:156px;font-size:80px;">Steve's <span style="color:{accent}">AI</span> Guide</div>
<div class="tagline" style="top:298px;width:960px;">{tagline}</div>
<div class="rule" style="top:430px;width:181px;"></div>
<div class="site" style="top:472px;font-weight:700;color:{accent};">{site}</div>
"""


def guide_cards():
    cards = []
    for number, guide in enumerate(GUIDES, 1):
        file, label, tagline, accent = GUIDE_CARDS[guide.file]
        cards.append(Card(file, f"Step {number} &middot; {label}", guide.title, tagline, accent))
    return cards


def page(body, accent):
    style = PAGE_STYLE.replace("ACCENT", accent)
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{style}</style></head><body>{body}</body></html>"


def card_page(card):
    body = CARD_BODY.format(brand=html.escape(BRAND), kicker=card.kicker,
                            title=html.escape(card.title), tagline=html.escape(card.tagline),
                            site=SITE)
    return page(body, card.accent)


def home_page():
    body = HOME_BODY.format(accent=WARM, tagline=html.escape(HOME_TAGLINE), site=SITE)
    return page(body, WARM)


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
