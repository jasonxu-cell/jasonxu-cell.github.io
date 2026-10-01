#!/usr/bin/env python3
'''Sync selected Obsidian notes into the static my_website notes pages.

Default behavior runs one sync pass. Use --watch to keep the process alive and
resync when mapped Markdown notes or Obsidian Picture attachments change.

Each pass also:
  * optimises embedded images: raster attachments >= 100 KB are published as
    ``<name>-optimized.webp`` (max 2400 px) and the page links the WebP;
    smaller images, GIFs and SVGs are copied unchanged;
  * applies the shared page shell/metadata from update_site_metadata.py
    (description, skip link, nav labels, lang) and content-hash ``?v=`` asset
    versions from site_assets.py;
  * pre-renders the Markdown into static HTML (scripts/prerender_markdown.js,
    needs Node.js) so search engines see the full note text.
'''

from __future__ import annotations

import argparse
import dataclasses
import html
import os
import re
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import quote, unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))

import update_site_metadata  # noqa: E402  (shared <head>/nav/shell for all pages)
from site_assets import apply_asset_versions  # noqa: E402
from site_images import SkipCache, optimize_into  # noqa: E402


@dataclasses.dataclass(frozen=True)
class NoteTarget:
    subject: str
    subject_title: str
    title: str
    filename: str
    vault_folder: Optional[str]
    vault_name: str
    aliases: Tuple[str, ...] = ()


NOTE_TARGETS: Tuple[NoteTarget, ...] = (
    NoteTarget("math", "Mathematics", "Mathematical Analysis", "mathematical-analysis.html", "Mathematics", "Mathematical Analysis.md", ("Real Analysis",)),
    NoteTarget("math", "Mathematics", "Complex Analysis", "complex-analysis.html", "Mathematics", "Complex Analysis.md"),
    NoteTarget("math", "Mathematics", "Equations of Mathematical Physics", "equations-of-mathematical-physics.html", "Mathematics", "Equations of Mathematical Physics.md"),
    NoteTarget("math", "Mathematics", "Algebra", "algebra.html", "Mathematics", "Algebra.md"),
    NoteTarget("math", "Mathematics", "Number Theory", "number-theory.html", "Mathematics", "Number Theory.md", ("Algebra & Number Theory", "Algebra and Number Theory")),
    NoteTarget("math", "Mathematics", "Functional Analysis", "functional-analysis.html", "Mathematics", "Functional Analysis.md"),
    NoteTarget("math", "Mathematics", "Geometry", "geometry.html", "Mathematics", "Geometry.md"),
    NoteTarget("math", "Mathematics", "Probability and Statistics", "probability-and-statistics.html", "Mathematics", "Probability & Statistics.md", ("Probability & Statistics",)),
    NoteTarget("math", "Mathematics", "Topology", "topology.html", "Mathematics", "Topology.md"),
    NoteTarget("math", "Mathematics", "Numerical Analysis", "numerical_analysis.html", "Mathematics", "Numerical Analysis.md", ("Computational Method",)),
    NoteTarget("physics", "Physics", "Mechanism", "mechanism.html", "Physics", "Mechanics.md", ("Mechanics",)),
    NoteTarget("physics", "Physics", "Electromagnetism", "electromagnetism.html", "Physics", "Electromagnetism.md"),
    NoteTarget("physics", "Physics", "Thermodynamics and Statistical Physics", "thermodynamics-and-statistical-physics.html", "Physics", "Thermodynamics and Statistical Physics.md"),
    NoteTarget("physics", "Physics", "Optics", "optics.html", "Physics", "Optics.md"),
    NoteTarget("physics", "Physics", "Quantum Physics", "quantum-physics.html", "Physics", "Quantum Mechanics.md", ("Quantum Mechanics",)),
    NoteTarget("electronic_engineering", "Electronic Technology", "Signals and Systems", "signals_and_systems.html", "Electronic Engineering", "Signals & Systems.md", ("Signal & System", "Signals & Systems")),
    NoteTarget("electronic_engineering", "Electronic Technology", "Analog Circuits", "analog_circuits.html", "Electronic Engineering", "Analog Circuits.md"),
    NoteTarget("electronic_engineering", "Electronic Technology", "Digital Circuits", "digital_circuits.html", "Electronic Engineering", "Digital Circuits.md"),
    NoteTarget("cs", "Computer Science", "Data Structure and Algorithm", "data_structure_and_algorithm.html", "Computer Science", "Data Structure & Algorithm.md", ("Data Structure & Algorithm",)),
    NoteTarget("cs", "Computer Science", "Computer Organization and Design", "computer_organization_and_design.html", "Computer Science", "Computer Organization & Design.md", ("Computer Organization & Design",)),
    NoteTarget("cs", "Computer Science", "Operating System", "operating_system.html", "Computer Science", "Operating System.md"),
    NoteTarget("cs", "Computer Science", "Computer Network", "computer_network.html", "Computer Science", "Computer Network.md"),
    NoteTarget("cs", "Computer Science", "Artificial Intelligence", "artificial_intelligence.html", "Computer Science", "Artificial Intelligence.md"),
    NoteTarget("cs", "Computer Science", "Parallel Computing", "Parallel_Computing.html", "Computer Science", "Parallel Computing.md"),
    NoteTarget("geoscience", "Geoscience", "Astronomy", "astronomy.html", "Geophysics", "Astronomy.md"),
    NoteTarget("geoscience", "Geoscience", "Geology", "geology.html", "Geophysics", "Geology.md"),
    NoteTarget("geoscience", "Geoscience", "Geomagnetism and Geoelectricity", "geomagnetism_and_geoelectricity.html", "Geophysics", "Geomagnetism & Geoelectricity.md", ("Geomagnetism & Geoelectricity",)),
    NoteTarget("geoscience", "Geoscience", "Seismology", "seismology.html", "Geophysics", "Seismology.md"),
    NoteTarget("geoscience", "Geoscience", "The Gravity and The Tide of Earth", "The_Gravity_and_The_Tide_of_Earth.html", "Geophysics", "The Gravity & the Tide of Earth.md", ("The Gravity & the Tide of Earth",)),
)

