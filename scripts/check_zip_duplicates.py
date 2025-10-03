#!/usr/bin/env python3
"""
Check for duplicate arcnames in ZIP files.
"""

import sys
import zipfile
from pathlib import Path


def check_zip_duplicates(zip_path: Path) -> tuple[bool, list[str]]:
    """
    Check for duplicate arcnames in a ZIP file.

    Args:
        zip_path: Path to the ZIP file to check

    Returns:
        Tuple of (has_duplicates, duplicate_names)
    """
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()

    # Count occurrences of each name
    name_counts = {}
    for name in names:
        name_counts[name] = name_counts.get(name, 0) + 1

    # Find duplicates
    duplicates = [name for name, count in name_counts.items() if count > 1]

    return len(duplicates) > 0, sorted(duplicates)


def main():
    """Main function for CLI usage."""
    if len(sys.argv) != 2:
        print("Usage: python check_zip_duplicates.py <zip_path>")
        sys.exit(1)

    zip_path = Path(sys.argv[1])

    if not zip_path.exists():
        print(f"Error: ZIP file not found: {zip_path}")
        sys.exit(1)

    has_duplicates, duplicates = check_zip_duplicates(zip_path)

    if has_duplicates:
        print(f"ERROR: Duplicate arcnames detected in {zip_path}:")
        for dup in duplicates:
            print(f"  - {dup}")
        sys.exit(2)
    else:
        print(f"SUCCESS: No duplicate arcnames found in {zip_path}")
        print(f"INFO: Total files: {len(zipfile.ZipFile(zip_path, 'r').namelist())}")


if __name__ == "__main__":
    main()
