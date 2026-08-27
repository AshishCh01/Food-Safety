"""Seed the initial complaint categories.

Usage (from Backend/):
    venv/Scripts/python.exe -m scripts.seed_complaint_categories

Idempotent: existing categories (matched by key) are left as-is.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.repositories import complaint_category_repository

CATEGORIES = [
    ("expired_food", "Expired Food", "Food being sold or served past its expiry date."),
    ("unhygienic_premises", "Unhygienic Conditions", "Unclean or unsanitary business premises."),
    ("spoiled_food", "Spoiled / Bad Food", "Food that is spoiled, rotten, or unfit for consumption."),
    ("contamination", "Contamination", "Foreign objects or contaminants found in food."),
    ("improper_storage", "Storage Issues", "Food stored at unsafe temperatures or in unsafe conditions."),
    ("other", "Other", "Other food-safety issues not covered by the categories above."),
]


def seed_categories(db) -> None:
    for key, name, description in CATEGORIES:
        category = complaint_category_repository.get_by_key(db, key)
        if category is not None:
            print(f"category {key} already exists, skipping")
            continue
        complaint_category_repository.create(db, key=key, name=name, description=description)
        print(f"created category {key} - {name}")


def main() -> None:
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
