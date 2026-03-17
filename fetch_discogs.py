#!/usr/bin/env python3
"""
One-time script to fetch 100 vinyl records from Discogs + cover art from iTunes.
Output is saved to data/records.json and committed to the repo.
No credentials needed after that — seed_data.py reads the JSON directly.

Usage:
    python fetch_discogs.py --token YOUR_PERSONAL_ACCESS_TOKEN
    python fetch_discogs.py  # will prompt for token
"""

import argparse
import json
import os
import time
import urllib.parse
import urllib.request


# ── Genres to sample across ───────────────────────────────────────────────────
# Focused on 1970s — naturally dark/moody cover art, fits the theme
GENRE_QUERIES = [
    {"genre": "Rock",        "style": "Prog Rock",         "count": 12},
    {"genre": "Rock",        "style": "Psychedelic Rock",  "count": 8},
    {"genre": "Rock",        "style": "Hard Rock",         "count": 8},
    {"genre": "Jazz",        "style": "Jazz-Funk",         "count": 10},
    {"genre": "Jazz",        "style": "Fusion",            "count": 8},
    {"genre": "Funk / Soul", "style": "Funk",              "count": 10},
    {"genre": "Funk / Soul", "style": "Soul",              "count": 8},
    {"genre": "Electronic",  "style": "Krautrock",         "count": 8},
    {"genre": "Reggae",      "style": "Roots Reggae",      "count": 7},
    {"genre": "Blues",       "style": "Electric Blues",     "count": 6},
    {"genre": "Rock",        "style": "Southern Rock",     "count": 5},
    {"genre": "Latin",       "style": "Latin Jazz",        "count": 5},
    {"genre": "Rock",        "style": "Glam",              "count": 5},
]

DECADE_RANGE = (1970, 1979)

DISCOGS_SEARCH = "https://api.discogs.com/database/search"
ITUNES_SEARCH  = "https://itunes.apple.com/search"
OUTPUT_PATH    = os.path.join(os.path.dirname(__file__), "data", "records.json")


def discogs_get(url, params, token):
    params["token"] = token
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{url}?{qs}",
        headers={"User-Agent": "VinylArchivesDemo/1.0"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def itunes_cover(artist, title):
    """Return a 600px iTunes artwork URL, or None."""
    term = urllib.parse.quote(f"{artist} {title}")
    req = urllib.request.Request(
        f"{ITUNES_SEARCH}?term={term}&entity=album&limit=3",
        headers={"User-Agent": "VinylArchivesDemo/1.0"}
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


def fetch_genre(genre, count, token, style=None):
    label = f"{genre}/{style}" if style else genre
    print(f"  Fetching {count} × {label}...", end=" ", flush=True)
    params = {
        "type":       "master",
        "genre":      genre,
        "format":     "Vinyl",
        "per_page":   count + 10,
        "page":       1,
        "sort":       "have",
        "sort_order": "desc",
        "year":       f"{DECADE_RANGE[0]}-{DECADE_RANGE[1]}",
    }
    if style:
        params["style"] = style
    data = discogs_get(DISCOGS_SEARCH, params, token)
    results = data.get("results", [])
    print(f"got {len(results)}")
    return results


def parse_release(raw, genre_label):
    """Normalise a Discogs search result into our schema."""
    title_field = raw.get("title", "")
    if " - " in title_field:
        artist, title = title_field.split(" - ", 1)
    else:
        artist, title = "Unknown", title_field

    artist = artist.strip()
    title  = title.strip()

    label   = (raw.get("label")  or [""])[0].strip()
    country = (raw.get("country") or "").strip()
    year    = raw.get("year") or raw.get("master_year") or None
    genres  = raw.get("genre")  or [genre_label]
    styles  = raw.get("style")  or []
    formats = raw.get("format") or []

    # Pick a clean format label
    fmt = "LP"
    for f in formats:
        if f in ("LP", "EP", '7"', '10"', '12"', "Album"):
            fmt = f
            break

    # Community rating from Discogs (0–5, often 3.5–4.5 for popular)
    community = raw.get("community", {}) or {}
    rating_raw = community.get("rating", {}) or {}
    rating = round(float(rating_raw.get("average") or 0), 1) or None

    return {
        "artist":  artist,
        "title":   title,
        "label":   label,
        "year":    int(year) if year else None,
        "genre":   genres,
        "styles":  styles[:4],        # cap at 4
        "format":  fmt,
        "country": country,
        "rating":  rating,
        "coverUrl": None,             # filled in next pass
        "_discogs_thumb": raw.get("cover_image") or raw.get("thumb") or None,
        "_itunes_query": f"{artist} {title}",
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch vinyl records from Discogs")
    parser.add_argument("--token", default="", help="Discogs personal access token")
    parser.add_argument("--skip-covers", action="store_true", help="Skip iTunes cover lookup (faster)")
    args = parser.parse_args()

    token = args.token or os.environ.get("DISCOGS_TOKEN") or input("Discogs personal access token: ").strip()
    if not token:
        raise SystemExit("Token required.")

    # ── 1. Fetch from Discogs ─────────────────────────────────────────────────
    print("\n── Fetching from Discogs ─────────────────────────")
    seen_titles = set()
    records = []

    for q in GENRE_QUERIES:
        try:
            raw_results = fetch_genre(q["genre"], q["count"] + 5, token, style=q.get("style"))
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        added = 0
        for raw in raw_results:
            if added >= q["count"]:
                break
            rec = parse_release(raw, q["genre"])
            key = f"{rec['artist'].lower()}|{rec['title'].lower()}"
            if key in seen_titles or not rec["artist"] or not rec["title"]:
                continue
            seen_titles.add(key)
            records.append(rec)
            added += 1

        # Discogs rate limit: 60 req/min — be polite
        time.sleep(1.1)

    print(f"\nCollected {len(records)} unique records")

    # ── 2. Resolve cover art: iTunes first, Discogs thumb as fallback ────────
    if not args.skip_covers:
        print("\n── Resolving cover art ───────────────────────────")
        for i, rec in enumerate(records):
            cover = itunes_cover(rec["artist"], rec["title"])
            if not cover:
                cover = rec.get("_discogs_thumb")
            rec["coverUrl"] = cover
            src = "iTunes" if cover and "mzstatic" in (cover or "") else ("Discogs" if cover else "none")
            status = "✓" if cover else "✗"
            print(f"  [{i+1:3}/{len(records)}] {status} [{src:7}] {rec['artist']} — {rec['title']}")
            time.sleep(0.25)

    # ── 3. Clean up internal keys ─────────────────────────────────────────────
    for rec in records:
        rec.pop("_itunes_query", None)
        rec.pop("_discogs_thumb", None)

    # ── 4. Save ───────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    covered = sum(1 for r in records if r.get("coverUrl"))
    print(f"\n✓ Saved {len(records)} records to {OUTPUT_PATH}")
    print(f"  Cover art resolved: {covered}/{len(records)}")


if __name__ == "__main__":
    main()
