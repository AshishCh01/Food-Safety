"""Seed the six Maharashtra divisions and 36 districts.

Usage (from Backend/):
    venv/Scripts/python.exe -m scripts.seed_districts

Idempotent: existing divisions/districts (matched by code) are left as-is.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.repositories import district_repository, division_repository
from app.models.district import District
from app.models.division import Division
from scripts.maharashtra_geography import DISTRICTS, DIVISIONS


def seed_divisions(db) -> dict[str, Division]:
    by_code: dict[str, Division] = {}
    for entry in DIVISIONS:
        division = division_repository.get_by_code(db, entry["code"])
        if division is None:
            division = Division(name=entry["name"], code=entry["code"])
            db.add(division)
            db.flush()
            print(f"created division {entry['code']} - {entry['name']}")
        else:
            print(f"division {entry['code']} already exists, skipping")
        by_code[entry["code"]] = division
    db.commit()
    return by_code


def seed_districts(db, divisions_by_code: dict[str, Division]) -> None:
    for name, code, division_code, centroid_lat, centroid_lon in DISTRICTS:
        district = district_repository.get_by_code(db, code)
        if district is not None:
            if district.centroid_latitude is None or district.centroid_longitude is None:
                district.centroid_latitude = centroid_lat
                district.centroid_longitude = centroid_lon
                print(f"district {code} already exists, backfilled centroid")
            else:
                print(f"district {code} already exists, skipping")
            continue
        district = District(
            name=name,
            code=code,
            division_id=divisions_by_code[division_code].id,
            centroid_latitude=centroid_lat,
            centroid_longitude=centroid_lon,
        )
        db.add(district)
        print(f"created district {code} - {name}")
    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        divisions_by_code = seed_divisions(db)
        seed_districts(db, divisions_by_code)
    finally:
        db.close()


if __name__ == "__main__":
    main()
