#!/usr/bin/env python3
"""
CrossPoint Nightly Firmware (.bin) Installer for Xteink X3 (and X4).

Fetches the latest nightly firmware binary from brendanlefebvre/crossink-nightlies
and optionally flashes it to the device over USB using esptool.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "brendanlefebvre/crossink-nightlies"
API_URL = f"https://api.github.com/repos/{REPO}/releases"
ASSET_PREFIX = "firmware-x3-x4-nightly-"


def fetch_releases(limit: int = 10) -> list[dict]:
    req = urllib.request.Request(
        f"{API_URL}?per_page={limit}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "crosspoint-x3-installer"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_x3_asset(release: dict) -> dict | None:
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if name.startswith(ASSET_PREFIX) and name.endswith(".bin"):
            return asset
    return None


def download_file(url: str, dest_path: str, expected_size: int | None = None) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "crosspoint-x3-installer"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest_path, "wb") as out:
        total = expected_size or int(resp.headers.get("Content-Length") or 0)
        downloaded = 0
        chunk_size = 65536
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded * 100 // total
                print(f"\rDownloading: {downloaded:,} / {total:,} bytes ({pct}%)", end="", flush=True)
            else:
                print(f"\rDownloading: {downloaded:,} bytes", end="", flush=True)
    print()


def flash_bin(bin_path: str, port: str | None, baud: int) -> int:
    esptool_cmd = shutil.which("esptool.py") or shutil.which("esptool")
    if esptool_cmd:
        cmd = [esptool_cmd]
    else:
        cmd = [sys.executable, "-m", "esptool"]

    if port:
        cmd.extend(["--port", port])
    cmd.extend(["--baud", str(baud), "write_flash", "0x0", bin_path])

    print("Running:", " ".join(cmd))
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except FileNotFoundError:
        print(
            "Error: esptool is not installed. Install it with:\n"
            "  pip install esptool\n"
            f"Then flash manually:\n"
            f"  esptool.py --baud {baud} write_flash 0x0 {bin_path}",
            file=sys.stderr,
        )
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download and optionally flash CrossPoint nightly .bin firmware for Xteink X3."
    )
    parser.add_argument("-l", "--list", action="store_true", help="List recent nightly releases for Xteink X3")
    parser.add_argument("-t", "--tag", help="Specific release tag to download (default: latest)")
    parser.add_argument("-o", "--output", help="Output .bin file path (default: original asset filename)")
    parser.add_argument("-d", "--download-only", action="store_true", help="Only download the .bin file, do not flash")
    parser.add_argument("-f", "--flash", action="store_true", help="Flash the downloaded .bin file via esptool")
    parser.add_argument("-p", "--port", help="Serial port for flashing (e.g. /dev/ttyACM0, COM3)")
    parser.add_argument("--baud", type=int, default=460800, help="Baud rate for flashing (default: 460800)")
    args = parser.parse_args()

    try:
        releases = fetch_releases(limit=15)
    except urllib.error.URLError as exc:
        print(f"Error fetching releases from GitHub: {exc}", file=sys.stderr)
        return 1

    if args.list:
        print(f"Recent Xteink X3 nightly releases from {REPO}:")
        found = 0
        for rel in releases:
            asset = find_x3_asset(rel)
            if asset:
                found += 1
                size_mb = asset["size"] / (1024 * 1024)
                print(f"  {rel['tag_name']:32s}  {asset['name']} ({size_mb:.2f} MB)")
        if not found:
            print("  No Xteink X3 nightly assets found.")
        return 0

    target_release = None
    target_asset = None
    for rel in releases:
        if args.tag and rel["tag_name"] != args.tag:
            continue
        asset = find_x3_asset(rel)
        if asset:
            target_release = rel
            target_asset = asset
            break

    if not target_release or not target_asset:
        msg = f"No Xteink X3 nightly .bin found" + (f" for tag '{args.tag}'" if args.tag else "")
        print(f"Error: {msg}.", file=sys.stderr)
        return 1

    dest_path = args.output or target_asset["name"]
    print(f"Release : {target_release['tag_name']} ({target_release['published_at']})")
    print(f"Asset   : {target_asset['name']} ({target_asset['size']:,} bytes)")
    print(f"Saving  : {dest_path}")

    download_file(target_asset["browser_download_url"], dest_path, target_asset["size"])
    print(f"Saved   : {os.path.abspath(dest_path)}")

    if args.flash and not args.download_only:
        return flash_bin(dest_path, args.port, args.baud)

    if not args.download_only and not args.flash:
        print(
            "\nTo flash this .bin to your Xteink X3:\n"
            f"  1. Web installer: https://crosspointreader.com/install (select Xteink X3 / Advanced flash controls)\n"
            f"  2. CLI (esptool): python3 {os.path.basename(__file__)} --flash --port <PORT>\n"
            f"     or: esptool.py --port <PORT> --baud {args.baud} write_flash 0x0 {dest_path}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
