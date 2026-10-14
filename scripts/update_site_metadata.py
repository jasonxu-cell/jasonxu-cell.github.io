#!/usr/bin/env python3
"""Keep the shared navigation, footer, and document metadata in sync.

Run after editing any page:

    python3 scripts/update_site_metadata.py

It updates every HTML page (including the note pages written by
sync_obsidian_notes.py, which applies the same rules when it generates them):
head metadata, primary navigation, skip link, footer, lazy images,
content-hash ``?v=`` versions for shared CSS/JS, and static pre-rendering of
Markdown pages (needs Node.js). It also dates every <time> from content changes
(files differing from HEAD get today's date; build churn is ignored), and
regenerates ``sitemap.xml`` and the homepage "Recently Updated" list from them.
"""

from __future__ import annotations

import html
import json
import posixpath
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_assets import apply_asset_versions  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://jasonxu-cell.github.io/"
OG_IMAGE = {
    "url": f"{SITE_URL}assets/og-image-yang.png",
    "width": "1731",
    "height": "909",
    "alt": "Yang — Geophysics · USTC",
}

DESCRIPTIONS = {
    "projects.html": (
        "Software projects by Yang, including Mathematics Notebook, an open-source "
        "Wolfram Language compatible notebook for macOS and Linux, powered by Mathics3."
    ),
    "interactive.html": "Interactive math and science experiments by Yang. Explore abstract ideas through hands-on visual demonstrations.",
    "interactive/archimedes.html": "Vary the number of polygon sides from 3 to 1000 and watch inscribed and circumscribed perimeters squeeze toward π from below and above.",
    "index.html": (
        "Yang is a geophysics undergraduate at USTC interested in seismology, "
        "earthquake mechanics, planetary science, and data-driven geophysics."
    ),
    "notes.html": (
        "Study notes by Yang on mathematics, physics, computer science, geoscience, "
        "and electronic engineering."
    ),
    "notes/math.html": (
        "Mathematics notes by Yang on analysis, algebra, geometry, numerical methods, "
        "probability, topology, and differential equations."
    ),
    "notes/physics.html": (
        "Physics notes by Yang on mechanics, electromagnetism, optics, thermodynamics, "
        "statistical physics, and quantum physics."
    ),
    "notes/cs.html": (
        "Computer science notes by Yang on algorithms, artificial intelligence, computer "
        "systems, networks, operating systems, and parallel computing."
    ),
    "notes/geoscience.html": (
        "Geoscience notes by Yang on seismology, geology, astronomy, gravity, geomagnetism, "
        "and geoelectricity."
    ),
    "notes/electronic_engineering.html": (
        "Electronic engineering notes by Yang on signals and systems, circuits, "
        "semiconductors, and electronic technology."
    ),
    "articles.html": (
        "Essays by Yang on space technology, mathematics, computing, and the history "
        "of science and technology."
    ),
    "ask.html": (
        "Ask Yang anything, anonymously: questions about geophysics, studying at "
        "USTC, notes, or anything else. Selected answers are published here."
    ),
    "articles/article_1.html": (
        "评估中国航天技术的发展现状、与世界领先水平的差距，以及面对国际技术限制时的应对策略。"
    ),
    "articles/article_2.html": (
        "解析并评论2026年新高考一卷、二卷数学压轴题的思路、方法与命题特点。"
    ),
    "articles/article_3.html": (
        "A concise history of programming languages, their major lineages, milestones, "
        "and programming paradigms."
    ),
    "notes/cs/computer_organization_and_design.html": (
        "Computer organization and design notes by Yang on instruction set architecture, "
        "CPU design, memory systems, bus systems, and I/O systems."
    ),
    "notes/electronic_engineering/analog_circuits.html": (
        "Analog circuits notes by Yang on semiconductor devices, diodes, MOSFETs, "
        "and bipolar junction transistors."
    ),
    "notes/electronic_engineering/digital_circuits.html": (
        "Digital circuits notes by Yang on Boolean algebra, binary coding, "
        "logic gates, and combinational logic circuits."
    ),
    "notes/cs/Parallel_Computing.html": "Planned study notes on parallel computing by Yang.",
    "notes/cs/operating_system.html": "Planned study notes on operating systems by Yang.",
    "notes/math/functional-analysis.html": "Planned study notes on functional analysis by Yang.",
    "notes/math/geometry.html": "Planned study notes on geometry by Yang.",
    "notes/math/topology.html": "Planned study notes on topology by Yang.",
}

