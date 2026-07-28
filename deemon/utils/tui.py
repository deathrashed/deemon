import os


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
BRIGHT_CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"


def _width():
    try:
        columns = os.get_terminal_size().columns
    except OSError:
        columns = 72
    return max(60, min(columns - 2, 84))


def header(title, subtitle=""):
    width = _width()
    line = "─" * (width - 2)
    print(f"{BRIGHT_CYAN}╭{line}╮{RESET}")
    title_padding = max(1, width - len(title) - 3)
    print(f"{BRIGHT_CYAN}│{RESET} {BOLD}{CYAN}{title}{RESET}{' ' * title_padding}{BRIGHT_CYAN}│{RESET}")
    if subtitle:
        subtitle_padding = max(1, width - len(subtitle) - 3)
        print(f"{BRIGHT_CYAN}│{RESET} {DIM}{subtitle}{RESET}{' ' * subtitle_padding}{BRIGHT_CYAN}│{RESET}")
    print(f"{BRIGHT_CYAN}╰{line}╯{RESET}")


def status(items):
    print(f"\n{DIM}{'  •  '.join(items)}{RESET}\n")


def section(icon, label):
    print(f"{BLUE}{icon} {BOLD}{label}{RESET}")
    print(f"{DIM}{'─' * (_width() - 4)}{RESET}")


def option(key, icon, label, description=""):
    text = f"  {BLUE}{key:>2}{RESET}  {CYAN}{icon}{RESET}  {BOLD}{label:<22}{RESET}"
    if description:
        text += f"{DIM}{description}{RESET}"
    print(text)


def prompt(label="Choice"):
    return input(f"\n{BLUE}❯{RESET} {BOLD}{label}:{RESET} ").strip()
