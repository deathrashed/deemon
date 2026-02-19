import logging
import platform
import sys
import time
from pathlib import Path

import click
import inquirer
from packaging.version import parse as parse_version
import requests

from os import system

from deemon import __version__
from deemon.cmd import download, rollback, backup, extra, tests, upgradelib
from deemon.cmd.artistconfig import artist_lookup
from deemon.cmd.monitor import Monitor
from deemon.cmd.profile import ProfileConfig
from deemon.cmd.refresh import Refresh
from deemon.cmd.search import Search
from deemon.cmd.show import Show
from deemon.core import notifier
from deemon.core.config import Config, LoadProfile
from deemon.core.db import Database
from deemon.core.logger import setup_logger
from deemon.utils import startup, dataprocessor, validate

logger = None
config = None
db = None


def clear_screen():
    """Clear the terminal screen"""
    if platform.system() == "Windows":
        _ = system('cls')
    else:
        _ = system('clear')


def interactive_menu():
    """Interactive menu for deemon"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 22}DEEMON{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Download{COLOR_RESET}                {COLOR_DIM}Download music{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Search{COLOR_RESET}                  {COLOR_DIM}Search & download{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}Monitor{COLOR_RESET}                 {COLOR_DIM}Monitor artists{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}4.{COLOR_RESET} {COLOR_BOLD}New Releases{COLOR_RESET}            {COLOR_DIM}View releases{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}5.{COLOR_RESET} {COLOR_BOLD}Configuration{COLOR_RESET}           {COLOR_DIM}Settings & backup{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}h.{COLOR_RESET} {COLOR_BOLD}Help{COLOR_RESET}                   {COLOR_DIM}Show cheatsheet{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}e.{COLOR_RESET} {COLOR_BOLD}Exit{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} What would you like to do? {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'download':
            download_menu()
        elif choice == '2' or choice.lower() == 'search':
            client = Search()
            client.search_menu()
        elif choice == '3' or choice.lower() == 'monitor':
            monitor_sub_menu()
        elif choice == '4' or choice.lower() == 'new releases':
            show_releases_menu()
        elif choice == '5' or choice.lower() == 'configuration':
            config_sub_menu()
        elif choice.lower() == 'h':
            cheatsheet_command()
            input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice.lower() == 'e':
            print(f"\n{COLOR_GREEN}Goodbye!{COLOR_RESET}\n")
            break
        elif choice == '':
            continue


def monitor_sub_menu():
    """Monitor submenu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 18}MONITOR OPTIONS{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Show Monitored{COLOR_RESET}            {COLOR_DIM}View tracked artists{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Monitor Artists{COLOR_RESET}           {COLOR_DIM}Add artists to track{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}Refresh Monitored{COLOR_RESET}         {COLOR_DIM}Check for new releases{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Monitor options {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'show':
            show_monitored_menu()
        elif choice == '2' or choice.lower() == 'monitor artists' or choice.lower() == 'monitor':
            monitor_menu()
        elif choice == '3' or choice.lower() == 'refresh':
            refresh_menu()
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue


def config_sub_menu():
    """Configuration submenu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 17}CONFIGURATION{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Configuration{COLOR_RESET}               {COLOR_DIM}Per-artist settings{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Backup/Restore{COLOR_RESET}             {COLOR_DIM}Save and restore{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}Profiles{COLOR_RESET}                  {COLOR_DIM}Manage profiles{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Configuration options {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'configuration':
            config_menu()
        elif choice == '2' or choice.lower() == 'backup':
            backup_menu()
        elif choice == '3' or choice.lower() == 'profiles':
            profile_menu()
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue


def monitor_menu():
    """Monitor artists menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"
    COLOR_RED = "\033[31m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 18}MONITOR ARTIST{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}By Artist Name{COLOR_RESET}           {COLOR_DIM}Search and add artist{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}By Artist ID{COLOR_RESET}             {COLOR_DIM}Add using artist ID{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}By URL{COLOR_RESET}                  {COLOR_DIM}Spotify or Deezer link{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}4.{COLOR_RESET} {COLOR_BOLD}From Playlist{COLOR_RESET}            {COLOR_DIM}Import from playlist{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}5.{COLOR_RESET} {COLOR_BOLD}From File{COLOR_RESET}               {COLOR_DIM}Import from file{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} How would you like to monitor? {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'name' or choice.lower() == 'artist name':
            print()
            artist = input(f"{COLOR_CYAN}Enter artist name{COLOR_RESET} {COLOR_DIM}(comma-separated for multiple){COLOR_RESET}: ").strip()
            if artist:
                monitor = Monitor()
                monitor.artists(dataprocessor.csv_to_list([artist]))
                print(f"\n{COLOR_GREEN}Artist(s) added to monitoring!{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '2' or choice.lower() == 'id' or choice.lower() == 'artist id':
            print()
            artist_id = input(f"{COLOR_CYAN}Enter artist ID{COLOR_RESET} {COLOR_DIM}(comma-separated for multiple){COLOR_RESET}: ").strip()
            if artist_id:
                try:
                    ids = [int(x.strip()) for x in artist_id.split(',')]
                    monitor = Monitor()
                    monitor.artist_ids(ids)
                    print(f"\n{COLOR_GREEN}Artist(s) added to monitoring!{COLOR_RESET}")
                    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
                except ValueError:
                    print(f"{COLOR_RED}Invalid artist ID format{COLOR_RESET}")
                    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '3' or choice.lower() == 'url':
            print()
            url = input(f"{COLOR_CYAN}Enter Spotify or Deezer artist URL:{COLOR_RESET} ").strip()
            if url:
                monitor = Monitor()
                monitor.set_options(False, False, False)
                url_id = url.split('/artist/')
                if len(url_id) > 1:
                    try:
                        monitor.artist_ids([int(url_id[1].split('?')[0])])
                        print(f"{COLOR_GREEN}\nArtist added to monitoring!{COLOR_RESET}")
                        input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
                    except ValueError:
                        print(f"{COLOR_RED}Invalid URL format{COLOR_RESET}")
                        input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Invalid artist URL{COLOR_RESET}")
                    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '4' or choice.lower() == 'playlist':
            print()
            url = input(f"{COLOR_CYAN}Enter Spotify or Deezer playlist URL:{COLOR_RESET} ").strip()
            if url:
                monitor = Monitor()
                url_id = url.split('/playlist/')
                if len(url_id) > 1:
                    include = input(f"{COLOR_YELLOW}Include artists from playlist? [y/N]:{COLOR_RESET} ").strip().lower() == 'y'
                    try:
                        monitor.playlists([int(url_id[1].split('?')[0])], include)
                        print(f"{COLOR_GREEN}\nPlaylist added to monitoring!{COLOR_RESET}")
                        input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
                    except ValueError:
                        print(f"{COLOR_RED}Invalid URL format{COLOR_RESET}")
                        input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Invalid playlist URL{COLOR_RESET}")
                    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '5' or choice.lower() == 'file':
            print()
            file_path = input(f"{COLOR_CYAN}Enter file path:{COLOR_RESET} ").strip()
            if file_path:
                monitor = Monitor()
                monitor.importer(file_path)
                print(f"{COLOR_GREEN}\nImport complete!{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue


def playlist_menu():
    """Playlist download menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 15}PLAYLIST DOWNLOAD{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Download all albums{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Download excluding existing{COLOR_RESET}  {COLOR_DIM}(use collection matcher){COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Playlist download mode {COLOR_RESET}").strip()

        if choice == '1':
            print()
            url = input(f"{COLOR_CYAN}Enter playlist URL (Spotify or Deezer):{COLOR_RESET} ").strip()
            if url:
                dl = download.Download()
                dl.download_playlist(url, use_collection_matcher=False)
            break
        elif choice == '2':
            print()
            url = input(f"{COLOR_CYAN}Enter playlist URL (Spotify or Deezer):{COLOR_RESET} ").strip()
            if url:
                dl = download.Download()
                dl.download_playlist(url, use_collection_matcher=True)
            break
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue

def file_menu():
    """File import menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 20}FILE IMPORT{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Artist file{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Album file{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}Track file{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} File type? {COLOR_RESET}").strip()

        if choice == '1':
            print()
            file_path = input(f"{COLOR_CYAN}Enter file path:{COLOR_RESET} ").strip()
            if file_path:
                dl = download.Download()
                dl.download(None, None, None, None, file_path, None, None, None)
            break
        elif choice == '2':
            print()
            file_path = input(f"{COLOR_CYAN}Enter file path:{COLOR_RESET} ").strip()
            if file_path:
                dl = download.Download()
                dl.download(None, None, None, None, None, None, file_path, None)
            break
        elif choice == '3':
            print()
            file_path = input(f"{COLOR_CYAN}Enter file path:{COLOR_RESET} ").strip()
            if file_path:
                dl = download.Download()
                dl.download(None, None, None, None, None, None, None, file_path)
            break
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue

def id_menu():
    """ID download menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 22}ID DOWNLOAD{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Artist ID{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Album ID{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}Track ID{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Select ID type {COLOR_RESET}").strip()

        dl = download.Download()

        if choice == '1':
            print()
            artist_id = input(f"{COLOR_CYAN}Enter artist ID:{COLOR_RESET} ").strip()
            print(f"{COLOR_DIM}comma-separated for multiple{COLOR_RESET}")
            if artist_id:
                ids = [int(x.strip()) for x in artist_id.split(',')]
                dl.download(None, ids, None, None, None, None, None, None)
            break
        elif choice == '2':
            print()
            album_id = input(f"{COLOR_CYAN}Enter album ID:{COLOR_RESET} ").strip()
            print(f"{COLOR_DIM}comma-separated for multiple{COLOR_RESET}")
            if album_id:
                ids = [int(x.strip()) for x in album_id.split(',')]
                dl.download(None, None, ids, None, None, None, None, None)
            break
        elif choice == '3':
            print()
            track_id = input(f"{COLOR_CYAN}Enter track ID:{COLOR_RESET} ").strip()
            print(f"{COLOR_DIM}comma-separated for multiple{COLOR_RESET}")
            if track_id:
                ids = [int(x.strip()) for x in track_id.split(',')]
                dl.download(None, None, None, None, None, None, None, ids)
            break
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue


def download_menu():
    """Download menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BLUE = "\033[34m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 18}DEEMON DOWNLOAD{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Artist - Album{COLOR_RESET}       {COLOR_DIM}(e.g. 'Slayer - Hell Awaits'){COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Artist{COLOR_RESET}                 {COLOR_DIM}(Download all releases){COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}ID{COLOR_RESET}                     {COLOR_DIM}(Artist/Album/Track ID){COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}4.{COLOR_RESET} {COLOR_BOLD}URL{COLOR_RESET}                    {COLOR_DIM}(Spotify/Deezer link){COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}5.{COLOR_RESET} {COLOR_BOLD}Playlist{COLOR_RESET}              {COLOR_DIM}(Full playlist download){COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}6.{COLOR_RESET} {COLOR_BOLD}Monitored{COLOR_RESET}             {COLOR_DIM}(All monitored artists){COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}7.{COLOR_RESET} {COLOR_BOLD}File{COLOR_RESET}                  {COLOR_DIM}(Import from file){COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} What would you like to download? {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'artist - album':
            download_artist_album_menu()
        elif choice == '2' or choice.lower() == 'artist':
            download_artist_menu()
        elif choice == '3' or choice.lower() == 'id':
            id_menu()
        elif choice == '4' or choice.lower() == 'url':
            dl = download.Download()
            print(f"\n{COLOR_CYAN}Enter a Spotify or Deezer URL:{COLOR_RESET}")
            print(f"{COLOR_DIM}(track, album, playlist, or artist){COLOR_RESET}")
            print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
            print()
            url = input(f"{COLOR_BRIGHT_BLUE}>{COLOR_RESET} ").strip()
            if url.lower() == 'b':
                continue
            if url:
                dl.download(None, None, None, [url], None, None, None, None)
                print(f"\n{COLOR_GREEN}Download complete!{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '5' or choice.lower() == 'playlist':
            playlist_menu()
        elif choice == '6' or choice.lower() == 'monitored':
            download_monitored()
        elif choice == '7' or choice.lower() == 'file':
            file_menu()
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue


def download_artist_album_menu():
    """Download Artist - Album menu with search results"""
    from deemon.core import api
    from deemon.cmd.search import Search
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"
    COLOR_RED = "\033[31m"

    clear_screen()
    print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
    print(f"{COLOR_BRIGHT_CYAN}{' ' * 15}ARTIST - ALBUM{COLOR_RESET}")
    print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

    print(f"{COLOR_CYAN}Enter Artist - Album (e.g., 'Misfits - Collection'){COLOR_RESET}")
    print(f"{COLOR_DIM}or just 'Artist' to search for albums{COLOR_RESET}")
    print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
    print()

    query = input(f"{COLOR_BRIGHT_BLUE}>{COLOR_RESET} ").strip()

    if query.lower() == 'b':
        return
    if not query:
        return

    # Check if it's "Artist - Album" format or just "Artist"
    if ' - ' in query:
        # Direct download Artist - Album
        dl = download.Download()
        print(f"\n{COLOR_CYAN}Searching for: {query}{COLOR_RESET}\n")
        dl.download(dataprocessor.csv_to_list([query]), None, None, None, None, None, None, None)
        print(f"\n{COLOR_GREEN}Download complete!{COLOR_RESET}")
        input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
    else:
        # Just artist name - show search results
        print(f"\n{COLOR_CYAN}Searching for albums by: {query}{COLOR_RESET}\n")
        platform_api = api.PlatformAPI()
        artist_results = platform_api.search_artist(query)

        if not artist_results:
            print(f"{COLOR_YELLOW}No artists found{COLOR_RESET}")
            input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
            return

        # Select artist
        if len(artist_results) > 1:
            print(f"{COLOR_DIM}Multiple artists found. Select one:{COLOR_RESET}\n")
            for idx, artist in enumerate(artist_results, start=1):
                print(f"{COLOR_BRIGHT_BLUE}{idx}.{COLOR_RESET} {COLOR_BOLD}{artist['name']}{COLOR_RESET}")
            print()
            choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Select artist {COLOR_RESET}").strip()
            try:
                selected_idx = int(choice) - 1
                if 0 <= selected_idx < len(artist_results):
                    selected_artist = artist_results[selected_idx]
                else:
                    print(f"{COLOR_YELLOW}Invalid selection{COLOR_RESET}")
                    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
                    return
            except ValueError:
                print(f"{COLOR_YELLOW}Invalid selection{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
                return
        else:
            selected_artist = artist_results[0]

        # Show albums for selected artist
        print(f"\n{COLOR_CYAN}Fetching albums for {selected_artist['name']}...{COLOR_RESET}\n")
        search = Search(active_api=platform_api)
        search.album_menu(selected_artist)


def download_artist_menu():
    """Download Artist menu with search results"""
    from deemon.core import api
    from deemon.cmd.search import Search
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"
    COLOR_RED = "\033[31m"

    clear_screen()
    print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
    print(f"{COLOR_BRIGHT_CYAN}{' ' * 18}DOWNLOAD ARTIST{COLOR_RESET}")
    print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

    print(f"{COLOR_CYAN}Enter artist name{COLOR_RESET}")
    print(f"{COLOR_DIM}or 'Artist - Album' to narrow down search{COLOR_RESET}")
    print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
    print()

    query = input(f"{COLOR_BRIGHT_BLUE}>{COLOR_RESET} ").strip()

    if query.lower() == 'b':
        return
    if not query:
        return

    # Check if it's "Artist - Album" format
    if ' - ' in query:
        # Search for specific album and download
        dl = download.Download()
        print(f"\n{COLOR_CYAN}Searching for: {query}{COLOR_RESET}\n")
        dl.download(dataprocessor.csv_to_list([query]), None, None, None, None, None, None, None)
        print(f"\n{COLOR_GREEN}Download complete!{COLOR_RESET}")
        input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        return

    # Just artist name - show search results
    print(f"\n{COLOR_CYAN}Searching for: {query}{COLOR_RESET}\n")
    platform_api = api.PlatformAPI()
    artist_results = platform_api.search_artist(query)

    if not artist_results:
        print(f"{COLOR_YELLOW}No artists found{COLOR_RESET}")
        input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        return

    # Select artist if multiple results
    if len(artist_results) > 1:
        print(f"{COLOR_DIM}Multiple artists found. Select one:{COLOR_RESET}\n")
        for idx, artist in enumerate(artist_results, start=1):
            print(f"{COLOR_BRIGHT_BLUE}{idx}.{COLOR_RESET} {COLOR_BOLD}{artist['name']}{COLOR_RESET}")
        print()
        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Select artist {COLOR_RESET}").strip()
        try:
            selected_idx = int(choice) - 1
            if 0 <= selected_idx < len(artist_results):
                selected_artist = artist_results[selected_idx]
            else:
                print(f"{COLOR_YELLOW}Invalid selection{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
                return
        except ValueError:
            print(f"{COLOR_YELLOW}Invalid selection{COLOR_RESET}")
            input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
            return
    else:
        selected_artist = artist_results[0]

    # Download all releases by selected artist
    artist_id = selected_artist['id']
    artist_name = selected_artist['name']

    print(f"\n{COLOR_CYAN}Downloading all releases by {artist_name}...{COLOR_RESET}\n")

    dl = download.Download()
    dl.artist_ids([artist_id])

    print(f"\n{COLOR_GREEN}Download complete!{COLOR_RESET}")
    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")


def refresh_menu():
    """Refresh menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 17}REFRESH OPTIONS{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}All Monitored Artists{COLOR_RESET}     {COLOR_DIM}Check all for new releases{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Specific Artist(s){COLOR_RESET}        {COLOR_DIM}Check specific artists{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}Playlist(s){COLOR_RESET}               {COLOR_DIM}Check playlists{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} What would you like to refresh? {COLOR_RESET}").strip()

        skip_download = False

        if choice == '1' or choice.lower() == 'all':
            skip = input(f"{COLOR_YELLOW}Skip downloading new releases? [y/N]:{COLOR_RESET} ").strip().lower()
            skip_download = (skip == 'y')
            print(f"\n{COLOR_CYAN}Refreshing all monitored artists...{COLOR_RESET}\n")
            refresh = Refresh(None, skip_download)
            refresh.run()
            print(f"\n{COLOR_GREEN}Refresh complete!{COLOR_RESET}")
            input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '2' or choice.lower() == 'specific':
            print()
            artist = input(f"{COLOR_CYAN}Enter artist name{COLOR_RESET} {COLOR_DIM}(comma-separated for multiple){COLOR_RESET}: ").strip()
            if artist:
                skip = input(f"{COLOR_YELLOW}Skip downloading new releases? [y/N]:{COLOR_RESET} ").strip().lower()
                skip_download = (skip == 'y')
                print(f"\n{COLOR_CYAN}Refreshing artist(s)...{COLOR_RESET}\n")
                refresh = Refresh(None, skip_download)
                refresh.run(artists=dataprocessor.csv_to_list([artist]))
                print(f"\n{COLOR_GREEN}Refresh complete!{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '3' or choice.lower() == 'playlist' or choice.lower() == 'playlists':
            print()
            playlist = input(f"{COLOR_CYAN}Enter playlist name{COLOR_RESET} {COLOR_DIM}(comma-separated for multiple){COLOR_RESET}: ").strip()
            if playlist:
                skip = input(f"{COLOR_YELLOW}Skip downloading new releases? [y/N]:{COLOR_RESET} ").strip().lower()
                skip_download = (skip == 'y')
                print(f"\n{COLOR_CYAN}Refreshing playlist(s)...{COLOR_RESET}\n")
                refresh = Refresh(None, skip_download)
                refresh.run(playlists=dataprocessor.csv_to_list([playlist]))
                print(f"\n{COLOR_GREEN}Refresh complete!{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue


def show_monitored_menu():
    """Show monitored menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"
    COLOR_RED = "\033[31m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 17}MONITORED ARTISTS{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        # Get all monitored artists
        show = Show()
        db_result = show.db.get_all_monitored_artists()

        if not db_result:
            print(f"{COLOR_YELLOW}No artists are being monitored{COLOR_RESET}")
            print(f"\n{COLOR_DIM}Press Enter to return...{COLOR_RESET}")
            input()
            return

        # Convert to list if needed
        if isinstance(db_result, dict):
            items = [db_result]
        else:
            items = list(db_result) if hasattr(db_result, '__iter__') else list(db_result.values())

        if not items:
            print(f"{COLOR_YELLOW}No artists are being monitored{COLOR_RESET}")
            print(f"\n{COLOR_DIM}Press Enter to return...{COLOR_RESET}")
            input()
            return

        # Display artists with pagination
        page_size = 15
        page = 0
        total_pages = (len(items) + page_size - 1) // page_size

        while True:
            clear_screen()
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{' ' * 17}MONITORED ARTISTS{COLOR_RESET}")
            if total_pages > 1:
                print(f"{COLOR_DIM}Page {page + 1} of {total_pages}{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(items))
            page_items = items[start_idx:end_idx]

            # Calculate column widths
            num_width = 5  # for "1." "2." etc
            artist_width = 35  # artist names max 35 chars
            id_width = 9  # space for IDs
            alerts_width = 8
            type_width = 6

            print(f"{COLOR_DIM}{'#':<{num_width}}  {'Artist':<{artist_width}} {'ID':<{id_width}} {'Alerts':<{alerts_width}} {'Type':<{type_width}}{COLOR_RESET}")
            print(f"{COLOR_DIM}{'-' * num_width}  {'-' * artist_width} {'-' * id_width} {'-' * alerts_width} {'-' * type_width}{COLOR_RESET}")

            for idx, item in enumerate(page_items, start=start_idx + 1):
                artist_id = str(item.get('artist_id', '-'))
                artist_name = (item.get('artist_name') or 'Unknown')[:35]
                alerts = "Yes" if item.get('alerts') else "No"
                record_type = (item.get('record_type') or 'all')[:6]

                # Color alerts
                if alerts == "Yes":
                    alerts_colored = f"{COLOR_GREEN}{alerts:<{alerts_width}}{COLOR_RESET}"
                else:
                    alerts_colored = f"{COLOR_DIM}{alerts:<{alerts_width}}{COLOR_RESET}"

                # Format: row number, artist name, ID, alerts, type
                print(f"{idx:<{num_width}}.  {COLOR_BOLD}{artist_name:<{artist_width}}{COLOR_RESET} {artist_id:<{id_width}} {alerts_colored} {record_type:<{type_width}}")

            print()
            # Build options
            options = []
            if total_pages > 1:
                if page > 0:
                    options.append(f"{COLOR_CYAN}(p){COLOR_RESET} Previous")
                if page < total_pages - 1:
                    options.append(f"{COLOR_CYAN}(n){COLOR_RESET} Next")
            options.append(f"{COLOR_CYAN}(a){COLOR_RESET} Add Artist")
            options.append(f"{COLOR_DIM}(b){COLOR_RESET} Back")
            options.append(f"{COLOR_CYAN}(d){COLOR_RESET} Download")
            options.append(f"{COLOR_CYAN}(r){COLOR_RESET} Refresh")
            options.append(f"{COLOR_RED}(u){COLOR_RESET} Unmonitor")

            print("  ".join(options))

            choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Enter selection or option {COLOR_RESET}").strip()

            if choice.lower() == 'b':
                return
            elif choice == '':
                continue
            elif choice == 'p' and page > 0:
                page -= 1
                continue
            elif choice == 'n' and page < total_pages - 1:
                page += 1
                continue

            # Check if a number was entered (artist selection)
            try:
                selected_idx = int(choice) - 1
                if 0 <= selected_idx < len(items):
                    artist_menu(show, items[selected_idx])
                    return
                else:
                    print(f"{COLOR_YELLOW}Invalid selection{COLOR_RESET}")
                    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
            except ValueError:
                if choice.lower() == 'a':
                    monitor_menu()
                elif choice.lower() == 'd':
                    download_monitored()
                elif choice.lower() == 'r':
                    refresh_monitored()
                elif choice.lower() == 'u':
                    unmonitored_artist(show, items)
                    return

def artist_menu(show, artist_item):
    """Menu for a single monitored artist"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"
    COLOR_RED = "\033[31m"

    artist_id = artist_item.get('artist_id')
    artist_name = artist_item.get('artist_name', 'Unknown')

    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_CYAN}Artist:{COLOR_RESET} {COLOR_BOLD}{artist_name}{COLOR_RESET}")
        print(f"{COLOR_CYAN}Artist ID:{COLOR_RESET} {artist_id}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}View Discography{COLOR_RESET}            {COLOR_DIM}Show all releases{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Check New Releases{COLOR_RESET}         {COLOR_DIM}Refresh for new{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}Download All{COLOR_RESET}                {COLOR_DIM}Download all releases{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}4.{COLOR_RESET} {COLOR_BOLD}Edit Settings{COLOR_RESET}               {COLOR_DIM}Configure this artist{COLOR_RESET}")
        print(f"{COLOR_RED}5.{COLOR_RESET} {COLOR_BOLD}Unmonitor{COLOR_RESET}                    {COLOR_DIM}Stop tracking{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} What would you like to do? {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'view' or choice.lower() == 'discography':
            view_discography(artist_name, artist_id)
        elif choice == '2' or choice.lower() == 'refresh' or choice.lower() == 'check':
            refresh_artist(artist_name, artist_id)
        elif choice == '3' or choice.lower() == 'download' or choice.lower() == 'download all':
            download_artist(artist_name, artist_id)
        elif choice == '4' or choice.lower() == 'edit' or choice.lower() == 'settings':
            from deemon.cmd.artistconfig import artist_lookup
            print(f"\n{COLOR_DIM}Opening configuration for: {artist_name}{COLOR_RESET}\n")
            artist_lookup(str(artist_id))
            input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '5' or choice.lower() == 'unmonitor':
            unmonitored_artist_by_id(artist_id)
            return
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue

def view_discography(artist_name, artist_id):
    """View artist discography using Search function"""
    from deemon.core import api
    from deemon.cmd.search import Search
    COLOR_RESET = "\033[0m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"

    print(f"\n{COLOR_CYAN}Loading discography for {artist_name}...{COLOR_RESET}")

    platform_api = api.PlatformAPI()
    artist_result = platform_api.get_artist_by_id(artist_id)

    if artist_result:
        search = Search(active_api=platform_api)
        search.album_menu(artist_result)
    else:
        print(f"{COLOR_YELLOW}Could not load artist information{COLOR_RESET}")
        input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")

def refresh_artist(artist_name, artist_id):
    """Refresh a single artist for new releases"""
    from deemon.cmd.refresh import Refresh
    COLOR_RESET = "\033[0m"
    COLOR_CYAN = "\033[36m"
    COLOR_GREEN = "\033[32m"
    COLOR_DIM = "\033[2m"

    print(f"\n{COLOR_CYAN}Checking {artist_name} for new releases...{COLOR_RESET}")
    print()

    refresh = Refresh(None, False)
    refresh.run(artists=[artist_name])

    print(f"\n{COLOR_GREEN}Refresh complete!{COLOR_RESET}")
    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")

def download_artist(artist_name, artist_id):
    """Download all releases for an artist"""
    from deemon.cmd import download as dl_mod
    COLOR_RESET = "\033[0m"
    COLOR_CYAN = "\033[36m"
    COLOR_GREEN = "\033[32m"
    COLOR_DIM = "\033[2m"

    print(f"\n{COLOR_CYAN}Preparing to download all releases by {artist_name}...{COLOR_RESET}")
    print()

    dl = dl_mod.Download()
    dl.artist_ids([artist_id])

    print(f"\n{COLOR_GREEN}Download complete!{COLOR_RESET}")
    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")

def unmonitored_artist(show, all_items):
    """Unmonitor an artist with selection"""
    from deemon.cmd.monitor import Monitor
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"
    COLOR_RED = "\033[31m"

    # Convert to list if needed
    if isinstance(all_items, dict):
        items = [all_items]
    else:
        items = list(all_items) if hasattr(all_items, '__iter__') else list(all_items.values())

    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 15}UNMONITOR ARTIST{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        for idx, item in enumerate(items, start=1):
            artist_name = item.get('artist_name', 'Unknown')
            print(f"{COLOR_BRIGHT_BLUE}{idx}.{COLOR_RESET} {COLOR_BOLD}{artist_name}{COLOR_RESET}")

        print()
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Select artist to unmonitor {COLOR_RESET}").strip()

        if choice.lower() == 'b':
            return
        elif choice == '':
            continue

        try:
            selected_idx = int(choice) - 1
            if 0 <= selected_idx < len(items):
                artist_to_remove = items[selected_idx]
                artist_name = artist_to_remove.get('artist_name', 'Unknown')
                artist_id = artist_to_remove.get('artist_id')

                print(f"\n{COLOR_YELLOW}Unmonitor: {artist_name}?{COLOR_RESET}")
                confirm = input(f"{COLOR_DIM}Confirm [y/N]:{COLOR_RESET} ").strip().lower()

                if confirm == 'y':
                    # Use Monitor class to remove artist
                    monitor = Monitor()
                    monitor.set_options(remove=True, dl_all=False, search=False)
                    monitor.artist_ids([artist_id])
                    print(f"{COLOR_GREEN}Unmonitored: {artist_name}{COLOR_RESET}")
                    input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
                return
            else:
                print(f"{COLOR_YELLOW}Invalid selection{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        except ValueError:
            print(f"{COLOR_RED}Invalid selection{COLOR_RESET}")
            input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")

def unmonitored_artist_by_id(artist_id):
    """Unmonitor an artist by ID"""
    from deemon.cmd.monitor import Monitor
    COLOR_RESET = "\033[0m"
    COLOR_CYAN = "\033[36m"
    COLOR_GREEN = "\033[32m"

    monitor = Monitor()
    monitor.set_options(remove=True, dl_all=False, search=False)
    monitor.artist_ids([artist_id])

    print(f"\n{COLOR_GREEN}Artist unmonitored{COLOR_RESET}")
    input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")

def download_monitored():
    """Download monitored artists with selection"""
    from deemon.cmd import download as dl_mod
    from deemon.core import api
    from deemon.cmd.search import Search
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"
    COLOR_RED = "\033[31m"

    db = Database()
    artists = db.get_all_monitored_artists()

    if not artists:
        print(f"{COLOR_YELLOW}No artists are being monitored{COLOR_RESET}")
        input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        return

    # Convert to list if needed
    if isinstance(artists, dict):
        items = [artists]
    else:
        items = list(artists) if hasattr(artists, '__iter__') else list(artists.values())

    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 18}DOWNLOAD MONITORED{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        for idx, item in enumerate(items, start=1):
            artist_name = item.get('artist_name', 'Unknown')
            print(f"{COLOR_BRIGHT_BLUE}{idx}.{COLOR_RESET} {COLOR_BOLD}{artist_name}{COLOR_RESET}")

        print()
        print(f"{COLOR_DIM}  {COLOR_CYAN}a.{COLOR_RESET} {COLOR_BOLD}Download All{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Select artist or option {COLOR_RESET}").strip()

        if choice.lower() == 'a' or choice.lower() == 'download all':
            dl = dl_mod.Download()
            dl.artist_ids([item.get('artist_id') for item in items])
            return
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue

        # Check if a number was entered (artist selection)
        try:
            selected_idx = int(choice) - 1
            if 0 <= selected_idx < len(items):
                artist_item = items[selected_idx]
                artist_id = artist_item.get('artist_id')
                artist_name = artist_item.get('artist_name', 'Unknown')

                # Show artist options menu
                while True:
                    clear_screen()
                    print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
                    print(f"{COLOR_CYAN}Artist:{COLOR_RESET} {COLOR_BOLD}{artist_name}{COLOR_RESET}")
                    print(f"{COLOR_CYAN}Artist ID:{COLOR_RESET} {artist_id}")
                    print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

                    print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}View Discography{COLOR_RESET}            {COLOR_DIM}Show all releases{COLOR_RESET}")
                    print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Check New Releases{COLOR_RESET}         {COLOR_DIM}Refresh for new{COLOR_RESET}")
                    print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}Download All{COLOR_RESET}                {COLOR_DIM}Download all releases{COLOR_RESET}")
                    print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
                    print()

                    action_choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} What would you like to do? {COLOR_RESET}").strip()

                    if action_choice == '1' or action_choice.lower() == 'view' or action_choice.lower() == 'discography':
                        view_discography(artist_name, artist_id)
                    elif action_choice == '2' or action_choice.lower() == 'refresh' or action_choice.lower() == 'check':
                        refresh_artist(artist_name, artist_id)
                    elif action_choice == '3' or action_choice.lower() == 'download' or action_choice.lower() == 'download all':
                        download_artist(artist_name, artist_id)
                    elif action_choice.lower() == 'b':
                        break
                    elif action_choice == '':
                        continue
            else:
                print(f"{COLOR_YELLOW}Invalid selection{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        except ValueError:
            print(f"{COLOR_YELLOW}Invalid selection{COLOR_RESET}")
            input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")

def refresh_monitored():
    """Refresh all monitored artists"""
    from deemon.cmd.refresh import Refresh
    COLOR_RESET = "\033[0m"
    COLOR_CYAN = "\033[36m"
    COLOR_GREEN = "\033[32m"
    COLOR_DIM = "\033[2m"

    print(f"{COLOR_CYAN}Checking all monitored artists for new releases...{COLOR_RESET}\n")

    refresh = Refresh(None, False)
    refresh.run()

    print(f"\n{COLOR_GREEN}Refresh complete!{COLOR_RESET}")
    input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")

def show_monitoring_styled(show_instance, artist: bool = True, query: str = None):
    """Display monitored artists or playlists with styled output"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    clear_screen()

    if artist:
        if query:
            db_result = show_instance.db.get_monitored_artist_by_name(query)
        else:
            db_result = show_instance.db.get_all_monitored_artists()

        if not db_result:
            if query:
                print(f"{COLOR_YELLOW}Artist not found:{COLOR_RESET} {query}")
            else:
                print(f"{COLOR_YELLOW}No artists are being monitored{COLOR_RESET}")
            input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
            return

        # Convert dict to list if single result
        if isinstance(db_result, dict):
            items = [db_result]
        else:
            items = db_result

        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 15}MONITORED ARTISTS{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        if len(items) == 0:
            print(f"{COLOR_YELLOW}No artists found{COLOR_RESET}")
            input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
            return

        print(f"{COLOR_DIM}{'ID':<8} {'Artist':<30} {'Alerts':<8} {'Bitrate':<10} {'Type':<8}{COLOR_RESET}")
        print(f"{COLOR_DIM}{'-' * 8} {'-' * 30} {'-' * 8} {'-' * 10} {'-' * 8}{COLOR_RESET}")

        for item in items:
            artist_id = str(item.get('artist_id', '-'))
            artist_name = (item.get('artist_name') or 'Unknown')[:30]
            alerts = f"{COLOR_GREEN}Yes{COLOR_RESET}" if item.get('alerts') else f"{COLOR_DIM}No{COLOR_RESET}"
            bitrate = item.get('bitrate') or '-'
            record_type = item.get('record_type') or '-'

            print(f"{artist_id:<8} {COLOR_BOLD}{artist_name}{COLOR_RESET:<30} {alerts:<20} {bitrate:<10} {record_type:<8}")

        print(f"\n{COLOR_DIM}Total: {len(items)} artist(s){COLOR_RESET}")
    else:
        if query:
            db_result = show_instance.db.get_monitored_playlist_by_name(query)
        else:
            db_result = show_instance.db.get_all_monitored_playlists()

        if not db_result:
            if query:
                print(f"{COLOR_YELLOW}Playlist not found:{COLOR_RESET} {query}")
            else:
                print(f"{COLOR_YELLOW}No playlists are being monitored{COLOR_RESET}")
            input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
            return

        # Convert dict to list if single result
        if isinstance(db_result, dict):
            items = [db_result]
        else:
            items = db_result

        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 13}MONITORED PLAYLISTS{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        if len(items) == 0:
            print(f"{COLOR_YELLOW}No playlists found{COLOR_RESET}")
            input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
            return

        print(f"{COLOR_DIM}{'ID':<8} {'Name':<35} {'URL':<6} {'Alerts':<8}{COLOR_RESET}")
        print(f"{COLOR_DIM}{'-' * 8} {'-' * 35} {'-' * 6} {'-' * 8}{COLOR_RESET}")

        for item in items:
            pl_id = str(item.get('id', '-'))[:8]
            pl_name = (item.get('title') or 'Unknown')[:35]
            url_id = item.get('url', '-').split('/')[-1][:6] if item.get('url') else '-'
            alerts = f"{COLOR_GREEN}Yes{COLOR_RESET}" if item.get('alerts') else f"{COLOR_DIM}No{COLOR_RESET}"

            print(f"{pl_id:<8} {COLOR_BOLD}{pl_name}{COLOR_RESET:<35} {url_id:<6} {alerts:<20}")

        print(f"\n{COLOR_DIM}Total: {len(items)} playlist(s){COLOR_RESET}")

    input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")


def show_releases_menu():
    """Show releases menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 16}SHOW RELEASES{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Recent releases{COLOR_RESET}            {COLOR_DIM}View new releases{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Future releases{COLOR_RESET}            {COLOR_DIM}Upcoming releases{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} What releases would you like to show? {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'recent':
            print()
            days = input(f"{COLOR_CYAN}How many days back{COLOR_DIM} [7]{COLOR_RESET}: {COLOR_RESET}").strip()
            if days:
                show = Show()
                show.releases(int(days) if days.isdigit() else 7, False)
            break
        elif choice == '2' or choice.lower() == 'future':
            print()
            days = input(f"{COLOR_CYAN}How many days ahead{COLOR_DIM} [7]{COLOR_RESET}: {COLOR_RESET}").strip()
            if days:
                show = Show()
                show.releases(int(days) if days.isdigit() else 7, True)
            break
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue


def config_menu():
    """Configuration menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 14}ARTIST CONFIGURATION{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Per-Artist Settings{COLOR_RESET}       {COLOR_DIM}Configure specific artist{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}View Current Config{COLOR_RESET}       {COLOR_DIM}Show all settings{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} What would you like to configure? {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'per-artist' or choice.lower() == 'settings':
            print()
            artist = input(f"{COLOR_CYAN}Enter artist name or ID:{COLOR_RESET} ").strip()
            if artist:
                artist_lookup(artist)
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '2' or choice.lower() == 'view' or choice.lower() == 'config':
            print(f"\n{COLOR_BOLD}Current configuration:{COLOR_RESET}")
            for key, value in config._CONFIG.items():
                print(f"  {COLOR_DIM}{key}:{COLOR_RESET} {value}")
            input(f"\n{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue


def backup_menu():
    """Backup menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"
    COLOR_RED = "\033[31m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 18}BACKUP / RESTORE{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Create Backup{COLOR_RESET}               {COLOR_DIM}Backup your data{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Restore From Backup{COLOR_RESET}        {COLOR_DIM}Restore from file{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} What would you like to do? {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'create' or choice.lower() == 'backup':
            include = input(f"{COLOR_YELLOW}Include log files? [y/N]:{COLOR_RESET} ").strip().lower()
            include_logs = (include == 'y')
            print(f"\n{COLOR_CYAN}Creating backup...{COLOR_RESET}")
            backup.run(include_logs)
            print(f"{COLOR_GREEN}\nBackup complete!{COLOR_RESET}")
            input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '2' or choice.lower() == 'restore':
            confirm = input(f"{COLOR_YELLOW}Are you sure? This will replace current data. [y/N]:{COLOR_RESET} ").strip().lower()
            if confirm == 'y':
                print(f"\n{COLOR_CYAN}Restoring from backup...{COLOR_RESET}")
                backup.restore()
                print(f"{COLOR_GREEN}\nRestore complete!{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
            else:
                print(f"{COLOR_DIM}Restore cancelled{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue


def profile_menu():
    """Profile menu"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    clear_screen()
    while True:
        clear_screen()
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{' ' * 20}PROFILES{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

        print(f"{COLOR_BRIGHT_BLUE}1.{COLOR_RESET} {COLOR_BOLD}Show Profiles{COLOR_RESET}               {COLOR_DIM}List all profiles{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}2.{COLOR_RESET} {COLOR_BOLD}Add New Profile{COLOR_RESET}            {COLOR_DIM}Create a profile{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}3.{COLOR_RESET} {COLOR_BOLD}Edit Profile{COLOR_RESET}              {COLOR_DIM}Modify a profile{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}4.{COLOR_RESET} {COLOR_BOLD}Delete Profile{COLOR_RESET}            {COLOR_DIM}Remove a profile{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_BLUE}5.{COLOR_RESET} {COLOR_BOLD}Clear Profile Config{COLOR_RESET}       {COLOR_DIM}Reset profile settings{COLOR_RESET}")
        print(f"{COLOR_DIM}  {COLOR_CYAN}b.{COLOR_RESET} {COLOR_BOLD}Back{COLOR_RESET}")
        print()

        choice = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} What would you like to do? {COLOR_RESET}").strip()

        if choice == '1' or choice.lower() == 'show' or choice.lower() == 'profiles':
            print()
            pc = ProfileConfig(None)
            pc.show()
            input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '2' or choice.lower() == 'add' or choice.lower() == 'new':
            print()
            profile_name = input(f"{COLOR_CYAN}Enter profile name:{COLOR_RESET} ").strip()
            if profile_name:
                pc = ProfileConfig(profile_name)
                pc.add()
                print(f"{COLOR_GREEN}\nProfile added!{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '3' or choice.lower() == 'edit':
            print()
            profile_name = input(f"{COLOR_CYAN}Enter profile name:{COLOR_RESET} ").strip()
            if profile_name:
                pc = ProfileConfig(profile_name)
                pc.edit()
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '4' or choice.lower() == 'delete':
            print()
            profile_name = input(f"{COLOR_CYAN}Enter profile name:{COLOR_RESET} ").strip()
            if profile_name:
                pc = ProfileConfig(profile_name)
                pc.delete()
                print(f"{COLOR_GREEN}\nProfile deleted!{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice == '5' or choice.lower() == 'clear':
            print()
            profile_name = input(f"{COLOR_CYAN}Enter profile name:{COLOR_RESET} ").strip()
            if profile_name:
                pc = ProfileConfig(profile_name)
                pc.clear()
                print(f"{COLOR_GREEN}\nProfile config cleared!{COLOR_RESET}")
                input(f"{COLOR_DIM}Press Enter to continue...{COLOR_RESET}")
        elif choice.lower() == 'b':
            return
        elif choice == '':
            continue

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True,
             no_args_is_help=False)
@click.option('--whats-new', is_flag=True, help="Show release notes from this version")
@click.option('--init', is_flag=True, help="""Initialize deemon application data
              directory. Warning: if directory exists, this will delete existing config and database.""")
@click.option('--arl', help="Update ARL")
@click.option('-P', '--profile', help="Specify profile to run deemon as")
@click.version_option(__version__, '-V', '--version', message='deemon %(version)s')
@click.option('-v', '--verbose', is_flag=True, help="Show debug output")
@click.pass_context
def run(ctx, whats_new, init, arl, verbose, profile):
    """Monitoring and alerting tool for new music releases using the Deezer API.

    deemon is a free and open source tool. To report issues or to contribute,
    please visit https://github.com/digitalec/deemon
    """
    global logger
    global config
    global db

    setup_logger(log_level='DEBUG' if verbose else 'INFO', log_file=startup.get_log_file())
    logger = logging.getLogger(__name__)
    logger.debug(f"deemon {__version__}")
    logger.debug(f"command: \"{' '.join([x for x in sys.argv[1:]])}\"")
    logger.debug("Python " + platform.python_version())
    logger.debug(platform.platform())
    logger.debug(f"deemon appdata is located at {startup.get_appdata_dir()}")
    
    if whats_new:
        return startup.get_changelog(__version__)

    if init:
        app_data_path = startup.get_appdata_dir()
        startup.reinit_appdata_dir(app_data_path)

    config = Config()
    db = Database()

    db.do_upgrade()
    tid = db.get_next_transaction_id()
    config.set('tid', tid, validate=False)
    
    if arl:
        if config.set("arl", arl):
            config._Config__write_modified_config()
            reload_config = Config()
            return print(f"ARL has been successfully updated to: {reload_config.arl()}")
        else:
            return print("Error when updating ARL.")

    if profile:
        profile_config = db.get_profile(profile)
        if profile_config:
            LoadProfile(profile_config)
        else:
            logger.error(f"Profile {profile} does not exist.")
            sys.exit(1)
    else:
        profile_config = db.get_profile_by_id(1)
        if profile_config:
            LoadProfile(profile_config)

    if not any(x in sys.argv[1:] for x in ['-h', '--help']):
        last_checked: int = int(db.last_update_check())
        next_check: int = last_checked + (config.check_update() * 86400)
        if config.release_channel() != db.get_release_channel()['value']:
            # If release_channel has changed, check for latest release
            logger.debug(f"Release channel changed to '{config.release_channel()}'")
            db.set_release_channel()
            last_checked = 0
        if time.time() >= next_check or last_checked == 0:
            logger.info(f"Checking for updates ({config.release_channel()})...")
            config.set('update_available', 0, False)
            latest_ver = str(startup.get_latest_version(config.release_channel()))
            if latest_ver:
                db.set_latest_version(latest_ver)
            db.set_last_update_check()
        new_version = db.get_latest_ver()
        if parse_version(new_version) > parse_version(__version__):
            if parse_version(new_version).major > parse_version(__version__).major:
                config.set('update_available', new_version, False)
                print("*" * 80)
                logger.info(f"deemon {parse_version(new_version).major} is available. "
                            f"Please see the release notes before upgrading.")
                logger.info("Release notes available at: https://github.com/digitalec/deemon/releases")
                print("*" * 80)
            else:
                config.set('update_available', new_version, False)
                print("*" * 50)
                logger.info(f"* New version is available: v{__version__} -> v{new_version}")
                if config.release_channel() == "beta":
                    logger.info("* To upgrade, run `pip install --upgrade --pre deemon`")
                else:
                    logger.info("* To upgrade, run `pip install --upgrade deemon`")
                print("*" * 50)
                print("")

    config.set("start_time", int(time.time()), False)

    if ctx.invoked_subcommand is None:
        interactive_menu()


@run.command(name='test')
@click.option('-e', '--email', is_flag=True, help="Send test notification to configured email")
@click.option('-E', '--exclusions', metavar="URL", type=str, help="Test exclude regex pattern against URL")
def test(email, exclusions):
    """Run tests on email configuration, exclusion filters, etc."""
    if email:
        notification = notifier.Notify()
        notification.test()
    elif exclusions:
        if config.exclusion_patterns() or config.exclusion_keywords:
            tests.exclusion_test(exclusions)
        else:
            logger.info("You don't have any exclusions configured or they're disabled")

@run.command(name='global', no_args_is_help=True)
@click.argument('url', nargs=-1, required=False)
@click.option('-b', '--bitrate', metavar="BITRATE", help='Set custom bitrate for this operation')
@click.option('-o', '--download-path', metavar="PATH", type=str, help='Specify custom download directory')
def global_command(url, bitrate, download_path):
    """
    Quick download by URL (Spotify/Deezer)

    
    Examples:
        global https://www.deezer.com/album/123456
        global https://open.spotify.com/track/xyz
        global "https://deezer.com/artist/456 -b 9"
    """
    if bitrate:
        config.set('bitrate', bitrate)
    if download_path:
        config.set('download_path', download_path)

    if not url:
        print("Enter a Spotify or Deezer URL:")
        print("  (track, album, playlist, or artist)")
        print("")
        url_input = input("\033[33m>\033[0m ")
        if url_input:
            url = [url_input]
        else:
            return

    dl = download.Download()
    dl.download(None, None, None, url, None, None, None, None)


@run.command(name='download', no_args_is_help=True)
@click.argument('artist', nargs=-1, required=False)
@click.option('-m', '--monitored', is_flag=True, help='Download all currently monitored artists')
@click.option('-i', '--artist-id', multiple=True, metavar='ID', type=int, help='Download by artist ID')
@click.option('-A', '--album-id', multiple=True, metavar='ID', type=int, help='Download by album ID')
@click.option('-T', '--track-id', multiple=True, metavar='ID', type=int, help='Download by track ID')
@click.option('-u', '--url', metavar='URL', multiple=True, help='Download by URL of artist/album/track/playlist')
@click.option('-f', '--file', metavar='FILE', help='Download batch of artists or artist IDs from file', hidden=True)
@click.option('--artist-file', metavar='FILE', help='Download batch of artists or artist IDs from file')
@click.option('--album-file', metavar='FILE', help='Download batch of album IDs from file')
@click.option('--track-file', metavar='FILE', help='Download batch of track IDs from file')
@click.option('-a', '--after', 'from_date', metavar="YYYY-MM-DD", type=str, help='Grab releases released after this date')
@click.option('-B', '--before', 'to_date', metavar="YYYY-MM-DD", type=str, help='Grab releases released before this date')
@click.option('-b', '--bitrate', metavar="BITRATE", help='Set custom bitrate for this operation')
@click.option('-o', '--download-path', metavar="PATH", type=str, help='Specify custom download directory')
@click.option('-t', '--record-type', metavar="TYPE", type=str, help='Specify record types to download')
@click.option('-c', '--collection-matcher', is_flag=True, help='Use collection matcher for playlists (skip existing tracks)')
@click.option('--band', metavar='BAND', type=str, help='Band/Artist name (for use with --album)')
@click.option('--album', metavar='ALBUM', type=str, help='Album name (for use with --band)')
def download_command(artist, artist_id, album_id, url, file, bitrate,
                     record_type, download_path, from_date, to_date,
                     monitored, track_id, track_file, artist_file,
                     album_file, collection_matcher, band, album):
    """
    Download specific artist, album ID or by URL

    \b
    Examples:
        download Mozart
        download -i 100 -t album -b 9
        download --band "Slayer" --album "South of Heaven"
    """

    if bitrate:
        config.set('bitrate', bitrate)
    if download_path:
        config.set('download_path', download_path)
    if record_type:
        config.set('record_type', record_type)

    # Handle --band and --album options
    if band and album:
        # Combine into "Band - Album" format
        combined_query = f"{band} - {album}"
        artists = [combined_query]
    elif band:
        artists = [band]
    elif album:
        logger.warning("--album option requires --band option")
        return
    else:
        artists = dataprocessor.csv_to_list(artist) if artist else None

    artist_ids = [x for x in artist_id] if artist_id else None
    album_ids = [x for x in album_id] if album_id else None
    track_ids = [x for x in track_id] if track_id else None
    urls = [x for x in url] if url else None

    if file:
        logger.info("WARNING: -f/--file has been replaced with --artist-file and will be removed in future versions.")
        artist_file = file

    if download_path and download_path != "":
        if Path(download_path).exists:
            config.set('download_path', download_path)
            logger.debug(f"Download path has changed: {config.download_path()}")
        else:
            return logger.error(f"Invalid download path: {download_path}")

    dl = download.Download()
    dl.set_dates(from_date, to_date)
    dl.download(artists, artist_ids, album_ids, urls, artist_file, track_file, album_file, track_ids, monitored=monitored)


@run.command(name='monitor', context_settings={"ignore_unknown_options": False}, no_args_is_help=True)
@click.argument('artist', nargs=-1)
@click.option('-a', '--alerts', is_flag=True, help="Enable or disable alerts")
@click.option('-b', '--bitrate', metavar="BITRATE", help="Specify bitrate")
@click.option('-D', '--download', 'dl', is_flag=True, help='Download all releases matching record type')
@click.option('-d', '--download-path', type=str, metavar="PATH", help='Specify custom download directory')
@click.option('-I', '--import', 'im', metavar="PATH", help="Monitor artists/IDs from file or directory")
@click.option('-i', '--artist-id', is_flag=True, help="Monitor artist by ID")
@click.option('-p', '--playlist', is_flag=True, help='Monitor Deezer playlist by URL')
@click.option('--include-artists', is_flag=True, help='Also monitor artists from playlist')
@click.option('-u', '--url', is_flag=True, help='Monitor artist by URL')
@click.option('-R', '--remove', is_flag=True, help='Stop monitoring an artist')
@click.option('-s', '--search', 'search_flag', is_flag=True, help='Show similar artist results to choose from')
@click.option('-T', '--time-machine', type=str, metavar="YYYY-MM-DD", help="Refresh newly added artists on this date")
@click.option('-t', '--record-type', metavar="TYPE", type=str, help='Specify record types to download')
def monitor_command(artist, im, playlist, include_artists, bitrate, record_type, alerts, artist_id,
                    dl, remove, url, download_path, search_flag, time_machine):
    """
    Monitor artist for new releases by ID, URL or name.

    \b
    Examples:
        monitor Mozart
        monitor --artist-id 100
        monitor --url https://www.deezer.com/us/artist/000
    """
    monitor = Monitor()
    if download_path:
        if not Path(download_path).exists():
            return logger.error("Invalid download path provided")

    if time_machine:
        validated = validate.validate_date(time_machine)
        if validated:
            monitor.time_machine = validated
        else:
            return logger.error("Date for time machine is invalid")
    
    if not alerts:
        alerts = None

    monitor.set_options(remove, dl, search_flag)
    monitor.set_config(bitrate, alerts, record_type, download_path)

    if url:
        artist_id = True
        urls = [x.replace(",", "") for x in artist]
        artist = []
        for u in urls:
            id_from_url = u.split('/artist/')
            try:
                aid = int(id_from_url[1])
            except (IndexError, ValueError):
                logger.error(f"Invalid artist URL -- {u}")
                return
            artist.append(aid)

    if playlist:
        urls = [x.replace(",", "") for x in artist]
        playlist_id = []
        for u in urls:
            id_from_url = u.split('/playlist/')
            try:
                aid = int(id_from_url[1])
            except (IndexError, ValueError):
                logger.error(f"Invalid playlist URL -- {u}")
                return
            playlist_id.append(aid)

    if im:
        monitor.importer(im)
    elif playlist:
        monitor.playlists(playlist_id, include_artists)
    elif artist_id:
        monitor.artist_ids(dataprocessor.csv_to_list(artist))
    elif artist:
        monitor.artists(dataprocessor.csv_to_list(artist))


@run.command(name='playlist')
@click.argument('url', nargs=1, required=True)
@click.option('-c', '--collection-matcher', is_flag=True, help='Use collection matcher (skip existing tracks)')
def playlist_command(url, collection_matcher):
    """
    Download a playlist by URL

    \b
    Examples:
        playlist https://www.deezer.com/playlist/123456
        playlist -c https://www.deezer.com/playlist/123456
    """
    dl = download.Download()
    dl.download_playlist(url, use_collection_matcher=collection_matcher)


@run.command(name='refresh')
@click.argument('NAME', nargs=-1, type=str, required=False)
@click.option('-p', '--playlist', is_flag=True, help="Refresh a specific playlist by name")
@click.option('-s', '--skip-download', is_flag=True, help="Skips downloading of new releases")
@click.option('-T', '--time-machine', metavar='DATE', type=str, help='Refresh as if it were this date (YYYY-MM-DD)')
def refresh_command(name, playlist, skip_download, time_machine):
    """Check artists for new releases"""

    if time_machine:
        time_machine = validate.validate_date(time_machine)
        if not time_machine:
            return logger.error("Date for time machine is invalid")

    logger.info(":: Starting database refresh")
    refresh = Refresh(time_machine, skip_download)
    if playlist:
        if not len(name):
            return logger.warning("You must provide the name of a playlist")
        refresh.run(playlists=dataprocessor.csv_to_list(name))
    elif name:
        refresh.run(artists=dataprocessor.csv_to_list(name))
    else:
        refresh.run()


@click.group(name="show")
def show_command():
    """
    Show monitored artists and latest releases
    """


@show_command.command(name="artists")
@click.argument('artist', nargs=-1, required=False)
@click.option('-c', '--csv', is_flag=True, help='Output artists as CSV')
@click.option('-e', '--export', type=Path, help='Export CSV data to file; same as -ce')
@click.option('-f', '--filter', type=str, help='Specify filter for CSV output')
@click.option('-H', '--hide-header', is_flag=True, help='Hide header on CSV output')
@click.option('-b', '--backup', type=Path, help='Backup artist IDs to CSV, same as -cHf id -e ...')
def show_artists(artist, csv, export, filter, hide_header, backup):
    """Show artist info monitored by profile"""
    if artist:
        artist = ' '.join([x for x in artist])

    show = Show()
    show.monitoring(artist=True, query=artist, export_csv=csv, save_path=export, filter=filter, hide_header=hide_header,
                    backup=backup)


@show_command.command(name="playlists")
@click.argument('title', nargs=-1, required=False)
@click.option('-c', '--csv', is_flag=True, help='Output artists as CSV')
@click.option('-f', '--filter', type=str, help='Specify filter for CSV output')
@click.option('-H', '--hide-header', is_flag=True, help='Hide header on CSV output')
@click.option('-i', '--playlist-id', is_flag=True, help='Show playlist info by playlist ID')
def show_artists(title, playlist_id, csv, filter, hide_header):
    """Show playlist info monitored by profile"""
    if title:
        title = ' '.join([x for x in title])

    show = Show()
    show.monitoring(artist=False, query=title, export_csv=csv, filter=filter, hide_header=hide_header, is_id=playlist_id)


@show_command.command(name="releases")
@click.argument('N', default=7)
@click.option('-f', '--future', is_flag=True, help='Display future releases')
def show_releases(n, future):
    """
    Show list of new or future releases
    """
    show = Show()
    show.releases(n, future)


run.add_command(show_command)


@run.command(name="backup")
@click.option('-i', '--include-logs', is_flag=True, help='include log files in backup')
@click.option('-r', '--restore', is_flag=True, help='Restore from existing backup')
def backup_command(restore, include_logs):
    """Backup configuration and database to a tar file"""

    if restore:
        backup.restore()
    else:
        backup.run(include_logs)


# TODO @click.option does not support nargs=-1; unable to use spaces without quotations
@run.command(name="api", help="View raw API data for artist, artist ID or playlist ID", hidden=True)
@click.option('-A', '--album-id', type=int, help='Get album ID result via API')
@click.option('-a', '--artist', type=str, help='Get artist result via API')
@click.option('-i', '--artist-id', type=int, help='Get artist ID result via API')
@click.option('-l', '--limit', type=int, help='Set max number of artist results; default=1', default=1)
@click.option('-p', '--playlist-id', type=int, help='Get playlist ID result via API')
@click.option('-r', '--raw', is_flag=True, help='Dump as raw data returned from API')
def api_test(artist, artist_id, album_id, playlist_id, limit, raw):
    """View API result - for testing purposes"""
    import deezer
    dz = deezer.Deezer()
    if artist or artist_id:
        if artist:
            result = dz.api.search_artist(artist, limit=limit)['data']
        else:
            result = dz.api.get_artist(artist_id)

        if raw:
            if isinstance(result, list):
                for row in result:
                    for key, value in row.items():
                        print(f"{key}: {value}")
                    print("\n")
            else:
                for key, value in result.items():
                    print(f"{key}: {value}")
        else:
            if isinstance(result, list):
                for row in result:
                    print(f"Artist ID: {row['id']}\nArtist Name: {row['name']}\n")
            else:
                print(f"Artist ID: {result['id']}\nArtist Name: {result['name']}")

    if album_id:
        result = dz.api.get_album(album_id)

        if raw:
            for key, value in result.items():
                print(f"{key}: {value}")
        else:
            print(f"Album ID: {result['id']}\nAlbum Title: {result['title']}")

    if playlist_id:
        result = dz.api.get_playlist(playlist_id)

        if raw:
            for key, value in result.items():
                print(f"{key}: {value}")
        else:
            print(f"Playlist ID: {result['id']}\nPlaylist Title: {result['title']}")


@run.command(name="reset")
def reset_db():
    """Reset monitoring database"""
    logger.warning("** WARNING: All artists and playlists will be removed regardless of profile! **")
    confirm = input(":: Type 'reset' to confirm: ")
    if confirm.lower() == "reset":
        print("")
        db.reset_database()
    else:
        logger.info("Reset aborted. Database has NOT been modified.")
    return


@run.command(name='profile')
@click.argument('profile', required=False)
@click.option('-a', '--add', is_flag=True, help="Add new profile")
@click.option('-c', '--clear', is_flag=True, help="Clear config for existing profile")
@click.option('-d', '--delete', is_flag=True, help="Delete an existing profile")
@click.option('-e', '--edit', is_flag=True, help="Edit an existing profile")
def profile_command(profile, add, clear, delete, edit):
    """Add, modify and delete configuration profiles"""

    pc = ProfileConfig(profile)
    if profile:
        if add:
            pc.add()
        elif clear:
            pc.clear()
        elif delete:
            pc.delete()
        elif edit:
            pc.edit()
        else:
            pc.show()
    else:
        pc.show()


@run.command(name="extra")
def extra_command():
    """Fetch extra release info"""
    extra.main()


@run.command(name="search")
@click.argument('query', nargs=-1, required=False)
def search(query):
    """Interactively search and download/monitor artists"""
    if query:
        query = ' '.join(query)

    client = Search()
    client.search_menu(query)


@run.command(name="cheatsheet")
def cheatsheet_command():
    """Show a quick reference guide for deemon commands"""
    COLOR_RESET = "\033[0m"
    COLOR_BOLD = "\033[1m"
    COLOR_CYAN = "\033[36m"
    COLOR_BRIGHT_CYAN = "\033[96m"
    COLOR_GREEN = "\033[32m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BRIGHT_BLUE = "\033[94m"
    COLOR_DIM = "\033[2m"

    clear_screen()
    print(f"{COLOR_BRIGHT_CYAN}{'=' * 70}{COLOR_RESET}")
    print(f"{COLOR_BRIGHT_CYAN}{' ' * 20}DEEMON CHEATSHEET{COLOR_RESET}")
    print(f"{COLOR_BRIGHT_CYAN}{'=' * 70}{COLOR_RESET}\n")

    print(f"{COLOR_BRIGHT_BLUE}▸ {COLOR_BOLD}DOWNLOADING{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}Artist - Album:{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon download \"Artist - Album\"{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon download --band \"Artist\" --album \"Album\"{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}By URL:{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon download --url \"URL\"{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon global \"URL\"{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}Playlist:{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon playlist \"URL\"{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon playlist -c \"URL\"{COLOR_RESET}  {COLOR_DIM}# skip existing{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}Discography:{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon discography -b \"Artist\" -a \"Album\"{COLOR_RESET}")

    print(f"\n{COLOR_BRIGHT_BLUE}▸ {COLOR_BOLD}MONITORING{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}Monitor artist:{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon monitor \"Artist Name\"{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon monitor -u \"Artist URL\"{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}Refresh (check new releases):{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon refresh{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon refresh \"Artist Name\"{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}Show monitored:{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon show artists{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon show releases{COLOR_RESET}  {COLOR_DIM}# last 7 days{COLOR_RESET}")

    print(f"\n{COLOR_BRIGHT_BLUE}▸ {COLOR_BOLD}CONFIGURATION{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}Set ARL:{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon --arl YOUR_ARL_TOKEN{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}Artist settings:{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon config \"Artist Name\"{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}Profiles:{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon profile{COLOR_RESET}")
    print(f"    {COLOR_GREEN}deemon -P \"profile-name\"{COLOR_RESET}")

    print(f"\n{COLOR_BRIGHT_BLUE}▸ {COLOR_BOLD}USEFUL OPTIONS{COLOR_RESET}")
    print(f"  {COLOR_CYAN}-b, --bitrate N{COLOR_RESET}      Set quality")
    print(f"  {COLOR_DIM}1=128kbps, 3=320kbps, 9=FLAC{COLOR_RESET}")
    print(f"  {COLOR_CYAN}-o, --download-path PATH{COLOR_RESET}  Custom download location")
    print(f"  {COLOR_CYAN}-t, --record-type TYPE{COLOR_RESET}  album, ep, single, all")
    print(f"  {COLOR_CYAN}-v, --verbose{COLOR_RESET}         Show debug output")
    print(f"  {COLOR_CYAN}-h, --help{COLOR_RESET}             Show help for any command")

    print(f"\n{COLOR_BRIGHT_BLUE}▸ {COLOR_BOLD}INTERACTIVE MODE{COLOR_RESET}")
    print(f"  {COLOR_GREEN}deemon{COLOR_RESET}                    Open interactive menu")
    print(f"  {COLOR_CYAN}h{COLOR_RESET}                        Show this cheatsheet (in menu)")
    print(f"  {COLOR_CYAN}q{COLOR_RESET} or {COLOR_CYAN}e{COLOR_RESET}                   Exit")

    print(f"\n{COLOR_DIM}For more help:{COLOR_RESET} {COLOR_CYAN}deemon --help{COLOR_RESET} {COLOR_DIM}or{COLOR_RESET} {COLOR_CYAN}deemon COMMAND --help{COLOR_RESET}\n")


@run.command(name="config")
@click.argument('artist', nargs=-1, required=True)
def config_command(artist):
    """Configure per-artist settings by name or ID"""
    artist = ' '.join([x for x in artist])
    artist_lookup(artist)


@run.command(name="rollback", no_args_is_help=True)
@click.argument('num', type=int, required=False)
@click.option('-v', '--view', is_flag=True, help="View recent refresh transactions")
def rollback_command(num, view):
    """Rollback a previous monitor or refresh transaction"""
    if view:
        rollback.view_transactions()
    elif num:
        rollback.rollback_last(num)


@run.command(name="discography", no_args_is_help=True)
@click.option('-b', '--band', type=str, help='Band or artist name')
@click.option('-a', '--album', type=str, help='Album name to identify artist')
@click.option('--include-singles', is_flag=True, help='Include singles in discography')
@click.option('--print-only', is_flag=True, help='Print album URLs instead of queueing downloads')
def discography_command(band, album, include_singles, print_only):
    if not band or not album:
        if sys.stdin.isatty():
            user_input = input("Enter band and album (Band Name - Album Name): ").strip()
        else:
            user_input = sys.stdin.read().strip()
        if " - " not in user_input:
            logger.error("Input must be in the format 'Band Name - Album Name'")
            return
        parts = user_input.split(" - ", 1)
        band = band or parts[0].strip()
        album = album or parts[1].strip()
    search_url = "https://api.deezer.com/search/album"
    try:
        response = requests.get(search_url, params={'q': f"{band} {album}", 'limit': 20}, timeout=10)
        response.raise_for_status()
        data = response.json()
        albums = data.get('data') or []
        if not albums:
            logger.error(f"No album found for: {band} - {album}")
            return
        found_album = albums[0]
    except Exception as e:
        logger.error(f"Error searching for album: {e}")
        return
    artist = found_album.get('artist') or {}
    artist_id = artist.get('id')
    artist_name = artist.get('name') or band
    if not artist_id:
        logger.error("Could not resolve artist from album search")
        return
    logger.info(f"Found artist: {artist_name} (ID: {artist_id})")
    albums_url = f"https://api.deezer.com/artist/{artist_id}/albums"
    all_albums = []
    url = albums_url
    try:
        while url:
            resp = requests.get(url, params={'limit': 100}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            all_albums.extend(data.get('data') or [])
            url = data.get('next')
            if url:
                time.sleep(0.3)
    except Exception as e:
        logger.error(f"Error fetching artist discography: {e}")
        return
    if not include_singles:
        filtered = []
        for alb in all_albums:
            record_type = (alb.get('record_type') or "").lower()
            if record_type in ['album', 'ep']:
                filtered.append(alb)
    else:
        filtered = all_albums
    seen_titles = set()
    unique_albums = []
    for alb in filtered:
        title = (alb.get('title') or "").lower()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_albums.append(alb)
    if not unique_albums:
        logger.error("No albums found in discography")
        return
    album_ids = []
    deezer_urls = []
    for alb in unique_albums:
        album_id = alb.get('id')
        if album_id:
            album_ids.append(int(album_id))
            deezer_urls.append(f"https://www.deezer.com/album/{album_id}")
    if print_only:
        for url in deezer_urls:
            print(url)
        return
    if not album_ids:
        logger.error("No valid album IDs found in discography")
        return
    logger.info(f"Queueing {len(album_ids)} albums from discography for download")
    dl = download.Download()
    for album_id in album_ids:
        album_url = f"https://www.deezer.com/album/{album_id}"
        dl.download(None, None, None, [album_url], None, None, None, None, auto=False)
    if dl.queue_list:
        dl.download_queue()
    else:
        logger.info("No releases could be queued from discography results.")


@click.group(name="library")
def library_command():
    """
    Library options such as upgrading from MP3 to FLAC
    """


@library_command.command(name="upgrade")
@click.argument('library', metavar='PATH')
@click.option('-A', '--album-only', is_flag=True, help="Get album IDs instead of track IDs (Fastest)")
@click.option('-E', '--allow-exclusions', is_flag=True, help="Allow exclusions to be applied")
@click.option('-O', '--output', metavar='PATH', help="Output file to save IDs (default: current directory)")
def library_upgrade_command(library, output, album_only, allow_exclusions):
    """ (BETA) Scans MP3 files in PATH and generates a text file containing album/track IDs """
    if not output:
        output = Path.cwd()
    upgradelib.upgrade(library, output, album_only, allow_exclusions)


run.add_command(library_command)
