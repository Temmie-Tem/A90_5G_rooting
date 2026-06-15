#!/usr/bin/env python3
"""V2476 host-only planner for ACDB acdb_ioctl LD_PRELOAD capture.

This unit does not boot Android or run the preload.  It turns the V2475
libacdbtap.so artifact into a bounded live-run recipe and records which private
ACDB inputs are available for host cross-validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "V2476"
BUILD_TAG = "v2476-audio-acdbtap-live-planner"
ROOT = Path(__file__).resolve().parents[5]
TAP_SO = ROOT / "workspace/private/builds/audio/v2475-acdbtap-interposer-build/bin/libacdbtap.so"
TAP_SHA256 = "7bf64bb04530202a8dc859db0826cd399ff34d51ea4628eb586808de82968be4"
V2324_VENDOR_DUMP = ROOT / "workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump"
DEFAULT_STAGE_DIR = ROOT / "workspace/private/inputs/audio/acdb-cross-validation/v2476"
DEFAULT_OUT_DIR = ROOT / "workspace/private/runs/audio/v2476-acdbtap-live-plan"
REMOTE_STAGE_DIR = "/data/local/tmp/a90-acdbtap-v2476"
REMOTE_INCOMING_LIB = f"{REMOTE_STAGE_DIR}/incoming/libacdbtap.so"
REMOTE_LIB = f"{REMOTE_STAGE_DIR}/lib/libacdbtap.so"
REMOTE_CAPTURE_DIR = "/data/local/tmp/a90-acdb-tap"
REMOTE_EVENTS = f"{REMOTE_CAPTURE_DIR}/acdbtap-events.jsonl"
AUDIO_SERVICE = "vendor.audio-hal"
AUDIO_PROCESS = "android.hardware.audio.service"
AUDIO_BINARY = "/vendor/bin/hw/android.hardware.audio.service"
TARGET_OUT_LEN = 4916
REQUIRED_DEP_LIBS = (
    "libaudcal.so",
    "libacdbloader.so",
    "libacdb-fts.so",
    "libacdbrtac.so",
    "libadiertac.so",
)
SOURCE_REFERENCES = (
    {
        "title": "Android init language: services are unique and setenv sets service process environment",
        "url": "https://android.googlesource.com/platform/system/core/+/master/init/README.md",
        "used_for": "init rc setenv is the clean persistent preload mechanism, but duplicate service definitions are ignored",
    },
    {
        "title": "Magisk module guide: service.sh, system overlays, sepolicy.rule, rootdir overlay.d",
        "url": "https://github.com/topjohnwu/Magisk/blob/master/docs/guides.md",
        "used_for": "ordinary service.sh is late_start only; system overlays can replace vendor files; sepolicy.rule exists for bounded policy patches",
    },
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def rel(path: Path | str) -> str:
    try:
        return str(Path(path).relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_state(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    state: dict[str, Any] = {"path": rel(path), "exists": path.exists()}
    if not path.exists():
        state["ok"] = False
        return state
    stat_result = path.stat()
    state.update({
        "size": stat_result.st_size,
        "mode": oct(stat_result.st_mode & 0o777),
        "sha256": sha256(path),
        "group_or_world_writable": bool(stat_result.st_mode & 0o022),
    })
    if expected_sha256:
        state["expected_sha256"] = expected_sha256
        state["sha256_ok"] = state["sha256"] == expected_sha256
    state["ok"] = bool(state.get("sha256_ok", True) and stat_result.st_size > 0)
    return state


def find_private_inputs() -> dict[str, Any]:
    libs: dict[str, list[dict[str, Any]]] = {name: [] for name in REQUIRED_DEP_LIBS}
    acdb_files: list[dict[str, Any]] = []
    search_roots = [V2324_VENDOR_DUMP, ROOT / "workspace/private/inputs", ROOT / "workspace/private/runs/audio"]
    seen: set[Path] = set()
    for base in search_roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            if path.name in libs:
                libs[path.name].append(file_state(path))
            if path.suffix == ".acdb" or "acdbdata" in path.parts:
                acdb_files.append(file_state(path))
    return {
        "search_roots": [rel(path) for path in search_roots],
        "dep_libs": libs,
        "acdb_files": acdb_files,
        "available_dep_lib_names": sorted(name for name, items in libs.items() if items),
        "missing_dep_lib_names": sorted(name for name, items in libs.items() if not items),
        "acdb_file_count": len(acdb_files),
    }


def stage_private_inputs(stage_dir: Path) -> dict[str, Any]:
    inventory = find_private_inputs()
    stage_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(stage_dir, 0o700)
    copied: list[dict[str, Any]] = []

    def copy_one(source: Path, relative: Path) -> None:
        destination = stage_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        os.chmod(destination, 0o600)
        copied.append({
            "source": rel(source),
            "destination": rel(destination),
            "sha256": sha256(destination),
            "size": destination.stat().st_size,
        })

    for name, items in inventory["dep_libs"].items():
        for index, item in enumerate(items):
            copy_one(ROOT / item["path"], Path("libs") / f"{index}-{name}")
    for index, item in enumerate(inventory["acdb_files"]):
        source = ROOT / item["path"]
        copy_one(source, Path("acdb") / f"{index}-{source.name}")

    for directory in [stage_dir, *(path for path in stage_dir.rglob("*") if path.is_dir())]:
        os.chmod(directory, 0o700)
    return {
        "stage_dir": rel(stage_dir),
        "copied_count": len(copied),
        "copied": copied,
        "inventory": inventory,
        "ok": bool(copied),
    }


def adb_base(args: argparse.Namespace) -> list[str]:
    command = [args.adb]
    if args.serial:
        command.extend(["-s", args.serial])
    return command


def adb_shell(args: argparse.Namespace, script: str) -> list[str]:
    return adb_base(args) + ["shell", script]


def adb_su(args: argparse.Namespace, script: str) -> list[str]:
    quoted = script.replace("'", "'\\''")
    return adb_shell(args, f"su -c '{quoted}'")


def adb_push(args: argparse.Namespace, local: str, remote: str) -> list[str]:
    return adb_base(args) + ["push", local, remote]


def live_command_plan(args: argparse.Namespace) -> dict[str, Any]:
    setup_script = f"""
