#!/usr/bin/env python3
"""Guarded S22+ P2 stock boot-only rollback helper.

This helper is intentionally narrow.  It only knows the SHA-pinned stock
boot-only rollback AP authorized for the S22+ P2 native-init first-light unit.
It refuses to call Odin unless the package hash and tar contents match the
authorized boot-only rollback payload and a single download-mode USB device is
selected.
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


EXPECTED_AP_SHA256 = "1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e"
EXPECTED_MEMBER = "boot.img.lz4"
DEFAULT_AP = Path("workspace/private/outputs/s22plus_native_init/odin4_stock_rollback_short/AP.tar.md5")
DEFAULT_ODIN = Path("/usr/bin/odin4")
DEFAULT_RUN_LATEST = Path("workspace/private/runs/s22plus_p2_magisk_chainload_live_latest.txt")
ACK_TOKEN = "S22PLUS-P2-STOCK-BOOT-ROLLBACK"
ODIN_DEVICE_RE = re.compile(r"/dev/bus/usb/\d+/\d+")


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").is_dir():
            return parent
    raise RuntimeError(f"could not locate repo root from {current}")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tar_members(path: Path) -> list[str]:
    with tarfile.open(path) as tar:
        return [member.name for member in tar.getmembers()]


def run(argv: list[str | Path], *, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(arg) for arg in argv],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested:
        path = requested
    elif (root / DEFAULT_RUN_LATEST).exists():
        path = Path((root / DEFAULT_RUN_LATEST).read_text(encoding="utf-8").strip())
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = Path("workspace/private/runs") / f"s22plus_p2_stock_boot_rollback_{stamp}"
    if not path.is_absolute():
        path = root / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def append_log(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def odin_devices(odin: Path, timeout: float = 10.0) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    result = run([odin, "-l"], timeout=timeout)
    found = ODIN_DEVICE_RE.findall(result.stdout + "\n" + result.stderr)
    unique = sorted(set(found))
    return result, unique


def wait_for_odin_device(odin: Path, wait_sec: int, log_path: Path) -> str | None:
    deadline = time.monotonic() + wait_sec
    last_output = ""
    while True:
        result, devices = odin_devices(odin)
        last_output = result.stdout + result.stderr
        append_log(log_path, f"[{utc_now()}] odin4 -l rc={result.returncode} devices={devices}")
        if len(devices) == 1:
            return devices[0]
        if len(devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin device list: {devices}")
        if time.monotonic() >= deadline:
            append_log(log_path, "last odin4 -l output:")
            append_log(log_path, last_output)
            return None
        time.sleep(1.0)


def poll_android_boot(wait_sec: int, log_path: Path) -> bool:
    deadline = time.monotonic() + wait_sec
    while True:
        devices = run(["adb", "devices", "-l"], timeout=10.0)
        props = run(
            [
                "adb",
                "shell",
                "getprop sys.boot_completed; "
                "getprop ro.product.model; "
                "getprop ro.product.device; "
                "getprop ro.boot.bootloader; "
                "getprop ro.boot.verifiedbootstate; "
                "getprop persist.sys.safemode",
            ],
            timeout=10.0,
        )
        append_log(log_path, f"[{utc_now()}] adb devices:")
        append_log(log_path, devices.stdout + devices.stderr)
        append_log(log_path, "props:")
        append_log(log_path, props.stdout + props.stderr)
        first = (props.stdout + props.stderr).splitlines()[0:1]
        if first == ["1"]:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(1.0)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ap", type=Path, default=DEFAULT_AP, help="stock boot-only rollback AP.tar.md5")
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN, help="odin4 executable")
    parser.add_argument("--run-dir", type=Path, help="private run directory for logs")
    parser.add_argument("--device", help="explicit /dev/bus/usb/... download-mode device")
    parser.add_argument("--wait-sec", type=int, default=0, help="wait for a single Odin device before live rollback")
    parser.add_argument("--post-boot-wait-sec", type=int, default=240, help="ADB boot-completed poll after live rollback")
    parser.add_argument("--live", action="store_true", help="actually run odin4 --reboot -a for the rollback AP")
    parser.add_argument("--ack", help=f"required with --live: {ACK_TOKEN}")
    args = parser.parse_args(argv)

    root = repo_root()
    ap = args.ap if args.ap.is_absolute() else root / args.ap
    odin = args.odin if args.odin.is_absolute() else root / args.odin
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_p2_stock_boot_rollback_guard.txt"

    append_log(log_path, f"=== {utc_now()} s22plus p2 stock boot rollback guard ===")
    append_log(log_path, f"ap={ap}")
    append_log(log_path, f"odin={odin}")

    if not ap.is_file():
        raise SystemExit(f"rollback AP not found: {ap}")
    if not odin.is_file() or not odin.exists():
        raise SystemExit(f"odin4 not found: {odin}")

    ap_sha = sha256_file(ap)
    members = tar_members(ap)
    append_log(log_path, f"ap_sha256={ap_sha}")
    append_log(log_path, f"tar_members={members}")
    if ap_sha != EXPECTED_AP_SHA256:
        raise SystemExit(f"rollback AP SHA mismatch: {ap_sha}")
    if members != [EXPECTED_MEMBER]:
        raise SystemExit(f"rollback AP must contain exactly {EXPECTED_MEMBER!r}, got {members!r}")

    selected_device = args.device
    list_result, listed_devices = odin_devices(odin)
    append_log(log_path, f"initial odin4 -l rc={list_result.returncode} devices={listed_devices}")
    append_log(log_path, list_result.stdout + list_result.stderr)
    if selected_device is None:
        if len(listed_devices) == 1:
            selected_device = listed_devices[0]
        elif len(listed_devices) > 1:
            raise SystemExit(f"refusing ambiguous Odin device list: {listed_devices}")
        elif args.wait_sec > 0:
            selected_device = wait_for_odin_device(odin, args.wait_sec, log_path)

    if not args.live:
        append_log(log_path, "dry_run=1 live_odin_not_called")
        if selected_device:
            print(f"dry-run ok: selected Odin device {selected_device}")
            return 0
        print("dry-run ok: package verified; no Odin download device detected")
        return 2

    if args.ack != ACK_TOKEN:
        raise SystemExit(f"--live requires --ack {ACK_TOKEN}")
    if not selected_device:
        raise SystemExit("no single Odin download-mode device detected; refusing live rollback")

    cmd = [odin, "--reboot", "-a", ap, "-d", selected_device]
    append_log(log_path, f"live_cmd={' '.join(str(part) for part in cmd)}")
    result = run(cmd, timeout=180.0)
    append_log(log_path, f"odin_exit={result.returncode}")
    append_log(log_path, result.stdout + result.stderr)
    if result.returncode != 0:
        print(f"rollback odin failed rc={result.returncode}; see {log_path}", file=sys.stderr)
        return result.returncode or 1

    boot_ok = poll_android_boot(args.post_boot_wait_sec, log_path)
    append_log(log_path, f"post_rollback_android_boot_completed={int(boot_ok)}")
    print(f"rollback odin rc=0; android_boot_completed={int(boot_ok)}; log={log_path}")
    return 0 if boot_ok else 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
