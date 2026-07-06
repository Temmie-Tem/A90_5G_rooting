#!/usr/bin/env python3
"""Collect S22+ P3 first-light evidence, then perform pinned stock boot rollback.

Host-side helper for the P3 direct-PID1 incident.  It is intentionally narrow:

- If TWRP/recovery or Android ADB is visible, collect read-only evidence first
  (`/proc/last_kmsg`, pstore, selected properties, boot-surface hashes where
  readable), then reboot to download mode.
- If Odin download mode is visible, perform only the already pinned stock
  boot-only rollback AP through the existing rollback guard.
- If no transport is visible, do nothing.

Dry-run is the default.  Live mode requires an explicit P3 ack and delegates the
actual Odin flash to `s22plus_p2_stock_boot_rollback_guard.py`, whose pinned
stock boot AP is also authorized for the P3 incident rollback.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_P3_AP_SHA256 = "21838b4e64656cead9804f9034ed554bf6737a9666d07001d30ec66c01364d8b"
EXPECTED_ROLLBACK_AP_SHA256 = "1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e"
EXPECTED_MEMBER = "boot.img.lz4"
P3_ACK_TOKEN = "S22PLUS-P3-COLLECT-AND-ROLLBACK"
P2_ROLLBACK_ACK_TOKEN = "S22PLUS-P2-STOCK-BOOT-ROLLBACK"
ODIN_DEVICE_RE = re.compile(r"/dev/bus/usb/\d+/\d+")

DEFAULT_P3_AP = Path("workspace/private/outputs/s22plus_native_init/direct_p3_v0_1/odin4/AP.tar.md5")
DEFAULT_ROLLBACK_AP = Path("workspace/private/outputs/s22plus_native_init/odin4_stock_rollback_short/AP.tar.md5")
DEFAULT_LATEST_RUN = Path("workspace/private/runs/s22plus_p3_direct_pid1_live_latest.txt")
DEFAULT_ODIN = Path("/usr/bin/odin4")
ROLLBACK_GUARD = Path("workspace/public/src/scripts/revalidation/s22plus_p2_stock_boot_rollback_guard.py")


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").is_dir():
            return parent
    raise RuntimeError(f"could not locate repo root from {current}")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def run(argv: list[str | Path], *, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(part) for part in argv],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tar_members(path: Path) -> list[str]:
    with tarfile.open(path) as tar:
        return [member.name for member in tar.getmembers()]


def append_log(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = requested
    elif (root / DEFAULT_LATEST_RUN).exists():
        run_dir = Path((root / DEFAULT_LATEST_RUN).read_text(encoding="utf-8").strip())
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = Path("workspace/private/runs") / f"s22plus_p3_collect_rollback_{stamp}"
    run_dir = resolve(root, run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def verify_boot_only_ap(path: Path, expected_sha: str, label: str, log_path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"{label} AP missing: {path}")
    actual_sha = sha256_file(path)
    members = tar_members(path)
    append_log(log_path, f"{label}_sha256={actual_sha}")
    append_log(log_path, f"{label}_members={members}")
    if actual_sha != expected_sha:
        raise SystemExit(f"{label} AP SHA mismatch: {actual_sha}")
    if members != [EXPECTED_MEMBER]:
        raise SystemExit(f"{label} AP must contain only {EXPECTED_MEMBER!r}, got {members!r}")


def odin_devices(odin: Path, log_path: Path, label: str) -> list[str]:
    result = run([odin, "-l"], timeout=10.0)
    output = result.stdout + result.stderr
    devices = sorted(set(ODIN_DEVICE_RE.findall(output)))
    append_log(log_path, f"[{utc_now()}] {label} odin4 -l rc={result.returncode} devices={devices}")
    append_log(log_path, output)
    return devices


def adb_rows(log_path: Path, label: str) -> list[tuple[str, str, str]]:
    result = run(["adb", "devices", "-l"], timeout=10.0)
    output = result.stdout + result.stderr
    append_log(log_path, f"[{utc_now()}] {label} adb devices -l rc={result.returncode}")
    append_log(log_path, output)
    rows: list[tuple[str, str, str]] = []
    for line in output.splitlines()[1:]:
        parts = line.split(maxsplit=2)
        if len(parts) >= 2:
            rows.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ""))
    return rows


def adb_shell_to_file(out_path: Path, command: str, timeout: float = 20.0) -> subprocess.CompletedProcess[str]:
    result = run(["adb", "shell", command], timeout=timeout)
    out_path.write_text(result.stdout + result.stderr, encoding="utf-8", errors="replace")
    return result


def collect_adb_evidence(run_dir: Path, log_path: Path) -> None:
    evidence_dir = run_dir / "p3_recovery_evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    run(["adb", "devices", "-l"], timeout=10.0).stdout
    (evidence_dir / "adb_devices_l.txt").write_text(
        run(["adb", "devices", "-l"], timeout=10.0).stdout,
        encoding="utf-8",
    )

    adb_shell_to_file(
        evidence_dir / "getprop_selected.txt",
        "getprop ro.twrp.version; "
        "getprop ro.boot.bootloader; "
        "getprop ro.product.model; "
        "getprop ro.product.device; "
        "getprop ro.boot.verifiedbootstate; "
        "getprop sys.boot_completed",
    )
    adb_shell_to_file(
        evidence_dir / "last_kmsg.txt",
        "if [ -r /proc/last_kmsg ]; then cat /proc/last_kmsg; else echo NO_PROC_LAST_KMSG; fi",
        timeout=40.0,
    )
    adb_shell_to_file(
        evidence_dir / "pstore_listing.txt",
        "if [ -d /sys/fs/pstore ]; then ls -la /sys/fs/pstore; else echo NO_PSTORE_DIR; fi",
    )
    adb_shell_to_file(
        evidence_dir / "pstore_text.txt",
        "if [ -d /sys/fs/pstore ]; then "
        "for f in /sys/fs/pstore/*; do "
        "[ -e \"$f\" ] || continue; "
        "echo ===$f===; head -c 1048576 \"$f\"; echo; "
        "done; "
        "else echo NO_PSTORE_DIR; fi",
        timeout=60.0,
    )
    adb_shell_to_file(
        evidence_dir / "boot_surface_sha256.txt",
        "for p in boot recovery vendor_boot vbmeta vbmeta_system; do "
        "if [ -e /dev/block/by-name/$p ]; then "
        "printf '%s ' \"$p\"; sha256sum /dev/block/by-name/$p; "
        "fi; "
        "done",
        timeout=60.0,
    )

    marker_hits = []
    for path in evidence_dir.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "S22_NATIVE_INIT_DIRECT_P3" in text:
            marker_hits.append(path.name)
    append_log(log_path, f"evidence_dir={evidence_dir}")
    append_log(log_path, f"p3_marker_hits={marker_hits}")


def wait_for_odin(odin: Path, wait_sec: int, log_path: Path) -> str | None:
    deadline = time.monotonic() + wait_sec
    while True:
        devices = odin_devices(odin, log_path, "wait")
        if len(devices) == 1:
            return devices[0]
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin devices: {devices}")
        if time.monotonic() >= deadline:
            return None
        time.sleep(1.0)


def run_rollback_guard(root: Path, run_dir: Path, rollback_ap: Path, odin: Path, wait_sec: int) -> int:
    guard = root / ROLLBACK_GUARD
    result = run(
        [
            "python3",
            guard,
            "--ap",
            rollback_ap,
            "--odin",
            odin,
            "--run-dir",
            run_dir,
            "--wait-sec",
            str(wait_sec),
            "--live",
            "--ack",
            P2_ROLLBACK_ACK_TOKEN,
        ],
        timeout=420.0,
    )
    (run_dir / "p3_delegated_stock_boot_rollback.txt").write_text(
        result.stdout + result.stderr,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p3-ap", type=Path, default=DEFAULT_P3_AP)
    parser.add_argument("--rollback-ap", type=Path, default=DEFAULT_ROLLBACK_AP)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--wait-sec", type=int, default=0, help="wait for ADB/Odin transport before acting")
    parser.add_argument("--download-wait-sec", type=int, default=120, help="wait for Odin after adb reboot download")
    parser.add_argument("--live", action="store_true", help="collect evidence and perform rollback when possible")
    parser.add_argument("--ack", help=f"required with --live: {P3_ACK_TOKEN}")
    args = parser.parse_args(argv)

    root = repo_root()
    p3_ap = resolve(root, args.p3_ap)
    rollback_ap = resolve(root, args.rollback_ap)
    odin = resolve(root, args.odin)
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_p3_collect_and_rollback.txt"

    append_log(log_path, f"=== {utc_now()} s22plus p3 collect and rollback ===")
    verify_boot_only_ap(p3_ap, EXPECTED_P3_AP_SHA256, "p3_candidate", log_path)
    verify_boot_only_ap(rollback_ap, EXPECTED_ROLLBACK_AP_SHA256, "stock_boot_rollback", log_path)

    if args.live and args.ack != P3_ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {P3_ACK_TOKEN}")

    deadline = time.monotonic() + args.wait_sec
    while True:
        odin_found = odin_devices(odin, log_path, "detect")
        adb_found = adb_rows(log_path, "detect")
        if odin_found or adb_found or time.monotonic() >= deadline:
            break
        time.sleep(1.0)

    if len(odin_found) > 1:
        raise SystemExit(f"refusing ambiguous Odin devices: {odin_found}")
    if len(adb_found) > 1:
        raise SystemExit(f"refusing ambiguous ADB devices: {adb_found}")

    if odin_found:
        append_log(log_path, f"decision=odin-visible device={odin_found[0]}")
        if not args.live:
            print(f"dry-run ok: Odin device visible for rollback: {odin_found[0]}")
            return 0
        return run_rollback_guard(root, run_dir, rollback_ap, odin, 0)

    if adb_found:
        _adb_id, state, detail = adb_found[0]
        append_log(log_path, f"decision=adb-visible state={state} detail={detail}")
        if state == "unauthorized":
            print("ADB device is unauthorized; cannot collect or reboot from host")
            return 4
        if state not in {"device", "recovery", "sideload"}:
            print(f"ADB state {state!r} is not actionable")
            return 5
        collect_adb_evidence(run_dir, log_path)
        if not args.live:
            print(f"dry-run ok: ADB {state} visible; evidence collection path verified")
            return 0
        reboot = run(["adb", "reboot", "download"], timeout=20.0)
        append_log(log_path, f"adb_reboot_download_rc={reboot.returncode}")
        append_log(log_path, reboot.stdout + reboot.stderr)
        selected = wait_for_odin(odin, args.download_wait_sec, log_path)
        if selected is None:
            print("ADB collection completed, but download-mode Odin did not appear", file=sys.stderr)
            return 6
        return run_rollback_guard(root, run_dir, rollback_ap, odin, 0)

    append_log(log_path, "decision=no-transport")
    print("no ADB/Odin transport visible; no action taken")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
