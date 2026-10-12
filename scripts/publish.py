#!/usr/bin/env python3
"""One command to run after editing notes.

Runs the full pipeline in order:
  1. sync_obsidian_notes.py    (Obsidian -> notes/*.html, images, pre-render)
  2. optimize_site_images.py   (site-wide WebP optimisation, --no-rebuild)
  3. update_site_metadata.py   (dates, Recently Updated, sitemap, asset hashes)

Usage:
    python3 scripts/publish.py                        # full pipeline
    python3 scripts/publish.py --dry-run              # preview sync + image changes
    python3 scripts/publish.py --only <note title>    # sync one note, then optimise + metadata
    python3 scripts/publish.py --prune-attachments    # also delete unreferenced attachments
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def find_python() -> str:
    """The build scripts need Pillow; the default python3 may not have it."""
    candidates = [sys.executable, "python3.12", "/usr/local/bin/python3"]
    for candidate in candidates:
        resolved = shutil.which(candidate) or candidate
        try:
            subprocess.run([resolved, "-c", "import PIL"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return resolved
        except (OSError, subprocess.CalledProcessError):
            continue
    print("warning: no Python with Pillow found; image optimisation may fail.", file=sys.stderr)
    return sys.executable


def run(step: str, command: list[str]) -> None:
    print(f"\n=== {step} ===", flush=True)
    subprocess.run(command, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Preview changes; skips the metadata pass.")
    parser.add_argument("--only", action="append", help="Sync only the note with this title (repeatable).")
    parser.add_argument("--prune-attachments", action="store_true", help="Delete unreferenced files in notes/attachments.")
    args = parser.parse_args(argv)

    python = find_python()
    sync_cmd = [python, str(SCRIPTS / "sync_obsidian_notes.py")]
    images_cmd = [python, str(SCRIPTS / "optimize_site_images.py"), "--no-rebuild"]

    if args.dry_run:
        sync_cmd.append("--dry-run")
        images_cmd.append("--dry-run")
    if args.prune_attachments:
        sync_cmd.append("--prune-attachments")
    for title in args.only or []:
        sync_cmd += ["--only", title]

    run("1/3 sync notes", sync_cmd)
    run("2/3 optimise images", images_cmd)
    if args.dry_run:
        print("\n=== 3/3 site metadata ===\nskipped in --dry-run mode (update_site_metadata.py has no dry-run).")
    else:
        run("3/3 site metadata", [python, str(SCRIPTS / "update_site_metadata.py")])

    print("\nDone.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
        raise SystemExit(130)
    except subprocess.CalledProcessError as error:
        print(f"\npublish.py: step failed with exit code {error.returncode}", file=sys.stderr)
        raise SystemExit(error.returncode or 1)
