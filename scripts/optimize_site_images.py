#!/usr/bin/env python3
"""Create WebP variants for large referenced images and point pages at them.

Scans every HTML/CSS file for image references (<img src>, Markdown
``![](...)``, LaTeX ``\\includegraphics{...}``, CSS ``url(...)``). Each local
raster image >= 100 KB gets a ``<name>-optimized.webp`` sibling (max 2400 px)
and the reference is rewritten to it, when the WebP is meaningfully smaller.

Usage:
    python3 scripts/optimize_site_images.py              # optimise + rewrite
    python3 scripts/optimize_site_images.py --dry-run    # report only
    python3 scripts/optimize_site_images.py --prune      # also delete originals
        # and other files in notes/attachments that no page references
        # (the Obsidian vault keeps every original)

Afterwards run ``python3 scripts/update_site_metadata.py`` so pre-rendered
pages pick up the new image URLs (the script does this automatically unless
--no-rebuild is given).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote, unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_images import SkipCache, optimize_into  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKIP_CACHE = ROOT / ".cache" / "image-optimization-skip.json"
ATTACHMENTS = ROOT / "notes" / "attachments"


def referenced_urls(source: str) -> list[str]:
    values = re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)', source, flags=re.IGNORECASE)
    values += re.findall(r'!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)', source)
    values += re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', source)
    values += re.findall(r'url\(["\']?([^"\')]+)', source, flags=re.IGNORECASE)
    return values


def owner_files() -> list[Path]:
    return sorted(
        path
        for pattern in ("*.html", "*.css")
        for path in ROOT.rglob(pattern)
        if not path.name.startswith("._")
        and not path.relative_to(ROOT).as_posix().startswith((".git/", ".cache/", "scripts/"))
    )


def rewritten_url(raw_url: str, webp_name: str) -> str:
    directory, _slash, filename = raw_url.rpartition("/")
    # Keep the same encoding style as the original reference.
    name = quote(webp_name) if "%" in filename else webp_name
    return f"{directory}/{name}" if directory else name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prune", action="store_true", help="Delete unreferenced files in notes/attachments.")
    parser.add_argument("--no-rebuild", action="store_true", help="Do not run update_site_metadata.py afterwards.")
    args = parser.parse_args(argv)

    owners = owner_files()
    references: dict[Path, list[tuple[Path, str]]] = defaultdict(list)
    for owner in owners:
        source = owner.read_text(encoding="utf-8")
        for raw_url in referenced_urls(source):
            if raw_url.startswith(("http:", "https:", "data:", "#", "$")):
                continue
            path = (owner.parent / unquote(raw_url)).resolve()
            if path.is_file():
                references[path].append((owner, raw_url))

    skip_cache = SkipCache(SKIP_CACHE)
    replacements: dict[Path, dict[str, str]] = defaultdict(dict)
    before = after = 0
    count = 0
    for source in sorted(references, key=lambda item: item.as_posix().lower()):
        webp_name = optimize_into(source, source.parent, skip_cache, dry_run=args.dry_run)
        if not webp_name:
            continue
        webp = source.parent / webp_name
        count += 1
        before += source.stat().st_size
        after += webp.stat().st_size if webp.exists() else 0
        for owner, raw_url in references[source]:
            replacements[owner][raw_url] = rewritten_url(raw_url, webp_name)

    changed_owners = 0
    for owner, mapping in replacements.items():
        text = owner.read_text(encoding="utf-8")
        updated = text
        for old, new in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
            # Only replace whole URL tokens, not substrings of longer names.
            updated = re.sub(r'(?<=[("{\'])' + re.escape(old) + r'(?=[)"}\'\s])', new.replace("\\", "\\\\"), updated)
        if updated != text:
            changed_owners += 1
            if not args.dry_run:
                owner.write_text(updated, encoding="utf-8")
    if not args.dry_run:
        skip_cache.save()

    verb = "Would use" if args.dry_run else "Using"
    print(
        f"{verb} WebP for {count} images in {changed_owners} files; payload "
        f"{before / 1e6:.1f} MB -> {after / 1e6:.1f} MB"
    )

    if args.prune:
        still_referenced: set[str] = set()
        for owner in owners:
            text = owner.read_text(encoding="utf-8")
            for raw_url in referenced_urls(text):
                path = (owner.parent / unquote(raw_url)).resolve()
                if path.parent == ATTACHMENTS.resolve():
                    still_referenced.add(path.name)
        removed = [
            path for path in sorted(ATTACHMENTS.iterdir())
            if path.is_file() and path.name not in still_referenced
        ]
        size = sum(path.stat().st_size for path in removed)
        verb = "Would remove" if args.dry_run else "Removed"
        print(f"{verb} {len(removed)} unreferenced attachments ({size / 1e6:.1f} MB)")
        if not args.dry_run:
            for path in removed:
                path.unlink()

    if not args.dry_run and not args.no_rebuild:
        subprocess.run([sys.executable, str(Path(__file__).with_name("update_site_metadata.py"))], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