SUBJECT_LABELS = {
    "math": "Mathematics",
    "physics": "Physics",
    "electronic_engineering": "Electronic Technology",
    "cs": "Computer Science",
    "geoscience": "Geoscience",
}

SUBJECT_PAGES = {
    "math": Path("notes/math.html"),
    "physics": Path("notes/physics.html"),
    "electronic_engineering": Path("notes/electronic_engineering.html"),
    "cs": Path("notes/cs.html"),
    "geoscience": Path("notes/geoscience.html"),
}

IMAGE_SUFFIXES = {
    ".avif",
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
}

DEFAULT_VAULT = Path(os.environ.get("OBSIDIAN_VAULT", "/Users/xuyang/Documents/Obsidian Vault"))
DEFAULT_ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://jasonxu-cell.github.io/"
OG_IMAGE_URL = f"{SITE_URL}assets/og-image-yang.png"
OG_IMAGE_ALT = "Yang — Geophysics · USTC"


class SyncError(RuntimeError):
    pass


def normalize_key(value: str) -> str:
    cleaned = value.replace("\u200c", "").replace("\u200b", "").replace("\ufeff", "")
    cleaned = cleaned.replace("&", " and ")
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fa5]+", "", cleaned).casefold()


def slugify(value: str) -> str:
    value = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[`*_>#-]", "", value).strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fa5]+", "-", value).strip("-")
    return value or "section"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, value: str, dry_run: bool) -> bool:
    if path.exists() and read_text(path) == value:
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    return True


def find_vault_file(vault: Path, target: NoteTarget) -> Optional[Path]:
    direct = (vault / target.vault_folder / target.vault_name) if target.vault_folder else (vault / target.vault_name)
    if direct.exists():
        return direct

    search_root = (vault / target.vault_folder) if target.vault_folder else vault
    aliases = {normalize_key(target.title), normalize_key(Path(target.vault_name).stem)}
    aliases.update(normalize_key(alias) for alias in target.aliases)

    if not search_root.exists():
        return None

    for candidate in search_root.rglob("*.md"):
        if normalize_key(candidate.stem) in aliases:
            return candidate
    return None


def extract_cards(subject_page: Path) -> Dict[str, Dict[str, object]]:
    text = read_text(subject_page)
    cards: Dict[str, Dict[str, object]] = {}
    card_pattern = re.compile(r'<a href="([^"]+)"\s+class="article-card">([\s\S]*?)</a>')

    for match in card_pattern.finditer(text):
        _href, block = match.groups()
        title_match = re.search(r"<h2>([\s\S]*?)</h2>", block)
        if not title_match:
            continue
        title = html.unescape(re.sub(r"\s+", " ", title_match.group(1)).strip())
        tags = [
            html.unescape(re.sub(r"\s+", " ", tag).strip())
            for tag in re.findall(r"<span>([\s\S]*?)</span>", block)
        ]
        time_match = re.search(r"<time(?: [^>]*)?>([\s\S]*?)</time>", block)
        time_text = html.unescape(re.sub(r"\s+", " ", time_match.group(1)).strip()) if time_match else "Aug 14, 2026"
        cards[title] = {"tags": tags, "time": time_text}
    return cards


def extract_all_cards(root: Path) -> Dict[str, Dict[str, Dict[str, object]]]:
    result: Dict[str, Dict[str, Dict[str, object]]] = {}
    for subject, rel_path in SUBJECT_PAGES.items():
        page = root / rel_path
        result[subject] = extract_cards(page) if page.exists() else {}
    return result


def extract_detail_intro(page: Path) -> Optional[str]:
    if not page.exists():
        return None

    text = read_text(page)
    header_match = re.search(r'<header class="article-detail-header">([\s\S]*?)</header>', text)
    if not header_match:
        return None

    intro_match = re.search(r"<p(?:\s[^>]*)?>[\s\S]*?</p>", header_match.group(1))
    if not intro_match:
        return None

    return intro_match.group(0)


def strip_frontmatter(text: str) -> str:
    return re.sub(r"\A\s*---\s*\n[\s\S]*?\n---\s*\n?", "", text, count=1).strip()


def iter_vault_images(vault: Path) -> Iterable[Path]:
    if not vault.exists():
        return

    for path in vault.rglob("*"):
        relative_parts = path.relative_to(vault).parts
        if any(part.startswith(".") for part in relative_parts):
            continue
        if path.is_file() and path.suffix.casefold() in IMAGE_SUFFIXES:
            yield path


def build_picture_index(vault: Path) -> Dict[str, Path]:
    index: Dict[str, Path] = {}

    # Preserve the original preference for files in Picture/, then fall back to
    # attachments stored elsewhere in the vault (including the vault root).
    picture_dir = vault / "Picture"
    if picture_dir.exists():
        for path in iter_vault_images(picture_dir):
            index.setdefault(path.name, path)

    for path in iter_vault_images(vault):
        index.setdefault(path.name, path)
    return index


def build_link_map(targets: Sequence[NoteTarget], vault_paths: Dict[NoteTarget, Path]) -> Dict[str, NoteTarget]:
    link_map: Dict[str, NoteTarget] = {}
    for target in targets:
        names = {target.title, Path(target.vault_name).stem, *target.aliases}
        vault_path = vault_paths.get(target)
        if vault_path:
            names.add(vault_path.stem)
        for name in names:
            link_map[normalize_key(name)] = target
    return link_map


def relative_note_link(current: NoteTarget, target: NoteTarget, anchor: Optional[str]) -> str:
    if current == target:
        base = ""
    elif current.subject == target.subject:
        base = target.filename
    else:
        base = f"../{target.subject}/{target.filename}"

    if anchor:
        suffix = f"#{slugify(anchor)}"
        return f"{base}{suffix}" if base else suffix
    return base or f"#{slugify(target.title)}"


def convert_wikilinks(text: str, current: NoteTarget, link_map: Dict[str, NoteTarget]) -> str:
    def replace(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        if not body:
            return ""

        if "|" in body:
            target_part, alias = body.split("|", 1)
            alias = alias.strip()
        else:
            target_part, alias = body, None

        if "#" in target_part:
            page_part, anchor = target_part.split("#", 1)
            page_part = page_part.strip()
            anchor = anchor.strip()
        else:
            page_part, anchor = target_part.strip(), None

        label = (alias or anchor or page_part).strip()
        if not label:
            label = page_part or anchor or ""

        if not page_part:
            return f"[{label}](#{slugify(anchor or label)})"

        target = link_map.get(normalize_key(page_part))
        if not target:
            return label

        return f"[{label}]({relative_note_link(current, target, anchor)})"

    return re.sub(r"(?<!!)\[\[([^\]]+)\]\]", replace, text)


class ImagePublisher:
    '''Publishes vault images into notes/attachments and decides which file
    name the page should link.

    Large raster images are published only as ``-optimized.webp``; the
    original is copied as well only when no WebP is used (small files, GIF,
    SVG, or when WebP would not be smaller).'''

    def __init__(self, root: Path, dry_run: bool, optimize: bool = True):
        self.attachments_dir = root / "notes" / "attachments"
        self.dry_run = dry_run
        self.optimize = optimize
        self.skip_cache = SkipCache(root / ".cache" / "image-optimization-skip.json")
        self._resolved: Dict[Path, str] = {}
        self.copied = 0
        self.optimized = 0

    def publish(self, source: Path) -> str:
        if source in self._resolved:
            return self._resolved[source]

        name: Optional[str] = None
        if self.optimize:
            webp = self.attachments_dir / f"{source.stem}-optimized.webp"
            was_fresh = webp.exists() and webp.stat().st_mtime_ns >= source.stat().st_mtime_ns
            name = optimize_into(source, self.attachments_dir, self.skip_cache, dry_run=self.dry_run)
            if name and not was_fresh:
                self.optimized += 1
        if name is None:
            if copy_image(source, self.attachments_dir / source.name, self.dry_run):
                self.copied += 1
            name = source.name

        self._resolved[source] = name
        return name

    @property
    def published(self) -> Set[str]:
        return set(self._resolved.values())

    def finish(self) -> None:
        if not self.dry_run:
            self.skip_cache.save()


def convert_obsidian_images(
    text: str,
    picture_index: Dict[str, Path],
    used_images: Set[Path],
    missing_images: Set[str],
    publisher: Optional[ImagePublisher] = None,
) -> str:
    def published_name(basename: str) -> Optional[str]:
        source = picture_index.get(basename)
        if not source:
            return None
        used_images.add(source)
        return publisher.publish(source) if publisher else basename

    def replace(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        parts = [part.strip() for part in body.split("|")]
        image_name = parts[0]
        width = next((part for part in parts[1:] if re.fullmatch(r"\d+", part)), None)
        basename = Path(image_name).name
        name = published_name(basename)
        if name is None:
            missing_images.add(image_name)
            name = basename

        encoded = quote(name)
        alt = Path(basename).stem
        width_suffix = f"{{width={width}}}" if width else ""
        return f"![{alt}](../attachments/{encoded}){width_suffix}"

    def replace_markdown_image(match: re.Match[str]) -> str:
        # Standard Markdown embeds of local vault files: ![alt](Picture/x.png)
        alt, target, rest = match.group(1), match.group(2), match.group(3) or ""
        if re.match(r"^(?:[a-z][a-z0-9+.-]*:|#|\.\./attachments/)", target, re.I):
            return match.group(0)
        basename = Path(unquote(target)).name
        if Path(basename).suffix.casefold() not in IMAGE_SUFFIXES:
            return match.group(0)
        name = published_name(basename)
        if name is None:
            missing_images.add(unquote(target))
            return match.group(0)
        return f"![{alt}](../attachments/{quote(name)}){rest}"

    text = re.sub(r"!\[\[([^\]]+)\]\]", replace, text)
    return re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)(\{width=\d+\})?", replace_markdown_image, text)


def prepare_markdown(
    target: NoteTarget,
    vault_path: Path,
    picture_index: Dict[str, Path],
    link_map: Dict[str, NoteTarget],
    used_images: Set[Path],
    missing_images: Set[str],
    publisher: Optional[ImagePublisher] = None,
) -> str:
    text = strip_frontmatter(read_text(vault_path))
    text = convert_obsidian_images(text, picture_index, used_images, missing_images, publisher)
    text = convert_wikilinks(text, target, link_map)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def datetime_attr(time_text: str) -> str:
    try:
        return datetime.strptime(time_text, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def html_page(
    target: NoteTarget,
    markdown: str,
    meta: Dict[str, object],
    detail_intro: Optional[str],
) -> str:
    intro_html = detail_intro
    legacy_intro = f"<p>{html.escape(f'Notes from the Obsidian vault on {target.title}.')}</p>"
    if intro_html is None or intro_html == legacy_intro:
        intro_html = f"<p>{html.escape(f'Note about {target.title}.')}</p>"
    tags = list(meta.get("tags") or [target.subject_title])
    time_text = str(meta.get("time") or "Aug 14, 2026")
    datetime_value = datetime_attr(time_text)
    tags_html = "\n".join(f"                    <span>{html.escape(str(tag))}</span>" for tag in tags)
    safe_markdown = markdown.replace("</script", "<\\/script")
    page_title = html.escape(f"{target.title} | Yang", quote=True)
    page_url = f"{SITE_URL}notes/{target.subject}/{quote(target.filename)}"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta property="og:title" content="{page_title}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Yang">
    <meta property="og:url" content="{page_url}">
    <meta property="og:image" content="{OG_IMAGE_URL}">
    <meta property="og:image:width" content="1731">
    <meta property="og:image:height" content="909">
    <meta property="og:image:alt" content="{OG_IMAGE_ALT}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{page_title}">
    <meta name="twitter:image" content="{OG_IMAGE_URL}">
    <meta name="twitter:image:alt" content="{OG_IMAGE_ALT}">
    <title>{html.escape(target.title)} | Yang</title>
    <link rel="stylesheet" href="../../style.css">
    <link rel="icon" type="image/png" sizes="32x32" href="../../assets/favicon-32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../../assets/favicon-16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="../../assets/apple-touch-icon.png">
</head>
<body>
    <a class="skip-link" href="#main-content">Skip to main content</a>
    <nav aria-label="Primary navigation">
        <div class="nav-links">
            <a href="../../index.html">Home</a>
            <a href="../../notes.html" aria-current="page">Notes</a>
            <a href="../../articles.html">Articles</a>
            <a href="../../research.html">Research</a>
            <a href="../../ask.html">Ask</a>
        </div>
    </nav>

    <main id="main-content" class="article-detail-page">
        <header class="article-detail-header">
            <a href="../{target.subject}.html" class="article-back-link">&larr; {html.escape(SUBJECT_LABELS[target.subject])}</a>
            <h1>{html.escape(target.title)}</h1>
            {intro_html}
            <div class="essay-meta article-detail-meta">
                <div class="essay-tags">
{tags_html}
                </div>
                <time{f' datetime="{datetime_value}"' if datetime_value else ''}>{html.escape(time_text)}</time>
            </div>
        </header>

        <div class="article-reader">
            <aside class="article-toc-panel" aria-label="Article contents">
                <p>Contents</p>
                <ol id="article-toc"></ol>
            </aside>

            <article class="markdown-body" id="markdown-body"></article>
        </div>

        <section class="article-comments" aria-labelledby="comments-title">
            <div class="article-comments-header">
                <h2 id="comments-title">Comments</h2>
                <p>Questions, corrections, and reading notes are welcome here.</p>
            </div>
            <div class="article-comments-widget" data-comments-repo="jasonxu-cell/jasonxu-cell.github.io"></div>
            <p class="article-comments-status" hidden>Comments load on the published website.</p>
            <noscript>Enable JavaScript to view comments.</noscript>
        </section>

        <script type="text/plain" id="article-markdown">
{safe_markdown}
        </script>
    </main>

    <footer class="site-footer">
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
    </footer>

    <script src="../../scripts/markdown-article.js"></script>
    <script src="../../scripts/comments.js"></script>
</body>
</html>
'''


def update_subject_links(root: Path, targets: Sequence[NoteTarget], dry_run: bool) -> int:
    changed = 0
    by_subject: Dict[str, List[NoteTarget]] = {}
    for target in targets:
        by_subject.setdefault(target.subject, []).append(target)

    for subject, subject_targets in by_subject.items():
        page = root / SUBJECT_PAGES[subject]
        if not page.exists():
            continue
        text = read_text(page)
        original = text
        for target in subject_targets:
            href = f"{target.subject}/{target.filename}"
            title_pattern = re.escape(target.title)
            pattern = re.compile(
                r'(<a href=")([^"]+)("\s+class="article-card">(?:(?!</a>).)*?<h2>\s*'
                + title_pattern
                + r"\s*</h2>)",
                re.S,
            )
            text, count = pattern.subn(r"\1" + href + r"\3", text, count=1)
            if count == 0:
                raise SyncError(f"Could not update href for {target.title} in {page}")
        if text != original:
            if not dry_run:
                page.write_text(text, encoding="utf-8")
            changed += 1
    return changed


def copy_image(source: Path, dest: Path, dry_run: bool) -> bool:
    source_stat = source.stat()
    if dest.exists():
        dest_stat = dest.stat()
        # exFAT stores modification times at 10 ms precision.
        same_mtime = abs(dest_stat.st_mtime_ns - source_stat.st_mtime_ns) < 10_000_000
        if same_mtime and dest_stat.st_size == source_stat.st_size:
            return False
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        # copy2() also copies macOS file flags. That raises EINVAL when the
        # website is on an exFAT volume, even though the file data was
        # copied successfully. Web assets only need their bytes and mtime.
        shutil.copyfile(source, dest)
        os.utime(dest, ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns))
        # macOS may create an AppleDouble metadata companion on exFAT.
        # It is not a web asset and should not be committed or deployed.
        dest.with_name(f"._{dest.name}").unlink(missing_ok=True)
    return True


def finalize_page(page: str, relative: str) -> str:
    '''Apply the site-wide head/nav/shell rules and asset versions.'''
    page = update_site_metadata.update_head(page, relative)
    page = update_site_metadata.replace_navigation(page, relative)
    page = update_site_metadata.update_shell(page, relative)
    return apply_asset_versions(page)


PRERENDER_SCRIPT = Path(__file__).resolve().parent / "prerender_markdown.js"
_prerender_warned = False


def prerender_pages(pages: List[str]) -> List[str]:
    '''Render the embedded Markdown to static HTML with the same renderer the
    browser uses. Falls back to client-side rendering if Node.js is missing.'''
    global _prerender_warned
    if not pages:
        return pages
    node = shutil.which("node")
    if not node:
        if not _prerender_warned:
            print("warning: Node.js not found; notes will be rendered in the browser only (worse SEO).", file=sys.stderr)
            _prerender_warned = True
        return pages
    completed = subprocess.run(
        [node, str(PRERENDER_SCRIPT), "--stdin-json"],
        input=json.dumps(pages).encode("utf-8"),
        stdout=subprocess.PIPE,
        check=True,
    )
    return json.loads(completed.stdout.decode("utf-8"))


def prune_attachments(attachments_dir: Path, keep: Set[str], dry_run: bool) -> List[str]:
    '''Delete attachments no synced note references (originals of optimised
    images, removed screenshots, ...). The Obsidian vault keeps the originals.'''
    removed: List[str] = []
    if not attachments_dir.exists():
        return removed
    for path in sorted(attachments_dir.iterdir()):
        if not path.is_file() or path.name in keep:
            continue
        removed.append(path.name)
        if not dry_run:
            path.unlink()
    return removed


def active_targets(root: Path, vault: Path) -> Tuple[List[NoteTarget], Dict[NoteTarget, Path], Dict[str, Dict[str, Dict[str, object]]], List[str]]:
    cards = extract_all_cards(root)
    targets: List[NoteTarget] = []
    vault_paths: Dict[NoteTarget, Path] = {}
    skipped: List[str] = []

    for target in NOTE_TARGETS:
        if target.title not in cards.get(target.subject, {}):
            skipped.append(f"{target.subject}/{target.title}: no website card")
            continue
        vault_path = find_vault_file(vault, target)
        if not vault_path:
            skipped.append(f"{target.subject}/{target.title}: no vault note")
            continue
        targets.append(target)
        vault_paths[target] = vault_path

    return targets, vault_paths, cards, skipped


def select_targets(
    targets: Sequence[NoteTarget],
    vault_paths: Dict[NoteTarget, Path],
    only: Optional[Sequence[str]],
) -> Tuple[List[NoteTarget], Dict[NoteTarget, Path]]:
    if not only:
        return list(targets), vault_paths

    requested = {normalize_key(value) for value in only}
    selected = [
        target
        for target in targets
        if normalize_key(target.title) in requested
        or normalize_key(f"{target.subject}/{target.title}") in requested
    ]
    if not selected:
        raise SyncError(f"No active notes matched --only: {', '.join(only)}")
    return selected, {target: vault_paths[target] for target in selected}


def sync_once(
    root: Path,
    vault: Path,
    dry_run: bool = False,
    quiet: bool = False,
    only: Optional[Sequence[str]] = None,
    optimize_images: bool = True,
    prerender: bool = True,
    prune: bool = False,
) -> Dict[str, object]:
    attachments_dir = root / "notes" / "attachments"
    all_targets, all_vault_paths, cards, skipped = active_targets(root, vault)
    targets, vault_paths = select_targets(all_targets, all_vault_paths, only)
    picture_index = build_picture_index(vault)
    link_map = build_link_map(all_targets, all_vault_paths)
    used_images: Set[Path] = set()
    missing_images: Set[str] = set()
    publisher = ImagePublisher(root, dry_run=dry_run, optimize=optimize_images)
    written_pages = 0

    # Pruning must know every image referenced by every note, not just --only.
    render_targets = all_targets if prune else targets
    pages: List[Tuple[Path, str]] = []
    for target in render_targets:
        markdown = prepare_markdown(
            target, all_vault_paths[target], picture_index, link_map, used_images, missing_images, publisher
        )
        if target not in targets:
            continue
        meta = cards[target.subject].get(target.title, {})
        out_path = root / "notes" / target.subject / target.filename
        relative = out_path.relative_to(root).as_posix()
        detail_intro = extract_detail_intro(out_path)
        pages.append((out_path, finalize_page(html_page(target, markdown, meta, detail_intro), relative)))

    rendered = prerender_pages([page for _path, page in pages]) if prerender else [page for _path, page in pages]
    for (out_path, _page), page in zip(pages, rendered):
        if write_text(out_path, page, dry_run=dry_run):
            written_pages += 1

    changed_subject_pages = update_subject_links(root, targets, dry_run=dry_run)
    publisher.finish()
    pruned = prune_attachments(attachments_dir, publisher.published, dry_run) if prune else []

    result = {
        "targets": len(targets),
        "written_pages": written_pages,
        "changed_subject_pages": changed_subject_pages,
        "used_images": len(used_images),
        "copied_images": publisher.copied,
        "optimized_images": publisher.optimized,
        "pruned_attachments": pruned,
        "missing_images": sorted(missing_images),
        "skipped": skipped,
    }

    if not quiet:
        action = "Would sync" if dry_run else "Synced"
        print(f"{action} {result['targets']} notes.")
        print(f"pages changed: {result['written_pages']}")
        print(f"subject pages changed: {result['changed_subject_pages']}")
        print(
            f"images used/copied/optimised: {result['used_images']}/"
            f"{result['copied_images']}/{result['optimized_images']}"
        )
        if pruned:
            verb = "would remove" if dry_run else "removed"
            print(f"unreferenced attachments {verb}: {len(pruned)}")
        if missing_images:
            print("missing images:")
            for name in sorted(missing_images):
                print(f"  - {name}")
        if skipped:
            print("skipped:")
            for item in skipped:
                print(f"  - {item}")
    return result


def iter_watch_paths(root: Path, vault: Path) -> Iterable[Path]:
    _targets, vault_paths, _cards, _skipped = active_targets(root, vault)
    for path in vault_paths.values():
        if path.exists():
            yield path
    yield from iter_vault_images(vault)
    for rel_path in SUBJECT_PAGES.values():
        path = root / rel_path
        if path.exists():
            yield path


def snapshot(paths: Iterable[Path]) -> Tuple[Tuple[str, int, int], ...]:
    values: List[Tuple[str, int, int]] = []
    for path in paths:
        try:
            stat = path.stat()
        except FileNotFoundError:
            values.append((str(path), -1, -1))
            continue
        values.append((str(path), stat.st_mtime_ns, stat.st_size))
    return tuple(sorted(values))


def watch(root: Path, vault: Path, interval: float, dry_run: bool, only: Optional[Sequence[str]] = None, **options: bool) -> None:
    print(f"Watching Obsidian notes in {vault}")
    print(f"Website root: {root}")
    sync_once(root, vault, dry_run=dry_run, only=only, **options)
    previous = snapshot(iter_watch_paths(root, vault))

    while True:
        time.sleep(interval)
        current = snapshot(iter_watch_paths(root, vault))
        if current == previous:
            continue
        time.sleep(min(max(interval, 1.0), 3.0))
        current = snapshot(iter_watch_paths(root, vault))
        previous = current
        print(time.strftime("\n[%Y-%m-%d %H:%M:%S] Change detected."))
        try:
            sync_once(root, vault, dry_run=dry_run, only=only, **options)
        except Exception as exc:
            print(f"Sync failed: {exc}", file=sys.stderr)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync selected Obsidian vault notes into my_website.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Website root directory.")
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT, help="Obsidian vault directory.")
    parser.add_argument("--watch", action="store_true", help="Keep running and resync when notes or attachments change.")
    parser.add_argument("--interval", type=float, default=5.0, help="Polling interval in seconds for --watch.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would change without writing files.")
    parser.add_argument("--quiet", action="store_true", help="Reduce output for one-shot sync.")
    parser.add_argument("--no-optimize-images", action="store_true", help="Copy attachments unchanged instead of publishing WebP versions.")
    parser.add_argument("--no-prerender", action="store_true", help="Skip static HTML pre-rendering (pages render in the browser only).")
    parser.add_argument(
        "--prune-attachments",
        action="store_true",
        help="Delete files in notes/attachments that no synced note references (originals stay in the vault).",
    )
    parser.add_argument(
        "--only",
        action="append",
        help="Sync only the note with this title (repeat for multiple notes).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    vault = args.vault.resolve()

    if not root.exists():
        raise SyncError(f"Website root does not exist: {root}")
    if not vault.exists():
        raise SyncError(f"Obsidian vault does not exist: {vault}")

    options = {
        "optimize_images": not args.no_optimize_images,
        "prerender": not args.no_prerender,
        "prune": args.prune_attachments,
    }
    if args.watch:
        watch(root, vault, interval=args.interval, dry_run=args.dry_run, only=args.only, **options)
    else:
        sync_once(root, vault, dry_run=args.dry_run, quiet=args.quiet, only=args.only, **options)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
        raise SystemExit(130)
    except Exception as error:
        print(f"sync_obsidian_notes.py: {error}", file=sys.stderr)
        raise SystemExit(1)
