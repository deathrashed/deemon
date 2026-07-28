import argparse
import re
import subprocess
import sys
from typing import Tuple

from deemon.core.resolver import InputResolver, ResolutionStatus
from deemon.integrations.km import REPORT_BAR, _heading, _section, normalize_macos_user_home


def _clean(text: str) -> str:
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)


def _summary(item) -> str:
    return f"{item.artist} - {item.title}" if item.artist else item.title


def render_preview(value: str) -> Tuple[str, bool]:
    from deemon.core.config import Config

    Config()
    result = InputResolver().resolve(value)
    report = _heading("QUICK GET", f"Resolving: {value}")
    if result.status is ResolutionStatus.RESOLVED:
        report.extend(_section("READY TO QUEUE"))
        for item in result.items:
            report.extend(
                [
                    f"  ⊜  {_summary(item)}",
                    f"     {item.kind.title()} · {item.deezer_url}",
                ]
            )
        report.extend(["", *_section("SUMMARY"), f"    Ready to queue: {len(result.items)} item(s)", "", REPORT_BAR, "  ◌  Preview only. No downloads were started.", REPORT_BAR])
        return "\n".join(report), True
    if result.candidates:
        report.extend(_section("⚠  NEEDS A MORE SPECIFIC SEARCH"))
        for candidate in result.candidates:
            summary = f"{candidate.artist} - {candidate.title}" if candidate.artist else candidate.title
            report.append(f"  ⊜  {summary}  ·  {candidate.deezer_url}")
    else:
        report.extend(_section("⚠  NEEDS ATTENTION"))
        report.append("  No safe Deezer match was found.")
    if result.errors:
        report.extend(["", *[f"  •  {error}" for error in result.errors]])
    return "\n".join(report), False


def render_download_report(value: str) -> Tuple[str, bool]:
    preview, resolved = render_preview(value)
    if not resolved:
        return preview, False
    result = subprocess.run(
        [sys.executable, "-m", "deemon", "get", "--yes", value],
        capture_output=True,
        text=True,
        check=False,
    )
    output = _clean(result.stdout + result.stderr)
    report = preview.replace("QUICK GET", "QUICK GET DOWNLOAD", 1).replace("Preview only. No downloads were started.", "Download requested.").splitlines()
    if result.returncode == 0 and "Downloads complete!" in output:
        report = [line.replace("Download requested.", "Done! Deemix finished processing the selected item(s).") for line in report]
        return "\n".join(report), True
    errors = [line.strip() for line in output.splitlines() if "error" in line.lower() or "failed" in line.lower() or "No ARL" in line]
    report = [line for line in report if line != "Download requested."]
    report.extend(["", *_section("⚠  NEEDS ATTENTION"), *[f"  •  {line}" for line in errors[-3:] or ["deemon did not report a completed download."]]])
    return "\n".join(report), False


def main() -> None:
    parser = argparse.ArgumentParser(description="Keyboard Maestro-friendly Quick Get command")
    parser.add_argument("--preview", action="store_true", help="Show the resolved download plan without downloading")
    parser.add_argument("input_value", nargs="+", help="Deezer/Spotify URL or artist and album query")
    args = parser.parse_args()
    normalize_macos_user_home()
    value = " ".join(args.input_value)
    report, success = render_preview(value) if args.preview else render_download_report(value)
    print(report)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
