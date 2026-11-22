"""Safe platform-specific download of GitHub Release assets.

Does not execute installers, extract archives or bypass OS security checks.
"""
from __future__ import annotations

import hashlib
import os
import platform
import re
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import certifi

MAX_DOWNLOAD_BYTES = 600 * 1024 * 1024
REPO = "crinconlab/filter-curve-digitizer"


def platform_asset_key(system=None, machine=None):
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()
    if system == "windows" and machine in ("amd64", "x86_64"):
        return "windows-x64"
    if system == "darwin" and machine in ("x86_64", "amd64"):
        return "macos-intel"
    if system == "darwin" and machine in ("arm64", "aarch64"):
        return "macos-apple-silicon"
    if system == "linux" and machine in ("x86_64", "amd64"):
        return "linux-x86_64"
    return None


def select_release_asset(release, key=None):
    """Return exact release asset or None; never download an ambiguous package."""
    key = key or platform_asset_key()
    patterns = {
        "windows-x64": ("windows", "x64", ".exe"),
        "macos-intel": ("macos", "intel", ".zip"),
        "macos-apple-silicon": ("macos", "apple-silicon", ".zip"),
        "linux-x86_64": ("linux", "x86_64", ".appimage"),
    }
    if key not in patterns:
        return None
    terms = patterns[key]
    matches = []
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        lower = name.lower()
        if all(term in lower for term in terms) and lower.endswith(terms[-1]):
            matches.append(asset)
    return matches[0] if len(matches) == 1 else None


def github_download_url(asset):
    """Require an HTTPS release-download URL from the intended repository."""
    raw = asset.get("browser_download_url", "")
    parsed = urllib.parse.urlsplit(raw)
    prefix = "/" + REPO + "/releases/download/"
    if parsed.scheme != "https" or parsed.hostname != "github.com" or not parsed.path.startswith(prefix):
        raise ValueError("Unexpected asset download URL.")
    if parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment:
        raise ValueError("Unexpected asset download URL parameters.")
    return raw


def safe_asset_filename(asset):
    name = asset.get("name", "")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,180}", name):
        raise ValueError("Unsafe release filename.")
    if name in (".", ".."):
        raise ValueError("Unsafe release filename.")
    return name


def expected_digest(asset):
    digest = asset.get("digest")
    if not digest:
        return None
    if isinstance(digest, str) and re.fullmatch(r"sha256:[a-fA-F0-9]{64}", digest):
        return digest.split(":", 1)[1].lower()
    raise ValueError("Unsupported release checksum metadata.")


def download_release_asset(asset, directory, context=None, progress=None):
    """Stream to a private .part file and verify SHA-256 if GitHub provides it."""
    name = safe_asset_filename(asset)
    url = github_download_url(asset)
    target_dir = Path(directory).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / name
    temp = target_dir / (name + ".part")
    if destination.exists() or temp.exists():
        raise FileExistsError("A file with this name already exists in Downloads.")
    request = urllib.request.Request(url, headers={"User-Agent": "Filter-Curve-Digitizer-Updater"})
    ca_context = context or ssl.create_default_context(cafile=certifi.where())
    written = 0
    digest = hashlib.sha256()
    try:
        # Exclusive create: never overwrite an existing download or partial file.
        with open(temp, "xb") as out, urllib.request.urlopen(request, context=ca_context, timeout=30) as response:
            declared = response.headers.get("Content-Length")
            total = int(declared) if declared and declared.isdigit() else 0
            if total > MAX_DOWNLOAD_BYTES:
                raise ValueError("Download exceeds maximum permitted size.")
            while True:
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_DOWNLOAD_BYTES:
                    raise ValueError("Download exceeds maximum permitted size.")
                out.write(chunk)
                digest.update(chunk)
                if progress:
                    progress(written, total)
        if not written:
            raise ValueError("Downloaded file is empty.")
        expected = expected_digest(asset)
        if expected is not None and digest.hexdigest() != expected:
            raise ValueError("SHA-256 checksum mismatch: download rejected.")
        temp.rename(destination)
    finally:
        if temp.exists():
            temp.unlink()
    return destination


def downloads_directory():
    # Resolve consistently across platforms. The user may choose another folder in future.
    return Path.home() / "Downloads"