set -eu
rm -rf {REMOTE_STAGE_DIR} {REMOTE_CAPTURE_DIR}
mkdir -p {REMOTE_STAGE_DIR}/incoming {REMOTE_STAGE_DIR}/lib {REMOTE_CAPTURE_DIR}
chmod 700 {REMOTE_STAGE_DIR} {REMOTE_STAGE_DIR}/incoming {REMOTE_STAGE_DIR}/lib
chmod 777 {REMOTE_CAPTURE_DIR}
echo A90_ACDBTAP_SETUP_OK
""".strip()
    install_script = f"""
set -eu
cp {REMOTE_INCOMING_LIB} {REMOTE_LIB}
chown 0:0 {REMOTE_LIB}
chmod 644 {REMOTE_LIB}
ls -lZ {REMOTE_LIB} {REMOTE_CAPTURE_DIR}
echo A90_ACDBTAP_INSTALL_OK
""".strip()
    preflight_script = f"""
set -eu
pidof {AUDIO_PROCESS} 2>/dev/null || true
getprop init.svc.{AUDIO_SERVICE} 2>/dev/null || true
ls -lZ {AUDIO_BINARY} {REMOTE_LIB} {REMOTE_CAPTURE_DIR}
echo A90_ACDBTAP_PREFLIGHT_OK
""".strip()
    start_script = f"""
set -eu
setprop ctl.stop {AUDIO_SERVICE}
sleep 2
OLD_PIDS="$(pidof {AUDIO_PROCESS} 2>/dev/null || true)"
if [ -n "$OLD_PIDS" ]; then
  echo A90_ACDBTAP_OLD_PIDS_STILL_PRESENT "$OLD_PIDS"
