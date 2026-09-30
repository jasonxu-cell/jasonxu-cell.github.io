#!/usr/bin/env python3
"""Keep the shared navigation, footer, and document metadata in sync."""

from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://jasonxu-cell.github.io/"
OG_IMAGE = {
    "url": f"{SITE_URL}assets/og-image-yang.png",
    "width": "1731",
    "height": "909",
    "alt": "Yang — Geophysics · USTC",
}

DESCRIPTIONS = {
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
    "research.html": (
        "Research projects by Yang in seismology, earthquake mechanics, planetary "
        "science, and data-driven geophysics."
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
    "research/gofar-transform-fault.html": (
        "Yang's research on earthquake mechanics and focal-mechanism variation at "
        "the Gofar transform fault."
    ),
    "research/lunar-water-content.html": (
        "Yang's interdisciplinary study of lunar water using spectral, neutron, and "
        "thermal remote-sensing observations."
    ),
    "notes/cs/computer_organization_and_design.html": (
        "计算机组成与设计课程笔记，涵盖指令系统、处理器、存储层次结构与计算机体系结构。"
    ),
    "notes/electronic_engineering/electronic_technology.html": (
        "电子技术课程笔记，整理电路、半导体器件、模拟电子技术与数字电子技术基础。"
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
    "notes/cs/computer_organization_and_design.html",
    "notes/electronic_engineering/electronic_technology.html",
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
        "Research" if relative.startswith("research") else
        "Ask" if relative == "ask.html" else ""
    )

    nav_match = re.search(r"<nav\b[^>]*>[\s\S]*?</nav>", source, flags=re.IGNORECASE)
    if not nav_match:
        return source

    nav = nav_match.group(0)
    if 'class="nav-links"' in nav and not re.search(r'<a\b[^>]*href="(?:\.\./)*ask\.html"', nav):
        nav = re.sub(
            r'(\s*</div>)',
            f'\n            <a href="{prefix}ask.html">Ask</a>' + r'\1',
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
        if title.endswith(" | Research"):
            title = f"{title} | Yang"
        elif re.search(r"\s+\|\s+Yang\s*$", title):
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
        "article" if relative.startswith(("articles/", "notes/", "research/")) else
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


def update_file(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    source = path.read_text(encoding="utf-8")
    updated = update_head(source, relative)
    updated = replace_navigation(updated, relative)
    updated = update_shell(updated, relative)
    updated = update_images(updated, relative)
    if updated == source:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def is_managed_page(path: Path) -> bool:
    """Skip macOS AppleDouble files and the note pages generated by
    sync_obsidian_notes.py (notes/<subject>/*.html), whose head and footer
    come from that script's template and would be reverted on the next sync."""
    relative = path.relative_to(ROOT).as_posix()
    if path.name.startswith("._"):
        return False
    return not (relative.startswith("notes/") and relative.count("/") == 2)


def main() -> None:
    changed = [
        path for path in sorted(ROOT.rglob("*.html"))
        if is_managed_page(path) and update_file(path)
    ]
    print(f"Updated {len(changed)} HTML files")


if __name__ == "__main__":
    main()