ZH_CN_PAGES = {
    "articles/article_1.html",
    "articles/article_2.html",
}

# Pages that exist in the repo but are not part of the public site.
UNLISTED_PAGES = {
    "404.html",
    "publications.html",
    "reading.html",
}

NOINDEX_PAGES = {
    "notes/cs/Parallel_Computing.html",
    "notes/cs/operating_system.html",
    "notes/math/functional-analysis.html",
    "notes/math/geometry.html",
    "notes/math/topology.html",
}


def extract(pattern: str, source: str, default: str = "") -> str:
    match = re.search(pattern, source, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return default
    return html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()


def page_description(relative: str, title: str) -> str:
    if relative in DESCRIPTIONS:
        return DESCRIPTIONS[relative]

    subject = title.split(" | ", 1)[0].strip()
    if relative.startswith("notes/") and relative.count("/") == 1:
        return f"Course notes and topic guides by Yang in {subject.lower()}."
    if relative.startswith("notes/"):
        return f"Study notes by Yang on {subject}, with explanations, derivations, and examples."
    return f"{subject} by Yang."


def replace_navigation(source: str, relative: str) -> str:
    prefix = "../" * (len(Path(relative).parts) - 1)
    section = (
        "Home" if relative == "index.html" else
        "Notes" if relative.startswith("notes") else
        "Articles" if relative.startswith("articles") else
        "Projects" if relative == "projects.html" or relative.startswith("projects/") else
        "Interactive" if relative == "interactive.html" or relative.startswith("interactive/") else
        "Ask" if relative == "ask.html" else ""
    )

    nav_match = re.search(r"<nav\b[^>]*>[\s\S]*?</nav>", source, flags=re.IGNORECASE)
    if not nav_match:
        return source

    nav = nav_match.group(0)
    # The Research section was removed from the site.
    nav = re.sub(r'\s*<a\b[^>]*href="(?:\.\./)*research\.html"[^>]*>[^<]*</a>', "", nav)
    if 'class="nav-links"' in nav and not re.search(r'<a\b[^>]*href="(?:\.\./)*ask\.html"', nav):
        nav = re.sub(
            r'(\s*</div>)',
            f'\n            <a href="{prefix}ask.html">Ask</a>' + r'\1',
            nav,
            count=1,
        )
    if 'class="nav-links"' in nav and not re.search(r'<a\b[^>]*href="(?:\.\./)*interactive\.html"', nav):
        nav = re.sub(
            r'(\s*<a\b[^>]*href="(?:\.\./)*ask\.html")',
            f'\n            <a href="{prefix}interactive.html">Interactive</a>' + r'\1',
            nav,
            count=1,
        )
    if 'class="nav-links"' in nav and not re.search(r'<a\b[^>]*href="(?:\.\./)*projects\.html"', nav):
        nav = re.sub(
            r'(\s*<a\b[^>]*href="(?:\.\./)*interactive\.html")',
            f'\n            <a href="{prefix}projects.html">Projects</a>' + r'\1',
            nav,
            count=1,
        )
    nav = re.sub(
        r"<nav(?![^>]*aria-label)([^>]*)>",
        r'<nav\1 aria-label="Primary navigation">',
        nav,
        count=1,
        flags=re.IGNORECASE,
    )
    nav = re.sub(r'\s+aria-current="page"', "", nav)
    if section:
        nav = re.sub(
            rf'(<a\s+href="[^"]*"[^>]*)(>{re.escape(section)}</a>)',
            r'\1 aria-current="page"\2',
            nav,
            count=1,
            flags=re.IGNORECASE,
        )
    return source[: nav_match.start()] + nav + source[nav_match.end() :]


def update_head(source: str, relative: str) -> str:
    title = extract(r"<title>([\s\S]*?)</title>", source, "Yang").strip()
    if relative != "index.html":
        if re.search(r"\s+\|\s+Yang\s*$", title):
            title = re.sub(r"\s+\|\s+Yang\s*$", " | Yang", title)
        elif not title.endswith(" | Yang"):
            title = f"{title} | Yang"
    source = re.sub(
        r"<title>[\s\S]*?</title>",
        f"<title>{html.escape(title)}</title>",
        source,
        count=1,
        flags=re.IGNORECASE,
    )
    description = DESCRIPTIONS.get(relative) or extract(
        r'<meta\s+name="description"\s+content="([^"]*)"\s*/?>', source
    )
    description = description or page_description(relative, title)
    page_type = (
        "article" if relative.startswith(("articles/", "notes/")) else
        "website"
    )
    locale = "zh_CN" if relative in ZH_CN_PAGES else "en_US"

    source = re.sub(
        r'<html\s+lang="[^"]+">',
        f'<html lang="{"zh-CN" if relative in ZH_CN_PAGES else "en"}">',
        source,
        count=1,
        flags=re.IGNORECASE,
    )

    for pattern in (
        r'\s*<meta\s+name="description"[^>]*>',
        r'\s*<meta\s+name="robots"[^>]*>',
        r'\s*<meta\s+property="og:(?:title|description|type|site_name|locale|url|image(?::\w+)?)"[^>]*>',
        r'\s*<meta\s+name="twitter:(?:card|title|description|image(?::\w+)?)"[^>]*>',
    ):
        source = re.sub(pattern, "", source, flags=re.IGNORECASE)

    escaped_title = html.escape(title, quote=True)
    escaped_description = html.escape(description, quote=True)
    robots = '\n    <meta name="robots" content="noindex,follow">' if relative in NOINDEX_PAGES else ""
    page_url = SITE_URL if relative == "index.html" else f"{SITE_URL}{relative}"
    image_alt = html.escape(OG_IMAGE["alt"], quote=True)
    metadata = (
        f'\n    <meta name="description" content="{escaped_description}">'
        f'{robots}'
        f'\n    <meta property="og:title" content="{escaped_title}">'
        f'\n    <meta property="og:description" content="{escaped_description}">'
        f'\n    <meta property="og:type" content="{page_type}">'
        f'\n    <meta property="og:site_name" content="Yang">'
        f'\n    <meta property="og:locale" content="{locale}">'
        f'\n    <meta property="og:url" content="{page_url}">'
        f'\n    <meta property="og:image" content="{OG_IMAGE["url"]}">'
        f'\n    <meta property="og:image:width" content="{OG_IMAGE["width"]}">'
        f'\n    <meta property="og:image:height" content="{OG_IMAGE["height"]}">'
        f'\n    <meta property="og:image:alt" content="{image_alt}">'
        f'\n    <meta name="twitter:card" content="summary_large_image">'
        f'\n    <meta name="twitter:title" content="{escaped_title}">'
        f'\n    <meta name="twitter:description" content="{escaped_description}">'
        f'\n    <meta name="twitter:image" content="{OG_IMAGE["url"]}">'
        f'\n    <meta name="twitter:image:alt" content="{image_alt}">'
    )
    source = re.sub(
        r'(<meta\s+name="viewport"[^>]*>)',
        r"\1" + metadata,
        source,
        count=1,
        flags=re.IGNORECASE,
    )
    return source


def update_images(source: str, relative: str) -> str:
    def add_loading(match: re.Match[str]) -> str:
        tag = match.group(0)
        if re.search(r"\bloading=", tag, flags=re.IGNORECASE):
            return tag
        if relative == "index.html" and "profile-photo" in tag:
            return tag
        closing = " />" if tag.endswith(" />") else ">"
        body = tag[: -len(closing)].rstrip()
        return f'{body} loading="lazy" decoding="async"{closing}'

    source = re.sub(r"<img\b[^>]*>", add_loading, source, flags=re.IGNORECASE)
    source = re.sub(
        r'(<a\b[^>]*target="_blank"(?![^>]*\brel=)[^>]*)(>)',
        r'\1 rel="noopener noreferrer"\2',
        source,
        flags=re.IGNORECASE,
    )
    return source


def update_shell(source: str, relative: str) -> str:
    prefix = "../" * (len(Path(relative).parts) - 1)
    source = re.sub(
        r"<main(?![^>]*\bid=)([^>]*)>",
        r'<main id="main-content"\1>',
        source,
        count=1,
        flags=re.IGNORECASE,
    )
    if "class=\"skip-link\"" not in source:
        source = re.sub(
            r"(<body[^>]*>)",
            r'\1\n    <a class="skip-link" href="#main-content">Skip to main content</a>',
            source,
            count=1,
            flags=re.IGNORECASE,
        )

    if "class=\"site-footer\"" not in source:
        footer = f'''\n\n    <footer class="site-footer">
        <p>© 2026 Yang</p>
        <nav class="footer-links footer-contact-icons" aria-label="Contact links">
            <a
                href="mailto:xu_ustc@mail.ustc.edu.cn"
                class="footer-contact-icon"
                aria-label="Email Yang"
                title="Email"
            >
                <svg class="footer-icon" viewBox="0 0 16 16" width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false"><path d="M.05 3.555A2 2 0 0 1 2 2h12a2 2 0 0 1 1.95 1.555L8 8.414zM0 4.697v7.104l5.803-3.558zM6.761 8.83l-6.57 4.027A2 2 0 0 0 2 14h12a2 2 0 0 0 1.808-1.144l-6.57-4.027L8 9.586zm3.436-.586L16 11.801V4.697z"/></svg>
            </a>
            <a
                href="https://github.com/jasonxu-cell"
                target="_blank"
                rel="noopener noreferrer"
                class="footer-contact-icon"
                aria-label="Yang on GitHub"
                title="GitHub"
            >
                <svg class="footer-icon" viewBox="0 0 16 16" width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8"/></svg>
            </a>
            <a
                href="https://orcid.org/0009-0004-5519-0849"
                target="_blank"
                rel="noopener noreferrer"
                class="footer-contact-icon"
                aria-label="ORCID"
                title="ORCID"
            >
                <svg class="footer-icon" viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false"><path d="M12 0C5.372 0 0 5.372 0 12s5.372 12 12 12 12-5.372 12-12S18.628 0 12 0zM7.369 4.378c.525 0 .947.431.947.947s-.422.947-.947.947a.95.95 0 0 1-.947-.947c0-.525.422-.947.947-.947zm-.722 3.038h1.444v10.041H6.647V7.416zm3.562 0h3.9c3.712 0 5.344 2.653 5.344 5.025 0 2.578-2.016 5.025-5.325 5.025h-3.919V7.416zm1.444 1.303v7.444h2.297c3.272 0 4.022-2.484 4.022-3.722 0-2.016-1.284-3.722-4.097-3.722h-2.222z"/></svg>
            </a>
            <a
                href="https://steamcommunity.com/profiles/76561199724275684/"
                target="_blank"
                rel="noopener noreferrer"
                class="footer-contact-icon"
                aria-label="Steam"
                title="Steam"
            >
                <svg class="footer-icon" viewBox="0 0 16 16" width="1em" height="1em" fill="currentColor" aria-hidden="true" focusable="false"><path d="M.329 10.333A8.01 8.01 0 0 0 7.99 16C12.414 16 16 12.418 16 8s-3.586-8-8.009-8A8.006 8.006 0 0 0 0 7.468l.003.006 4.304 1.769A2.2 2.2 0 0 1 5.62 8.88l1.96-2.844-.001-.04a3.046 3.046 0 0 1 3.042-3.043 3.046 3.046 0 0 1 3.042 3.043 3.047 3.047 0 0 1-3.111 3.044l-2.804 2a2.223 2.223 0 0 1-3.075 2.11 2.22 2.22 0 0 1-1.312-1.568L.33 10.333Z"/><path d="M4.868 12.683a1.715 1.715 0 0 0 1.318-3.165 1.7 1.7 0 0 0-1.263-.02l1.023.424a1.261 1.261 0 1 1-.97 2.33l-.99-.41a1.7 1.7 0 0 0 .882.84Zm3.726-6.687a2.03 2.03 0 0 0 2.027 2.029 2.03 2.03 0 0 0 2.027-2.029 2.03 2.03 0 0 0-2.027-2.027 2.03 2.03 0 0 0-2.027 2.027m2.03-1.527a1.524 1.524 0 1 1-.002 3.048 1.524 1.524 0 0 1 .002-3.048"/></svg>
            </a>
        </nav>
    </footer>'''
        source = source.replace("</main>", "</main>" + footer, 1)
    return source


def transform(source: str, relative: str) -> str:
    if relative == "404.html":
        # Served at any depth by GitHub Pages, so it keeps its own root-relative
        # head and navigation; only the asset versions are managed.
        return apply_asset_versions(source, ROOT)
    updated = update_head(source, relative)
    updated = replace_navigation(updated, relative)
    updated = update_shell(updated, relative)
    updated = update_images(updated, relative)
    # The live region made screen readers announce the whole article when it
    # was injected by JavaScript; the content is now static HTML.
    updated = re.sub(r'(<article class="markdown-body" id="markdown-body")\s+aria-live="polite"', r"\1", updated)
    return apply_asset_versions(updated, ROOT)


PRERENDER_SCRIPT = Path(__file__).resolve().parent / "prerender_markdown.js"


def prerender(pages: list[str]) -> list[str]:
    node = shutil.which("node")
    if not node or not pages:
        if pages:
            print("warning: Node.js not found; Markdown pages were not pre-rendered.", file=sys.stderr)
        return pages
    completed = subprocess.run(
        [node, str(PRERENDER_SCRIPT), "--stdin-json"],
        input=json.dumps(pages).encode("utf-8"),
        stdout=subprocess.PIPE,
        check=True,
    )
    return json.loads(completed.stdout.decode("utf-8"))


def page_lastmod(source: str) -> str:
    """Date for <lastmod>: the newest <time datetime> on the page, if any.

    Detail pages carry one date; listing pages carry one per entry, so the
    newest entry is when the listing last changed."""
    dates = re.findall(r'<time\b[^>]*datetime="(\d{4}-\d{2}-\d{2})', source)
    return max(dates) if dates else ""


RECENT_UPDATES_LIMIT = 5
RECENT_UPDATES_BEGIN = "<!-- recent-updates:begin -->"
RECENT_UPDATES_END = "<!-- recent-updates:end -->"

RECENT_KIND_LABELS = {
    "math": "Math",
    "physics": "Physics",
    "cs": "CS",
    "geoscience": "Geoscience",
    "electronic_engineering": "Electronic Engineering",
}


def recent_updates(pages: list[tuple[str, str]]) -> list[tuple[str, str, str, str]]:
    """Newest content pages (articles, notes, interactive) by their <time> date."""
    items = []
    for relative, source in pages:
        if relative in UNLISTED_PAGES or relative in NOINDEX_PAGES:
            continue
        if relative.startswith("articles/") and relative.count("/") == 1:
            kind = "Article"
        elif relative.startswith("notes/") and relative.count("/") == 2:
            subject = relative.split("/")[1]
            kind = RECENT_KIND_LABELS.get(subject, subject.replace("_", " ").title())
        elif relative.startswith("interactive/") and relative.count("/") == 1:
            kind = "Interactive"
        else:
            continue
        date = page_lastmod(source)
        if not date:
            continue
        title = re.sub(
            r"\s*\|\s*Yang\s*$", "",
            extract(r"<title>([\s\S]*?)</title>", source, relative),
        )
        items.append((date, title, relative, kind))
    items.sort(key=lambda item: (item[0], item[2]), reverse=True)
    return items[:RECENT_UPDATES_LIMIT]


def recent_updates_block(items: list[tuple[str, str, str, str]]) -> str:
    rows = "\n".join(
        "                        <li>\n"
        f'                            <a href="{relative}">{html.escape(title)}</a>\n'
        f'                            <span class="recent-updates-kind">{kind}</span>\n'
        f'                            <time datetime="{date}">{date}</time>\n'
        "                        </li>"
        for date, title, relative, kind in items
    )
    return (
        f"{RECENT_UPDATES_BEGIN}\n"
        '                <section class="recent-updates" aria-labelledby="recent-updates-title">\n'
        '                    <p class="recent-updates-title" id="recent-updates-title">Recently Updated</p>\n'
        '                    <ol class="recent-updates-list">\n'
        f"{rows}\n"
        "                    </ol>\n"
        "                </section>\n"
        f"                {RECENT_UPDATES_END}"
    )


def inject_recent_updates(source: str, items: list[tuple[str, str, str, str]]) -> str:
    """Rewrite the marked homepage block; leave the page alone if it's gone."""
    pattern = re.escape(RECENT_UPDATES_BEGIN) + r"[\s\S]*?" + re.escape(RECENT_UPDATES_END)
    if not re.search(pattern, source):
        return source
    return re.sub(pattern, lambda _: recent_updates_block(items), source, count=1)


MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

TIME_RE = re.compile(r"<time\b[^>]*>[^<]*</time>", flags=re.IGNORECASE)
CARD_RE = re.compile(r'<a\b[^>]*href="([^"#]+\.html)[^"]*"[^>]*>[\s\S]*?</a>', flags=re.IGNORECASE)


def display_date(iso: str) -> str:
    year, month, day = iso.split("-")
    return f"{MONTH_ABBR[int(month) - 1]} {int(day)}, {year}"


def retime(tag: str, iso: str) -> str:
    """Rewrite a <time> tag, keeping its display style (ISO vs. 'Mon D, YYYY')."""
    if 'datetime="' in tag:
        tag = re.sub(r'datetime="[^"]*"', f'datetime="{iso}"', tag, count=1)
    else:
        tag = re.sub(r"<time\b", f'<time datetime="{iso}"', tag, count=1)
    text = iso if re.search(r">\d{4}-\d{2}-\d{2}<", tag) else display_date(iso)
    return re.sub(r">[^<]*</time>$", lambda _: f">{text}</time>", tag)


def resolve_href(relative: str, href: str) -> str:
    if re.match(r"[a-z][a-z0-9+.-]*:", href, flags=re.IGNORECASE):
        return ""  # absolute URL or mailto:
    return posixpath.normpath(posixpath.join(posixpath.dirname(relative), href))


def normalize_page(source: str) -> str:
    """Strip build churn (?v= hashes, <time> values, the script-managed primary
    navigation) so only real edits count."""
    source = re.sub(r"\?v=[0-9a-f]+", "?v=", source)
    source = re.sub(r'<nav\b[^>]*aria-label="Primary navigation"[^>]*>[\s\S]*?</nav>', "<nav></nav>", source)
    return TIME_RE.sub("<time></time>", source)


def head_source(relative: str) -> str:
    try:
        return subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return ""


def content_dates(pages: list[tuple[str, str]]) -> dict[str, str]:
    """Last content-change date per detail page, derived from git.

    A page's date advances to today when its content differs from HEAD (build
    churn like ?v= bumps is normalized away); untouched pages keep the date
    already in the file. Since the script runs right before committing, "today"
    is the upcoming commit date. Without git, every page keeps its date."""
    dirty: set[str] = set()
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", "*.html"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
        for entry in status.splitlines():
            path = entry[3:].split(" -> ")[-1].strip('"')
            if path.endswith(".html"):
                dirty.add(path)
    except (OSError, subprocess.CalledProcessError):
        pass

    today = date.today().isoformat()
    dates: dict[str, str] = {}
    for relative, source in pages:
        if relative in UNLISTED_PAGES or relative in NOINDEX_PAGES:
            continue
        if not (
            relative.startswith("articles/") and relative.count("/") == 1
            or relative.startswith("notes/") and relative.count("/") == 2
            or relative.startswith("interactive/") and relative.count("/") == 1
        ):
            continue
        if relative not in dirty:
            dates[relative] = page_lastmod(source)
            continue
        old = head_source(relative)
        if old and normalize_page(old) == normalize_page(source):
            dates[relative] = page_lastmod(old)
        else:
            dates[relative] = today
    return dates


def update_times(source: str, relative: str, dates: dict[str, str]) -> str:
    """Date every <time>: card entries follow the linked page's date, the rest
    follow the page's own. The generated Recently Updated block is skipped;
    inject_recent_updates() fills it afterwards."""
    assignments = []  # (start, end, iso date)
    card_spans = []
    for card in CARD_RE.finditer(source):
        card_spans.append(card.span())
        target = resolve_href(relative, card.group(1))
        iso = dates.get(target) if target else None
        if not iso:
            continue
        for time in TIME_RE.finditer(card.group(0)):
            assignments.append((card.start() + time.start(), card.start() + time.end(), iso))
    own = dates.get(relative)
    if own:
        recent = re.search(
            re.escape(RECENT_UPDATES_BEGIN) + r"[\s\S]*?" + re.escape(RECENT_UPDATES_END), source
        )
        for time in TIME_RE.finditer(source):
            if any(start <= time.start() < end for start, end in card_spans):
                continue
            if recent and recent.start() <= time.start() < recent.end():
                continue
            assignments.append((time.start(), time.end(), own))
    for start, end, iso in sorted(assignments, reverse=True):
        source = source[:start] + retime(source[start:end], iso) + source[end:]
    return source


def write_sitemap(pages: list[tuple[str, str]]) -> None:
    entries = []
    for relative, source in sorted(pages):
        if relative in UNLISTED_PAGES or relative in NOINDEX_PAGES:
            continue
        loc = SITE_URL if relative == "index.html" else f"{SITE_URL}{relative}"
        lastmod = page_lastmod(source)
        entries.append(
            "  <url>\n"
            f"    <loc>{html.escape(loc, quote=True)}</loc>\n"
            + (f"    <lastmod>{lastmod}</lastmod>\n" if lastmod else "")
            + "  </url>"
        )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    target = ROOT / "sitemap.xml"
    if not target.exists() or target.read_text(encoding="utf-8") != sitemap:
        target.write_text(sitemap, encoding="utf-8")
        print(f"Wrote sitemap.xml ({len(entries)} URLs)")


def is_managed_page(path: Path) -> bool:
    """Skip macOS AppleDouble files and anything outside the published site."""
    relative = path.relative_to(ROOT).as_posix()
    if path.name.startswith("._"):
        return False
    return not relative.startswith((".git/", ".cache/", "scripts/"))


def main() -> None:
    paths = [path for path in sorted(ROOT.rglob("*.html")) if is_managed_page(path)]
    originals = [path.read_text(encoding="utf-8") for path in paths]
    updated = [transform(source, path.relative_to(ROOT).as_posix()) for path, source in zip(paths, originals)]

    markdown_indexes = [i for i, page in enumerate(updated) if 'id="article-markdown"' in page]
    rendered = prerender([updated[i] for i in markdown_indexes])
    for i, page in zip(markdown_indexes, rendered):
        updated[i] = page

    dates = content_dates([(path.relative_to(ROOT).as_posix(), page) for path, page in zip(paths, updated)])
    if dates:
        # The homepage "Last updated" fallback tracks the newest content page.
        dates["index.html"] = max(dates.values())
    updated = [
        update_times(page, path.relative_to(ROOT).as_posix(), dates) if dates else page
        for path, page in zip(paths, updated)
    ]

    recent = recent_updates([(path.relative_to(ROOT).as_posix(), page) for path, page in zip(paths, updated)])
    for i, path in enumerate(paths):
        if path.relative_to(ROOT).as_posix() == "index.html":
            updated[i] = inject_recent_updates(updated[i], recent)

    changed = 0
    for path, source, page in zip(paths, originals, updated):
        if page != source:
            path.write_text(page, encoding="utf-8")
            changed += 1
    print(f"Updated {changed} HTML files ({len(markdown_indexes)} Markdown pages pre-rendered)")
    write_sitemap([(path.relative_to(ROOT).as_posix(), page) for path, page in zip(paths, updated)])


if __name__ == "__main__":
    main()
