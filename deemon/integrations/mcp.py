import sys
import json
import re
import io
import time
import logging
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from deemon.core.config import Config as DeemonConfig
from deemon.core.resolver import InputResolver, ResolutionStatus
from deemon.core import api
from deemon.cmd.download import Download
from deemon.cmd.monitor import Monitor
from deemon.core.db import Database

DeemonConfig()

logger = logging.getLogger(__name__)

mcp = FastMCP("deemon")


# ── Bitrate helpers ────────────────────────────────────────────────────
# Deemon CLI expects "128", "320", or "FLAC" (not the numeric key 1/3/9).
# Map consistently everywhere a bitrate is accepted.

_BITRATE_MAP: dict[int, str] = {1: "128", 3: "320", 9: "FLAC"}


def _bitrate_str(code: int) -> str:
    return _BITRATE_MAP.get(code, "320")


def _bitrate_code(label: str) -> int:
    """Reverse lookup — return the numeric key for a bitrate label."""
    rev = {v: k for k, v in _BITRATE_MAP.items()}
    return rev.get(label, 3)


def pick_best_album(releases: list) -> dict:
    """Pick the best album version, preferring original releases over remasters/reissues."""
    albums = [r for r in releases if r.get('record_type') == 'album']
    if not albums:
        albums = [r for r in releases if r.get('record_type') in ('album', 'ep', 'single')]
    if not albums:
        albums = releases
    if len(albums) == 1:
        return albums[0]
    non_remastered = [
        a for a in albums
        if 'remaster' not in a.get('title', '').lower()
        and 'reissue' not in a.get('title', '').lower()
        and 'deluxe' not in a.get('title', '').lower()
        and 'expanded' not in a.get('title', '').lower()
        and 'bonus' not in a.get('title', '').lower()
    ]
    if non_remastered:
        non_remastered.sort(key=lambda a: a.get('release_date', ''))
        return non_remastered[0]
    albums.sort(key=lambda a: (a.get('release_date', ''), len(a.get('title', ''))))
    return albums[0]


def _build_download_path() -> str:
    """Resolve the effective download directory from deemon/deemix config."""
    cfg = DeemonConfig()
    path = cfg.download_path()
    if path:
        return path
    # Fallback: try deemix config
    import json as _json
    deemix_path = Path.home() / "Library" / "Application Support" / "deemix" / "config.json"
    if deemix_path.exists():
        try:
            data = _json.loads(deemix_path.read_text())
            dl = data.get("downloadLocation", "")
            if dl:
                return dl
        except Exception:
            pass
    return str(Path.home() / "Downloads")


