#!/usr/bin/env python3
"""Seed the database with sample categories and products.

Usage:
    python -m scripts.seed
    python -m scripts.seed --fresh
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.seeders import seed_catalog
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed categories and products")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete existing categories and products before seeding",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = seed_catalog(db, fresh=args.fresh)
        if result.get("skipped"):
            print(
                "Database already has data. "
                "Run with --fresh to clear and re-seed."
            )
            print(f"  categories: {result['categories']}")
            print(f"  products:   {result['products']}")
            return

        print("Seed completed successfully.")
        print(f"  categories: {result['categories']}")
        print(f"  products:   {result['products']}")
    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
