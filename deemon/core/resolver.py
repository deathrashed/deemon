from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from unidecode import unidecode


class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"
    INVALID = "invalid"
    ERROR = "error"


@dataclass(frozen=True)
class ResolvedItem:
    kind: str
    deezer_url: str
    title: str
    artist: str | None = None
    confidence: float = 1.0
    provenance: str = "deezer"


@dataclass(frozen=True)
class Resolution:
    status: ResolutionStatus
    input_value: str
    items: list[ResolvedItem] = field(default_factory=list)
    candidates: list[ResolvedItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "input": self.input_value,
            "resolved": [asdict(item) for item in self.items],
            "candidates": [asdict(item) for item in self.candidates],
            "warnings": self.warnings,
            "errors": self.errors,
        }


def _normalise(value: str) -> str:
    return " ".join("".join(char if char.isalnum() else " " for char in unidecode(value).lower()).split())


class InputResolver:
    def __init__(self, active_api=None, http_get=requests.get):
        if active_api is None:
            from deemon.core.api import PlatformAPI
            active_api = PlatformAPI()
        self.api = active_api
        self.http_get = http_get

    def resolve(self, value: str) -> Resolution:
        value = value.strip()
        if not value:
            return Resolution(ResolutionStatus.INVALID, value, errors=["Input is empty."])
        if Path(value).expanduser().is_file():
            return Resolution(ResolutionStatus.UNSUPPORTED, value, errors=["File intake is handled by the existing --artist-file, --album-file, and --track-file commands."])
        parsed = urlparse(value)
        host = parsed.netloc.lower()
        if "deezer.com" in host:
            return self._resolve_deezer_url(value)
        if "spotify.com" in host or value.startswith("spotify:"):
            return self._resolve_spotify_url(value)
        if " - " in value:
            artist, album = value.split(" - ", 1)
            return self._resolve_artist_album(artist, album, value)
        return self._resolve_artist(value)

    def _resolve_deezer_url(self, value: str) -> Resolution:
        parts = [part for part in urlparse(value).path.split("/") if part]
        for index, part in enumerate(parts[:-1]):
            if part in {"artist", "album", "track", "playlist"} and parts[index + 1].isdigit():
                entity_id = parts[index + 1]
                item = ResolvedItem(part, f"https://www.deezer.com/{part}/{entity_id}", f"Deezer {part} {entity_id}")
                return Resolution(ResolutionStatus.RESOLVED, value, items=[item])
        return Resolution(ResolutionStatus.INVALID, value, errors=["Expected a Deezer artist, album, track, or playlist URL with a numeric ID."])

    def _resolve_artist(self, value: str) -> Resolution:
        search_result = self.api.search_artist(value, limit=5)
        results = search_result.get("results", []) if isinstance(search_result, dict) else []
        exact = [artist for artist in results if _normalise(artist["name"]) == _normalise(value)]
        choices = exact or results
        candidates = [ResolvedItem("artist", f"https://www.deezer.com/artist/{artist['id']}", artist["name"], artist["name"], 1.0 if artist in exact else 0.6, "deezer-search") for artist in choices]
        if len(candidates) == 1:
            return Resolution(ResolutionStatus.RESOLVED, value, items=candidates)
        if candidates:
            return Resolution(ResolutionStatus.AMBIGUOUS, value, candidates=candidates, errors=["More than one Deezer artist matches this input."])
        return Resolution(ResolutionStatus.ERROR, value, errors=["No Deezer artist matched this input."])

    def _resolve_artist_album(self, artist_name: str, album_name: str, input_value: str) -> Resolution:
        matches: list[ResolvedItem] = []
        search_result = self.api.search_artist(artist_name, limit=5)
        artists = search_result.get("results", []) if isinstance(search_result, dict) else []
        for artist in artists:
            album_result = self.api.get_artist_albums({"artist_id": artist["id"], "artist_name": artist["name"]})
            releases = album_result.get("releases", []) if isinstance(album_result, dict) else []
            for album in releases:
                if _normalise(album.get("title", "")) == _normalise(album_name):
                    matches.append(ResolvedItem("album", f"https://www.deezer.com/album/{album['id']}", album["title"], artist["name"], 1.0, "deezer-search"))
        if len(matches) == 1:
            return Resolution(ResolutionStatus.RESOLVED, input_value, items=matches)
        if matches:
            return Resolution(ResolutionStatus.AMBIGUOUS, input_value, candidates=matches, errors=["More than one Deezer album exactly matches this artist and title."])
        return Resolution(ResolutionStatus.ERROR, input_value, errors=["No exact Deezer album matched this artist and title."])

    def _resolve_spotify_url(self, value: str) -> Resolution:
        kind = next((part for part in ("artist", "album", "track", "playlist") if f"/{part}/" in value), None)
        if kind == "playlist":
            return Resolution(ResolutionStatus.UNSUPPORTED, value, errors=["Spotify playlists require configured Spotify API access."])
        if kind is None:
            return Resolution(ResolutionStatus.INVALID, value, errors=["Expected a Spotify artist, album, track, or playlist URL."])
        try:
            response = self.http_get("https://open.spotify.com/oembed", params={"url": value}, timeout=10)
            response.raise_for_status()
            title = response.json().get("title", "").strip()
        except requests.RequestException as exc:
            return Resolution(ResolutionStatus.ERROR, value, errors=[f"Spotify metadata lookup failed: {exc}"])
        if not title:
            return Resolution(ResolutionStatus.ERROR, value, errors=["Spotify metadata lookup did not return a title."])
        artist_name = None
        if kind in {"artist", "album"}:
            try:
                embed_url = value.replace("open.spotify.com/", "open.spotify.com/embed/", 1)
                embed_response = self.http_get(embed_url, timeout=10)
                embed_response.raise_for_status()
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', embed_response.text)
                entity = json.loads(match.group(1))["props"]["pageProps"]["state"]["data"]["entity"] if match else {}
                title = entity.get("title") or entity.get("name") or title
                artist_name = entity.get("subtitle")
            except (KeyError, TypeError, ValueError, requests.RequestException):
                pass
        if kind == "artist":
            search_result = self.api.search_artist(title, limit=5)
            artists = search_result.get("results", []) if isinstance(search_result, dict) else []
            exact = [artist for artist in artists if _normalise(artist.get("name", "")) == _normalise(title)]
            candidates = [ResolvedItem("artist", f"https://www.deezer.com/artist/{artist['id']}", artist["name"], artist["name"], 1.0 if artist in exact else 0.6, "spotify-public-embed") for artist in exact or artists]
            if len(exact) == 1:
                return Resolution(ResolutionStatus.RESOLVED, value, items=candidates)
            if candidates:
                return Resolution(ResolutionStatus.AMBIGUOUS, value, candidates=candidates, errors=["Deezer artist match was not unique enough to download automatically."])
            return Resolution(ResolutionStatus.ERROR, value, errors=["No Deezer artist was found for Spotify metadata."])
        search_result = self.api.search_album(title, limit=5)
        albums = search_result.get("results", []) if isinstance(search_result, dict) else []
        exact = [album for album in albums if _normalise(album.get("title", "")) == _normalise(title) and (not artist_name or _normalise(album.get("artist", {}).get("name", "")) == _normalise(artist_name))]
        candidates = [ResolvedItem("album", f"https://www.deezer.com/album/{album['id']}", album["title"], album.get("artist", {}).get("name"), 0.95 if album in exact else 0.5, "spotify-public-embed" if artist_name else "spotify-oembed") for album in exact or albums]
        if len(exact) == 1:
            return Resolution(ResolutionStatus.RESOLVED, value, items=candidates)
        if candidates:
            return Resolution(ResolutionStatus.AMBIGUOUS, value, candidates=candidates, warnings=["Spotify fallback could not identify a unique Deezer match."], errors=["Deezer match was not unique enough to download automatically."])
        return Resolution(ResolutionStatus.ERROR, value, errors=["No Deezer match was found for Spotify metadata."])
