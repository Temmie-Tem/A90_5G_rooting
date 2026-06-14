#!/usr/bin/env python3
"""Build the V2373 APK-style Android AudioTrack route stimulus.

This is a host-only fallback artifact for the route-delta path.  Outputs stay
under workspace/private and are intended for a future exact-gated Android
handoff only; this builder does not install or run the APK.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any


RUN_ID = "V2373"
ROOT = Path(__file__).resolve().parents[5]
SOURCE_ROOT = ROOT / "workspace/public/src/android/audio_route_stimulus_apk"
JAVA_SRC_ROOT = SOURCE_ROOT / "src"
MANIFEST = SOURCE_ROOT / "AndroidManifest.xml"
RES_DIR = SOURCE_ROOT / "res"
OUT_DIR = ROOT / "workspace/private/builds/audio/v2373-android-route-stimulus-apk"
APK_NAME = "A90AudioRouteStimulus.apk"
ANDROID_SDK = ROOT / "workspace/private/inputs/android-sdk-v2368"
JDK_MARKER = ROOT / "workspace/private/inputs/toolchains/temurin17-v2368/.v2368-ready"
DEBUG_KEYSTORE = ROOT / "workspace/private/inputs/android-debug/v2373-audio-route-stimulus-debug.keystore"
DEBUG_STOREPASS = "android"
DEBUG_KEY_ALIAS = "androiddebugkey"


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


def read_marker(marker: Path) -> Path | None:
    if not marker.exists():
        return None
    text = marker.read_text().strip()
    if not text:
        return None
    return ROOT / text if not text.startswith("/") else Path(text)


def default_java_home() -> Path | None:
    java_home = read_marker(JDK_MARKER)
    if java_home and (java_home / "bin/javac").exists():
        return java_home
    return None


def tool_env(java_home: Path | None, android_sdk: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["ANDROID_HOME"] = str(android_sdk)
    env["ANDROID_SDK_ROOT"] = str(android_sdk)
    path_parts = []
    if java_home:
        env["JAVA_HOME"] = str(java_home)
        path_parts.append(str(java_home / "bin"))
    path_parts.append(str(android_sdk / "build-tools/35.0.0"))
    path_parts.append(env.get("PATH", ""))
    env["PATH"] = ":".join(path_parts)
    return env


def tool(path: Path) -> str | None:
    return str(path) if path.exists() else None


def discover_state(args: argparse.Namespace) -> dict[str, Any]:
    android_sdk = args.android_sdk or ANDROID_SDK
    java_home = args.java_home or default_java_home()
    build_tools = android_sdk / "build-tools/35.0.0"
    android_jar = android_sdk / "platforms/android-31/android.jar"
    java_sources = sorted(JAVA_SRC_ROOT.glob("**/*.java"))
    javac = args.javac or (str(java_home / "bin/javac") if java_home and (java_home / "bin/javac").exists() else shutil.which("javac"))
    java = str(java_home / "bin/java") if java_home and (java_home / "bin/java").exists() else shutil.which("java")
    keytool = str(java_home / "bin/keytool") if java_home and (java_home / "bin/keytool").exists() else shutil.which("keytool")
    state = {
        "run_id": RUN_ID,
        "source_root": rel(SOURCE_ROOT),
        "manifest": rel(MANIFEST),
        "manifest_exists": MANIFEST.exists(),
        "res_dir": rel(RES_DIR),
        "res_dir_exists": RES_DIR.exists(),
        "java_sources": [rel(path) for path in java_sources],
        "java_source_count": len(java_sources),
        "android_sdk": rel(android_sdk),
        "android_jar": rel(android_jar),
        "android_jar_exists": android_jar.exists(),
        "java_home": rel(java_home) if java_home else None,
        "javac": javac,
        "java": java,
        "keytool": keytool,
        "aapt": tool(build_tools / "aapt"),
        "d8": tool(build_tools / "d8"),
        "zipalign": tool(build_tools / "zipalign"),
        "apksigner": tool(build_tools / "apksigner"),
        "debug_keystore": rel(args.keystore or DEBUG_KEYSTORE),
    }
    required = (
        state["manifest_exists"],
        state["res_dir_exists"],
        state["java_source_count"] > 0,
        state["android_jar_exists"],
        state["javac"],
        state["java"],
        state["keytool"],
        state["aapt"],
        state["d8"],
        state["zipalign"],
        state["apksigner"],
    )
    state["can_build"] = all(bool(item) for item in required)
    state["missing"] = [
        name for name, present in (
            ("manifest", state["manifest_exists"]),
            ("res_dir", state["res_dir_exists"]),
            ("java_sources", state["java_source_count"] > 0),
            ("android_jar", state["android_jar_exists"]),
            ("javac", state["javac"]),
            ("java", state["java"]),
            ("keytool", state["keytool"]),
            ("aapt", state["aapt"]),
            ("d8", state["d8"]),
            ("zipalign", state["zipalign"]),
            ("apksigner", state["apksigner"]),
        ) if not present
    ]
    return state


def run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)


def ensure_debug_keystore(keytool: str, keystore: Path, env: dict[str, str]) -> dict[str, Any]:
    keystore.parent.mkdir(parents=True, exist_ok=True)
    if keystore.exists():
        return {"path": rel(keystore), "created": False, "sha256": sha256(keystore), "mode": oct(keystore.stat().st_mode & 0o777)}
    command = [
        keytool,
        "-genkeypair",
        "-noprompt",
        "-keystore", str(keystore),
        "-storepass", DEBUG_STOREPASS,
        "-keypass", DEBUG_STOREPASS,
        "-alias", DEBUG_KEY_ALIAS,
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000",
        "-dname", "CN=A90 Route Stimulus,O=A90 NativeInit,C=KR",
    ]
    run(command, env=env)
    keystore.chmod(0o600)
    return {"path": rel(keystore), "created": True, "sha256": sha256(keystore), "mode": oct(keystore.stat().st_mode & 0o777)}


def add_classes_to_apk(apk_path: Path, classes_dex: Path) -> None:
    with zipfile.ZipFile(apk_path, "a", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(classes_dex, "classes.dex")


def build(args: argparse.Namespace) -> dict[str, Any]:
    state = discover_state(args)
    out_dir = args.out_dir or OUT_DIR
    result: dict[str, Any] = {
        "run_id": RUN_ID,
        "decision": "v2373-android-route-stimulus-apk-dry-run" if args.dry_run else "v2373-android-route-stimulus-apk-build",
        "state": state,
        "out_dir": rel(out_dir),
        "built": False,
        "device_action": "none",
    }
    if args.dry_run or not state["can_build"]:
        result["missing"] = state["missing"]
        return result

    android_sdk = args.android_sdk or ANDROID_SDK
    java_home = args.java_home or default_java_home()
    env = tool_env(java_home, android_sdk)
    keystore = args.keystore or DEBUG_KEYSTORE
    classes_dir = out_dir / "classes"
    dex_dir = out_dir / "dex"
    unsigned_apk = out_dir / "unsigned-resources.apk"
    unsigned_with_dex = out_dir / "unsigned-with-dex.apk"
    aligned_apk = out_dir / "aligned.apk"
    signed_apk = out_dir / APK_NAME
    manifest_path = out_dir / "manifest.json"

    shutil.rmtree(out_dir, ignore_errors=True)
    classes_dir.mkdir(parents=True)
    dex_dir.mkdir(parents=True)

    java_sources = sorted(JAVA_SRC_ROOT.glob("**/*.java"))
    run([
        state["javac"],
        "-source", "1.8",
        "-target", "1.8",
        "-classpath", str(android_sdk / "platforms/android-31/android.jar"),
        "-d", str(classes_dir),
        *[str(path) for path in java_sources],
    ], env=env)
    class_files = sorted(classes_dir.glob("**/*.class"))
    run([state["d8"], "--output", str(dex_dir), *[str(path) for path in class_files]], env=env)
    run([
        state["aapt"],
        "package",
        "-f",
        "-M", str(MANIFEST),
        "-S", str(RES_DIR),
        "-I", str(android_sdk / "platforms/android-31/android.jar"),
        "-F", str(unsigned_apk),
    ], env=env)
    shutil.copy2(unsigned_apk, unsigned_with_dex)
    add_classes_to_apk(unsigned_with_dex, dex_dir / "classes.dex")
    run([state["zipalign"], "-f", "4", str(unsigned_with_dex), str(aligned_apk)], env=env)
    keystore_state = ensure_debug_keystore(state["keytool"], keystore, env)
    run([
        state["apksigner"],
        "sign",
        "--ks", str(keystore),
        "--ks-key-alias", DEBUG_KEY_ALIAS,
        "--ks-pass", f"pass:{DEBUG_STOREPASS}",
        "--key-pass", f"pass:{DEBUG_STOREPASS}",
        "--out", str(signed_apk),
        str(aligned_apk),
    ], env=env)
    verify = run([state["apksigner"], "verify", "--verbose", str(signed_apk)], env=env)
    signed_apk.chmod(0o600)
    result.update({
        "built": True,
        "apk": rel(signed_apk),
        "apk_sha256": sha256(signed_apk),
        "apk_size": signed_apk.stat().st_size,
        "apk_mode": oct(signed_apk.stat().st_mode & 0o777),
        "package": "com.a90.nativeinit.audio",
        "activity": "com.a90.nativeinit.audio.A90AudioRouteStimulusActivity",
        "action": "com.a90.nativeinit.audio.PLAY_ROUTE_STIMULUS",
        "am_start_example": (
            "am start -W -n com.a90.nativeinit.audio/.A90AudioRouteStimulusActivity "
            "-a com.a90.nativeinit.audio.PLAY_ROUTE_STIMULUS "
            "--ei duration_ms 2000 --ei sample_rate 48000 --ef amplitude 0.05 --ez speaker true"
        ),
        "keystore": keystore_state,
        "apksigner_verify_tail": verify.stdout[-2000:],
    })
    manifest_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report APK build readiness without building")
    parser.add_argument("--android-sdk", type=Path)
    parser.add_argument("--java-home", type=Path)
    parser.add_argument("--javac")
    parser.add_argument("--keystore", type=Path)
    parser.add_argument("--out-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if (args.dry_run or result.get("built")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
