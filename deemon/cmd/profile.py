import logging

from deemon.core.config import Config as config
from deemon.core.db import Database

logger = logging.getLogger(__name__)


class ProfileConfig:
    def __init__(self, profile_name):
        self.db = Database()
        self.profile_name = profile_name
        self.profile = None

    # TODO move this to utils
    @staticmethod
    def print_header(message: str = None):
        print("deemon Profile Editor")
        if message:
            print(":: " + message + "\n")
        else:
            print("")

    def edit(self):
        profile = self.db.get_profile(self.profile_name)
        self.print_header(f"Configuring '{profile['name']}' (Profile ID: {profile['id']})")
        modified = 0
        for property in profile:
            if property == "id":
                continue
            allowed_opts = config.allowed_values(property)
            if isinstance(allowed_opts, dict):
                allowed_opts = [str(x.lower()) for x in allowed_opts.values()]

            while True:
                friendly_text = property.replace("_", " ").title()
                user_input = input(f"{friendly_text} [{profile[property]}]: ").lower()
                if user_input == "":
                    break
                # TODO move to function to share with Config.set()?
                elif user_input == "false" or user_input == "0":
                    user_input = False
                elif user_input == "true" or user_input == "1":
                    user_input = True
                elif property == "name" and self.profile_name != user_input:
                    if self.db.get_profile(user_input):
                        print("Name already in use")
                        continue
                if user_input == "none" and property != "name":
                    user_input = None
                elif allowed_opts:
                    if user_input not in allowed_opts:
                        print(f"Allowed options: " + ', '.join(str(x) for x in allowed_opts))
                        continue
                logger.debug(f"User set {property} to {user_input}")
                profile[property] = user_input
                modified += 1
                break

        if modified > 0:
            user_input = input("\n:: Save these settings? [y|N] ")
            if user_input.lower() != "y":
                logger.info("No changes made, exiting...")
            else:
                self.db.update_profile(profile)
                print(f"\nProfile '{profile['name']}' has been updated!")
        else:
            print("No changes made, exiting...")

    def add(self):
        COLOR_RESET = "\033[0m"
        COLOR_CYAN = "\033[36m"
        COLOR_GREEN = "\033[32m"
        COLOR_YELLOW = "\033[33m"
        COLOR_DIM = "\033[2m"

        new_profile = {}
        profile_config = self.db.get_profile(self.profile_name)
        if profile_config:
            return logger.error(f"Profile {self.profile_name} already exists")
        else:
            logger.info("Adding new profile: " + self.profile_name)
            print(f"{COLOR_CYAN}** Any option left blank will fallback to global config **{COLOR_RESET}\n")
            new_profile['name'] = self.profile_name

        menu = [
            {'setting': 'email', 'type': str, 'text': 'Email address', 'allowed': []},
            {'setting': 'alerts', 'type': bool, 'text': 'Alerts', 'allowed': config.allowed_values('alerts')},
            {'setting': 'bitrate', 'type': str, 'text': 'Bitrate',
             'allowed': list(config.allowed_values('bitrate').values())},
            {'setting': 'record_type', 'type': str, 'text': 'Record Type',
             'allowed': config.allowed_values('record_type')},
            {'setting': 'plex_baseurl', 'type': str, 'text': 'Plex Base URL', 'allowed': []},
            {'setting': 'plex_token', 'type': str, 'text': 'Plex Token', 'allowed': []},
            {'setting': 'plex_library', 'type': str, 'text': 'Plex Library', 'allowed': []},
            {'setting': 'download_path', 'type': str, 'text': 'Download Path', 'allowed': []},
        ]

        for m in menu:
            repeat = True
            while repeat:
                user_input = input(f"{COLOR_CYAN}{m['text']}:{COLOR_RESET} ").strip()

                if user_input == "":
                    new_profile[m['setting']] = None
                    break

                # Handle boolean type
                if m['type'] == bool:
                    user_input_lower = user_input.lower()
                    if user_input_lower in ['true', '1', 'yes', 'y']:
                        new_profile[m['setting']] = True
                        break
                    elif user_input_lower in ['false', '0', 'no', 'n']:
                        new_profile[m['setting']] = False
                        break
                    else:
                        print(f"{COLOR_YELLOW} - Allowed options: True, False{COLOR_RESET}")
                        continue

                # Handle string type with allowed options
                if m['type'] == str:
                    if len(m['allowed']) > 0:
                        if user_input in m['allowed']:
                            new_profile[m['setting']] = user_input
                            break
                        else:
                            print(f"{COLOR_YELLOW} - Allowed options: {', '.join(str(x) for x in m['allowed'])}{COLOR_RESET}")
                            continue
                    else:
                        new_profile[m['setting']] = user_input
                        break

        print("\n")
        i = input(":: Save these settings? [y|N] ")
        if i.lower() != "y":
            return logger.info("Operation cancelled. No changes saved.")
        else:
            self.db.create_profile(new_profile)
            print(f"{COLOR_GREEN}Profile '{self.profile_name}' created!{COLOR_RESET}")
            logger.debug(f"New profile created with the following configuration: {new_profile}")

    def delete(self):
        profile_config = self.db.get_profile(self.profile_name)
        if not profile_config:
            return logger.error(f"Profile {self.profile_name} not found")

        if profile_config['id'] == 1:
            return logger.info("You cannot delete the default profile.")

        i = input(f":: Remove the profile '{self.profile_name}'? [y|N] ")
        if i.lower() == "y":
            self.db.delete_profile(self.profile_name)
            return logger.info("Profile " + self.profile_name + " deleted.")
        else:
            return logger.info("Operation cancelled")

    def show(self):
        COLOR_RESET = "\033[0m"
        COLOR_BOLD = "\033[1m"
        COLOR_CYAN = "\033[36m"
        COLOR_BRIGHT_CYAN = "\033[96m"
        COLOR_GREEN = "\033[32m"
        COLOR_YELLOW = "\033[33m"
        COLOR_BRIGHT_BLUE = "\033[94m"
        COLOR_DIM = "\033[2m"

        if not self.profile_name:
            profile = self.db.get_all_profiles()
            print(f"\n{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{' ' * 20}PROFILES{COLOR_RESET}")
            print(f"{COLOR_BRIGHT_CYAN}{'=' * 60}{COLOR_RESET}\n")
        else:
            profile = [self.db.get_profile(self.profile_name)]
            if len(profile) == 0:
                return logger.error(f"Profile {self.profile_name} not found")

        if not profile:
            print(f"{COLOR_YELLOW}No profiles found{COLOR_RESET}")
            return

        for idx, p in enumerate(profile, start=1):
            # Extract values with defaults
            name = p.get('name', 'N/A')
            email = p.get('email') or '-'
            alerts = p.get('alerts')
            bitrate = p.get('bitrate') or '-'
            rtype = p.get('record_type') or '-'
            url = p.get('plex_baseurl') or '-'
            dl_path = p.get('download_path') or '-'

            # Format alerts
            alerts_str = f"{COLOR_GREEN}Yes{COLOR_RESET}" if alerts else f"{COLOR_DIM}No{COLOR_RESET}"

            # Display profile
            if len(profile) > 1:
                print(f"{COLOR_BRIGHT_BLUE}{idx}.{COLOR_RESET} {COLOR_BOLD}{name}{COLOR_RESET}")
            else:
                print(f"{COLOR_BRIGHT_CYAN}Profile:{COLOR_RESET} {COLOR_BOLD}{name}{COLOR_RESET}")

            print(f"  {COLOR_DIM}{'Email':<15}{COLOR_RESET} {email}")
            print(f"  {COLOR_DIM}{'Alerts':<15}{COLOR_RESET} {alerts_str}")
            print(f"  {COLOR_DIM}{'Bitrate':<15}{COLOR_RESET} {bitrate}")
            print(f"  {COLOR_DIM}{'Record Type':<15}{COLOR_RESET} {rtype}")
            print(f"  {COLOR_DIM}{'Plex URL':<15}{COLOR_RESET} {url}")
            print(f"  {COLOR_DIM}{'Download Path':<15}{COLOR_RESET} {dl_path}")

            if len(profile) > 1:
                print()

        if len(profile) == 1:
            print()

    def clear(self):
        profile = self.db.get_profile(self.profile_name)
        self.print_header(f"Configuring '{profile['name']}' (Profile ID: {profile['id']})")
        if not profile:
            return logger.error(f"Profile {self.profile_name} not found")

        for value in profile:
            if value in ["id", "name"]:
                continue
            profile[value] = None
        self.db.update_profile(profile)
        logger.info("All values have been cleared.")
