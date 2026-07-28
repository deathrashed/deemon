import argparse
import os
import re
import subprocess
import sys


REPORT_BAR = "────────────────────────────────────────────────────────────"


def _clean(text: str) -> str:
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)


def _heading(title: str, detail: str = "") -> list:
    lines = [REPORT_BAR, f"  ❋  {title}", REPORT_BAR]
    if detail:
        lines.extend([f"  {detail}", ""])
    return lines


def _section(title: str) -> list:
    return [REPORT_BAR, f"  ⊕  {title}", REPORT_BAR]


def normalize_macos_user_home() -> None:
    if sys.platform != "darwin":
        return
    console_user = subprocess.run(
        ["stat", "-f", "%Su", "/dev/console"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if not console_user or console_user in {"root", "loginwindow"}:
        return
    console_home = subprocess.run(
        ["dscl", ".", "-read", f"/Users/{console_user}", "NFSHomeDirectory"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    if len(console_home) < 2 or not os.path.isdir(console_home[-1]):
        return
    os.environ["HOME"] = console_home[-1]
    os.environ["XDG_CONFIG_HOME"] = os.path.join(console_home[-1], ".config")


def render_report(raw: str, status: int) -> str:
    clean = _clean(raw)
    lines = [line.rstrip() for line in clean.splitlines()]
    artist_match = re.search(r"^Found artist: (.+?) \(ID: (\d+)\)$", clean, re.MULTILINE)
    queued = re.findall(r"^\[\+\] Queueing: (.+?)\.\.\.$", clean, re.MULTILINE)
    errors = [line.strip() for line in lines if "error" in line.lower() or "failed" in line.lower() or "No ARL" in line]
    artist = artist_match.group(1) if artist_match else "Discography download"
    report = _heading(artist, "Discography download · Deezer collection")
    if artist_match:
        report.extend([f"  Deezer artist ID: {artist_match.group(2)}", ""])
    if queued:
        report.extend(_section("RELEASES QUEUED"))
        report.extend(f"  ⊜  {release}" for release in queued)
        report.append("")
    report.extend(_section("SUMMARY"))
    report.append(f"    Releases queued: {len(queued)}")
    if status == 0 and "Downloads complete!" in clean:
        report.extend(["", REPORT_BAR, f"  󰄬  Done! {len(queued)} release(s) sent to Deemix.", REPORT_BAR])
    else:
        report.extend(_section("⚠  NEEDS ATTENTION"))
        report.extend(f"  •  {line}" for line in errors[-3:] or ["deemon did not report a completed download."])
    return "\n".join(report)


def render_preview(raw: str, status: int, artist: str, album: str) -> str:
    clean = _clean(raw)
    releases = re.findall(r"^\s*\d+\.\s+(.+?)\s+\[([A-Z]+) · ([^\]]+)\]$", clean, re.MULTILINE)
    errors = [line.strip() for line in clean.splitlines() if "error" in line.lower() or "failed" in line.lower()]
    report = _heading(artist, f"Discography preview · resolving via: {album}")
    if status == 0 and releases:
        report.extend(_section("RELEASES THAT WOULD BE DOWNLOADED"))
        for title, record_type, year in releases:
            report.append(f"  ⊜  {title}  ·  {record_type.title()} · {year}")
        report.extend(["", *_section("SUMMARY"), f"    Releases to download: {len(releases)}", "", REPORT_BAR, "  ◌  Preview only. No downloads were started.", REPORT_BAR])
    else:
        report.extend(_section("⚠  NEEDS ATTENTION"))
        report.extend(f"  •  {line}" for line in errors or ["No releases could be resolved."])
    return "\n".join(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Keyboard Maestro-friendly discography command")
    parser.add_argument("--preview", action="store_true", help="Show releases without downloading")
    parser.add_argument("artist")
    parser.add_argument("album")
    args = parser.parse_args()
    normalize_macos_user_home()
    command = [sys.executable, "-m", "deemon", "discography", "--band", args.artist, "--album", args.album]
    if args.preview:
        command.append("--preview")
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        print(render_preview(result.stdout + result.stderr, result.returncode, args.artist, args.album))
        raise SystemExit(result.returncode)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    print(render_report(result.stdout + result.stderr, result.returncode))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
