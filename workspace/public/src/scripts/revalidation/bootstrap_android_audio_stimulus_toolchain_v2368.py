#!/usr/bin/env python3
"""Bootstrap the private Android/JDK toolchain for the audio route stimulus.

This host-only helper stages a private Temurin JDK plus Android SDK command-line
installation under workspace/private so V2366 can build A90AudioRouteStimulus.dex.
It never writes outside workspace/private except for temporary extraction dirs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


RUN_ID = "V2368"
ROOT = Path(__file__).resolve().parents[5]
PRIVATE_INPUTS = ROOT / "workspace/private/inputs"
DOWNLOAD_DIR = PRIVATE_INPUTS / "downloads/v2368-android-audio-toolchain"
JDK_BASE = PRIVATE_INPUTS / "toolchains/temurin17-v2368"
ANDROID_SDK = PRIVATE_INPUTS / "android-sdk-v2368"
CMDLINE_TOOLS_DIR = ANDROID_SDK / "cmdline-tools/latest"

# Pin the exact archives observed from official Adoptium/Android downloads for this run.
JDK_URL = (
    "https://github.com/adoptium/temurin17-binaries/releases/download/"
    "jdk-17.0.19%2B10/OpenJDK17U-jdk_x64_linux_hotspot_17.0.19_10.tar.gz"
)
CMDLINE_TOOLS_URL = "https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip"
SDK_PACKAGES = ("platforms;android-31", "build-tools;35.0.0")
ANDROID_JAR = ANDROID_SDK / "platforms/android-31/android.jar"
D8 = ANDROID_SDK / "build-tools/35.0.0/d8"
MANIFEST = ROOT / "workspace/private/builds/audio/v2368-android-audio-toolchain/manifest.json"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_name(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if not name:
        raise ValueError(f"URL has no archive filename: {url}")
    return name


def run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


def download(url: str, dest: Path, *, force: bool) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        return {
            "path": rel(dest),
            "sha256": sha256(dest),
            "downloaded": False,
            "size": dest.stat().st_size,
            "url": url,
        }
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    run(["curl", "-L", "--fail", "--show-error", "--output", str(tmp), url])
    tmp.replace(dest)
    return {
        "path": rel(dest),
        "sha256": sha256(dest),
        "downloaded": True,
        "size": dest.stat().st_size,
        "url": url,
    }


def extract_jdk(archive: Path, *, force: bool) -> Path:
    marker = JDK_BASE / ".v2368-ready"
    if marker.exists() and not force:
        java_home = read_marker(marker)
        if (java_home / "bin/javac").exists():
            return java_home
    shutil.rmtree(JDK_BASE, ignore_errors=True)
    JDK_BASE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a90-jdk-v2368-") as tmp_dir:
        with tarfile.open(archive, "r:gz") as tar_archive:
            tar_archive.extractall(tmp_dir)
        candidate_roots = [
            candidate
            for candidate in Path(tmp_dir).iterdir()
            if candidate.is_dir() and (candidate / "bin/javac").exists()
        ]
        if len(candidate_roots) != 1:
            raise RuntimeError(f"expected one JDK root in {archive}, found {len(candidate_roots)}")
        java_home = JDK_BASE / candidate_roots[0].name
        shutil.move(str(candidate_roots[0]), str(java_home))
    marker.write_text(rel(java_home) + "\n")
    return java_home


def read_marker(marker: Path) -> Path:
    text = marker.read_text().strip()
    path = ROOT / text if not text.startswith("/") else Path(text)
    return path


def chmod_bin_tools(directory: Path) -> None:
    bin_dir = directory / "bin"
    if not bin_dir.exists():
        return
    for item in bin_dir.iterdir():
        if item.is_file():
            item.chmod(item.stat().st_mode | 0o111)


def extract_cmdline_tools(archive: Path, *, force: bool) -> None:
    if (CMDLINE_TOOLS_DIR / "bin/sdkmanager").exists() and not force:
        chmod_bin_tools(CMDLINE_TOOLS_DIR)
        return
    if CMDLINE_TOOLS_DIR.exists():
        shutil.rmtree(CMDLINE_TOOLS_DIR)
    CMDLINE_TOOLS_DIR.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a90-cmdline-tools-v2368-") as tmp_dir:
        with zipfile.ZipFile(archive) as zip_archive:
            zip_archive.extractall(tmp_dir)
        root = Path(tmp_dir) / "cmdline-tools"
        if not (root / "bin/sdkmanager").exists():
            raise RuntimeError(f"sdkmanager not found in {archive}")
        CMDLINE_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        for item in root.iterdir():
            shutil.move(str(item), str(CMDLINE_TOOLS_DIR / item.name))
    chmod_bin_tools(CMDLINE_TOOLS_DIR)


def tool_env(java_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["JAVA_HOME"] = str(java_home)
    env["ANDROID_HOME"] = str(ANDROID_SDK)
    env["ANDROID_SDK_ROOT"] = str(ANDROID_SDK)
    env["PATH"] = f"{java_home / 'bin'}:{CMDLINE_TOOLS_DIR / 'bin'}:{ANDROID_SDK / 'build-tools/35.0.0'}:" + env.get("PATH", "")
    return env


def install_sdk_packages(java_home: Path) -> list[dict[str, Any]]:
    sdkmanager = CMDLINE_TOOLS_DIR / "bin/sdkmanager"
    if not sdkmanager.exists():
        raise FileNotFoundError(sdkmanager)
    env = tool_env(java_home)
    command = [str(sdkmanager), "--sdk_root=" + str(ANDROID_SDK), *SDK_PACKAGES]
    proc = run(command, env=env, input_text="y\n" * 64)
    return [{"command": command, "stdout_tail": proc.stdout[-4000:]}]


def status(java_home: Path | None = None) -> dict[str, Any]:
    if java_home is None:
        marker = JDK_BASE / ".v2368-ready"
        java_home = read_marker(marker) if marker.exists() else JDK_BASE
    javac = java_home / "bin/javac"
    java = java_home / "bin/java"
    out: dict[str, Any] = {
        "run_id": RUN_ID,
        "jdk_home": rel(java_home),
        "android_sdk": rel(ANDROID_SDK),
        "cmdline_tools": rel(CMDLINE_TOOLS_DIR),
        "javac": rel(javac),
        "java_exists": java.exists(),
        "javac_exists": javac.exists(),
        "sdkmanager_exists": (CMDLINE_TOOLS_DIR / "bin/sdkmanager").exists(),
        "android_jar": rel(ANDROID_JAR),
        "android_jar_exists": ANDROID_JAR.exists(),
        "d8": rel(D8),
        "d8_exists": D8.exists(),
        "sdk_packages": list(SDK_PACKAGES),
        "ready": bool(javac.exists() and ANDROID_JAR.exists() and D8.exists()),
    }
    if javac.exists():
        out["javac_version"] = run([str(javac), "-version"]).stdout.strip()
    if D8.exists():
        out["d8_version"] = run([str(D8), "--version"], env=tool_env(java_home)).stdout.strip()
    return out


def bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    if args.status_only:
        return {"decision": "v2368-android-audio-toolchain-status", "status": status()}
    if args.dry_run:
        return {
            "decision": "v2368-android-audio-toolchain-dry-run",
            "downloads": {
                "jdk": {"url": JDK_URL, "dest": rel(DOWNLOAD_DIR / archive_name(JDK_URL))},
                "cmdline_tools": {"url": CMDLINE_TOOLS_URL, "dest": rel(DOWNLOAD_DIR / archive_name(CMDLINE_TOOLS_URL))},
            },
            "install": {"android_sdk": rel(ANDROID_SDK), "packages": list(SDK_PACKAGES)},
            "status": status(),
        }

    jdk_archive = DOWNLOAD_DIR / archive_name(JDK_URL)
    cmdline_archive = DOWNLOAD_DIR / archive_name(CMDLINE_TOOLS_URL)
    downloads = {
        "jdk": download(JDK_URL, jdk_archive, force=args.force_download),
        "cmdline_tools": download(CMDLINE_TOOLS_URL, cmdline_archive, force=args.force_download),
    }
    extract_cmdline_tools(cmdline_archive, force=args.force_extract)
    java_home = extract_jdk(jdk_archive, force=args.force_extract)
    installs: list[dict[str, Any]] = []
    if not (ANDROID_JAR.exists() and D8.exists()) or args.force_sdk_install:
        installs = install_sdk_packages(java_home)
    state = status(java_home)
    result = {
        "decision": "v2368-android-audio-toolchain-ready" if state["ready"] else "v2368-android-audio-toolchain-incomplete",
        "downloads": downloads,
        "installs": installs,
        "status": state,
        "sources": {
            "android_cmdline_tools": "https://developer.android.com/tools",
            "sdkmanager": "https://developer.android.com/tools/sdkmanager",
            "cmdline_release_notes": "https://developer.android.com/tools/releases/cmdline-tools",
            "temurin": "https://adoptium.net/temurin/releases/?version=17",
        },
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="show planned private downloads/install paths")
    parser.add_argument("--status-only", action="store_true", help="show current private toolchain status")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--force-extract", action="store_true")
    parser.add_argument("--force-sdk-install", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = bootstrap(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.dry_run or args.status_only:
        return 0
    return 0 if result.get("decision") == "v2368-android-audio-toolchain-ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
