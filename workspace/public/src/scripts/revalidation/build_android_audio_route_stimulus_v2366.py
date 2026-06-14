#!/usr/bin/env python3
"""Build the A90 Android AudioTrack route-delta stimulus DEX.

The script is intentionally host-toolchain gated.  It writes outputs only under
workspace/private and refuses to claim success unless javac, d8/dx, and an
Android platform android.jar are present.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


RUN_ID = "V2366"
ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "workspace/public/src/android/audio_route_stimulus/A90AudioRouteStimulus.java"
OUT_DIR = ROOT / "workspace/private/builds/audio/v2366-android-route-stimulus"
CLASS_NAME = "A90AudioRouteStimulus"


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


def discover_android_jars(android_home: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if android_home:
        candidates.extend(sorted(android_home.glob("platforms/*/android.jar")))
    for env_name in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = __import__("os").environ.get(env_name)
        if value:
            candidates.extend(sorted(Path(value).glob("platforms/*/android.jar")))
    return list(dict.fromkeys(candidates))


def discover_state(args: argparse.Namespace) -> dict[str, Any]:
    android_home = args.android_home
    android_jars = discover_android_jars(android_home)
    selected_android_jar = args.android_jar or (android_jars[-1] if android_jars else None)
    d8 = args.d8 or shutil.which("d8")
    dx = args.dx or shutil.which("dx")
    javac = args.javac or shutil.which("javac")
    return {
        "source": rel(SOURCE),
        "source_exists": SOURCE.exists(),
        "javac": javac,
        "d8": d8,
        "dx": dx,
        "android_home": str(android_home) if android_home else None,
        "android_jar": str(selected_android_jar) if selected_android_jar else None,
        "android_jar_exists": bool(selected_android_jar and selected_android_jar.exists()),
        "can_build": bool(SOURCE.exists() and javac and (d8 or dx) and selected_android_jar and selected_android_jar.exists()),
    }


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def build(args: argparse.Namespace) -> dict[str, Any]:
    state = discover_state(args)
    result: dict[str, Any] = {
        "run_id": RUN_ID,
        "decision": "v2366-android-route-stimulus-build-dry-run" if args.dry_run else "v2366-android-route-stimulus-build",
        "state": state,
        "out_dir": rel(OUT_DIR),
    }
    if args.dry_run or not state["can_build"]:
        result["built"] = False
        result["missing"] = [
            name for name in ("source_exists", "javac", "android_jar_exists")
            if not state.get(name)
        ]
        if not (state.get("d8") or state.get("dx")):
            result["missing"].append("d8_or_dx")
        return result

    classes_dir = OUT_DIR / "classes"
    dex_dir = OUT_DIR / "dex"
    dex_path = OUT_DIR / "A90AudioRouteStimulus.dex"
    manifest_path = OUT_DIR / "manifest.json"
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    classes_dir.mkdir(parents=True)
    dex_dir.mkdir(parents=True)

    run([
        state["javac"],
        "-source", "1.8",
        "-target", "1.8",
        "-classpath", state["android_jar"],
        "-d", str(classes_dir),
        str(SOURCE),
    ])
    if state.get("d8"):
        run([state["d8"], "--output", str(dex_dir), str(classes_dir / f"{CLASS_NAME}.class")])
        produced = dex_dir / "classes.dex"
    else:
        run([state["dx"], "--dex", f"--output={dex_dir / 'classes.dex'}", str(classes_dir)])
        produced = dex_dir / "classes.dex"
    shutil.copy2(produced, dex_path)
    dex_path.chmod(0o600)
    result.update({
        "built": True,
        "dex": rel(dex_path),
        "sha256": sha256(dex_path),
        "size": dex_path.stat().st_size,
        "mode": oct(dex_path.stat().st_mode & 0o777),
    })
    manifest_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report toolchain availability without building")
    parser.add_argument("--android-home", type=Path)
    parser.add_argument("--android-jar", type=Path)
    parser.add_argument("--javac")
    parser.add_argument("--d8")
    parser.add_argument("--dx")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if (args.dry_run or result.get("built")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
