#!/usr/bin/env python3
"""
Deemon Missing Releases Downloader

Uses deemon's built-in CollectionMatcher to check what's already in the
local music collection and only download releases that are MISSING.

Usage:
    python3 deemon_download_missing.py "Artist Name" "Album Name"
    python3 deemon_download_missing.py "Artist Name" "Album Name" --include-singles

The Album Name is used to identify the correct artist on Deezer.
"""

import sys
import os
import logging
import argparse
import json

# Ensure we can import deemon modules
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Suppress noisy debug logging from deemon internals
logging.getLogger("deemon").setLevel(logging.WARNING)


def main():
    parser = argparse.ArgumentParser(
        description="Download missing releases by checking against local collection"
    )
    parser.add_argument("artist", help="Artist/band name")
    parser.add_argument("album", help="Album name to identify the artist on Deezer")
    parser.add_argument(
        "--include-singles",
        action="store_true",
        help="Include singles and EPs in the download"
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Only print missing album URLs, don't download"
    )
    parser.add_argument(
        "--report-json",
        action="store_true",
        help="Print a structured read-only discography report and don't download"
    )
    args = parser.parse_args()

    # ── 1. Import deemon modules ──────────────────────────────────────────
    from deemon.core.config import Config as DeemonConfig
    from deemon.core.api import PlatformAPI
    from deemon.cmd.download import Download
    from deemon.core.rileys_collection_matcher import CollectionMatcher

    # Ensure HOME etc. are set for deemix
    if not os.environ.get("HOME"):
        os.environ["HOME"] = "/Users/rd"
    if not os.environ.get("XDG_CONFIG_HOME"):
        os.environ["XDG_CONFIG_HOME"] = "/Users/rd/.config"

    # Initialize deemon config (required before using PlatformAPI)
    DeemonConfig()

    # ── 2. Set up API and search for the artist ───────────────────────────
    api = PlatformAPI()
    artist_result = api.search_artist(args.artist, limit=5)
    if not artist_result.get("results"):
        logger.error(f"Artist not found: {args.artist}")
        sys.exit(1)

    # Try to find the right artist by matching on the album
    search_url = "https://api.deezer.com/search/album"
    import requests
    import time

    try:
        resp = requests.get(
            search_url,
            params={"q": f"{args.artist} {args.album}", "limit": 10},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        found_albums = data.get("data") or []
        if not found_albums:
            logger.error(f"No album found for: {args.artist} - {args.album}")
            sys.exit(1)
        found_album = found_albums[0]
    except Exception as e:
        logger.error(f"Error searching for album: {e}")
        sys.exit(1)

    artist = found_album.get("artist") or {}
    artist_id = artist.get("id")
    artist_name = artist.get("name") or args.artist

    if not artist_id:
        logger.error("Could not resolve artist from album search")
        sys.exit(1)

    artist_header = f"{artist_name}"
    logger.info("")
    logger.info(f"{'─' * 60}")
    logger.info(f"  🎵  {artist_header}")
    logger.info(f"{'─' * 60}")
    logger.info(f"  Discography on Deezer · resolving via: {args.album}")
    logger.info("")

    # ── 3. Fetch full discography from Deezer ─────────────────────────────
    albums_url = f"https://api.deezer.com/artist/{artist_id}/albums"
    all_albums = []
    url = albums_url

    try:
        while url:
            resp = requests.get(url, params={"limit": 100}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            all_albums.extend(data.get("data") or [])
            url = data.get("next")
            if url:
                time.sleep(0.3)
    except Exception as e:
        logger.error(f"Error fetching artist discography: {e}")
        sys.exit(1)

    if not all_albums:
        logger.error("No albums found in discography")
        sys.exit(1)

    # ── 4. Filter by type (optional singles) ──────────────────────────────
    if not args.include_singles:
        filtered = [
            alb for alb in all_albums
            if (alb.get("record_type") or "").lower() in ["album", "ep"]
        ]
        type_label = "albums & EPs (no singles)"
    else:
        filtered = all_albums
        type_label = "albums, EPs & singles"

    total_before = len(all_albums)
    total_after_type = len(filtered)
    logger.info(f"  Total releases on Deezer:  {total_before}")
    logger.info(f"  After filtering ({type_label}): {total_after_type}")
    logger.info("")

    # ── 5. Deduplicate by title ───────────────────────────────────────────
    seen_titles = set()
    unique_albums = []
    for alb in filtered:
        title = (alb.get("title") or "").lower()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_albums.append(alb)

    duplicates = total_after_type - len(unique_albums)
    if duplicates > 0:
        logger.info(f"  Removed {duplicates} duplicate title(s)")
        logger.info("")

    if not unique_albums:
        logger.error("No unique albums found in discography after filtering")
        sys.exit(1)

    # ── 6. Build album data for collection matcher ────────────────────────
    deezer_albums = []
    for alb in unique_albums:
        deezer_albums.append({
            "artist": artist_name,
            "album": alb.get("title", "Unknown"),
            "year": str(alb.get("release_date", "") or "")[:4],
            "release_date": alb.get("release_date") or "",
            "record_type": (alb.get("record_type") or "release").lower(),
            "id": alb.get("id"),
            "url": f"https://www.deezer.com/album/{alb.get('id')}",
        })

    # ── 7. Check against local collection ─────────────────────────────────
    logger.info(f"{'─' * 60}")
    logger.info("  🔍  Checking against local collection...")
    logger.info(f"{'─' * 60}")
    matcher = CollectionMatcher()

    missing_albums = []
    existing_albums = []
    for album_data in deezer_albums:
        artist_name_check = album_data["artist"]
        album_title = album_data["album"]
        album_year = album_data["year"]
        display = f"    {artist_name_check} - {album_title}  ({album_year})"

        if matcher.is_album_in_collection(artist_name_check, album_title, album_year):
            existing_albums.append(album_data)
        else:
            logger.info(f"  ⬜  {artist_name_check} - {album_title}  ({album_year})")
            missing_albums.append(album_data)

    if args.report_json:
        report = {
            "artist": artist_name,
            "artist_id": artist_id,
            "resolved_via": args.album,
            "filter": type_label,
            "total_releases": total_before,
            "filtered_releases": total_after_type,
            "duplicate_titles_skipped": duplicates,
            "releases": deezer_albums,
            "existing": existing_albums,
            "missing": missing_albums,
        }
        print("REPORT_JSON:" + json.dumps(report, ensure_ascii=False), flush=True)
        sys.exit(0)

    # ── 8. Summary ────────────────────────────────────────────────────────
    logger.info("")
    logger.info(f"{'─' * 60}")
    logger.info(f"  📊  SUMMARY")
    logger.info(f"{'─' * 60}")
    logger.info(f"     Already in collection:  {len(existing_albums)}")
    logger.info(f"     Missing — to download:  {len(missing_albums)}")
    if duplicates > 0:
        logger.info(f"     Duplicate titles skipped: {duplicates}")
    logger.info(f"{'─' * 60}")
    logger.info("")

    if not missing_albums:
        logger.info(f"  ✅  Complete collection! Nothing to download.")
        print(f"\nNOTIFY: {artist_name} — Already in collection: {len(existing_albums)}/{len(deezer_albums)} ✅  Nothing to download.", flush=True)
        sys.exit(0)

    if args.print_only:
        logger.info(f"  Missing album URLs:")
        logger.info("")
        for alb in missing_albums:
            print(alb["url"])
        print(f"\nNOTIFY: {artist_name} — Already had: {len(existing_albums)} | Missing: {len(missing_albums)} (--print-only mode)", flush=True)
        print(f"\nNOTIFY: {artist_name} — Already had: {len(existing_albums)} | Missing: {len(missing_albums)} (--print-only mode)")
        sys.exit(0)

    # ── 9. Download missing albums ────────────────────────────────────────
    logger.info(f"  ⬇️   Downloading {len(missing_albums)} missing release(s)...")
    logger.info("")
    dl = Download(active_api=api)
    for alb in missing_albums:
        album_url = alb["url"]
        dl.download(None, None, None, [album_url], None, None, None, None, auto=False)

    if dl.queue_list:
        dl.download_queue()
        downloaded = min(len(missing_albums), len(dl.queue_list))
        logger.info("")
        logger.info(f"{'─' * 60}")
        logger.info(f"  ✅  Done! {len(missing_albums)} release(s) downloaded.")
        logger.info(f"{'─' * 60}")
        print(f"\nNOTIFY: {artist_name} — Already had: {len(existing_albums)} | Missing: {len(missing_albums)} | Downloaded: {len(missing_albums)} ✅")
    else:
        logger.info("  No releases could be queued for download.")
        print(f"\nNOTIFY: {artist_name} — Already had: {len(existing_albums)} | {len(missing_albums)} missing, but none could be queued ❌")


if __name__ == "__main__":
    main()
