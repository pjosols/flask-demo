#!/usr/bin/env python3
"""
Fetch specific artist/era records from Discogs and append to data/records.json.
Resolves cover art via iTunes with Discogs fallback.

Usage:
    python fetch_targeted.py
"""

import json
import os
import time
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("DISCOGS_PAT", "")
if not TOKEN:
    raise SystemExit("Set DISCOGS_PAT in .env")

HEADERS = {"User-Agent": "VinylArchivesDemo/1.0"}
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "records.json")

TARGETS = [
    {"artist": "Tom Waits",            "years": (1980, 1989), "count": 6},
    {"artist": "Patti Smith",          "years": (1975, 1979), "count": 4},
    {"artist": "Neil Young",           "years": (1970, 1989), "count": 8},
    {"artist": "Velvet Underground",   "years": (1967, 1979), "count": 4},
    {"artist": "Lou Reed",             "years": (1972, 1989), "count": 5},
    {"genre": "Hip Hop",               "years": (1980, 1989), "count": 10},
]


def discogs_get(url, params):
    params["token"] = TOKEN
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{qs}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def itunes_cover(artist, title):
    term = urllib.parse.quote(f"{artist} {title}")
    req = urllib.request.Request(
        f"https://itunes.apple.com/search?term={term}&entity=album&limit=3",
        headers=HEADERS,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        for result in data.get("results", []):
            art = result.get("artworkUrl100", "")
            if art:
                return art.replace("100x100bb", "600x600bb")
    except Exception:
        pass
    return None


def fetch_target(target):
    params = {
        "type": "master",
        "format": "Vinyl",
        "per_page": target["count"] + 10,
        "page": 1,
        "sort": "have",
        "sort_order": "desc",
        "year": f"{target['years'][0]}-{target['years'][1]}",
    }
    if "artist" in target:
        params["artist"] = target["artist"]
        label = f"{target['artist']} ({target['years'][0]}–{target['years'][1]})"
    else:
        params["genre"] = target["genre"]
        label = f"{target['genre']} ({target['years'][0]}–{target['years'][1]})"

    print(f"  Fetching {target['count']} × {label}...", end=" ", flush=True)
    data = discogs_get("https://api.discogs.com/database/search", params)
    results = data.get("results", [])
    print(f"got {len(results)}")
    return results


def parse_release(raw):
    title_field = raw.get("title", "")
    if " - " in title_field:
        artist, title = title_field.split(" - ", 1)
    else:
        artist, title = "Unknown", title_field

    year = raw.get("year") or raw.get("master_year") or None
    formats = raw.get("format") or []
    fmt = "LP"
    for f in formats:
        if f in ("LP", "EP", '7"', '10"', '12"', "Album"):
            fmt = f
            break

    return {
        "artist": artist.strip(),
        "title": title.strip(),
        "label": (raw.get("label") or [""])[0].strip(),
        "year": int(year) if year else None,
        "genre": raw.get("genre") or [],
        "styles": (raw.get("style") or [])[:4],
        "format": fmt,
        "country": (raw.get("country") or "").strip(),
        "rating": None,
        "coverUrl": None,
        "_discogs_thumb": raw.get("cover_image") or raw.get("thumb") or None,
    }


def main():
    # Load existing records
    existing = []
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    seen = {f"{r['artist'].lower()}|{r['title'].lower()}" for r in existing}
    print(f"Existing: {len(existing)} records\n")

    new_records = []
    for target in TARGETS:
        try:
            results = fetch_target(target)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        added = 0
        for raw in results:
            if added >= target["count"]:
                break
            rec = parse_release(raw)
            key = f"{rec['artist'].lower()}|{rec['title'].lower()}"
            if key in seen or not rec["artist"] or not rec["title"]:
                continue
            seen.add(key)
            new_records.append(rec)
            added += 1
        time.sleep(1.1)

    print(f"\nNew records to add: {len(new_records)}")

    # Resolve covers
    print("\n── Resolving cover art ───────────────────────────")
    for i, rec in enumerate(new_records):
        cover = itunes_cover(rec["artist"], rec["title"])
        if not cover:
            cover = rec.get("_discogs_thumb")
        rec["coverUrl"] = cover
        rec.pop("_discogs_thumb", None)
        status = "✓" if cover else "✗"
        print(f"  [{i+1:3}/{len(new_records)}] {status}  {rec['artist']} — {rec['title']}")
        time.sleep(0.25)

    # Merge and save
    all_records = existing + new_records
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Added {len(new_records)} records (total: {len(all_records)})")
    print("Run 'python seed_data.py' to reload into MongoDB")


if __name__ == "__main__":
    main()
