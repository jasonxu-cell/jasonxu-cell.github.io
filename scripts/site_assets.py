#!/usr/bin/env python3
"""Content-hash cache busting for the site's shared CSS/JS files.

Every page links shared assets as ``style.css?v=<hash>``. The hash comes from
the file contents, so it changes exactly when the file changes, and every page
uses the same value (no more hand-edited, drifting ``?v=`` strings).
"""

from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Site-relative paths of assets that get a version query.
VERSIONED_ASSETS = (
    "style.css",
    "research.css",
    "scripts/markdown-article.js",
    "scripts/note-search.js",
    "scripts/comments.js",
    "scripts/ask.js",
)


@lru_cache(maxsize=None)
def _hash(path: str, mtime_ns: int, size: int) -> str:
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()[:10]


def asset_version(relative: str, root: Path = ROOT) -> str:
    path = root / relative
    stat = path.stat()
    return _hash(str(path), stat.st_mtime_ns, stat.st_size)


def asset_url(relative: str, prefix: str = "", root: Path = ROOT) -> str:
    """``asset_url("style.css", "../../")`` -> ``../../style.css?v=1a2b3c4d5e``"""
    return f"{prefix}{relative}?v={asset_version(relative, root)}"


def apply_asset_versions(source: str, root: Path = ROOT) -> str:
    """Rewrite every href/src pointing at a versioned asset to the current hash."""
    for relative in VERSIONED_ASSETS:
        if not (root / relative).exists():
            continue
        version = asset_version(relative, root)
        pattern = re.compile(
            r'((?:href|src)=")((?:\.\./)*)' + re.escape(relative) + r'(?:\?v=[^"]*)?(")'
        )
        source = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}{relative}?v={version}{m.group(3)}", source)
    return source
