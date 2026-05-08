import sys
import json
import os
import time
from pathlib import Path

# Add the current directory to sys.path so we can import deemon
sys.path.append(str(Path(__file__).parent))

try:
    from deemon.core.db import Database
    from deemon.core.config import Config
    from deemon.cmd.search import Search
    from deemon.cmd.show import Show
    from deemon.core import api
    from deemon.utils import dataprocessor
    from deemon.cmd.monitor import Monitor
    from deemon.cmd.download import Download
except ImportError as e:
    print(json.dumps({"error": f"Import error: {str(e)}. Make sure you are running from the deemon directory."}))
    sys.exit(1)

def get_artists():
    with Database() as db:
        artists = db.get_all_monitored_artists()
        return list(artists) if artists else []

def get_playlists():
    with Database() as db:
        playlists = db.get_all_monitored_playlists()
        return list(playlists) if playlists else []

def get_releases(days=30):
    with Database() as db:
        now = int(time.time())
        since = now - (days * 24 * 60 * 60)
        releases = db.show_new_releases(since, now)
        return list(releases) if releases else []

def search_artist(query):
    platform_api = api.PlatformAPI()
    results = platform_api.search_artist(query)
    return results

def get_artist_albums(artist_id):
    platform_api = api.PlatformAPI()
    artist = platform_api.get_artist_by_id(int(artist_id))
    if not artist:
        return {"error": "Artist not found"}
    query = {"artist_id": artist['id'], "artist_name": artist['name']}
    results = platform_api.get_artist_albums(query)
    return results

def monitor_artist(artist_id):
    monitor = Monitor()
    # Monitor expects IDs as strings or ints
    monitor.artist_ids([int(artist_id)])
    return {"status": "success", "message": f"Artist {artist_id} added to monitoring"}

def download_url(url):
    dl = Download()
    dl.download(None, None, None, [url], None, None, None, None)
    return {"status": "success", "message": f"Download started for {url}"}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        return

    cmd = sys.argv[1]
    
    try:
        if cmd == "artists":
            print(json.dumps(get_artists()))
        elif cmd == "playlists":
            print(json.dumps(get_playlists()))
        elif cmd == "releases":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            print(json.dumps(get_releases(days)))
        elif cmd == "search":
            query = " ".join(sys.argv[2:])
            print(json.dumps(search_artist(query)))
        elif cmd == "albums":
            artist_id = sys.argv[2]
            print(json.dumps(get_artist_albums(artist_id)))
        elif cmd == "monitor":
            artist_id = sys.argv[2]
            print(json.dumps(monitor_artist(artist_id)))
        elif cmd == "download":
            url = sys.argv[2]
            print(json.dumps(download_url(url)))
        else:
            print(json.dumps({"error": f"Unknown command: {cmd}"}))
    except Exception as e:
        import traceback
        print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}))

if __name__ == "__main__":
    # Ensure environment is set up if not already
    if "HOME" not in os.environ:
        os.environ["HOME"] = "/Users/rd"
    if "XDG_CONFIG_HOME" not in os.environ:
        os.environ["XDG_CONFIG_HOME"] = "/Users/rd/.config"
    
    # Initialize config to ensure it's loaded
    Config()
    
    main()
