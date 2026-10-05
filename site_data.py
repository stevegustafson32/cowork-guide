"""Shared site data: the path, the apps, and the dated change log.

build-nav.py, build-search-index.py and check-stale.py all read from here,
so the guide order and the product facts live in one place.
"""

from typing import NamedTuple


class Guide(NamedTuple):
    file: str
    title: str
    read_time: str
    is_new: bool


class App(NamedTuple):
    url: str
    name: str
    audience: str
    is_new: bool


class Page(NamedTuple):
    file: str
    label: str
    kind: str


class Change(NamedTuple):
    """One product change.

    `date` is the event date and never moves. `applied` is the day the
    guides were revised for it; empty means they have not been yet.
    """
    date: str
    title: str
    body: str
    source: str
    pages: tuple
    applied: str = ""


# The path, in reading order. Read times come from the homepage ramp cards.
GUIDES = [
    Guide("prompting.html", "The Prompting Guide", "45 min", False),
    Guide("beginner.html", "Claude Beginner", "35 min", False),
    Guide("level-2.html", "Claude Advanced", "50 min", False),
    Guide("workflows.html", "Claude in Action", "30 min", False),
    Guide("claude-code-2.html", "Claude Code 2.0", "40 min", False),
    Guide("claude-design.html", "Claude Design", "35 min", False),
    Guide("claude-office.html", "Claude in Office", "30 min", False),
    Guide("claude-writing.html", "Claude Writing", "25 min", False),
    Guide("claude-everywhere.html", "Claude Everywhere", "20 min", False),
    Guide("claude-plugins.html", "Claude Plugins", "15 min", True),
]

# Where the last guide's "Next" link goes.
AFTER_PATH = Page("people.html", "People I Learn From", "About")

APPS = [
    App("https://keyroom.stevesaiguide.com", "Keyroom", "Residential real estate", False),
    App("https://boardroom.stevesaiguide.com", "Boardroom", "Commercial real estate", False),
    App("https://toolroom.stevesaiguide.com", "Toolroom", "Builders &amp; GCs", False),
    App("https://righthand.stevesaiguide.com", "Righthand", "Executive assistants", True),
    App("https://students.stevesaiguide.com", "Recall", "Students", True),
]

# Pages that get the nav but sit outside the path. `kind` is the tag a
# search result shows beside the label.
EXTRAS = [
    Page("index.html", "Home", "Home"),
    Page("people.html", "People I Learn From", "About"),
    Page("whats-changed.html", "What Changed", "Updates"),
    Page("follow-up-tracker.html", "Follow-Up Tracker", "Plugin"),
    Page("linkedin-audience-simulator.html", "LinkedIn Audience Simulator", "Plugin"),
    Page("linkedin-content-engine.html", "LinkedIn Content Engine", "Plugin"),
    Page("linkedin-feed-tracker.html", "LinkedIn Feed Tracker", "Plugin"),
]
EXTRA_PAGES = [page.file for page in EXTRAS]

GUIDE_KIND = "Guide"

NUMBER_WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "eleven", "twelve")


def count_word(n):
    """Spell a small count the way the site copy does ("nine guides")."""
    return NUMBER_WORDS[n]


def change_id(change):
    """Anchor for one change-log entry; stable because the date never moves."""
    slug = "".join(ch if ch.isalnum() else "-" for ch in change.title.lower())
    return f"c-{change.date}-" + "-".join(part for part in slug.split("-") if part)


# Last full edition before the change log began. Pages no change has
# touched since keep this date on their stamp.
BASE_EDITION = "2026-08-18"
CHANGELOG_PAGE = "whats-changed.html"
MERGE_ANCHOR = "c-2026-09-16-cowork-and-chat-are-one-claude"

# Shown only while Anthropic's merge of Cowork into Claude is still rolling
# out, for readers whose app has the old Chat / Cowork switch. When the
# rollout ends, set both values to "" and rebuild; every page drops them.
ROLLOUT = {
    "full": (
        '<div class="info-box tip sag-rollout">'
        "<strong>Two versions of the app are in use right now.</strong> "
        "Anthropic began merging Cowork into Claude on September 16, 2026, "
        "starting with Pro and Max plans. Look at the box where you type. "
        "If it shows a <strong>Chat / Cowork</strong> switch, you have the "
        "earlier version: pick <strong>Cowork</strong> before you send any "
        "task that works with files. If there is no switch, you have the "
        "merged app and can skip that step. Everything else in this guide is "
        f'the same on both. <a href="{CHANGELOG_PAGE}#{MERGE_ANCHOR}">What changed</a>.'
        "</div>"
    ),
    "line": (
        '<p class="sag-rollout">Message box shows a Chat / Cowork switch? '
        "Pick <strong>Cowork</strong> for this. "
        f'<a href="{CHANGELOG_PAGE}#{MERGE_ANCHOR}">Why</a>.</p>'
    ),
}

# Cloudflare Web Analytics site token. Empty means no beacon is written.
ANALYTICS_TOKEN = ""

