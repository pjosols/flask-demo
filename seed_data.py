#!/usr/bin/env python3
"""
Seed MongoDB with vinyl records from data/records.json.
Run fetch_discogs.py first to generate the JSON (requires a Discogs token).
After that, this script needs no credentials — just MongoDB.

Usage:
    python seed_data.py
    python seed_data.py --connection mongodb://localhost:27017/
"""

import argparse
import json
import os
import random


DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "records.json")


def _fake_rating():
    """Weighted random rating: skews toward 3.5–4.5 (realistic for curated collections)."""
    return random.choice([2.5, 3.0, 3.0, 3.5, 3.5, 3.5, 4.0, 4.0, 4.0, 4.5, 4.5, 5.0])


def seed_records(connection_string="mongodb://localhost:27017/"):
    from pymongo import MongoClient

    if not os.path.exists(DATA_PATH):
        raise SystemExit(
            f"Data file not found: {DATA_PATH}\n"
            "Run fetch_discogs.py first to generate it."
        )

    with open(DATA_PATH, encoding="utf-8") as f:
        records = [r for r in json.load(f) if 1970 <= (r.get("year") or 0) <= 1989]

    # Backfill null ratings with fake data
    for rec in records:
        if not rec.get("rating"):
            rec["rating"] = _fake_rating()

    print(f"Loaded {len(records)} records from {DATA_PATH}")

    client = MongoClient(connection_string)
    db = client["vinyl_database"]
    collection = db["records"]

    print("Dropping existing collection...")
    db.drop_collection("records")

    result = collection.insert_many(records)
    print(f"Inserted {len(result.inserted_ids)} records")

    print("Creating indexes...")
    from app.tools.db_init import create_indexes
    create_indexes(db)

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed MongoDB with vinyl records")
    parser.add_argument("--connection", default="mongodb://localhost:27017/",
                        help="MongoDB connection string (default: mongodb://localhost:27017/)")
    args = parser.parse_args()
    seed_records(args.connection)
