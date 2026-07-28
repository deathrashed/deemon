import os
import unicodedata


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
BRIGHT_CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"

WORDMARK = (
    "██████╗ ███████╗███████╗███╗   ███╗ ██████╗ ███╗   ██╗",
    "██╔══██╗██╔════╝██╔════╝████╗ ████║██╔═══██╗████╗  ██║",
    "██║  ██║█████╗  █████╗  ██╔████╔██║██║   ██║██╔██╗ ██║",
    "██║  ██║██╔══╝  ██╔══╝  ██║╚██╔╝██║██║   ██║██║╚██╗██║",
    "██████╔╝███████╗███████╗██║ ╚═╝ ██║╚██████╔╝██║ ╚████║",
    "╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝",
)


def width():
    try:
        columns = os.get_terminal_size().columns
    except OSError:
        columns = 80
    return max(60, min(79, columns - 1))


def visible_width(value):
    return sum(2 if unicodedata.east_asian_width(char) in {'F', 'W'} else 1 for char in value)


def centered(value, available=None):
    available = available or width() - 2
    padding = max(0, (available - visible_width(value)) // 2)
    return f"{' ' * padding}{value}"


def _centered_line(value):
    value = centered(value)
    return f"{value}{' ' * max(0, width() - 2 - visible_width(value))}"


def _border(left, fill, right):
    return f"{BRIGHT_CYAN}{left}{fill * (width() - 2)}{right}{RESET}"


def main_header():
    print(_border("╭", "─", "╮"))
    print(f"{BRIGHT_CYAN}│{RESET}{' ' * (width() - 2)}{BRIGHT_CYAN}│{RESET}")
    for line in WORDMARK:
        print(f"{BRIGHT_CYAN}│{RESET}{CYAN}{_centered_line(line)}{RESET}{BRIGHT_CYAN}│{RESET}")
    print(f"{BRIGHT_CYAN}│{RESET}{' ' * (width() - 2)}{BRIGHT_CYAN}│{RESET}")
    tagline = "SEARCH  •  DOWNLOAD  •  MONITOR"
    print(f"{BRIGHT_CYAN}│{RESET}{CYAN}{_centered_line(tagline)}{RESET}{BRIGHT_CYAN}│{RESET}")
    print(f"{BRIGHT_CYAN}│{RESET}{' ' * (width() - 2)}{BRIGHT_CYAN}│{RESET}")
    print(_border("╰", "─", "╯"))


def header(title, subtitle="", icon=""):
    title_text = f"{icon}  {title}"
    print(_border("╭", "─", "╮"))
    print(f"{BRIGHT_CYAN}│{RESET}{CYAN}{_centered_line(title_text)}{RESET}{BRIGHT_CYAN}│{RESET}")
    if subtitle:
        print(f"{BRIGHT_CYAN}│{RESET}{DIM}{_centered_line(subtitle)}{RESET}{BRIGHT_CYAN}│{RESET}")
    print(_border("╰", "─", "╯"))


def status(items):
    text = "  •  ".join(items)
    print(f"\n{DIM}{centered(text)}{RESET}")


def section(icon, label):
    print()
    print(f"  {BLUE}{icon}{RESET} {CYAN}{label.upper()}{RESET}")
    print(f"  {DIM}{'─' * (width() - 4)}{RESET}")


def option(key, icon, label, description=""):
    print(f"   {BLUE}{key:<2}{RESET} {CYAN}{icon}{RESET}  {label:<21}{DIM}{description}{RESET}")


def detail(label, value):
    print(f"  {CYAN}{label:<14}{RESET}{BOLD}{value}{RESET}")


def hint(value):
    print(f"\n{DIM}{centered(value)}{RESET}")


def prompt(label="Choice"):
    return input(f"\n{BLUE}❯{RESET} {label}:{RESET} ").strip()


def input_screen(title, subtitle, prompt_label, hint_text="", icon="󰈙"):
    header(title, subtitle, icon)
    if hint_text:
        hint(hint_text)
    return input(f"\n{BLUE}❯{RESET} {prompt_label}:{RESET} ").strip()