# Product changes since the August 2026 edition, oldest first. Every entry
# was read on the source page on 2026-10-04. Wording stays close to the
# source; anything the source does not say is left out.
CHANGES = [
    Change(
        "2026-08-25",
        "Memory works across chat and Cowork",
        "Memory now carries between chat and Cowork in the cloud. You can edit "
        "or delete Topics in Settings > Memory. On by default for Free, Pro and "
        "Max; off by default for Team and Enterprise.",
        "https://support.claude.com/en/articles/12138966-release-notes",
        ("level-2.html", "beginner.html"),
        "2026-10-04",
    ),
    Change(
        "2026-08-26",
        "Claude in Chrome is generally available",
        "On every paid plan. Chrome only: no other Chromium browsers, no mobile. "
        "Claude now approves actions it judges safe on its own, using the same "
        "mechanism as auto mode in Claude Code; you can switch back to manual "
        "approval in settings. A classifier checks each action against what you "
        "asked for and blocks mismatches.",
        "https://claude.com/blog/claude-in-chrome-generally-available",
        ("level-2.html", "claude-everywhere.html", "beginner.html", "prompting.html"),
        "2026-10-05",
    ),
    Change(
        "2026-08-26",
        "The desktop app has its own browser",
        "A browser opens in the side panel when a task needs a website. It is "
        "Claude's browser, separate from yours; you bring logins over site by "
        "site, and banking, email and single sign-on sites are excluded unless "
        "you include them. Pro, Max and Team. If you already use Claude in "
        "Chrome, that stays the default.",
        "https://claude.com/blog/cowork-built-in-browser",
        ("level-2.html", "claude-everywhere.html"),
        "2026-10-05",
    ),
    Change(
        "2026-09-01",
        "Claude Fable 5.1",
        "Replaces Fable 5 as the most capable model. Anthropic's model page "
        "dates it September 2026; the app release notes say September 1.",
        "https://www.anthropic.com/claude-fable-and-mythos-5-1",
        ("beginner.html", "prompting.html"),
        "2026-10-04",
    ),
    Change(
        "2026-09-15",
        "Claude for Small Business adds 43 workflows",
        "The plugin now ships 43 workflows and 27 new integrations, including "
        "Monday Brief, Speed to Lead, Proposal Builder, Social Content Engine "
        "and Close the Month. Every workflow starts in approval mode. Available "
        "on every paid plan.",
        "https://claude.com/blog/claude-for-small-business-launches-new-workflows-integrations-and-training-programs",
        ("workflows.html",),
        "2026-10-05",
    ),
    Change(
        "2026-09-16",
        "Cowork and chat are one Claude",
        "You no longer choose between Chat and Cowork before starting; what "
        "Cowork could do is available from any conversation. Local folders, the "
        "built-in browser and computer use still need Claude Desktop. The "
        "permission setting in the message box is Manual (the default, asks "
        "before each action) or Auto. Cowork's Global instructions are now "
        "Instructions for Claude in Settings > General. Existing tasks, "
        "projects, connectors and skills carry over. Rolling out to Pro and "
        "Max first; Team and Free follow; Enterprise gets 30 days' notice. "
        "Claude Docs and Claude Slides launched in beta on paid plans, and "
        "Claude Design works inside any conversation.",
        "https://claude.com/blog/cowork-is-now-claude",
        ("beginner.html", "level-2.html", "claude-everywhere.html", "claude-code-2.html",
         "claude-design.html", "claude-office.html", "claude-writing.html",
         "prompting.html", "workflows.html", "index.html", "people.html",
         "follow-up-tracker.html", "linkedin-audience-simulator.html",
         "linkedin-content-engine.html", "linkedin-feed-tracker.html"),
        "2026-10-04",
    ),
    Change(
        "2026-09-22",
        "Claude Opus 5.5",
        "Replaces Opus 5. Anthropic says it performs at the level of Fable 5.1 "
        "on most work at a lower price than Opus 5. Five-hour usage limits went "
        "up on Pro, Max and Team.",
        "https://www.anthropic.com/claude-opus-5-5",
        ("beginner.html", "claude-design.html", "prompting.html"),
        "2026-10-04",
    ),
    Change(
        "2026-09-23",
        "Claude Marketplace",
        "One place to find plugins and connectors (more than 2,000), "
        "Claude-powered products from partners, and service partners.",
        "https://claude.com/blog/claude-marketplace",
        ("beginner.html", "level-2.html", "claude-plugins.html"),
        "2026-10-04",
    ),
    Change(
        "2026-09-25",
        "Plugin directory submission portal",
        "Developers on paid plans can submit a plugin (a GitHub repo of skills, "
        "connectors or both) to the Claude directory. Each submission is "
        "validated and safety-scanned, then reviewed. Published plugins get "
        "install and search analytics.",
        "https://claude.com/blog/build-plugins-for-claude",
        ("level-2.html", "claude-plugins.html"),
        "2026-10-04",
    ),
    Change(
        "2026-09-28",
        "Claude Sonnet 5.5",
        "Replaces Sonnet 5 as the faster, lower-cost complement to Opus 5.5. "
        "Anthropic positions it for well-scoped everyday tasks and polished "
        "documents, with Opus 5.5 stronger on complex, open-ended work.",
        "https://www.anthropic.com/claude-sonnet-5-5",
        ("beginner.html",),
        "2026-10-04",
    ),
    Change(
        "2026-09-28",
        "Claude Code starts in auto mode",
        "From version 2.1.283, interactive terminal and VS Code sessions start "
        "in auto mode, where a classifier reviews each action instead of you. "
        "Plan Mode is still there; it is no longer where a new session begins. "
        "Pick it from the mode indicator, or start a message with /plan.",
        "https://code.claude.com/docs/en/permission-modes",
        ("claude-code-2.html", "prompting.html"),
        "2026-10-05",
    ),
    Change(
        "2026-10-01",
        "Claude Code mods",
        "Small TypeScript functions, shipped inside plugins, that change how "
        "Claude Code works. Anthropic says they run with the same access to "
        "your machine as Claude Code itself, are not sandboxed, and should be "
        "installed only from sources you trust.",
        "https://claude.com/blog/claude-code-mods",
        ("claude-code-2.html", "claude-plugins.html"),
        "2026-10-05",
    ),
]
