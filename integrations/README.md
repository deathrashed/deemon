# Integrations

Optional launcher assets are kept separate from the Python package.

- `keyboard-maestro/`: importable Keyboard Maestro macros. The checked-in examples target this checkout and use its `scripts/` wrappers by absolute path, so they also work from Keyboard Maestro's restricted shell environment.
- `raycast-shell/`: Raycast Script Commands. They also call `deemon` from `PATH` and do not embed a personal home directory or checkout path.

Keyboard Maestro includes two additional discography exports:

- `Discography Preview.kmmacros`: lists the exact releases, type, and year without downloading.
- `Discography Clean Report.kmmacros`: downloads the selected discography and displays a colour-free summary instead of raw CLI logging.
- `Quick Get Preview.kmmacros`: resolves a Deezer or Spotify URL and shows the artist, title, type, and Deezer target before queueing.
- `Show Recent Releases.kmmacros`: opens the current monitored-release list in a result window.
- `Refresh Monitored (No Download).kmmacros`: checks monitored artists for releases while explicitly skipping downloads.

The checked-in macros call `scripts/km-discography.sh` or `scripts/deemon-wrapper.sh`
by absolute path. This is intentional: Keyboard Maestro does not reliably inherit an
interactive shell `PATH`. Public users should replace `/Users/rd/Scripts/Riley/deemon`
with their own checkout path after import.

The full Raycast extension is a separate project and is not vendored here.
