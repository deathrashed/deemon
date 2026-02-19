import logging
import os
import sys

import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tqdm import tqdm

import deemix.errors
import deezer
from deezer import errors
import plexapi.exceptions
from plexapi.server import PlexServer

from deemon import utils
from deemon.core import dmi, db, api, common
from deemon.core.config import Config as config
from deemon.utils import ui, dataprocessor, startup, dates

logger = logging.getLogger(__name__)

COLOR_YELLOW = "\033[33m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_RED = "\033[31m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"


class QueueItem:
    # TODO - Accept new playlist tracks for output/alerts
    def __init__(self, artist=None, album=None, track=None, playlist=None,
                 bitrate: str = None, download_path: str = None,
                 release_full: dict = None):
        self.artist_name = None
        self.album_id = None
        self.album_title = None
        self.track_id = None
        self.track_title = None
        self.url = None
        self.playlist_title = None
        self.bitrate = bitrate or config.bitrate()
        self.download_path = download_path or config.download_path()
        self.release_type = None
        
        if release_full:
            self.artist_name = release_full['artist_name']
            self.album_id = release_full['id']
            self.album_title = release_full['title']
            self.url = f"https://www.deezer.com/album/{self.album_id}"
            self.release_type = release_full['record_type']
            self.bitrate = release_full['bitrate']
            self.download_path = release_full['download_path']

        if artist:
            try:
                self.artist_name = artist["artist_name"]
            except KeyError:
                self.artist_name = artist["name"]
            if not album and not track:
                self.url = artist["link"]

        if album:
            if not artist:
                self.artist_name = album["artist"]["name"]
            self.album_id = album["id"]
            self.album_title = album["title"]
            try:
                self.url = album["link"]
            except KeyError:
                self.url = f"https://www.deezer.com/album/{album['id']}"

        if track:
            self.artist_name = track["artist"]["name"]
            self.track_id = track["id"]
            self.track_title = track["title"]
            self.url = f"https://deezer.com/track/{self.track_id}"

        if playlist:
            try:
                self.url = playlist["link"]
            except KeyError:
                logger.debug("DEPRECATED dict key: playlist['url'] should not be used in favor of playlist['link']")
                self.url = playlist.get("url", None)
            self.playlist_title = playlist["title"]


def get_deemix_bitrate(bitrate: str):
    for bitrate_id, bitrate_name in config.allowed_values('bitrate').items():
        if bitrate_name.lower() == bitrate.lower():
            logger.debug(f"Setting deemix bitrate to {str(bitrate_id)}")
            return bitrate_id


def get_plex_server():
    if (config.plex_baseurl() != "") and (config.plex_token() != ""):
        session = None
        if not config.plex_ssl_verify():
            requests.packages.urllib3.disable_warnings()
            session = requests.Session()
            session.verify = False
        try:
            print("Plex settings found, trying to connect (10s)... ", end="")
            plex_server = PlexServer(config.plex_baseurl(), config.plex_token(), timeout=10, session=session)
            print(" OK")
            return plex_server
        except Exception as e:
            print(" FAILED")
            logger.error("Error: Unable to reach Plex server, please refresh manually.")
            logger.debug(e)
            return False


def refresh_plex(plexobj):
    try:
        plexobj.library.section(config.plex_library()).update()
        logger.debug("Plex library refreshed successfully")
    except plexapi.exceptions.BadRequest as e:
        logger.error("Error occurred while refreshing your library. See logs for additional info.")
        logger.debug(f"Error during Plex refresh: {e}")
    except plexapi.exceptions.NotFound as e:
        logger.error("Error: Plex library not found. See logs for additional info.")
        logger.debug(f"Error during Plex refresh: {e}")


class Download:

    def __init__(self, active_api=None):
        super().__init__()
        self.api = active_api or api.PlatformAPI()
        self.dz = deezer.Deezer()
        self.di = dmi.DeemixInterface()
        self.queue_list = []
        self.db = db.Database()
        self.bitrate = None
        self.release_from = None
        self.release_to = None
        self.verbose = os.environ.get("VERBOSE")
        self.duplicate_id_count = 0

    def set_dates(self, from_date: str = None, to_date: str = None) -> None:
        """Set to/from dates to get while downloading"""
        if from_date:
            try:
                self.release_from = dates.str_to_datetime_obj(from_date)
            except ValueError as e:
                raise ValueError(f"Invalid date provided - {from_date}: {e}")
        if to_date:
            try:
                self.release_to = dates.str_to_datetime_obj(to_date)
            except ValueError as e:
                raise ValueError(f"Invalid date provided - {to_date}: {e}")



    def extract_playlist_albums(self, playlist_url):
        """Extract album IDs from a Spotify or Deezer playlist"""
        import re
        import time
        
        try:
            logger.info(f"Extracting albums from playlist...")
            
            if 'deezer.com/playlist/' in playlist_url:
                match = re.search(r'deezer\.com/playlist/(\d+)', playlist_url)
                if not match:
                    logger.error("Could not extract Deezer playlist ID")
                    return []
                
                playlist_id = match.group(1)
                dz = self.api.dz
                
                playlist_info = dz.api.get_playlist(playlist_id)
                playlist_name = playlist_info.get('title', 'Unknown Playlist')
                logger.info(f"Processing playlist: {playlist_name}")
                
                album_ids = set()
                url = f"/playlist/{playlist_id}/tracks"
                
                while url:
                    tracks_data = dz.api.get(url)
                    if 'data' not in tracks_data:
                        break
                    
                    for track in tracks_data['data']:
                        if track.get('album'):
                            album_id = track['album']['id']
                            album_ids.add(album_id)
                    
                    url = tracks_data.get('next')
                    if url:
                        time.sleep(0.2)
                
                logger.info(f"Found {len(album_ids)} unique albums in playlist")
                return list(album_ids)
            
            elif 'spotify.com/playlist/' in playlist_url:
                match = re.search(r'spotify.com/playlist/([a-zA-Z0-9]+)', playlist_url)
                if not match:
                    logger.error("Could not extract Spotify playlist ID")
                    return []
                
                playlist_id = match.group(1)
                
                try:
                    import deemix.utils.localpaths as localpaths
                except ImportError:
                    logger.error("deemix.utils.localpaths not available")
                    return []
                
                from pathlib import Path
                if config.deemix_path() == "":
                    deemix_config_dir = Path(localpaths.getConfigFolder())
                else:
                    deemix_config_dir = Path(config.deemix_path())
                
                spotify_config_dir = deemix_config_dir / 'spotify'
                spotify_config_file = spotify_config_dir / 'config.json'
                
                if not spotify_config_file.exists():
                    logger.error(f"Spotify config not found at {spotify_config_file}")
                    return []
                
                import json
                import base64
                with open(spotify_config_file, 'r') as f:
                    spotify_config = json.load(f)
                
                client_id = spotify_config.get('clientId')
                client_secret = spotify_config.get('clientSecret')
                
                if not client_id or not client_secret:
                    logger.error("Spotify credentials not configured")
                    return []
                
                credentials = f"{client_id}:{client_secret}"
                encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
                
                headers = {
                    'Authorization': f'Basic {encoded_credentials}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                data = {'grant_type': 'client_credentials'}
                
                response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data, timeout=10)
                response.raise_for_status()
                token_data = response.json()
                access_token = token_data.get('access_token')
                
                if not access_token:
                    logger.error("Failed to get Spotify access token")
                    return []
                
                headers = {'Authorization': f'Bearer {access_token}'}
                
                playlist_response = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}', headers=headers, timeout=10)
                playlist_response.raise_for_status()
                playlist_data = playlist_response.json()
                
                playlist_name = playlist_data.get('name', 'Unknown Playlist')
                logger.info(f"Processing playlist: {playlist_name}")
                
                dz = self.api.dz
                album_ids = set()
                url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
                
                while url:
                    tracks_response = requests.get(url, headers=headers, timeout=10)
                    tracks_response.raise_for_status()
                    tracks_data = tracks_response.json()
                
                    if 'items' not in tracks_data:
                        break
                
                    for item in tracks_data['items']:
                        try:
                            track = item.get('track')
                            if not track or not track.get('album'):
                                continue
                            
                            album = track['album']
                            spotify_album_id = album.get('id')
                            if not spotify_album_id:
                                continue
                            
                            album_response = requests.get(
                                f'https://api.spotify.com/v1/albums/{spotify_album_id}',
                                headers=headers,
                                timeout=10
                            )
                            album_response.raise_for_status()
                            album_data = album_response.json()
                            
                            artist_name = None
                            if album_data.get('artists'):
                                artist_name = album_data['artists'][0].get('name')
                            album_title = album_data.get('name')
                            external_ids = album_data.get('external_ids') or {}
                            upc = external_ids.get('upc')
                
                            resolved_id = None
                            if upc:
                                try:
                                    dz_album_response = requests.get(
                                        f'https://api.deezer.com/album/upc:{upc}',
                                        timeout=10
                                    )
                                    dz_album_response.raise_for_status()
                                    dz_album = dz_album_response.json()
                                    dz_album_id = dz_album.get('id')
                                    if dz_album_id:
                                        resolved_id = int(dz_album_id)
                                except Exception as e:
                                    logger.debug(f"Error during Deezer UPC lookup for Spotify album {spotify_album_id}: {e}")
                
                            if not resolved_id and artist_name and album_title:
                                try:
                                    query = f'artist:\"{artist_name}\" album:\"{album_title}\"'
                                    dz_search_response = requests.get(
                                        'https://api.deezer.com/search/album',
                                        params={'q': query},
                                        timeout=10
                                    )
                                    dz_search_response.raise_for_status()
                                    dz_data = dz_search_response.json()
                                    albums = dz_data.get('data') or []
                                    for candidate in albums:
                                        candidate_id = candidate.get('id')
                                        if not candidate_id:
                                            continue
                                        album_info = self.api.get_album(int(candidate_id))
                                        if album_info:
                                            resolved_id = int(candidate_id)
                                            break
                                except Exception as e:
                                    logger.debug(f"Error during Deezer album search for '{artist_name} - {album_title}': {e}")
                
                            if resolved_id:
                                album_ids.add(resolved_id)
                            else:
                                logger.debug(f"Could not resolve Deezer album for Spotify album '{artist_name} - {album_title}'")
                        except Exception as e:
                            logger.debug(f"Error processing Spotify playlist item: {e}")
                            continue
                
                    url = tracks_data.get('next')
                    if url:
                        time.sleep(0.1)
                
                logger.info(f"Found {len(album_ids)} unique albums in playlist")
                return list(album_ids)
            
            else:
                logger.error("Unknown playlist URL format")
                return []
        
        except Exception as e:
            logger.error(f"Error extracting playlist albums: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []

    def download_playlist(self, playlist_url: str, use_collection_matcher: bool = False):
        """Download albums from a playlist, optionally filtering with collection matcher"""
        album_ids = self.extract_playlist_albums(playlist_url)
        
        if not album_ids:
            logger.error(f"Could not extract albums from playlist: {playlist_url}")
            return
        
        logger.info(f"Found {len(album_ids)} unique albums in playlist")
        
        if use_collection_matcher:
            try:
                from deemon.core.rileys_collection_matcher import CollectionMatcher
                matcher = CollectionMatcher()
                
                filtered_albums = []
                skipped_albums = []
                
                for album_id in album_ids:
                    try:
                        album_info = self.api.get_album(album_id)
                        artist_name = album_info['artist']['name']
                        album_name = album_info['title']
                        
                        if matcher.is_album_in_collection(artist_name, album_name):
                            logger.info(f"Skipping (already in collection): {artist_name} - {album_name}")
                            skipped_albums.append((artist_name, album_name))
                        else:
                            filtered_albums.append(album_id)
                    except Exception as e:
                        logger.debug(f"Error checking album {album_id}: {e}")
                        filtered_albums.append(album_id)
                
                logger.info(f"Skipped {len(skipped_albums)} albums already in collection")
                logger.info(f"Downloading {len(filtered_albums)} new albums")
                album_ids = filtered_albums
            except ImportError:
                logger.warning("Collection matcher not available, downloading all albums")
        
        for album_id in album_ids:
            album_url = f"https://www.deezer.com/album/{album_id}"
            self.download(None, None, None, [album_url], None, None, None, None, auto=False)
        
        if len(self.queue_list) > 0:
            logger.info(f"{COLOR_GREEN}Queued {len(self.queue_list)} albums for download{COLOR_RESET}")
            self.download_queue()
        else:
            logger.info("No albums to download")

    # @performance.timeit
    def download_queue(self, queue_list: list = None):
        if queue_list:
            self.queue_list = queue_list

        if not self.di.login():
            logger.error(f"{COLOR_RED}Failed to login, aborting download...{COLOR_RESET}")
            return False

        if self.queue_list:
            plex = get_plex_server()
            print("")
            logger.info(f"{COLOR_CYAN}:: Sending {len(self.queue_list)} release(s) to deemix for download:{COLOR_RESET}")

            with open(startup.get_appdata_dir() / "queue.csv", "w", encoding="utf-8") as f:
                f.writelines(','.join([str(x) for x in vars(self.queue_list[0]).keys()]) + "\n")
                logger.debug(f"Writing queue to CSV file - {len(self.queue_list)} items in queue")
                for q in self.queue_list:
                    raw_values = [str(x) for x in vars(q).values()]
                    # TODO move this to shared function
                    for i, v in enumerate(raw_values):
                        if '"' in v:
                            raw_values[i] = v.replace('"', "'")
                        if ',' in v:
                            raw_values[i] = f'"{v}"'
                    f.writelines(','.join(raw_values) + "\n")
            logger.debug(f"Queue exported to {startup.get_appdata_dir()}/queue.csv")

            failed_count = []
            download_progress = tqdm(
                self.queue_list,
                total=len(self.queue_list),
                desc="Downloading releases...",
                ascii=" #",
                bar_format=ui.TQDM_FORMAT
            )
            for index, item in enumerate(download_progress):
                i = str(index + 1)
                t = str(len(download_progress))
                download_progress.set_description_str(f"Downloading release {i} of {t}...")
                dx_bitrate = get_deemix_bitrate(item.bitrate)
                if self.verbose == "true":
                    logger.debug(f"Processing queue item {vars(item)}")
                try:
                    if item.download_path:
                        download_path = item.download_path
                    else:
                        download_path = None

                    if item.artist_name:
                        if item.album_title:
                            logger.info(f"   > {item.artist_name} - {item.album_title}... ")
                            self.di.download_url([item.url], dx_bitrate, download_path)
                        else:
                            logger.info(f"   > {item.artist_name} - {item.track_title}... ")
                            self.di.download_url([item.url], dx_bitrate, download_path)
                    else:
                        logger.info(f"   > {item.playlist_title} (playlist)...")
                        self.di.download_url([item.url], dx_bitrate, download_path, override_deemix=True)
                except (deemix.errors.GenerationError, errors.WrongGeolocation) as e:
                    logger.debug(e)
                    failed_count.append([(item, "No tracks listed or unavailable in your country")])
                except Exception as e:
                    if item.artist_name and item.album_title:
                        logger.info(f"The following error occured while downloading {item.artist_name} - {item.album_title}: {e}")
                    elif item.artist_name and item.track_title:
                        logger.info(f"The following error occured while downloading {item.artist_name} - {item.track_title}: {e}")
                    else:
                        logger.info(f"The following error occured while downloading {item.playlist_title}: {e}")
                    pass


            failed_count = [x for x in failed_count if x]

            print("")
            if len(failed_count):
                logger.info(f"   [!] Downloads completed with {len(failed_count)} error(s):")
                with open(startup.get_appdata_dir() / "failed.csv", "w", encoding="utf-8") as f:
                    f.writelines(','.join([str(x) for x in vars(self.queue_list[0]).keys()]) + "\n")
                    for failed in failed_count:
                        try:
                            raw_values = [str(x) for x in vars(failed[0]).values()]
                        except TypeError as e:
                            print(f"Error reading from failed.csv. Entry that failed was either invalid or empty: {failed}")
                            logger.error(e)
                        else:
                            # TODO move this to shared function
                            for i, v in enumerate(raw_values):
                                if '"' in v:
                                    raw_values[i] = v.replace('"', "'")
                                if ',' in v:
                                    raw_values[i] = f'"{v}"'
                            f.writelines(','.join(raw_values) + "\n")
                            print(f"+ {failed[0].artist_name} - {failed[0].album_title} --- Reason: {failed[1]}")
                print("")
                logger.info(f":: Failed downloads exported to: {startup.get_appdata_dir()}/failed.csv")
            else:
                logger.info("   Downloads complete!")
            if plex and (config.plex_library() != ""):
                refresh_plex(plex)
        return True

    def download(self, artist, artist_id, album_id, url,
                 artist_file, track_file, album_file, track_id, auto=True, monitored=False):

        def filter_artist_by_record_type(artist):
            album_api = self.api.get_artist_albums(query={'artist_name': '', 'artist_id': artist['id']})
            filtered_albums = []
            for album in album_api['releases']:
                if (album['record_type'] == config.record_type()) or config.record_type() == "all":
                    album_date = dates.str_to_datetime_obj(album['release_date'])
                    if self.release_from and self.release_to:
                        if album_date > self.release_from and album_date < self.release_to:
                            filtered_albums.append(album)
                    elif self.release_from:
                        if album_date > self.release_from:
                            filtered_albums.append(album)
                    elif self.release_to:
                        if album_date < self.release_to:
                            filtered_albums.append(album)
                    else:
                        filtered_albums.append(album)
            return filtered_albums

        def get_api_result(artist=None, artist_id=None, album_id=None, track_id=None):
            if artist:
                try:
                    return self.api.search_artist(artist, limit=1)['results'][0]
                except (deezer.api.DataException, IndexError):
                    logger.error(f"Artist {artist} not found.")
            if artist_id:
                try:
                    return self.api.get_artist_by_id(artist_id)
                except (deezer.api.DataException, IndexError):
                    logger.error(f"Artist ID {artist_id} not found.")
            if album_id:
                try:
                    return self.api.get_album(album_id)
                except (deezer.api.DataException, IndexError):
                    logger.error(f"Album ID {album_id} not found.")
            if track_id:
                try:
                    return self.api.get_track(track_id)
                except (deezer.api.DataException, IndexError):
                    logger.error(f"Track ID {track_id} not found.")

        def queue_filtered_releases(api_object):
            filtered = filter_artist_by_record_type(api_object)
            filtered = common.exclude_filtered_versions(filtered)

            for album in filtered:
                if not queue_item_exists(album['id']):
                    logger.info(f"{COLOR_CYAN}[+] Queueing: {api_object['name']} - {album['title']}{COLOR_RESET}")
                    self.queue_list.append(QueueItem(artist=api_object, album=album))

        def queue_item_exists(i):
            for q in self.queue_list:
                if q.album_id == i:
                    logger.debug(f"Album ID {i} is already in queue")
                    self.duplicate_id_count += 1
                    return True
            return False
        
        def normalize_title(title: str) -> str:
            import re
            title = title.lower().strip()
            suffixes = [
                r'\s*-\s*remastered.*',
                r'\s*\(remastered.*\)',
                r'\s*\[remastered.*\]',
                r'\s*-\s*deluxe.*',
                r'\s*\(deluxe.*\)',
                r'\s*\[deluxe.*\]',
                r'\s*-\s*expanded.*',
                r'\s*\(expanded.*\)',
                r'\s*\[expanded.*\]',
                r'\s*-\s*bonus.*',
                r'\s*\(bonus.*\)',
                r'\s*\[bonus.*\]',
                r'\s*\[explicit\]',
                r'\s*\(explicit\)',
                r'\s*\(\d{4}\)',
                r'\s*\[\d{4}\]',
                r'\s*-\s*\d{4}.*',
                r'\s*\(\d{4}.*\)',
                r'\s*\[\d{4}.*\]',
                r'\s*-\s*reissue.*',
                r'\s*\(reissue.*\)',
                r'\s*\[reissue.*\]',
                r'\s*-\s*anniversary.*',
                r'\s*\(anniversary.*\)',
                r'\s*\[anniversary.*\]',
                r'\s*-\s*edition.*',
                r'\s*\(edition.*\)',
                r'\s*\[edition.*\]',
            ]
            for suffix in suffixes:
                title = re.sub(suffix, '', title, flags=re.IGNORECASE)
            return title.strip()
        
        def process_artist_by_name(name):
            if ' - ' in name:
                artist_part, album_part = [x.strip() for x in name.split(' - ', 1)]

                print(f"{COLOR_CYAN}Searching for '{COLOR_BOLD}{album_part}{COLOR_CYAN}' by '{COLOR_BOLD}{artist_part}{COLOR_CYAN}'...{COLOR_RESET}")

                artist_results = self.api.search_artist(artist_part, config.query_limit())
                if not artist_results['results']:
                    logger.warning(f"{COLOR_YELLOW}Artist not found:{COLOR_RESET} {artist_part}")
                    return

                normalized_query = normalize_title(album_part)
                found_album = None

                for artist in artist_results['results']:
                    artist_albums = self.api.get_artist_albums({'artist_id': artist['id'], 'artist_name': artist['name']})['releases']

                    # First try exact match (case insensitive)
                    for album in artist_albums:
                        album_title_lower = album['title'].lower()
                        album_part_lower = album_part.lower()
                        if album_part_lower in album_title_lower or album_title_lower in album_part_lower:
                            found_album = (artist, album)
                            break

                    if found_album:
                        break

                    # Then try normalized match
                    for album in artist_albums:
                        normalized_album = normalize_title(album['title'])
                        if normalized_query in normalized_album or normalized_album in normalized_query:
                            found_album = (artist, album)
                            break

                    if found_album:
                        break

                if found_album:
                    artist, album = found_album
                    print(f"{COLOR_GREEN}Album found:{COLOR_RESET} {artist['name']} - {album['title']}")
                    print(f"{COLOR_CYAN}Release Date:{COLOR_RESET} {dates.get_year(album['release_date'])}")
                    print(f"{COLOR_CYAN}Type:{COLOR_RESET} {album['record_type'].title()}")
                    print(f"{COLOR_CYAN}Starting download...{COLOR_RESET}\n")
                    if not queue_item_exists(album['id']):
                        self.queue_list.append(QueueItem(artist=artist, album=album))
                    return
                else:
                    logger.warning(f"{COLOR_YELLOW}Album '{album_part}' not found for artist '{artist_part}'{COLOR_RESET}")
                    logger.info(f"{COLOR_DIM}Tip: Use 'deemon search' and search for '{artist_part}' to see available albums{COLOR_RESET}")
                return

            artist_result = get_api_result(artist=name)
            if not artist_result:
                return
            logger.debug(f"Requested Artist: '{name}', Found: '{artist_result['name']}'")
            if artist_result:
                queue_filtered_releases(artist_result)

        def process_artist_by_id(i):
            artist_id_result = get_api_result(artist_id=i)
            if not artist_id_result:
                return
            logger.debug(f"Requested Artist ID: {i}, Found: {artist_id_result['name']}")
            if artist_id_result:
                queue_filtered_releases(artist_id_result)

        def process_album_by_id(i):
            logger.debug("Processing album by ID")
            album_id_result = get_api_result(album_id=i)
            if not album_id_result:
                logger.error(f"{COLOR_RED}   [!] Album ID {i} was not found - it may be geoblocked or unavailable{COLOR_RESET}")
                return
            logger.debug(f"Requested album: {i}, "
                         f"Found: {album_id_result['artist']['name']} - {album_id_result['title']}")
            if album_id_result and not queue_item_exists(album_id_result['id']):
                logger.info(f"{COLOR_CYAN}[+] Queueing: {album_id_result['artist']['name']} - {album_id_result['title']}{COLOR_RESET}")
                self.queue_list.append(QueueItem(album=album_id_result))

        def process_track_by_id(id):
            logger.debug("Processing track by ID")
            track_id_result = get_api_result(track_id=id)
            if not track_id_result:
                return
            logger.debug(f"Requested track: {id}, "
                         f"Found: {track_id_result['artist']['name']} - {track_id_result['title']}")
            if track_id_result and not queue_item_exists(id):
                self.queue_list.append(QueueItem(track=track_id_result))

        def process_track_file(id):
            if not queue_item_exists(id):
                track_data = {
                    "artist": {
                        "name": "TRACK ID"
                    },
                    "id": id,
                    "title": id
                }
                self.queue_list.append(QueueItem(track=track_data))

        def process_playlist_by_id(id):
            playlist_api = self.api.get_playlist(id)
            self.queue_list.append(QueueItem(playlist=playlist_api))

        def process_artist_album_entry(entry):
            """Process 'artist - album' format entry from file"""
            if ' - ' not in entry:
                logger.warning(f"Skipping invalid format: '{entry}'. Expected format: 'artist - album'")
                return
            
            artist_part, album_part = [x.strip() for x in entry.split(' - ', 1)]
            
            artist_results = self.api.search_artist(artist_part, limit=1)
            if not artist_results.get('results'):
                logger.warning(f"Artist not found: '{artist_part}'")
                return
            
            artist = artist_results['results'][0]
            artist_albums = self.api.get_artist_albums({'artist_id': artist['id'], 'artist_name': artist['name']})['releases']
            
            for album in artist_albums:
                if album_part.lower() in album['title'].lower():
                    logger.info(f"Found: {artist['name']} - {album['title']}")
                    if not queue_item_exists(album['id']):
                        logger.info(f"{COLOR_CYAN}[+] Queueing: {artist['name']} - {album['title']}{COLOR_RESET}")
                        self.queue_list.append(QueueItem(artist={'artist_name': artist['name'], 'name': artist['name'], 'link': f"https://www.deezer.com/artist/{artist['id']}"}, album=album))
                    else:
                        logger.debug(f"Album already in queue: {artist['name']} - {album['title']}")
                    return
            
            logger.warning(f"Album not found: '{album_part}' by '{artist_part}'")

        def process_artist_album_file(album_list):
            """Process a list of 'artist - album' entries from file"""
            logger.info(f"Processing {len(album_list)} artist-album entries")
            with ThreadPoolExecutor(max_workers=self.api.max_threads) as ex:
                list(tqdm(ex.map(process_artist_album_entry, album_list),
                        total=len(album_list),
                        desc=f"Fetching album data for {len(album_list)} "
                             f"album(s), please wait...", ascii=" #",
                        bar_format=ui.TQDM_FORMAT))

        def extract_id_from_url(url):
            id_group = ['artist', 'album', 'track', 'playlist']
            
            # Check for Spotify URLs first
            if 'spotify.com' in url:
                return 'spotify', url
            
            # Check for YouTube URLs
            if 'youtube.com' in url or 'youtu.be' in url:
                return 'youtube', url
            
            # Check for playlist URLs
            if '/playlist/' in url:
                return 'playlist', url
            
            for group in id_group:
                id_type = group
                try:
                    # Strip ID from URL
                    id_from_url = url.split(f'/{group}/')[1]

                    # Support for share links: http://deezer.com/us/track/12345?utm_campaign...
                    id_from_url_extra = id_from_url.split('?')[0]

                    id = int(id_from_url_extra)
                    logger.debug(f"Extracted group={id_type}, id={id}")
                    return id_type, id
                except (IndexError, ValueError) as e:
                    continue
            return False, False

        def convert_spotify_to_deezer_url(spotify_url):
            import re
            import json
            import base64
            from pathlib import Path
            
            try:
                logger.info("Converting Spotify URL to Deezer URL...")
                
                track_match = re.search(r'spotify\.com/track/([a-zA-Z0-9]+)', spotify_url)
                album_match = re.search(r'spotify\.com/album/([a-zA-Z0-9]+)', spotify_url)
                artist_match = re.search(r'spotify\.com/artist/([a-zA-Z0-9]+)', spotify_url)
                playlist_match = re.search(r'spotify\.com/playlist/([a-zA-Z0-9]+)', spotify_url)
                
                if not any([track_match, album_match, artist_match, playlist_match]):
                    logger.error(f"Unsupported Spotify URL format: {spotify_url}")
                    return None
                
                if playlist_match:
                    logger.error("Spotify playlists are not supported via URL conversion")
                    return None
                
                try:
                    import deemix.utils.localpaths as localpaths
                except ImportError:
                    logger.error("deemix.utils.localpaths not available for Spotify conversion")
                    return None
                
                if config.deemix_path() == "":
                    deemix_config_dir = Path(localpaths.getConfigFolder())
                else:
                    deemix_config_dir = Path(config.deemix_path())
                
                spotify_config_dir = deemix_config_dir / 'spotify'
                spotify_config_file = spotify_config_dir / 'config.json'
                
                if not spotify_config_file.exists():
                    logger.error(f"Spotify config not found at {spotify_config_file}")
                    return None
                
                with open(spotify_config_file, 'r') as f:
                    spotify_config = json.load(f)
                
                client_id = spotify_config.get('clientId')
                client_secret = spotify_config.get('clientSecret')
                
                if not client_id or not client_secret:
                    logger.error("Spotify credentials not configured")
                    return None
                
                credentials = f"{client_id}:{client_secret}"
                encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
                
                headers = {
                    'Authorization': f'Basic {encoded_credentials}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                data = {'grant_type': 'client_credentials'}
                
                token_response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data, timeout=10)
                token_response.raise_for_status()
                token_data = token_response.json()
                access_token = token_data.get('access_token')
                
                if not access_token:
                    logger.error("Failed to get Spotify access token")
                    return None
                
                spotify_headers = {'Authorization': f'Bearer {access_token}'}
                
                def convert_album_id_to_deezer(album_id):
                    album_response = requests.get(f'https://api.spotify.com/v1/albums/{album_id}', headers=spotify_headers, timeout=10)
                    album_response.raise_for_status()
                    album_data = album_response.json()
                    
                    artist_name = None
                    if album_data.get('artists'):
                        artist_name = album_data['artists'][0].get('name')
                    album_title = album_data.get('name')
                    upc = (album_data.get('external_ids') or {}).get('upc')
                    
                    if upc:
                        try:
                            dz_album_response = requests.get(f'https://api.deezer.com/album/upc:{upc}', timeout=10)
                            dz_album_response.raise_for_status()
                            dz_album = dz_album_response.json()
                            dz_album_id = dz_album.get('id')
                            if dz_album_id:
                                logger.info(f"Found Deezer album by UPC: {dz_album_id}")
                                return ('album', int(dz_album_id))
                        except Exception as e:
                            logger.error(f"Error during Deezer UPC lookup: {e}")
                    
                    if artist_name and album_title:
                        try:
                            query = f'artist:\"{artist_name}\" album:\"{album_title}\"'
                            dz_search_response = requests.get(
                                'https://api.deezer.com/search/album',
                                params={'q': query},
                                timeout=10
                            )
                            dz_search_response.raise_for_status()
                            dz_data = dz_search_response.json()
                            albums = dz_data.get('data') or []
                            if albums:
                                best = albums[0]
                                dz_album_id = best.get('id')
                                if dz_album_id:
                                    logger.info(
                                        f"Found Deezer album by search: {dz_album_id} - "
                                        f"{best.get('title')} by {best.get('artist', {}).get('name')}"
                                    )
                                    return ('album', int(dz_album_id))
                        except Exception as e:
                            logger.error(f"Error during Deezer search lookup: {e}")
                    
                    return None
                
                if track_match:
                    track_id = track_match.group(1)
                    track_response = requests.get(f'https://api.spotify.com/v1/tracks/{track_id}', headers=spotify_headers, timeout=10)
                    track_response.raise_for_status()
                    track_data = track_response.json()
                    album_id = track_data.get('album', {}).get('id')
                    if not album_id:
                        logger.error("Could not resolve album from Spotify track")
                        return None
                    return convert_album_id_to_deezer(album_id)
                
                if album_match:
                    album_id = album_match.group(1)
                    return convert_album_id_to_deezer(album_id)
                
                if artist_match:
                    artist_id = artist_match.group(1)
                    artist_albums_response = requests.get(f'https://api.spotify.com/v1/artists/{artist_id}/albums?limit=1', headers=spotify_headers, timeout=10)
                    artist_albums_response.raise_for_status()
                    artist_albums = artist_albums_response.json().get('items') or []
                    if not artist_albums:
                        logger.error("No albums found for Spotify artist")
                        return None
                    album_id = artist_albums[0].get('id')
                    if not album_id:
                        logger.error("Could not resolve album from Spotify artist")
                        return None
                    return convert_album_id_to_deezer(album_id)
                
                logger.error(f"Could not parse Spotify ID from URL: {spotify_url}")
                return None
                
            except Exception as e:
                logger.error(f"Error converting Spotify URL: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                return None

        def convert_youtube_to_deezer_url(youtube_url):
            import re
            
            try:
                logger.info(f"Converting YouTube URL to Deezer URL...")
                
                # Parse YouTube URL to extract video ID
                patterns = [
                    r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]+)',
                    r'youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)'
                ]
                
                video_id = None
                is_playlist = 'playlist' in youtube_url
                
                for pattern in patterns:
                    match = re.search(pattern, youtube_url)
                    if match:
                        video_id = match.group(1)
                        break
                
                if not video_id:
                    logger.error("Could not extract video ID from YouTube URL")
                    return None
                
                # Extract metadata using yt-dlp
                try:
                    import yt_dlp
                except ImportError:
                    logger.error("yt-dlp is not installed. Install with: pip install yt-dlp")
                    return None
                
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': is_playlist,
                    'ignoreerrors': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=False)
                    
                    if not info:
                        logger.error("Failed to extract YouTube metadata")
                        return None
                    
                    # Handle playlists - use first entry
                    if is_playlist and 'entries' in info:
                        logger.info(f"Processing YouTube playlist, using first track")
                        if info['entries']:
                            info = info['entries'][0]
                        else:
                            logger.error("Playlist has no entries")
                            return None
                
                title = info.get('title', '')
                
                # Parse artist and track from title
                def parse_video_title(title):
                    # Remove common suffixes
                    title = re.sub(r'\s*\(.*?\)', '', title)
                    title = re.sub(r'\s*\[.*?\]', '', title)
                    title = re.sub(r'\s*「.*?」', '', title)
                    title = re.sub(r'\s*【.*?】', '', title)
                    title = re.sub(r'\s*-\s*Official\s+(Video|Audio|MV)', '', title, flags=re.IGNORECASE)
                    title = re.sub(r'\s*-\s*Lyrics', '', title, flags=re.IGNORECASE)

                    # Try different patterns
                    patterns = [
                        r'^(.+?)\s*[-:：]\s*(.+)',
                        r'^\[(.+?)\]\s*(.+)',
                        r'^(.+?)「(.+?)」',
                        r'^(.+?)【(.+?)】',
                    ]

                    for pattern in patterns:
                        match = re.match(pattern, title)
                        if match:
                            return match.group(1).strip(), match.group(2).strip()

                    # Fallback - try to split by common separators
                    parts = re.split(r'[-:：]', title, maxsplit=1)
                    if len(parts) == 2:
                        return parts[0].strip(), parts[1].strip()

                    return None, title.strip()

                artist, track = parse_video_title(title)

                if not track:
                    logger.error(f"Could not parse track from title: {title}")
                    return None

                logger.info(f"Extracted from YouTube: artist='{artist}', track='{track}'")

                dz = self.api.dz
                deezer_id = None

                # Search Deezer for track
                if artist:
                    try:
                        deezer_id = dz.api.get_track_id_from_metadata(artist, track, None)
                    except Exception as e:
                        logger.warning(f"Deezer track metadata search failed: {e}")
                        deezer_id = None
                else:
                    # If no artist, search by track name only
                    logger.info(f"Searching for track by name only: '{track}'")
                    try:
                        search_results = dz.api.search_track(track)
                        if search_results and len(search_results) > 0:
                            deezer_id = str(search_results[0]['id'])
                            deezer_id_int = int(deezer_id)
                            logger.info(f"Found Deezer track: {deezer_id_int} - {search_results[0]['artist']['name']} - {search_results[0]['title']}")
                            return ('track', deezer_id_int)
                        else:
                            deezer_id = None
                    except Exception as e:
                        logger.warning(f"Deezer track search failed: {e}")
                        deezer_id = None

                if deezer_id and deezer_id != '0':
                    deezer_id_int = int(deezer_id)
                    logger.info(f"Found Deezer track: {deezer_id_int}")
                    return ('track', deezer_id_int)

                # Fallback: try album search if artist is available
                if artist:
                    try:
                        search_query = f"{artist} {track}"
                        search_results = dz.api.search_album(search_query)
                        if search_results and len(search_results) > 0:
                            deezer_id = search_results[0]['id']
                            logger.info(f"Found Deezer album: {deezer_id}")
                            return ('album', deezer_id)
                    except Exception as e:
                        logger.warning(f"Deezer album search failed: {e}")

                logger.error(f"Could not find matching Deezer track/album")
                return None

            except Exception as e:
                logger.error(f"Error converting YouTube URL: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                return None

        def extract_playlist_albums(playlist_url):
            import re
            import time
            
            try:
                logger.info("Extracting albums from playlist...")
                
                if 'deezer.com/playlist/' in playlist_url:
                    match = re.search(r'deezer\.com/playlist/(\d+)', playlist_url)
                    if not match:
                        logger.error("Could not extract Deezer playlist ID")
                        return []
                    
                    playlist_id = match.group(1)
                    dz = self.api.dz
                    
                    playlist_info = dz.api.get_playlist(playlist_id)
                    playlist_name = playlist_info.get('title', 'Unknown Playlist')
                    logger.info(f"Processing playlist: {playlist_name}")
                    
                    album_ids = set()
                    url = f"/playlist/{playlist_id}/tracks"
                    
                    while url:
                        tracks_data = dz.api.get(url)
                        if 'data' not in tracks_data:
                            break
                        
                        for track in tracks_data['data']:
                            if track.get('album'):
                                album_id = track['album']['id']
                                album_ids.add(album_id)
                        
                        url = tracks_data.get('next')
                        if url:
                            time.sleep(0.2)
                    
                    logger.info(f"{COLOR_CYAN}Found {len(album_ids)} unique albums in playlist{COLOR_RESET}")
                    return list(album_ids)
                
                elif 'spotify.com/playlist/' in playlist_url:
                    match = re.search(r'spotify\.com/playlist/([a-zA-Z0-9]+)', playlist_url)
                    if not match:
                        logger.error("Could not extract Spotify playlist ID")
                        return []
                    
                    playlist_id = match.group(1)
                    
                    try:
                        import deemix.utils.localpaths as localpaths
                    except ImportError:
                        logger.error("deemix.utils.localpaths not available")
                        return []
                    
                    from pathlib import Path
                    if config.deemix_path() == "":
                        deemix_config_dir = Path(localpaths.getConfigFolder())
                    else:
                        deemix_config_dir = Path(config.deemix_path())
                    
                    spotify_config_dir = deemix_config_dir / 'spotify'
                    spotify_config_file = spotify_config_dir / 'config.json'
                    
                    if not spotify_config_file.exists():
                        logger.error(f"Spotify config not found at {spotify_config_file}")
                        return []
                    
                    import json
                    import base64
                    with open(spotify_config_file, 'r') as f:
                        spotify_config = json.load(f)
                    
                    client_id = spotify_config.get('clientId')
                    client_secret = spotify_config.get('clientSecret')
                    
                    if not client_id or not client_secret:
                        logger.error("Spotify credentials not configured")
                        return []
                    
                    credentials = f"{client_id}:{client_secret}"
                    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
                    
                    headers = {
                        'Authorization': f'Basic {encoded_credentials}',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                    
                    data = {'grant_type': 'client_credentials'}
                    
                    response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data, timeout=10)
                    response.raise_for_status()
                    token_data = response.json()
                    access_token = token_data.get('access_token')
                    
                    if not access_token:
                        logger.error("Failed to get Spotify access token")
                        return []
                    
                    headers = {'Authorization': f'Bearer {access_token}'}
                    
                    playlist_response = requests.get(f'https://api.spotify.com/v1/playlists/{playlist_id}', headers=headers, timeout=10)
                    playlist_response.raise_for_status()
                    playlist_data = playlist_response.json()
                    
                    playlist_name = playlist_data.get('name', 'Unknown Playlist')
                    logger.info(f"Processing playlist: {playlist_name}")
                    
                    dz = self.api.dz
                    album_ids = set()
                    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
                    
                    while url:
                        tracks_response = requests.get(url, headers=headers, timeout=10)
                        tracks_response.raise_for_status()
                        tracks_data = tracks_response.json()
                        
                        if 'items' not in tracks_data:
                            break
                        
                        for item in tracks_data['items']:
                            track = item.get('track')
                            if track and track.get('album'):
                                album_name = track['album']['name']
                                artist_name = track['album']['artists'][0]['name'] if track['album'].get('artists') else ''
                                upc = track['album'].get('external_ids', {}).get('upc')
                                
                                deezer_id = None
                                if upc:
                                    try:
                                        from deemix.itemgen import generateAlbumItem
                                        album = generateAlbumItem(dz, f"upc:{upc}", config.bitrate())
                                        deezer_id = album.id
                                    except Exception:
                                        pass
                                
                                if not deezer_id:
                                    deezer_id = dz.api.get_track_id_from_metadata(artist_name, '', album_name)
                                    if deezer_id and deezer_id != '0':
                                        deezer_id = int(deezer_id)
                                    else:
                                        search_results = dz.api.search_album(f"{artist_name} {album_name}")
                                        if search_results and len(search_results) > 0:
                                            deezer_id = search_results[0]['id']
                                
                                if deezer_id:
                                    album_ids.add(deezer_id)
                        
                        url = tracks_data.get('next')
                        if url:
                            time.sleep(0.1)
                    
                    logger.info(f"Found {len(album_ids)} unique albums in playlist")
                    return list(album_ids)
                
                else:
                    logger.error("Unknown playlist URL format")
                    return []
            
            except Exception as e:
                logger.error(f"Error extracting playlist albums: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                return []

        if url:
            logger.debug("Processing URLs")
            for u in url:
                egroup, eid = extract_id_from_url(u)
                if not egroup or not eid:
                    logger.error(f"Invalid URL -- {u}")
                    continue

                if egroup == "spotify":
                    converted = convert_spotify_to_deezer_url(u)
                    if converted:
                        converted_group, converted_id = converted
                        if converted_group == "album":
                            process_album_by_id(converted_id)
                        elif converted_group == "track":
                            process_track_by_id(converted_id)
                    else:
                        logger.error(f"Could not convert Spotify URL: {u}")
                elif egroup == "youtube":
                    converted = convert_youtube_to_deezer_url(u)
                    if converted:
                        converted_group, converted_id = converted
                        if converted_group == "album":
                            process_album_by_id(converted_id)
                        elif converted_group == "track":
                            process_track_by_id(converted_id)
                    else:
                        logger.error(f"Could not convert YouTube URL: {u}")
                elif egroup == "artist":
                    process_artist_by_id(eid)
                elif egroup == "album":
                    process_album_by_id(eid)
                elif egroup == "playlist":
                    album_ids = extract_playlist_albums(u)
                    if album_ids:
                        for album_id in album_ids:
                            process_album_by_id(album_id)
                    else:
                        logger.error(f"Could not extract albums from playlist: {u}")
                elif egroup == "track":
                    process_track_by_id(eid)

        if artist:
            logger.debug("Processing artist names")
            for a in artist:
                process_artist_by_name(a)

        if self.duplicate_id_count > 0:
            logger.info(f"Cleaned up {self.duplicate_id_count} duplicate release(s). See log for additional info.")

        if auto:
            if len(self.queue_list):
                self.download_queue()
            else:
                print("")
                logger.info("No releases found matching applied filters.")
