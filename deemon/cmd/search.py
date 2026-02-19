import logging
import sys

from deezer import Deezer

from deemon.cmd import download
from deemon.cmd import monitor as mon
from deemon.core import db, api
from deemon.core.config import Config as config
from deemon.utils import dates

logger = logging.getLogger(__name__)

# Color codes
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_BLUE = "\033[34m"
COLOR_MAGENTA = "\033[35m"
COLOR_CYAN = "\033[36m"
COLOR_WHITE = "\033[37m"
# Bright colors
COLOR_BRIGHT_RED = "\033[91m"
COLOR_BRIGHT_GREEN = "\033[92m"
COLOR_BRIGHT_YELLOW = "\033[93m"
COLOR_BRIGHT_BLUE = "\033[94m"
COLOR_BRIGHT_MAGENTA = "\033[95m"
COLOR_BRIGHT_CYAN = "\033[96m"


class Search:
    def __init__(self, active_api=None):
        self.api = active_api or api.PlatformAPI()
        self.artist_id: int = None
        self.artist: str = None
        self.choices: list = []
        self.status_message: str = None
        self.queue_list = []
        self.select_mode = False
        self.explicit_only = False
        self.search_results: str = None

        self.sort: str = "release_date"
        self.filter: str = None
        self.desc: bool = True

        self.gte_year = None
        self.lte_year = None
        self.eq_year = None

        self.db = db.Database()
        self.dz = Deezer()

    @staticmethod
    def truncate_artist(name: str):
        if len(name) > 45:
            return name[0:40] + "..."
        return name

    def get_latest_release(self, artist_id: int):
        try:
            all_releases = self.dz.api.get_artist_albums(artist_id)['data']
            sorted_releases = sorted(all_releases, key=lambda x: x['release_date'], reverse=True)
            latest_release = sorted_releases[0]
        except IndexError:
            return "       - No releases found"
        return f"       - Latest release: {latest_release['title']} ({dates.get_year(latest_release['release_date'])})"

    def display_monitored_status(self, artist_id: int):
        if self.db.get_monitored_artist_by_id(artist_id):
            return "[M] "
        return "    "

    @staticmethod
    def has_duplicate_artists(name: str, artist_dicts: dict):
        names = [x['name'] for x in artist_dicts if x['name'] == name]
        if len(names) > 1:
            return True

    def show_mini_queue(self):
        num_queued = len(self.queue_list)
        if num_queued > 0:
            return f" ({str(num_queued)} Queued)"
        return ""

    def search_menu(self, query: str = None):
        exit_search: bool = False
        quick_search: bool = False

        while exit_search is False:
            self.clear()
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{' ' * 15}DEEMON SEARCH{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

            if len(self.queue_list) > 0:
                self.display_options(options=f"{COLOR_GREEN}(d){COLOR_RESET} Download Queue  {COLOR_CYAN}(Q){COLOR_RESET} Show Queue  {COLOR_DIM}(b){COLOR_RESET} Back")
            if query:
                search_query = query
                query = None
            else:
                print(f"{COLOR_DIM}Enter an artist or album to search ('artist - album' for albums){COLOR_RESET}")
                print(f"{COLOR_DIM}Type 'b' to go back{COLOR_RESET}\n")
                search_query = input(f"{COLOR_BRIGHT_BLUE}>{COLOR_RESET} {self.show_mini_queue()} ")
                if search_query.lower() == "b":
                    return
                if search_query == "exit":
                    if self.exit_search():
                        sys.exit()
                    continue
                elif search_query == "d":
                    if len(self.queue_list) > 0:
                        self.start_queue()
                        continue
                elif search_query == "Q":
                    if len(self.queue_list) > 0:
                        self.queue_menu()
                    else:
                        self.status_message = "Queue is empty"
                    continue
                elif search_query == "":
                    continue

            self.clear()
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{' ' * 15}DEEMON SEARCH{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

            if ' - ' in search_query:
                artist_part, album_part = [x.strip() for x in search_query.split(' - ', 1)]
                return self.search_artist_album(artist_part, album_part)

            self.search_results = self.api.search_artist(search_query, config.query_limit())
            if not self.search_results['results']:
                self.status_message = f"{COLOR_YELLOW}No results found for:{COLOR_RESET} " + search_query
                continue

            smart_search = None
            if config.smart_search():
                for result in self.search_results['results']:
                    if result['name'].lower() == search_query.lower():
                        if not smart_search:
                            smart_search = result
                        else:
                            smart_search = None
                            break

            if smart_search:
                self.artist = smart_search['name']
                album_selected = self.album_menu(smart_search)
                if album_selected:
                    return [album_selected]

            artist_selected = self.artist_menu(self.search_results['query'], self.search_results['results'], quick_search)
            if artist_selected:
                return [artist_selected]

    def queue_menu_options(self, page: int = 0, total_pages: int = 1):
        options = []
        if len(self.queue_list) > 0:
            options.append(f"{COLOR_GREEN}(d){COLOR_RESET} Download Queue")
        options.append(f"{COLOR_YELLOW}(c){COLOR_RESET} Clear Queue")
        if page > 0:
            options.append(f"{COLOR_CYAN}(p){COLOR_RESET} Previous")
        if page < total_pages - 1:
            options.append(f"{COLOR_CYAN}(n){COLOR_RESET} Next")
        options.append(f"{COLOR_DIM}(b){COLOR_RESET} Back")

        ui_options = "  ".join(options)
        self.display_options(options=ui_options)

    def artist_menu(self, query: str, results: dict, artist_only: bool = False):
        exit_artist: bool = False
        page = 0
        page_size = 10  # Number of results per page

        while exit_artist is False:
            self.clear()
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
            print(f"{COLOR_CYAN}Search results for artist:{COLOR_RESET} {COLOR_BOLD}{query}{COLOR_RESET}")
            total_pages = (len(results) + page_size - 1) // page_size
            if total_pages > 1:
                print(f"{COLOR_DIM}Page {page + 1} of {total_pages}{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

            # Calculate page slice
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(results))
            page_results = results[start_idx:end_idx]

            for display_idx, option in enumerate(page_results, start=start_idx + 1):
                monitored_status = self.display_monitored_status(option['id'])
                if monitored_status.strip():
                    monitored_colored = f"{COLOR_GREEN}[M]{COLOR_RESET} "
                else:
                    monitored_colored = "    "

                print(f"{monitored_colored}{COLOR_BRIGHT_BLUE}{display_idx}.{COLOR_RESET} {COLOR_BOLD}{self.truncate_artist(option['name'])}{COLOR_RESET}")
                if self.has_duplicate_artists(option['name'], results):
                    print(f"    {COLOR_DIM}{self.get_latest_release(option['id'])}{COLOR_RESET}")
                    print(f"    {COLOR_DIM}       - Artist ID: {COLOR_YELLOW}{str(option['id'])}{COLOR_RESET}")
                    if not option.get('nb_album'):
                        option['nb_album'] = self.dz.api.get_artist(option['id'])['nb_album']
                    print(f"    {COLOR_DIM}       - Total releases: {COLOR_YELLOW}{str(option['nb_album'])}{COLOR_RESET}")
                    self.status_message = f"{COLOR_YELLOW}Duplicate artists found{COLOR_RESET}"

            print()
            # Build pagination options
            options = []
            options.append(f"{COLOR_DIM}(b){COLOR_RESET} Back")
            if total_pages > 1:
                if page > 0:
                    options.append(f"{COLOR_CYAN}(home){COLOR_RESET} First")
                if page < total_pages - 1:
                    options.append(f"{COLOR_CYAN}(end){COLOR_RESET} Last")
                if page > 0:
                    options.append(f"{COLOR_CYAN}(p){COLOR_RESET} Previous")
                if page < total_pages - 1:
                    options.append(f"{COLOR_CYAN}(n){COLOR_RESET} Next")
                options.append(f"{COLOR_CYAN}(g){COLOR_RESET} Goto Page")
            if len(self.queue_list) > 0:
                options.append(f"{COLOR_GREEN}(d){COLOR_RESET} Download Queue")
                options.append(f"{COLOR_CYAN}(Q){COLOR_RESET} Show Queue")

            self.display_options(options="  ".join(options))
            response = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Please choose an option or type 'exit'{self.show_mini_queue()}: {COLOR_RESET}").strip()
            if response == "d":
                if len(self.queue_list) > 0:
                    self.start_queue()
                    continue
            elif response == "Q":
                if len(self.queue_list) > 0:
                    self.queue_menu()
                else:
                    self.status_message = "Queue is empty"
                continue
            elif response == "b":
                break
            elif response == "home":
                page = 0
                continue
            elif response == "end":
                page = total_pages - 1
                continue
            elif response == "n":
                if page < total_pages - 1:
                    page += 1
                continue
            elif response == "p":
                if page > 0:
                    page -= 1
                continue
            elif response == "g":
                if total_pages > 1:
                    page_input = input(f"{COLOR_DIM}Enter page number (1-{total_pages}):{COLOR_RESET} ").strip()
                    try:
                        new_page = int(page_input) - 1
                        if 0 <= new_page < total_pages:
                            page = new_page
                        else:
                            self.status_message = f"{COLOR_YELLOW}Page must be between 1 and {total_pages}{COLOR_RESET}"
                    except ValueError:
                        self.status_message = f"{COLOR_RED}Invalid page number{COLOR_RESET}"
                continue
            elif response == "exit":
                if self.exit_search() and not artist_only:
                    sys.exit()
                else:
                    return
            elif response == "":
                continue

            try:
                response = int(response)
            except ValueError:
                self.status_message = f"{COLOR_RED}Invalid selection:{COLOR_RESET} {response}"
            else:
                response = response - 1
                if response in range(len(results)):
                    self.artist = results[response]['name']
                    if artist_only:
                        self.clear()
                        return results[response]
                    self.album_menu(results[response])
                else:
                    self.status_message = f"{COLOR_RED}Invalid selection:{COLOR_RESET} {response}"
                    continue

    @staticmethod
    def normalize_title(title: str) -> str:
        """Normalize title for fuzzy matching by removing common suffixes and normalizing case"""
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

    def search_artist_album(self, artist_query: str, album_query: str):
        """Search for a specific album by an artist"""
        self.clear()
        print(f"{COLOR_CYAN}Searching for '{COLOR_BOLD}{album_query}{COLOR_CYAN}' by '{COLOR_BOLD}{artist_query}{COLOR_CYAN}'...{COLOR_RESET}\n")

        artist_results = self.api.search_artist(artist_query, config.query_limit())
        if not artist_results['results']:
            self.status_message = f"{COLOR_YELLOW}No artists found for:{COLOR_RESET} {artist_query}"
            return None

        normalized_query = self.normalize_title(album_query)

        for artist in artist_results['results']:
            artist_albums = self.api.get_artist_albums({'artist_id': artist['id'], 'artist_name': artist['name']})['releases']

            for album in artist_albums:
                normalized_album = self.normalize_title(album['title'])
                if normalized_query in normalized_album or normalized_album in normalized_query:
                    self.artist = artist['name']
                    self.show_single_album(artist, album)
                    return

        self.status_message = f"{COLOR_YELLOW}No album '{album_query}' found for artist '{artist_query}'{COLOR_RESET}"
        return None

    def show_single_album(self, artist: dict, album: dict):
        """Display a single album and provide options to download/queue it"""
        while True:
            self.clear()
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_GREEN}Album found:{COLOR_RESET} {COLOR_BOLD}{artist['name']}{COLOR_RESET} - {COLOR_BOLD}{album['title']}{COLOR_RESET}")
            print(f"{COLOR_CYAN}Release Date:{COLOR_RESET} {COLOR_YELLOW}{dates.get_year(album['release_date'])}{COLOR_RESET}")
            print(f"{COLOR_CYAN}Type:{COLOR_RESET} {COLOR_YELLOW}{album['record_type'].title()}{COLOR_RESET}")
            if album.get('explicit_lyrics', 0) > 0:
                print(f"{COLOR_RED}[E] Explicit Content{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

            # Build options string
            options = []
            options.append(f"{COLOR_GREEN}(d){COLOR_RESET} {COLOR_BRIGHT_GREEN}Download Now{COLOR_RESET}")
            options.append(f"{COLOR_YELLOW}(q){COLOR_RESET} Queue Album")
            if len(self.queue_list) > 0:
                options.append(f"{COLOR_CYAN}(D){COLOR_RESET} Download Queue")
                options.append(f"{COLOR_CYAN}(Q){COLOR_RESET} Show Queue")
            options.append(f"{COLOR_DIM}(b){COLOR_RESET} Back")

            self.display_options(options="  ".join(options))

            response = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Please choose an option{self.show_mini_queue()}: {COLOR_RESET}").strip().lower()

            if response == "q":
                self.send_to_queue(album)
                self.status_message = f"{COLOR_GREEN}Album queued:{COLOR_RESET} {artist['name']} - {album['title']}"
            elif response == "d":
                # Download this album instantly
                self.send_to_queue(album)
                self.start_queue()
                return
            elif response == "D":
                if len(self.queue_list) > 0:
                    self.start_queue()
                else:
                    self.status_message = "Queue is empty"
            elif response == "Q":
                if len(self.queue_list) > 0:
                    self.queue_menu()
                else:
                    self.status_message = "Queue is empty"
            elif response == "b":
                return
            elif response == "":
                continue

    def get_filtered_year(self):
        if self.gte_year and self.lte_year:
            return f"{self.gte_year} - {self.lte_year}"
        elif self.gte_year:
            return f">={self.gte_year}"
        elif self.lte_year:
            return f"<={self.lte_year}"
        elif self.eq_year:
            return f"{self.eq_year}"
        else:
            return "All"

    def album_menu_header(self, artist: str, page: int = None, total_pages: int = None):
        filter_text = "All" if not self.filter else self.filter.title()
        filter_year = self.get_filtered_year()
        if self.explicit_only:
            filter_text = filter_text + " (Explicit Only)"
        desc_text = "desc" if self.desc else "asc"
        sort_text = self.sort.replace("_", " ").title() + " (" + desc_text + ")"
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_CYAN}Discography for artist:{COLOR_RESET} {COLOR_BOLD}{artist}{COLOR_RESET}")
        if total_pages and page:
            print(f"{COLOR_DIM}Page {page} of {total_pages}{COLOR_RESET}")
        print(f"{COLOR_DIM}Filter: {COLOR_YELLOW}{filter_text}{COLOR_RESET}{COLOR_DIM} | Sort: {COLOR_YELLOW}{sort_text}{COLOR_RESET}{COLOR_DIM} | Year: {COLOR_YELLOW}{filter_year}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

    def album_menu_options(self, monitored, page: int = 0, total_pages: int = 1):
        print("")
        if not monitored:
            monitor_opt = f"{COLOR_GREEN}(m){COLOR_RESET} Monitor"
        else:
            monitor_opt = f"{COLOR_YELLOW}(m){COLOR_RESET} Stop Monitoring"
        ui_filter = f"{COLOR_DIM}Filters:{COLOR_RESET} {COLOR_CYAN}(*){COLOR_RESET} All  {COLOR_CYAN}(a){COLOR_RESET} Albums  {COLOR_CYAN}(e){COLOR_RESET} EP  {COLOR_CYAN}(s){COLOR_RESET} Singles {COLOR_DIM}-{COLOR_RESET} {COLOR_CYAN}(E){COLOR_RESET} Explicit {COLOR_CYAN}(r){COLOR_RESET} Reset"
        ui_sort = f"   {COLOR_DIM}Sort:{COLOR_RESET} {COLOR_CYAN}(y){COLOR_RESET} Release Date {COLOR_DIM}(desc){COLOR_RESET}  {COLOR_CYAN}(Y){COLOR_RESET} Release Date {COLOR_DIM}(asc){COLOR_RESET}  {COLOR_CYAN}(t){COLOR_RESET} Title {COLOR_DIM}(desc){COLOR_RESET}  {COLOR_CYAN}(T){COLOR_RESET} Title {COLOR_DIM}(asc){COLOR_RESET}"
        ui_mode = f"   {COLOR_DIM}Mode:{COLOR_RESET} {COLOR_CYAN}(S){COLOR_RESET} Toggle Select"

        # Build options based on page
        options = []
        options.append(f"{COLOR_DIM}(b){COLOR_RESET} Back")
        if total_pages > 1:
            if page > 0:
                options.append(f"{COLOR_CYAN}(home){COLOR_RESET} First")
            if page < total_pages - 1:
                options.append(f"{COLOR_CYAN}(end){COLOR_RESET} Last")
            if page > 0:
                options.append(f"{COLOR_CYAN}(p){COLOR_RESET} Previous")
            if page < total_pages - 1:
                options.append(f"{COLOR_CYAN}(n){COLOR_RESET} Next")
            options.append(f"{COLOR_CYAN}(g){COLOR_RESET} Goto Page")
        if len(self.queue_list) > 0:
            options.append(f"{COLOR_GREEN}(d){COLOR_RESET} Download Queue")
            options.append(f"{COLOR_CYAN}(Q){COLOR_RESET} Show Queue")
        options.append(f"{COLOR_CYAN}(f){COLOR_RESET} Queue Filtered")
        options.append(monitor_opt)

        ui_options = "  ".join(options)
        self.display_options(ui_filter, ui_sort, ui_mode, ui_options)

    @staticmethod
    def explicit_lyrics(is_explicit):
        if is_explicit > 0:
            return f"[E]"
        else:
            return f"   "

    def item_selected(self, id):
        if self.select_mode:
            if [x for x in self.queue_list if x.album_id == id or x.track_id == id]:
                return "[*] "
            else:
                return "[ ] "
        else:
            return "    "

    def show_mode(self):
        if self.select_mode:
            return "[SELECT] "
        return ""

    def album_menu(self, artist: dict):
        exit_album_menu: bool = False
        # Rewrite DICT to follow old format used by get_artist_albums
        artist_tmp = {'artist_id': artist['id'], 'artist_name': artist['name']}

        artist_albums = self.api.get_artist_albums(artist_tmp)['releases']
        page = 0
        page_size = 15  # Number of albums per page

        while exit_album_menu is False:
            self.clear()
            filtered_choices = self.filter_choices(artist_albums)

            # Add page info to header
            total_pages = (len(filtered_choices) + page_size - 1) // page_size
            self.album_menu_header(artist['name'], page + 1, total_pages if total_pages > 1 else None)

            # Calculate page slice
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(filtered_choices))
            page_choices = filtered_choices[start_idx:end_idx]

            for display_idx, album in enumerate(page_choices, start=start_idx + 1):
                # Colorize explicit lyrics indicator
                explicit = self.explicit_lyrics(album['explicit_lyrics'])
                if explicit.strip():
                    explicit_colored = f"{COLOR_RED}[E]{COLOR_RESET}"
                else:
                    explicit_colored = "   "

                # Colorize selected indicator
                selected = self.item_selected(album['id'])
                if selected.strip():
                    selected_colored = f"{COLOR_GREEN}[*]{COLOR_RESET} "
                else:
                    selected_colored = selected

                # Colorize year
                year = dates.get_year(album['release_date'])

                print(f"{explicit_colored} {selected_colored}{COLOR_BRIGHT_BLUE}{display_idx}.{COLOR_RESET} {COLOR_DIM}({COLOR_YELLOW}{year}{COLOR_DIM}){COLOR_RESET} "
                      f"{COLOR_BOLD}{album['title']}{COLOR_RESET}")

            monitored = self.db.get_monitored_artist_by_id(artist['id'])
            self.album_menu_options(monitored, page, total_pages)

            prompt = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} {self.show_mode()}Please choose an option or type 'exit'{self.show_mini_queue()}: {COLOR_RESET}").strip()
            if prompt == "a":
                self.filter = "album"
                page = 0  # Reset to first page when filter changes
            elif prompt == "e":
                self.filter = "ep"
                page = 0
            elif prompt == "s":
                self.filter = "single"
                page = 0
            elif prompt == "*":
                self.filter = None
                page = 0
            elif prompt == "E":
                self.explicit_only ^= True
            elif prompt == "r":
                self.filter = None
                self.explicit_only = False
                self.sort = "release_date"
                self.desc = True
                self.gte_year = None
                self.lte_year = None
                self.eq_year = None
                page = 0
            elif prompt.startswith(">="):
                self.eq_year = None
                self.gte_year = int(prompt[2:])
            elif prompt.startswith("<="):
                self.eq_year = None
                self.lte_year = int(prompt[2:])
            elif prompt.startswith("="):
                self.lte_year = None
                self.gte_year = None
                self.eq_year = int(prompt[1:])
            elif prompt == "y":
                self.sort = "release_date"
                self.desc = True
            elif prompt == "Y":
                self.sort = "release_date"
                self.desc = False
            elif prompt == "t":
                self.sort = "title"
                self.desc = True
            elif prompt == "T":
                self.sort = "title"
                self.desc = False
            elif prompt == "S":
                self.select_mode ^= True
            elif prompt == "m":
                if monitored:
                    stop = True
                else:
                    stop = False
                record_type = self.filter or config.record_type()
                self.clear()
                monitor = mon.Monitor()
                monitor.set_config(None, None, record_type, None)
                monitor.set_options(stop, False, False)
                monitor.artist_ids([artist['id']])
            elif prompt == "f":
                if len(filtered_choices) > 0:
                    for item in filtered_choices:
                        self.send_to_queue(item)
                else:
                    self.status_message = "No items to add"
            elif prompt == "d":
                if len(self.queue_list) > 0:
                    self.start_queue()
            elif prompt == "Q":
                if len(self.queue_list) > 0:
                    self.queue_menu()
                else:
                    self.status_message = "Queue is empty"
            elif prompt == "home":
                page = 0
                continue
            elif prompt == "end":
                page = total_pages - 1
                continue
            elif prompt == "n":
                if page < total_pages - 1:
                    page += 1
                continue
            elif prompt == "p":
                if page > 0:
                    page -= 1
                continue
            elif prompt == "g":
                if total_pages > 1:
                    page_input = input(f"{COLOR_DIM}Enter page number (1-{total_pages}):{COLOR_RESET} ").strip()
                    try:
                        new_page = int(page_input) - 1
                        if 0 <= new_page < total_pages:
                            page = new_page
                        else:
                            self.status_message = f"{COLOR_YELLOW}Page must be between 1 and {total_pages}{COLOR_RESET}"
                    except ValueError:
                        self.status_message = f"{COLOR_RED}Invalid page number{COLOR_RESET}"
                continue
            elif prompt == "b":
                break
            elif prompt == "":
                self.status_message = "Hint: to exit, type 'exit'!"
                continue
            elif prompt == "exit":
                if self.exit_search():
                    sys.exit()
            else:
                try:
                    selected_index = (int(prompt) - 1)
                except ValueError:
                    self.status_message = "Invalid filter, sort or option provided"
                    continue
                except IndexError:
                    self.status_message = "Invalid selection, please choose from above"
                    continue

                if selected_index in range(len(filtered_choices)):
                    if self.select_mode:
                        selected_item = filtered_choices[selected_index]
                        self.send_to_queue(selected_item)
                        continue
                    else:
                        # Show album options menu instead of going straight to track menu
                        self.album_options_menu(filtered_choices[selected_index])
                else:
                    self.status_message = "Invalid selection, please choose from above"
                    continue

    def track_menu_options(self, page: int = 0, total_pages: int = 1):
        options = []
        options.append(f"{COLOR_DIM}(b){COLOR_RESET} Back")
        if page > 0:
            options.append(f"{COLOR_CYAN}(p){COLOR_RESET} Previous")
        if page < total_pages - 1:
            options.append(f"{COLOR_CYAN}(n){COLOR_RESET} Next")
        if len(self.queue_list) > 0:
            options.append(f"{COLOR_GREEN}(d){COLOR_RESET} Download Queue")
            options.append(f"{COLOR_CYAN}(Q){COLOR_RESET} Show Queue")

        ui_options = "  ".join(options)
        self.display_options(options=ui_options)

    def track_menu_header(self, album, page: int = None, total_pages: int = None):
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
        print(f"{COLOR_CYAN}Artist:{COLOR_RESET} {COLOR_BOLD}{self.artist}{COLOR_RESET}  |  {COLOR_CYAN}Album:{COLOR_RESET} {COLOR_BOLD}{album['title']}{COLOR_RESET}")
        if total_pages and page:
            print(f"{COLOR_DIM}Page {page} of {total_pages}{COLOR_RESET}")
        print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

    def album_options_menu(self, album: dict):
        """Show options for a single album when selected from album list"""
        while True:
            self.clear()
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_GREEN}Selected Album:{COLOR_RESET} {COLOR_BOLD}{self.artist}{COLOR_RESET} - {COLOR_BOLD}{album['title']}{COLOR_RESET}")
            print(f"{COLOR_CYAN}Release Date:{COLOR_RESET} {COLOR_YELLOW}{dates.get_year(album['release_date'])}{COLOR_RESET}")
            print(f"{COLOR_CYAN}Type:{COLOR_RESET} {COLOR_YELLOW}{album['record_type'].title()}{COLOR_RESET}")
            if album.get('explicit_lyrics', 0) > 0:
                print(f"{COLOR_RED}[E] Explicit Content{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

            options = []
            options.append(f"{COLOR_GREEN}(d){COLOR_RESET} {COLOR_BRIGHT_GREEN}Download Now{COLOR_RESET}")
            options.append(f"{COLOR_YELLOW}(q){COLOR_RESET} Queue Album")
            options.append(f"{COLOR_CYAN}(t){COLOR_RESET} View Tracks")
            if len(self.queue_list) > 0:
                options.append(f"{COLOR_CYAN}(D){COLOR_RESET} Download Queue")
                options.append(f"{COLOR_CYAN}(Q){COLOR_RESET} Show Queue")
            options.append(f"{COLOR_DIM}(b){COLOR_RESET} Back to Album List")

            self.display_options(options="  ".join(options))

            response = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Please choose an option{self.show_mini_queue()}: {COLOR_RESET}").strip().lower()

            if response == "q":
                self.send_to_queue(album)
                self.status_message = f"{COLOR_GREEN}Album queued:{COLOR_RESET} {self.artist} - {album['title']}"
                break
            elif response == "d":
                # Download this album instantly
                self.send_to_queue(album)
                self.start_queue()
                return
            elif response == "t":
                self.track_menu(album)
                return
            elif response == "D":
                if len(self.queue_list) > 0:
                    self.start_queue()
                else:
                    self.status_message = "Queue is empty"
                return
            elif response == "Q":
                if len(self.queue_list) > 0:
                    self.queue_menu()
                else:
                    self.status_message = "Queue is empty"
                return
            elif response == "b":
                return
            elif response == "":
                continue

    def track_menu(self, album):
        exit_track_menu: bool = False
        track_list = self.dz.api.get_album_tracks(album['id'])['data']
        self.select_mode = True
        page = 0
        page_size = 20  # Number of tracks per page

        while not exit_track_menu:
            self.clear()
            total_pages = (len(track_list) + page_size - 1) // page_size
            self.track_menu_header(album, page + 1, total_pages if total_pages > 1 else None)

            # Calculate page slice
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(track_list))
            page_tracks = track_list[start_idx:end_idx]

            for display_idx, track in enumerate(page_tracks, start=start_idx + 1):
                # Colorize selected indicator
                selected = self.item_selected(track['id'])
                if selected.strip():
                    selected_colored = f"{COLOR_GREEN}[*]{COLOR_RESET} "
                else:
                    selected_colored = selected

                print(f"{selected_colored}{COLOR_BRIGHT_BLUE}{display_idx}.{COLOR_RESET} {COLOR_BOLD}{track['title']}{COLOR_RESET}")
            self.track_menu_options(page, total_pages)

            prompt = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} {self.show_mode()}Please choose an option or type 'exit'{self.show_mini_queue()}: {COLOR_RESET}").strip()
            if prompt == "d":
                if len(self.queue_list) > 0:
                    self.start_queue()
                else:
                    self.status_message = "Queue is empty"
            elif prompt == "Q":
                if len(self.queue_list) > 0:
                    self.queue_menu()
                else:
                    self.status_message = "Queue is empty"
            elif prompt == "n":
                if page < total_pages - 1:
                    page += 1
                continue
            elif prompt == "p":
                if page > 0:
                    page -= 1
                continue
            elif prompt == "b":
                self.select_mode = False
                break
            elif prompt == "":
                self.status_message = "Hint: to exit, type 'exit'!"
                continue
            elif prompt == "exit":
                if self.exit_search():
                    sys.exit()
            else:
                try:
                    selected_index = (int(prompt) - 1)
                except ValueError:
                    self.status_message = "Invalid filter, sort or option provided"
                    continue
                except IndexError:
                    self.status_message = "Invalid selection, please choose from above"
                    continue

                if selected_index in range(len(track_list)):
                    selected_item = track_list[selected_index]
                    selected_item['record_type'] = 'track'
                    self.send_to_queue(selected_item)
                    continue
                else:
                    self.status_message = "Invalid selection, please choose from above"
                    continue

    def search_header(self):
        pass

    def queue_menu(self):
        exit_queue_list = False
        page = 0
        page_size = 15  # Number of queue items per page

        while exit_queue_list is False:
            self.clear()
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{' ' * 20}DOWNLOAD QUEUE{COLOR_RESET}")

            total_pages = max(1, (len(self.queue_list) + page_size - 1) // page_size)
            if len(self.queue_list) > page_size:
                print(f"{COLOR_DIM}Page {page + 1} of {total_pages}{COLOR_RESET}")

            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")

            # Calculate page slice
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(self.queue_list))
            page_queue = self.queue_list[start_idx:end_idx]

            for display_idx, q in enumerate(page_queue, start=start_idx + 1):
                if q.album_title:
                    print(f"{COLOR_BRIGHT_BLUE}{display_idx}.{COLOR_RESET} {COLOR_BOLD}{q.artist_name}{COLOR_RESET} - {COLOR_YELLOW}{q.album_title}{COLOR_RESET}")
                else:
                    print(f"{COLOR_BRIGHT_BLUE}{display_idx}.{COLOR_RESET} {COLOR_BOLD}{q.artist_name}{COLOR_RESET} - {COLOR_YELLOW}{q.track_title}{COLOR_RESET}")
            print("")
            self.queue_menu_options(page, total_pages)
            response = input(f"{COLOR_BRIGHT_BLUE}::{COLOR_RESET} Please choose an option or type exit {self.show_mini_queue()}: {COLOR_RESET}").strip()
            if response == "d":
                if len(self.queue_list) > 0:
                    self.start_queue()
                else:
                    self.status_message = "Queue is empty"
            if response == "c":
                self.queue_list = []
                break
            if response == "n":
                if page < total_pages - 1:
                    page += 1
                continue
            if response == "p":
                if page > 0:
                    page -= 1
                continue
            if response == "b":
                break
            if response == "exit":
                if self.exit_search():
                    sys.exit()
            try:
                response = int(response) - 1
            except ValueError:
                continue
            if response in range(len(self.queue_list)):
                self.queue_list.pop(response)
                if len(self.queue_list) == 0:
                    break
                # Adjust page if we removed the last item on current page
                if start_idx >= len(self.queue_list) and page > 0:
                    page -= 1

    def exit_search(self):
        if len(self.queue_list) > 0:
            exit_all = input(":: Quit before downloading queue? [y|N] ")
            if exit_all.lower() != 'y':
                return False
        return True

    def display_options(self, filter=None, sort=None, mode=None, options=None):
        if filter:
            print(filter)
        if sort:
            print(sort)
        if mode:
            print(mode)
        if options:
            print("")
            print(options)
        if self.status_message:
            print(f"{COLOR_BRIGHT_YELLOW}** {self.status_message} **{COLOR_RESET}")
            self.status_message = None

    @staticmethod
    def clear():
        from os import system, name
        if name == 'nt':
            _ = system('cls')
        else:
            _ = system('clear')

    def filter_choices(self, choices):
        apply_filter = [x for x in choices if x['record_type'] == self.filter or self.filter is None]
        if self.explicit_only:
            apply_filter = [x for x in apply_filter if x['explicit_lyrics'] > 0]

        if any([self.gte_year, self.lte_year, self.eq_year]):
            if self.eq_year:
                apply_filter = [x for x in apply_filter if dates.get_year(x['release_date']) == self.eq_year]
            elif self.gte_year and self.lte_year:
                apply_filter = [x for x in apply_filter if dates.get_year(x['release_date']) >= self.gte_year and dates.get_year(x['release_date']) <= self.lte_year]
            elif self.gte_year:
                apply_filter = [x for x in apply_filter if dates.get_year(x['release_date']) >= self.gte_year]
            elif self.lte_year:
                apply_filter = [x for x in apply_filter if dates.get_year(x['release_date']) <= self.lte_year]

        return sorted(apply_filter, key=lambda x: x[self.sort], reverse=self.desc)

    def start_queue(self):
        self.clear()
        dl = download.Download(active_api=self.api)
        dl.queue_list = self.queue_list
        download_result = dl.download_queue()
        self.queue_list.clear()
        if download_result:
            self.status_message = "Downloads complete"
        else:
            self.status_message = "Downloads failed, please check logs"

    def send_to_queue(self, item):
        if item['record_type'] in ['album', 'ep', 'single']:
            album = {
                'id': item['id'],
                'title': item['title'],
                'link': item['link'],
                'artist': {
                    'name': self.artist
                }
            }
            for i, q in enumerate(self.queue_list):
                if q.album_id == album['id']:
                    del self.queue_list[i]
                    return
            self.queue_list.append(download.QueueItem(album=album))
        elif item['record_type'] == 'track':
            track = {
                'id': item['id'],
                'title': item['title'],
                'link': item['link'],
                'artist': {
                    'name': self.artist
                }
            }
            for i, q in enumerate(self.queue_list):
                if q.track_id == track['id']:
                    del self.queue_list[i]
                    return

            self.queue_list.append(download.QueueItem(track=track))

        else:
            logger.error("Unknown record type. Please report this to add support:")
            logger.error(item)