@mcp.tool()
def search_artists(query: str, limit: int = 10) -> str:
    """Search for artists on Deezer. Returns a JSON list of matching artists."""
    try:
        platform_api = api.PlatformAPI()
        results = platform_api.search_artist(query, limit)
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_artist_albums(artist_id: int) -> str:
    """Get all albums/releases for a Deezer artist ID. Returns JSON."""
    try:
        platform_api = api.PlatformAPI()
        artist = platform_api.get_artist_by_id(int(artist_id))
        if not artist:
            return json.dumps({"error": "Artist not found"})
        query = {"artist_id": artist['id'], "artist_name": artist['name']}
        results = platform_api.get_artist_albums(query)
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_album_info(album_id: int) -> str:
    """Get details for a specific Deezer album ID. Returns JSON."""
    try:
        platform_api = api.PlatformAPI()
        album = platform_api.get_album(int(album_id))
        if not album:
            return json.dumps({"error": "Album not found"})
        return json.dumps(album)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def download_url(url: str) -> str:
    """Download an album/track/playlist from a Deezer or Spotify URL."""
    try:
        resolution = InputResolver().resolve(url)
        if resolution.status is not ResolutionStatus.RESOLVED:
            return json.dumps(resolution.to_dict())
        dl = Download()
        resolved_urls = [item.deezer_url for item in resolution.items]
        dl.download(None, None, None, resolved_urls, None, None, None, None)
        return json.dumps({
            "status": "success",
            "input": url,
            "resolved": resolved_urls,
            "message": f"Download started for {len(resolved_urls)} resolved item(s)",
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def download_album(album_id: int) -> str:
    """Download a Deezer album by its ID."""
    url = f"https://www.deezer.com/album/{album_id}"
    return download_url(url)


@mcp.tool()
def download_album_by_name(artist_name: str, album_name: str) -> str:
    """Search for an artist, find the best matching album, and download it.
    Prefers original releases over remasters/reissues/deluxe editions."""
    try:
        platform_api = api.PlatformAPI()
        search_results = platform_api.search_artist(artist_name, 5)
        results = search_results.get('results', [])
        if not results:
            return json.dumps({"error": f"No artists found for: {artist_name}"})
        exact = [r for r in results if r['name'].lower() == artist_name.lower()]
        artist = exact[0] if exact else results[0]
        artist_tmp = {'artist_id': artist['id'], 'artist_name': artist['name']}
        albums_result = platform_api.get_artist_albums(artist_tmp)
        releases = albums_result.get('releases', [])
        if not releases:
            return json.dumps({"error": f"No releases found for {artist_name}"})
        normalized_query = album_name.lower().strip()
        matches = []
        for release in releases:
            title = release.get('title', '').lower()
            if normalized_query == title or title.startswith(normalized_query + ' ') or title.startswith(normalized_query + '(') or title.startswith(normalized_query + '-'):
                matches.append(release)
            elif f' {normalized_query} ' in f' {title} ' or f'({normalized_query})' in title or f'-{normalized_query}' in title:
                matches.append(release)
        if not matches:
            for release in releases:
                title = release.get('title', '').lower()
                if normalized_query in title:
                    matches.append(release)
        if not matches:
            return json.dumps({"error": f"Album '{album_name}' not found for {artist_name}"})
        best = pick_best_album(matches)
        url = best.get('link') or f"https://www.deezer.com/album/{best['id']}"
        dl = Download()
        dl.download(None, None, None, [url], None, None, None, None)
        return json.dumps({
            "status": "success",
            "message": f"Download started for {artist['name']} - {best['title']}",
            "album_id": best['id'],
            "album_title": best['title'],
            "release_date": best.get('release_date')
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def download_track(track_id: int) -> str:
    """Download a Deezer track by its ID."""
    url = f"https://www.deezer.com/track/{track_id}"
    return download_url(url)


@mcp.tool()
def monitor_artist(artist_id: int) -> str:
    """Start monitoring a Deezer artist for new releases by ID."""
    try:
        monitor = Monitor()
        monitor.artist_ids([int(artist_id)])
        return json.dumps({"status": "success", "message": f"Artist {artist_id} added to monitoring"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_monitored_artists() -> str:
    """List all monitored artists and their metadata."""
    try:
        with Database() as db:
            artists = db.get_all_monitored_artists()
            return json.dumps(list(artists) if artists else [])
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_recent_releases(days: int = 30) -> str:
    """List recent new releases from monitored artists within the last N days."""
    try:
        with Database() as db:
            now = int(time.time())
            since = now - (days * 24 * 60 * 60)
            releases = db.show_new_releases(since, now)
            return json.dumps(list(releases) if releases else [])
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── New tools for agent-friendly operation ──────────────────────────


@mcp.tool()
def search_albums(query: str, limit: int = 10) -> str:
    """Search for albums on Deezer by name. Returns JSON list with id, title, artist."""
    try:
        platform_api = api.PlatformAPI()
        results = platform_api.search_album(query, limit)
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_track_info(track_id: int) -> str:
    """Get details for a specific Deezer track ID. Returns JSON with artist, album, title."""
    try:
        platform_api = api.PlatformAPI()
        track = platform_api.get_track(track_id)
        return json.dumps(track if track else {"error": "Track not found"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def download_artist_discography(
    artist_id: int,
    record_type: str = "all",
    bitrate: int = 3,
) -> str:
    """Download all releases for a Deezer artist by their artist ID.

    *record_type* controls which releases to grab: "all", "album", "ep", "single",
    or a comma-separated combination like "album,ep".
    *bitrate*: 1 = 128kbps, 3 = 320kbps, 9 = FLAC.
    Queues everything into one batch and processes it, avoiding the interactive menu.
    """
    try:
        platform_api = api.PlatformAPI()
        artist = platform_api.get_artist_by_id(int(artist_id))
        if not artist:
            return json.dumps({"error": f"Artist ID {artist_id} not found"})

        releases_data = platform_api.get_artist_albums(
            {"artist_id": artist["id"], "artist_name": artist["name"]}
        )
        releases = releases_data.get("releases", [])
        if not releases:
            return json.dumps({"error": f"No releases found for artist {artist['name']}"})

        # Filter by record type
        if record_type != "all":
            allowed = [r.strip() for r in record_type.split(",")]
            releases = [r for r in releases if r.get("record_type") in allowed]

        if not releases:
            return json.dumps({
                "error": f"No releases match record_type '{record_type}' for {artist['name']}"
            })

        # Queue each release using its Deezer URL (bypasses deemon's filtering)
        bitrate_label = _bitrate_str(bitrate)
        dl = Download()
        queued = []
        for r in releases:
            url = r.get("link") or f"https://www.deezer.com/album/{r['id']}"
            dl.download(None, None, None, [url], None, None, None, None, auto=False, bitrate=bitrate_label)
            queued.append({
                "id": r["id"],
                "title": r["title"],
                "record_type": r.get("record_type"),
                "release_date": r.get("release_date"),
            })

        # Process the full queue at once
        if dl.queue_list:
            dl.download_queue()
            return json.dumps({
                "status": "success",
                "artist": artist["name"],
                "artist_id": artist["id"],
                "queued": len(queued),
                "releases": queued,
                "bitrate": bitrate_label,
                "download_path": _build_download_path(),
            })
        else:
            return json.dumps({
                "status": "empty",
                "artist": artist["name"],
                "message": "No releases were queued (possibly already downloaded or filtered).",
            })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def download_artist_by_name(
    artist_name: str,
    record_type: str = "all",
    bitrate: int = 3,
) -> str:
    """Search for an artist by name and download their entire discography.

    Finds the best matching Deezer artist, then queues all their releases
    for download. *record_type*: "all", "album", "ep", "single", or "album,ep".
    *bitrate*: 1 = 128kbps, 3 = 320kbps, 9 = FLAC.
    """
    try:
        platform_api = api.PlatformAPI()
        search_results = platform_api.search_artist(artist_name, 5)
        results = search_results.get("results", [])
        if not results:
            return json.dumps({"error": f"No artists found for '{artist_name}'"})

        # Prefer exact match, else use first result
        exact = [r for r in results if r["name"].lower() == artist_name.lower()]
        artist = exact[0] if exact else results[0]

        # Delegate to discography download
        return download_artist_discography(artist["id"], record_type, bitrate)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def download_album_with_fallback(
    artist_name: str,
    album_name: str,
    bitrate: int = 3,
    fallback_bitrate: int = 1,
) -> str:
    """Download an album; retries failed tracks at a lower bitrate.

    Downloads *album_name* by *artist_name* at *bitrate* (default 320kbps).
    If any tracks fail, retries those at *fallback_bitrate* (default 128kbps).
    Returns a report of which tracks needed fallback.
    """
    import logging as _logging

    try:
        platform_api = api.PlatformAPI()
        search_results = platform_api.search_artist(artist_name, 5)
        results = search_results.get("results", [])
        if not results:
            return json.dumps({"error": f"No artists found for: {artist_name}"})

        exact = [r for r in results if r["name"].lower() == artist_name.lower()]
        artist = exact[0] if exact else results[0]
        artist_tmp = {"artist_id": artist["id"], "artist_name": artist["name"]}
        albums_result = platform_api.get_artist_albums(artist_tmp)
        releases = albums_result.get("releases", [])

        if not releases:
            return json.dumps({"error": f"No releases found for {artist_name}"})

        matched = [r for r in releases if album_name.lower() in r.get("title", "").lower()]
        if not matched:
            return json.dumps({
                "error": f"Album '{album_name}' not found for {artist_name}",
                "available": [r["title"] for r in releases],
            })

        best = pick_best_album(matched)
        url = best.get("link") or f"https://www.deezer.com/album/{best['id']}"

        bitrate_label = _bitrate_str(bitrate)
        fallback_label = _bitrate_str(fallback_bitrate) if fallback_bitrate != bitrate else None

        # ── Capture deemon's own logger output ────────────────────
        deemon_logger = _logging.getLogger("deemon")
        orig_level = deemon_logger.level
        deemon_logger.setLevel(_logging.INFO)
        log_capture = io.StringIO()
        handler = _logging.StreamHandler(log_capture)
        handler.setFormatter(_logging.Formatter("%(message)s"))
        deemon_logger.addHandler(handler)

        try:
            # First attempt at requested bitrate
            dl = Download()
            dl.bitrate = bitrate_label
            dl.download(None, None, None, [url], None, None, None, None)
        finally:
            deemon_logger.removeHandler(handler)
            deemon_logger.setLevel(orig_level)

        log_text = log_capture.getvalue()
        failed_tracks = []
        for line in log_text.splitlines():
            m = re.search(r"Downloading:\s*(.*?)\.\.\.\s*failed", line, re.IGNORECASE)
            if m:
                failed_tracks.append(m.group(1).strip())

        fallback_used = False
        fallback_failed = []
        if failed_tracks and fallback_bitrate != bitrate:
            fallback_used = True
            # Retry the full album at the fallback bitrate; deemon will
            # overwrite/re-download those tracks.
            deemon_logger.setLevel(_logging.INFO)
            handler2 = _logging.StreamHandler(io.StringIO())
            handler2.setFormatter(_logging.Formatter("%(message)s"))
            deemon_logger.addHandler(handler2)
            try:
                dl2 = Download()
                dl2.bitrate = fallback_label
                dl2.download(None, None, None, [url], None, None, None, None)
            finally:
                deemon_logger.removeHandler(handler2)
                deemon_logger.setLevel(orig_level)

            fallback_log = handler2.stream.getvalue()
            for line in fallback_log.splitlines():
                m = re.search(r"Downloading:\s*(.*?)\.\.\.\s*failed", line, re.IGNORECASE)
                if m:
                    fallback_failed.append(m.group(1).strip())

        return json.dumps({
            "status": "success",
            "artist": artist["name"],
            "album": best["title"],
            "album_id": best["id"],
            "bitrate": bitrate_label,
            "failed_tracks": failed_tracks,
            "fallback_attempted": fallback_used,
            "fallback_bitrate": fallback_label if fallback_used else None,
            "fallback_still_failed": fallback_failed if fallback_failed else None,
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_download_path() -> str:
    """Return the configured download/staging directory where deemon places files."""
    return json.dumps({"download_path": _build_download_path()})


@mcp.tool()
def get_deemon_config() -> str:
    """Return current deemon configuration (bitrate, download path, record type, ARL status)."""
    try:
        cfg = DeemonConfig()
        import json as _json
        arl = cfg.arl()
        has_arl = bool(arl)
        # Check if deemix ARL is available as fallback
        deemix_arl_path = Path.home() / "Library" / "Application Support" / "deemix" / "login.json"
        if not has_arl and deemix_arl_path.exists():
            try:
                data = _json.loads(deemix_arl_path.read_text())
                if data.get("arl"):
                    has_arl = True
            except Exception:
                pass

        return json.dumps({
            "bitrate": cfg.bitrate(),
            "record_type": cfg.record_type(),
            "download_path": _build_download_path(),
            "arl_configured": has_arl,
            "profile_id": cfg.profile_id(),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def main():
    mcp.run()


if __name__ == "__main__":
    main()
