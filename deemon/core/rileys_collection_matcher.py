#!/usr/bin/env python3
"""
Collection Matcher - Deduplication Module for Spotify Toolkit

This module scans the local music collection and matches album metadata
against Spotify album data to identify albums already in the collection.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import unicodedata


def load_collection_path() -> Path:
    """Load audio library path from credentials.json or use default."""
    default_path = Path("/Volumes/Eksternal/Audio")
    config_path = Path.home() / ".config" / "deemixkit" / "credentials.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                configured_path = config.get('paths', {}).get('audio_library')
                if configured_path:
                    return Path(configured_path)
        except Exception:
            pass
    
    return default_path


class CollectionMatcher:
    """Handles matching Spotify albums against local music collection."""
    
    def __init__(self, collection_path: str = None):
        """
        Initialize the collection matcher.
        
        Args:
            collection_path: Path to the local music collection (optional, loads from config if not provided)
        """
        if collection_path is None:
            collection_path = str(load_collection_path())
        self.collection_path = Path(collection_path)
        self.collection_cache = {}
        self._build_collection_index()
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison by:
        - Converting to lowercase
        - Removing diacritics/accents
        - Removing edition/remaster/version text
        - Removing special characters
        - Removing extra whitespace
        - Removing common words that might differ (the, a, an)
        
        Args:
            text: Input text
            
        Returns:
            str: Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove diacritics/accents
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Remove everything in parentheses or brackets (often contains edition info)
        # Examples: (Remastered), (Full Dynamic Range Edition), [Deluxe], etc.
        text = re.sub(r'\s*[\(\[\{]([^\)\]\}]*)[\)\]\}]\s*', ' ', text)
        
        # Remove "+" and everything after it (common in compilations/demos)
        # Examples: "Album + Demo", "Album + EP", etc.
        text = re.sub(r'\s*\+.*$', '', text)
        
        # Remove ellipsis and trailing dots
        text = re.sub(r'\.{2,}$', '', text)
        text = re.sub(r'\.$', '', text)
        
        # Remove common articles and possessives at the start
        text = re.sub(r'^(the|a|an)\s+', '', text)
        
        # Remove apostrophes and possessives
        text = re.sub(r"'s?\b", '', text)
        
        # Remove special characters and punctuation, keep only alphanumeric and spaces
        text = re.sub(r'[^\w\s]', '', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common edition/version keywords that might not have been in parentheses
        edition_keywords = [
            'remaster', 'remastered', 'edition', 'deluxe', 'bonus', 'expanded',
            'anniversary', 'reissue', 'special', 'limited', 'collectors', 'collector',
            'extended', 'version', 'vol', 'volume', 'disc', 'cd', 'lp', 'ep',
            'digital', 'vinyl', 'anniversary', 'explicit', 'clean', 'instrumental',
            'live', 'acoustic', 'unplugged', 'demo', 'bootleg', 'rerecorded',
            'redux', 'revisited', 'enhanced', 'super', 'ultimate', 'definitive',
            'complete', 'compiled', 'best', 'greatest', 'hits', 'full', 'dynamic',
            'range', 'hd', 'hq', 'hi res', 'highres', 'flac', 'wav', 'mp3'
        ]
        
        # Build regex pattern to remove these keywords and anything after them
        pattern = r'\s+(' + '|'.join(edition_keywords) + r')\b.*$'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Also remove year patterns (YYYY) that might be at the end
        text = re.sub(r'\s+\d{4}\s*$', '', text)
        
        return text.strip()
    
    def _extract_album_info_from_folder(self, folder_name: str) -> Tuple[str, str]:
        """
        Extract year and album name from folder name.
        Expected format: "YYYY - Album Name" or just "Album Name"
        
        Args:
            folder_name: Name of the album folder
            
        Returns:
            Tuple[str, str]: (year, album_name)
        """
        # Try to match "YYYY - Album Name" format
        match = re.match(r'^(\d{4})\s*-\s*(.+)$', folder_name)
        if match:
            year = match.group(1)
            album_name = match.group(2).strip()
            return year, album_name
        
        # If no year prefix, return empty year and full folder name
        return "", folder_name.strip()
    
    def _extract_info_from_filename(self, filename: str, fallback_artist: str, fallback_album: str) -> Tuple[str, str]:
        """
        Extract artist and album information from an audio filename.
        Common patterns:
        - "Artist - Album - Track.mp3"
        - "Artist - Track.mp3"
        - "Track Number - Artist - Track.mp3"
        - "Track Number. Track Name.mp3"
        
        Args:
            filename: The audio filename (without extension)
            fallback_artist: Artist name from folder structure (fallback)
            fallback_album: Album name from folder structure (fallback)
            
        Returns:
            Tuple[str, str]: (artist, album) - uses fallback if can't extract from filename
        """
        # Remove common track number prefixes (e.g., "01 -", "1.", "01.")
        filename = re.sub(r'^\d{1,3}[\s\.\-]+', '', filename)
        
        # Try pattern: "Artist - Album - Track"
        match = re.match(r'^([^-]+)\s*-\s*([^-]+)\s*-\s*(.+)$', filename)
        if match:
            artist = match.group(1).strip()
            album = match.group(2).strip()
            return artist, album
        
        # Try pattern: "Artist - Track" (use folder album name)
        match = re.match(r'^([^-]+)\s*-\s*(.+)$', filename)
        if match:
            artist = match.group(1).strip()
            return artist, fallback_album
        
        # If no pattern matched, use folder-based info
        return fallback_artist, fallback_album
    
    def _build_collection_index(self):
        """
        Scan the music collection and build an index of artists and albums.
        Scans both folder names AND audio files for maximum matching accuracy.
        Structure: {normalized_artist: {normalized_album: (original_artist, original_album, path)}}
        """
        print(f"Scanning music collection at: {self.collection_path}")
        
        if not self.collection_path.exists():
            print(f"Warning: Collection path does not exist: {self.collection_path}")
            return
        
        album_count = 0
        audio_extensions = {'.mp3', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.wav', '.ape', '.opus'}
        
        # Iterate through genre folders
        for genre_dir in self.collection_path.iterdir():
            if not genre_dir.is_dir():
                continue
            
            # Skip hidden folders and files
            if genre_dir.name.startswith('.'):
                continue
            
            # Iterate through alphabetical folders
            for alpha_dir in genre_dir.iterdir():
                if not alpha_dir.is_dir():
                    continue
                
                if alpha_dir.name.startswith('.'):
                    continue
                
                # Iterate through artist folders
                for artist_dir in alpha_dir.iterdir():
                    if not artist_dir.is_dir():
                        continue
                    
                    if artist_dir.name.startswith('.'):
                        continue
                    
                    artist_name = artist_dir.name
                    normalized_artist = self._normalize_text(artist_name)
                    
                    if normalized_artist not in self.collection_cache:
                        self.collection_cache[normalized_artist] = {}
                    
                    # Iterate through album folders
                    for album_dir in artist_dir.iterdir():
                        if not album_dir.is_dir():
                            continue
                        
                        if album_dir.name.startswith('.'):
                            continue
                        
                        # Extract album info from folder name
                        year, album_name = self._extract_album_info_from_folder(album_dir.name)
                        normalized_album = self._normalize_text(album_name)
                        
                        # Store folder-based info in cache
                        self.collection_cache[normalized_artist][normalized_album] = {
                            'artist': artist_name,
                            'album': album_name,
                            'year': year,
                            'path': str(album_dir),
                            'genre': genre_dir.name
                        }
                        
                        album_count += 1
                        
                        # ALSO scan audio files in this album folder for additional matching
                        # This catches albums where the folder name doesn't match perfectly
                        for audio_file in album_dir.iterdir():
                            if audio_file.is_file() and audio_file.suffix.lower() in audio_extensions:
                                # Try to extract artist and album from filename
                                # Common patterns: "Artist - Album - Track.mp3", "Artist - Track.mp3", etc.
                                file_artist, file_album = self._extract_info_from_filename(audio_file.stem, artist_name, album_name)
                                
                                if file_artist and file_album:
                                    norm_file_artist = self._normalize_text(file_artist)
                                    norm_file_album = self._normalize_text(file_album)
                                    
                                    # Add this as an additional entry if different from folder
                                    if norm_file_artist not in self.collection_cache:
                                        self.collection_cache[norm_file_artist] = {}
                                    
                                    if norm_file_album not in self.collection_cache[norm_file_artist]:
                                        self.collection_cache[norm_file_artist][norm_file_album] = {
                                            'artist': file_artist,
                                            'album': file_album,
                                            'year': year,
                                            'path': str(album_dir),
                                            'genre': genre_dir.name
                                        }
                                
                                # Only need to check one file per album
                                break
        
        print(f"Found {album_count} albums in collection from {len(self.collection_cache)} artists")
    
    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.85) -> bool:
        """
        Check if two strings are similar enough using fuzzy matching.
        Handles plurals, spelling variations, and minor differences.
        
        Args:
            str1: First string
            str2: Second string
            threshold: Similarity threshold (0-1)
            
        Returns:
            bool: True if strings are similar enough
        """
        if not str1 or not str2:
            return False
        
        # Exact match
        if str1 == str2:
            return True
        
        # Check if one contains the other (handles plurals, small additions)
        if str1 in str2 or str2 in str1:
            # Make sure they're at least 70% similar in length
            len_ratio = min(len(str1), len(str2)) / max(len(str1), len(str2))
            if len_ratio >= 0.70:
                return True
        
        # Calculate Levenshtein distance ratio
        len1, len2 = len(str1), len(str2)
        if len1 == 0 or len2 == 0:
            return False
        
        # If lengths are too different, not a match
        if abs(len1 - len2) > max(len1, len2) * 0.3:
            return False
        
        # Create distance matrix
        d = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            d[i][0] = i
        for j in range(len2 + 1):
            d[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if str1[i-1] == str2[j-1] else 1
                d[i][j] = min(
                    d[i-1][j] + 1,      # deletion
                    d[i][j-1] + 1,      # insertion
                    d[i-1][j-1] + cost  # substitution
                )
        
        distance = d[len1][len2]
        max_len = max(len1, len2)
        similarity = 1 - (distance / max_len)
        
        return similarity >= threshold
    
    def is_album_in_collection(self, artist_name: str, album_name: str, year: str = None) -> bool:
        """
        Check if an album is already in the collection.
        Uses fuzzy matching to handle spelling variations, plurals, and minor differences.
        
        Args:
            artist_name: Name of the artist
            album_name: Name of the album
            year: Optional release year for additional matching
            
        Returns:
            bool: True if album is in collection, False otherwise
        """
        normalized_artist = self._normalize_text(artist_name)
        normalized_album = self._normalize_text(album_name)
        
        # Check exact artist match
        if normalized_artist in self.collection_cache:
            # Check exact album match
            if normalized_album in self.collection_cache[normalized_artist]:
                return True
            
            # Try fuzzy match on album names for this exact artist
            for cached_album in self.collection_cache[normalized_artist].keys():
                if self._fuzzy_match(normalized_album, cached_album, threshold=0.85):
                    return True
        
        # Try fuzzy artist match  
        for cached_artist in self.collection_cache.keys():
            if self._fuzzy_match(normalized_artist, cached_artist, threshold=0.90):
                # Found similar artist, check for exact album match
                if normalized_album in self.collection_cache[cached_artist]:
                    return True
                
                # Try fuzzy album match too
                for cached_album in self.collection_cache[cached_artist].keys():
                    if self._fuzzy_match(normalized_album, cached_album, threshold=0.85):
                        return True
        
        return False
    
    def get_album_info(self, artist_name: str, album_name: str) -> Dict:
        """
        Get information about an album in the collection.
        
        Args:
            artist_name: Name of the artist
            album_name: Name of the album
            
        Returns:
            Dict: Album information or None if not found
        """
        normalized_artist = self._normalize_text(artist_name)
        normalized_album = self._normalize_text(album_name)
        
        if normalized_artist in self.collection_cache:
            if normalized_album in self.collection_cache[normalized_artist]:
                return self.collection_cache[normalized_artist][normalized_album]
        
        return None
    
    def filter_existing_albums(self, albums_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter a list of album data, separating existing and new albums.
        
        Args:
            albums_data: List of album dictionaries with 'artist' and 'album' keys
            
        Returns:
            Tuple[List[Dict], List[Dict]]: (new_albums, existing_albums)
        """
        new_albums = []
        existing_albums = []
        
        for album_data in albums_data:
            artist = album_data.get('artist', '')
            album = album_data.get('album', '')
            year = album_data.get('year', '')
            
            if self.is_album_in_collection(artist, album, year):
                existing_albums.append(album_data)
            else:
                new_albums.append(album_data)
        
        return new_albums, existing_albums
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the collection.
        
        Returns:
            Dict: Statistics including artist count, album count, etc.
        """
        total_albums = sum(len(albums) for albums in self.collection_cache.values())
        total_artists = len(self.collection_cache)
        
        # Count albums by genre
        genre_counts = {}
        for artist_albums in self.collection_cache.values():
            for album_info in artist_albums.values():
                genre = album_info.get('genre', 'Unknown')
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        return {
            'total_artists': total_artists,
            'total_albums': total_albums,
            'genres': genre_counts
        }


# Standalone test function
def test_matcher():
    """Test the collection matcher with sample data."""
    matcher = CollectionMatcher()
    
    # Print stats
    stats = matcher.get_collection_stats()
    print("\nCollection Statistics:")
    print(f"Total Artists: {stats['total_artists']}")
    print(f"Total Albums: {stats['total_albums']}")
    print("\nAlbums by Genre:")
    for genre, count in sorted(stats['genres'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {genre}: {count}")
    
    # Test some sample matches
    print("\n--- Testing Sample Matches ---")
    
    # Test exact match
    test_cases = [
        ("A Tribe Called Quest", "The Low End Theory"),
        ("Eminem", "The Marshall Mathers LP"),
        ("Metallica", "Master of Puppets"),
        ("Unknown Artist", "Unknown Album"),  # Should not match
    ]
    
    for artist, album in test_cases:
        result = matcher.is_album_in_collection(artist, album)
        print(f"{artist} - {album}: {'FOUND' if result else 'NOT FOUND'}")
        
        if result:
            info = matcher.get_album_info(artist, album)
            if info:
                print(f"  -> {info['artist']} - {info['album']} ({info['year']}) [{info['genre']}]")


if __name__ == "__main__":
    test_matcher()

