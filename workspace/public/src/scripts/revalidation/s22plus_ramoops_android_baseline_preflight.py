#!/usr/bin/env python3
"""Read-only Android baseline preflight for S22+ ramoops capture.

This helper does not flash, reboot, write sysfs, write partitions, or stage files
on the device. It verifies the connected Android baseline before any future
ramoops DTBO + M18 capture run:

- one matching S22+ ADB device;
- orange verified-boot state and completed Android boot;
- Magisk/root available;
- current boot partition equals the known Magisk baseline;
- current dtbo partition equals stock FYG8 DTBO.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import s22plus_ramoops_dtbo_m18_capture_live_gate as gate


EXPECTED_DTBO_SHA256 = gate.EXPECTED_STOCK_DTBO_RAW_SHA256
EXPECTED_BOOT_SHA256 = gate.EXPECTED_M18_BASE_BOOT_SHA256
EXPECTED_BUILD = gate.EXPECTED_BUILD
EXPECTED_DEVICE = gate.EXPECTED_DEVICE
EXPECTED_MODEL = gate.EXPECTED_MODEL


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").is_dir():
            return parent
    raise RuntimeError(f"could not locate repo root from {current}")


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def run(argv: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def adb(serial: str | None, *args: str, timeout: float = 20.0) -> subprocess.CompletedProcess[str]:
    argv = ["adb"]
    if serial:
        argv.extend(["-s", serial])
    argv.extend(args)
    return run(argv, timeout)


def adb_shell(serial: str | None, command: str, timeout: float = 20.0) -> subprocess.CompletedProcess[str]:
    return adb(serial, "shell", command, timeout=timeout)


def adb_devices(serial: str | None) -> list[tuple[str, str, str]]:
    result = adb(serial, "devices", "-l", timeout=10.0)
    rows: list[tuple[str, str, str]] = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split(maxsplit=2)
        if len(parts) >= 2:
            rows.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ""))
    return rows


def select_device(serial: str | None) -> str:
    rows = adb_devices(serial)
    usable = [row for row in rows if row[1] == "device"]
    if serial:
        usable = [row for row in usable if row[0] == serial]
    if len(usable) != 1:
        raise SystemExit(f"expected exactly one usable ADB device, got {[(row[1], row[2]) for row in usable]!r}")
    return usable[0][0]


def parse_key_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def get_props(serial: str) -> dict[str, str]:
    command = (
        "printf 'model='; getprop ro.product.model; "
        "printf 'device='; getprop ro.product.device; "
        "printf 'bootloader='; getprop ro.boot.bootloader; "
        "printf 'incremental='; getprop ro.build.version.incremental; "
        "printf 'vbstate='; getprop ro.boot.verifiedbootstate; "
        "printf 'boot_recovery='; getprop ro.boot.boot_recovery; "
        "printf 'boot_completed='; getprop sys.boot_completed; "
        "printf 'bootanim='; getprop init.svc.bootanim; "
        "printf 'su_id='; su -c id 2>/dev/null || true"
    )
    result = adb_shell(serial, command, timeout=25.0)
    values = parse_key_values(result.stdout + result.stderr)
    values["_rc"] = str(result.returncode)
    return values


def read_partition_hash(serial: str, by_name: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9._+-]+", by_name):
        raise ValueError(f"unsafe by-name partition: {by_name!r}")
    command = f"su -c 'dd if=/dev/block/by-name/{by_name} bs=4096 2>/dev/null | sha256sum'"
    result = adb_shell(serial, command, timeout=90.0)
    text = result.stdout + result.stderr
    match = re.search(r"\b([0-9a-fA-F]{64})\b", text)
    return {
        "partition": by_name,
        "returncode": result.returncode,
        "sha256": match.group(1).lower() if match else "",
        "bytes_of_output": len(text.encode("utf-8", errors="replace")),
    }


def read_ramoops_status(serial: str) -> dict[str, Any]:
    command = (
        "su -c '"
        "p=/proc/device-tree/reserved-memory/ramoops_region/status; "
        "if [ -e \"$p\" ]; then printf status=; tr \"\\000\" \"\\n\" < \"$p\"; "
        "else echo status_absent=1; fi'"
    )
    result = adb_shell(serial, command, timeout=20.0)
    text = result.stdout + result.stderr
    values = parse_key_values(text)
    return {
        "returncode": result.returncode,
        "status": values.get("status", ""),
        "status_absent": values.get("status_absent") == "1",
        "bytes_of_output": len(text.encode("utf-8", errors="replace")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", help="optional ADB serial to pin")
    parser.add_argument("--out", type=Path, help="optional JSON output path")
    args = parser.parse_args(argv)

    serial = select_device(args.serial)
    props = get_props(serial)
    boot_hash = read_partition_hash(serial, "boot")
    dtbo_hash = read_partition_hash(serial, "dtbo")
    ramoops = read_ramoops_status(serial)

    checks = {
        "model": props.get("model") == EXPECTED_MODEL,
        "device": props.get("device") == EXPECTED_DEVICE,
        "bootloader": props.get("bootloader") == EXPECTED_BUILD,
        "incremental": props.get("incremental") == EXPECTED_BUILD,
        "vbstate_orange": props.get("vbstate") == "orange",
        "boot_recovery_zero": props.get("boot_recovery") == "0",
        "boot_completed": props.get("boot_completed") == "1",
        "bootanim_stopped": props.get("bootanim") == "stopped",
        "root_available": "uid=0(root)" in props.get("su_id", ""),
        "boot_sha_matches_magisk_baseline": boot_hash["sha256"] == EXPECTED_BOOT_SHA256,
        "dtbo_sha_matches_stock": dtbo_hash["sha256"] == EXPECTED_DTBO_SHA256,
        "ramoops_status_disabled": ramoops["status"] == "disabled",
    }

    report: dict[str, Any] = {
        "generated_at_utc": utc_now(),
        "purpose": "read-only Android baseline preflight before S22+ ramoops DTBO + M18 capture",
        "device_action": "read-only-adb",
        "writes_performed": False,
        "serial_redacted": True,
        "props": {
            "model": props.get("model", ""),
            "device": props.get("device", ""),
            "bootloader": props.get("bootloader", ""),
            "incremental": props.get("incremental", ""),
            "vbstate": props.get("vbstate", ""),
            "boot_recovery": props.get("boot_recovery", ""),
            "boot_completed": props.get("boot_completed", ""),
            "bootanim": props.get("bootanim", ""),
            "su_id_root": "uid=0(root)" in props.get("su_id", ""),
        },
        "partition_hashes": {
            "boot": boot_hash,
            "dtbo": dtbo_hash,
            "expected_boot_sha256": EXPECTED_BOOT_SHA256,
            "expected_dtbo_sha256": EXPECTED_DTBO_SHA256,
        },
        "ramoops": ramoops,
        "checks": checks,
        "result": "pass" if all(checks.values()) else "fail",
    }

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        root = repo_root()
        out = resolve(root, args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