fi
(
  export LD_PRELOAD={REMOTE_LIB}
  export A90_ACDBTAP_DIR={REMOTE_CAPTURE_DIR}
  exec {AUDIO_BINARY}
) > {REMOTE_STAGE_DIR}/manual-audio-hal.stdout 2> {REMOTE_STAGE_DIR}/manual-audio-hal.stderr &
echo $! > {REMOTE_STAGE_DIR}/manual-audio-hal.pid
sleep 3
NEW_PIDS="$(pidof {AUDIO_PROCESS} 2>/dev/null || true)"
echo A90_ACDBTAP_MANUAL_HAL_PIDS "$NEW_PIDS"
for pid in $NEW_PIDS; do
  if grep -q libacdbtap /proc/$pid/maps 2>/dev/null; then
    echo A90_ACDBTAP_PRELOAD_CONFIRMED pid=$pid
  fi
done
""".strip()
    verify_script = f"""
set -eu
ls -lR {REMOTE_CAPTURE_DIR} {REMOTE_STAGE_DIR} 2>&1 || true
if [ -f {REMOTE_EVENTS} ]; then
  cat {REMOTE_EVENTS}
fi
logcat -d -v threadtime | grep -Ei 'avc:|denied|linker|LD_PRELOAD|libacdbtap|acdb|audio_hw|ACDB|AudioTrack' | tail -300 || true
dmesg | grep -Ei 'avc:|denied|libacdbtap|audio|acdb' | tail -300 || true
echo A90_ACDBTAP_VERIFY_DONE
""".strip()
    cleanup_script = f"""
set -eu
if [ -f {REMOTE_STAGE_DIR}/manual-audio-hal.pid ]; then
  kill "$(cat {REMOTE_STAGE_DIR}/manual-audio-hal.pid)" 2>/dev/null || true
