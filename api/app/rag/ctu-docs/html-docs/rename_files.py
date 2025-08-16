#!/usr/bin/env python3
"""
Script to rename markdown files based on their title metadata.
Removes accents, punctuation, and converts to snake_case.

Run this script with:

```python
python rename_files.py ctu-admission-docs
```
"""

import re
import unicodedata
from pathlib import Path

import frontmatter
from loguru import logger


def strip_accents(s: str) -> str:
    """Remove accents from text."""

    # special case for đ
    s = s.replace("đ", "d").replace("Đ", "D")

    normalized = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def extract_title_from_markdown(file_path: Path) -> str | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
            title = post.metadata.get("title")
            return str(title) if title is not None else None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None


def clean_title_to_filename(title: str) -> str:
    if not title:
        return ""

    # Remove quotes if present
    title = title.strip("\"'")

    # Remove accents
    title = strip_accents(title)

    # Convert to lowercase
    title = title.lower()

    # Remove punctuation and special characters, keep only alphanumeric and spaces
    title = re.sub(r"[^\w\s]", " ", title)

    # Replace multiple spaces with single space and strip
    title = re.sub(r"\s+", " ", title).strip()

    # Convert spaces to underscores (snake_case)
    title = title.replace(" ", "_")

    # Remove any leading/trailing underscores
    title = title.strip("_")

    return title


def rename_markdown_files(directory: str, dry_run: bool = True):
    """Rename all markdown files in the directory based on their title metadata."""
    directory_path = Path(directory)

    if not directory_path.exists():
        logger.error(f"Directory {directory} does not exist!")
        return

    # Find all markdown files
    md_files = list(directory_path.glob("*.md"))

    if not md_files:
        logger.error(f"No markdown files found in {directory}")
        return

    logger.info(f"Found {len(md_files)} markdown files")
    logger.info("=" * 80)

    rename_operations: list[tuple[Path, Path, str]] = []

    for md_file in md_files:
        title = extract_title_from_markdown(md_file)

        if not title:
            logger.error(f"{md_file.name}: No title found in metadata")
            continue

        new_filename = clean_title_to_filename(title)

        if not new_filename:
            logger.error(
                f"{md_file.name}: Could not generate filename from title: '{title}'"
            )
            continue

        new_filename += ".md"
        new_path = md_file.parent / new_filename

        # Check if new filename already exists (and it's not the same file)
        if new_path.exists() and new_path != md_file:
            logger.warning(
                f"{md_file.name}: Target filename '{new_filename}' already exists"
            )
            continue

        # Skip if no change needed
        if md_file.name == new_filename:
            logger.info(f"{md_file.name}: No change needed")
            continue

        rename_operations.append((md_file, new_path, title))

        logger.info(f"{md_file.name} -> {new_filename}")
        logger.info(f"   Title: '{title}'")
        logger.info("")

    if not rename_operations:
        logger.info("No files to rename.")
        return

    logger.info("=" * 80)
    logger.info(f"Total files to rename: {len(rename_operations)}")

    if dry_run:
        logger.info("\nDRY RUN MODE - No files will actually be renamed")
    else:
        logger.info("\nExecuting rename operations...")

        for old_path, new_path, _ in rename_operations:
            try:
                old_path.rename(new_path)
                logger.info(f"Renamed: {old_path.name} -> {new_path.name}")
            except Exception as e:
                logger.error(f"Failed to rename {old_path.name}: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Rename markdown files based on their title metadata",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "dir",
        type=str,
        help="Directory containing markdown files",
    )
    parser.add_argument("--dry_run", action="store_true", help="Dry run mode")

    args = parser.parse_args()

    rename_markdown_files(args.dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
