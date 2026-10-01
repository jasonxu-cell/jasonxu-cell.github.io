#!/usr/bin/env python3
"""Shared WebP optimisation helpers for the website build scripts.

Used by:
  * optimize_site_images.py  - one-off / manual pass over the whole site
  * sync_obsidian_notes.py   - optimises attachments automatically on sync

The encoder is ``cwebp`` when it is installed (best quality/size), otherwise
Pillow's WebP encoder, so the scripts work on any machine with Pillow.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

from PIL import Image, ImageOps

# Images smaller than this are already cheap; converting them is not worth it.
MIN_BYTES = 100 * 1024
# Longest edge of the published image. Note screenshots are displayed at most
# ~900 CSS px wide, so 2400 px still looks sharp on 2x/3x screens.
MAX_DIMENSION = 2400
# Keep the WebP only when it is meaningfully smaller than the original.
KEEP_RATIO = 0.93
RASTER_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
OPTIMIZED_SUFFIX = "-optimized.webp"
# exFAT stores modification times with coarse precision.
MTIME_SLACK_NS = 2_000_000_000


def optimized_name(name: str) -> str:
    """``foo bar.png`` -> ``foo bar-optimized.webp``."""
    return f"{Path(name).stem}{OPTIMIZED_SUFFIX}"


def is_optimizable(path: Path) -> bool:
    return (
        path.suffix.lower() in RASTER_SUFFIXES
        and not path.name.endswith(OPTIMIZED_SUFFIX)
    )


def is_fresh(output: Path, source: Path) -> bool:
    """True when ``output`` exists and was produced after ``source`` changed."""
    try:
        return output.stat().st_mtime_ns + MTIME_SLACK_NS >= source.stat().st_mtime_ns
    except FileNotFoundError:
        return False


def _image_details(path: Path):
    with Image.open(path) as image:
        has_alpha = image.mode in {"RGBA", "LA", "PA"} or "transparency" in image.info
        frames = getattr(image, "n_frames", 1)
        return image.width, image.height, has_alpha, image.format, frames


def _encode_with_cwebp(source: Path, output: Path, quality: int, has_alpha: bool,
                       width: int, height: int, max_dimension: int) -> None:
    command = [
        "cwebp", "-quiet", "-q", str(quality), "-m", "6", "-mt",
        "-metadata", "icc", "-sharp_yuv",
    ]
    if has_alpha:
        command += ["-alpha_q", "100", "-exact"]
    if max(width, height) > max_dimension:
        command += ["-resize", str(max_dimension), "0"] if width >= height else ["-resize", "0", str(max_dimension)]
    command += [str(source), "-o", str(output)]
    subprocess.run(command, check=True)


def _encode_with_pillow(source: Path, output: Path, quality: int, has_alpha: bool,
                        max_dimension: int) -> None:
    with Image.open(source) as original:
        icc_profile = original.info.get("icc_profile")
        image = ImageOps.exif_transpose(original)
        image = image.convert("RGBA" if has_alpha else "RGB")
        if max(image.size) > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
        options = {"quality": quality, "method": 6}
        if icc_profile:
            options["icc_profile"] = icc_profile
        image.save(output, "WEBP", **options)


def make_webp(source: Path, output: Path, max_dimension: int = MAX_DIMENSION) -> bool:
    """Encode ``source`` to ``output`` as WebP.

    Returns True when the WebP was written and is worth using. When it is not
    (GIF/animated input, or no real size win) nothing is left at ``output``.
    """
    width, height, has_alpha, image_format, frames = _image_details(source)
    # cwebp cannot read GIFs and animated images would lose their animation.
    if image_format == "GIF" or frames > 1:
        return False

    quality = 88 if source.suffix.lower() == ".png" else 82
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)

    if shutil.which("cwebp"):
        _encode_with_cwebp(source, output, quality, has_alpha, width, height, max_dimension)
    else:
        _encode_with_pillow(source, output, quality, has_alpha, max_dimension)

    if output.stat().st_size >= source.stat().st_size * KEEP_RATIO:
        output.unlink()
        return False
    return True


class SkipCache:
    """Remembers sources where WebP gave no benefit, so they are not re-encoded
    on every sync. Keyed by file name + size + mtime; stored outside the
    published folders (see .gitignore)."""

    def __init__(self, path: Path):
        self.path = path
        self._data: Dict[str, str] = {}
        self._dirty = False
        try:
            self._data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            self._data = {}

    @staticmethod
    def _signature(source: Path) -> str:
        stat = source.stat()
        return f"{stat.st_size}:{stat.st_mtime_ns // MTIME_SLACK_NS}"

    def should_skip(self, source: Path) -> bool:
        return self._data.get(source.name) == self._signature(source)

    def remember(self, source: Path) -> None:
        self._data[source.name] = self._signature(source)
        self._dirty = True

    def save(self) -> None:
        if not self._dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        self._dirty = False


def optimize_into(source: Path, output_dir: Path, skip_cache: Optional[SkipCache] = None,
                  dry_run: bool = False) -> Optional[str]:
    """Create/refresh ``output_dir/<stem>-optimized.webp`` for ``source``.

    Returns the WebP file name to reference, or None when the original file
    should be used instead (small image, GIF, SVG, or WebP not smaller).
    """
    if not is_optimizable(source) or source.stat().st_size < MIN_BYTES:
        return None
    if skip_cache and skip_cache.should_skip(source):
        return None

    output = output_dir / optimized_name(source.name)
    if is_fresh(output, source):
        return output.name
    if dry_run:
        return output.name

    try:
        written = make_webp(source, output)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"  ! could not optimise {source.name}: {error}")
        return None

    if not written:
        if skip_cache:
            skip_cache.remember(source)
        return None
    # macOS may create an AppleDouble companion on exFAT volumes.
    output.with_name(f"._{output.name}").unlink(missing_ok=True)
    return output.name