fi
setprop ctl.start {AUDIO_SERVICE} || true
sleep 2
rm -rf {REMOTE_STAGE_DIR} {REMOTE_CAPTURE_DIR}
getprop init.svc.{AUDIO_SERVICE} 2>/dev/null || true
echo A90_ACDBTAP_CLEANUP_OK
""".strip()
    return {
        "mode": "manual-root-reexec-preload-candidate",
        "why_not_rc_overlay_first": "ordinary Magisk service.sh cannot change an already-defined init service environment; Android init setenv would require an rc definition path, and duplicate service definitions are ignored",
        "why_manual_first": "ephemeral, no boot image change beyond the checked Android handoff, and it directly proves whether the HAL binary can run with LD_PRELOAD before designing a heavier Magisk rootdir overlay",
        "commands": {
            "android_handoff": "reuse checked Android handoff from V2451/V2365; no native boot artifact change in this planner",
            "setup_dirs": adb_su(args, setup_script),
            "push_libacdbtap": adb_push(args, rel(TAP_SO), REMOTE_INCOMING_LIB),
            "install_libacdbtap": adb_su(args, install_script),
            "preflight_audio_hal": adb_su(args, preflight_script),
            "logcat_clear": adb_base(args) + ["logcat", "-b", "main", "-b", "system", "-b", "crash", "-b", "events", "-c"],
            "manual_stop_and_reexec_hal_with_preload": adb_su(args, start_script),
            "run_known_good_audiotrack_stimulus": "reuse APK AudioTrack stimulus path from V2377/V2458 after preload confirmation",
            "verify_capture_and_avc": adb_su(args, verify_script),
            "pull_private_capture_dir": adb_base(args) + ["pull", REMOTE_CAPTURE_DIR, "<private-run-dir>/acdbtap-device-artifacts"],
            "cleanup_restore_init_service": adb_su(args, cleanup_script),
            "rollback_v2321": "reuse checked V2321 rollback path from Android recovery",
        },
        "acceptance": {
            "jsonl": REMOTE_EVENTS,
            "target_predicate": f"at least one metadata row with out_len == {TARGET_OUT_LEN}",
            "public_report_fields_only": ["cmd", "in_len", "out_len", "ret", "sha256"],
            "raw_bytes_private_only": True,
        },
        "abort_classifiers": [
            "preload-not-in-maps",
            "audio-hal-reexec-failed",
            "selinux-preload-open-denied",
            "selinux-capture-write-denied",
            "no-acdbtap-events",
            "acdbtap-events-no-4916",
        ],
        "selinux_policy": {
            "default": "enforcing observation only; capture avc and stop on denial",
            "not_silent": True,
            "follow_on_only": "bounded setenforce/magiskpolicy assist may be designed only after a denial is captured and cleanup/restore is explicit",
        },
    }


def command_safety(plan: dict[str, Any]) -> dict[str, Any]:
    flat = json.dumps(plan, sort_keys=True)
    forbidden = {
        "native_cal_set_symbol": "AUDIO_SET_CALIBRATION",
        "native_cal_allocate_symbol": "AUDIO_ALLOCATE_CALIBRATION",
        "native_tinyplay": "tinyplay",
        "native_tinymix_set": "tinymix set",
        "fastboot": "fastboot",
        "raw_dd": " dd ",
        "nonboot_partition": "/dev/block/by-name/efs",
        "silent_permissive": "setenforce 0",
        "magisk_install_module": "magisk --install-module",
    }
    findings = [{"name": name, "needle": needle} for name, needle in forbidden.items() if needle in flat]
    required = [
        "LD_PRELOAD",
        "libacdbtap.so",
        AUDIO_PROCESS,
        AUDIO_BINARY,
        REMOTE_CAPTURE_DIR,
        "rollback_v2321",
        "selinux-preload-open-denied",
    ]
    missing = [needle for needle in required if needle not in flat]
    return {
        "ok": not findings and not missing,
        "findings": findings,
        "missing_required_needles": missing,
        "forbidden": sorted(forbidden),
        "required": required,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    tap = file_state(TAP_SO, expected_sha256=TAP_SHA256)
    private_inventory = find_private_inputs()
    staged = None
    if args.stage_private_inputs:
        staged = stage_private_inputs(args.stage_dir)
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "generated_at": now_iso(),
        "decision": "v2476-acdbtap-live-planner-host-only",
        "host_only": True,
        "device_action": "none",
        "tap_artifact": tap,
        "private_cross_validation_inventory": private_inventory,
        "private_cross_validation_staging": staged,
        "source_references": list(SOURCE_REFERENCES),
        "live_plan": live_command_plan(args),
        "boundaries": [
            "no live Android boot in V2476",
            "no native /dev/msm_audio_cal ioctl",
            "no native mixer write",
            "no native PCM playback",
            "raw acdbtap .bin files stay under workspace/private only",
            "SELinux denial is evidence; do not silently disable enforcing",
        ],
    }
    payload["command_safety"] = command_safety(payload)
    payload["future_live_ready"] = bool(tap.get("ok") and payload["command_safety"].get("ok"))
    blockers: list[str] = []
    if not tap.get("ok"):
        blockers.append("V2475 libacdbtap.so missing or SHA mismatch")
    if not payload["command_safety"].get("ok"):
        blockers.append("command safety scan failed")
    if private_inventory["acdb_file_count"] == 0:
        blockers.append("host cross-validation acdb .acdb files not present in current private dump")
    missing_libs = [name for name in private_inventory["missing_dep_lib_names"] if name != "libacdb-fts.so"]
    if missing_libs:
        blockers.append(f"some requested ACDB dep libs are missing from current private dump: {missing_libs}")
    payload["future_live_blockers"] = blockers
    payload["ok"] = bool(tap.get("ok") and payload["command_safety"].get("ok"))
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR / "plan.json")
    parser.add_argument("--stage-dir", type=Path, default=DEFAULT_STAGE_DIR)
    parser.add_argument("--stage-private-inputs", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(args.out.parent, 0o700)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "decision": payload["decision"],
        "ok": payload["ok"],
        "future_live_ready": payload["future_live_ready"],
        "future_live_blockers": payload["future_live_blockers"],
        "out": rel(args.out),
    }, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
