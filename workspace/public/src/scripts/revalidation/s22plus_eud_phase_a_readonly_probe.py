#!/usr/bin/env python3
"""Read-only S22+ Qualcomm EUD Phase-A feasibility probe.

This helper performs only observation:

- no flash, reboot, partition write, sysfs write, module insertion, or EUD enable;
- Android/root preflight plus Magisk boot hash check;
- inventory of EUD module files/state, sysfs/platform nodes, live DT nodes, and
  dmesg hints.

Phase-B EUD enable remains a separate attended, ack-gated unit if Phase A finds
an enable control worth trying.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from s22plus_m3_observable_live_gate import (
    DEFAULT_ODIN,
    DEFAULT_RUN_ROOT,
    adb_exec_out,
    adb_shell,
    append_log,
    repo_root,
    require_current_android,
    resolve,
    run,
    utc_now,
)
from s22plus_m5_usb_acm_live_gate import verify_android_stability
from s22plus_sec_debug_mid_sysrq_gate import verify_current_boot_hash


EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
REPORT_PATH = Path("docs/reports/S22PLUS_EUD_PHASE_A_READONLY_PROBE_2026-07-08.md")
STEER_PATH = Path("docs/reports/S22PLUS_EUD_FEASIBILITY_PROBE_STEER_2026-07-08.md")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def resolve_run_dir(root: Path, requested: Path | None) -> Path:
    if requested is not None:
        run_dir = resolve(root, requested)
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir
    stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_eud_phase_a_readonly_{stamp}")
    for suffix in range(100):
        run_dir = base if suffix == 0 else Path(f"{base}_{suffix:02d}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return run_dir
    raise SystemExit(f"could not allocate unique run directory under {base.parent}")


def redact(text: str) -> str:
    text = re.sub(r"RFCT[0-9A-Z]+", "<REDACTED_SERIAL>", text)
    text = re.sub(r'((?:androidboot|sec_debug)\.[A-Za-z0-9_.-]*serial[A-Za-z0-9_.-]*=)"?[^"\s]+"?', r"\1<REDACTED>", text)
    text = re.sub(r'(kernel\.sec_debug\.ap_serial = )"[^"]+"', r'\1"<REDACTED_AP_SERIAL>"', text)
    text = re.sub(r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", "<REDACTED_MAC>", text)
    return text


def safe_name(name: str) -> str:
    cleaned = name.strip("/").replace("/", "__").replace("*", "glob")
    return re.sub(r"[^A-Za-z0-9_.+-]", "_", cleaned) or "root"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def host_command(run_dir: Path, label: str, argv: list[str | Path], timeout: float) -> dict[str, Any]:
    completed = run(argv, timeout=timeout)
    text = redact(completed.stdout + completed.stderr)
    write_text(run_dir / "host" / f"{label}.txt", text)
    summary = {
        "label": label,
        "rc": completed.returncode,
        "bytes": len(text.encode("utf-8", errors="replace")),
    }
    if label == "lsusb":
        summary["eud_usb_hint"] = bool(re.search(r"\bEUD\b|Embedded USB Debug|Qualcomm.*debug|05c6:", text, re.IGNORECASE))
    return summary


def adb_su_text(serial: str, command: str, *, timeout: float = 30.0) -> tuple[int, str]:
    result = adb_exec_out(command, serial=serial, timeout=timeout)
    text = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    return result.returncode, redact(text)


def collect_command(
    run_dir: Path,
    serial: str,
    label: str,
    command: str,
    *,
    timeout: float = 30.0,
) -> tuple[dict[str, Any], str]:
    rc, text = adb_su_text(serial, command, timeout=timeout)
    write_text(run_dir / "android" / f"{label}.txt", text)
    return {
        "label": label,
        "rc": rc,
        "bytes": len(text.encode("utf-8", errors="replace")),
        "line_count": len([line for line in text.splitlines() if line.strip()]),
    }, text


def parse_enable_attrs(text: str) -> list[dict[str, str]]:
    attrs: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("ATTR "):
            continue
        parts = line.split(" ", 3)
        if len(parts) == 4:
            attrs.append({"path": parts[1], "name": parts[2], "value": parts[3].strip()})
    return attrs


def collect_host_baseline(run_dir: Path, log_path: Path, odin: Path) -> dict[str, Any]:
    summary = {
        "lsusb": host_command(run_dir, "lsusb", ["lsusb"], 10.0),
        "ip_link": host_command(run_dir, "ip_link_json", ["ip", "-j", "link"], 10.0),
        "dmesg_tail": host_command(
            run_dir,
            "dmesg_tail",
            ["bash", "-lc", "dmesg -T 2>/dev/null | tail -n 240 || true"],
            10.0,
        ),
    }
    if odin.is_file():
        summary["odin_l"] = host_command(run_dir, "odin_l", [odin, "-l"], 10.0)
    append_log(log_path, f"host_baseline={json.dumps(summary, sort_keys=True)}")
    return summary


def collect_android_inventory(run_dir: Path, log_path: Path, serial: str) -> dict[str, Any]:
    commands: tuple[tuple[str, str, float], ...] = (
        (
            "props",
            "printf 'model='; getprop ro.product.model; "
            "printf 'device='; getprop ro.product.device; "
            "printf 'incremental='; getprop ro.build.version.incremental; "
            "printf 'boot_completed='; getprop sys.boot_completed; "
            "printf 'verifiedbootstate='; getprop ro.boot.verifiedbootstate; "
            "printf 'boot_recovery='; getprop ro.boot.boot_recovery; "
            "printf 'kernel='; uname -a; "
            "printf 'su='; id",
            20.0,
        ),
        (
            "eud_module_state",
            "printf 'lsmod_eud\\n'; lsmod 2>/dev/null | grep -i eud || true; "
            "printf 'proc_modules_eud\\n'; cat /proc/modules 2>/dev/null | grep -i eud || true; "
            "printf 'module_files_eud\\n'; "
            "for d in /vendor/lib/modules /vendor_dlkm/lib/modules /odm/lib/modules /lib/modules; do "
            "  [ -d \"$d\" ] && find \"$d\" -maxdepth 4 \\( -name '*eud*.ko*' -o -name 'eud*' \\) -print 2>/dev/null; "
            "done | sort -u | head -100",
            30.0,
        ),
        (
            "eud_sysfs_paths",
            "find /sys/bus/platform/devices /sys/devices/platform /sys/devices "
            "\\( -iname '*eud*' -o -path '*/eud/*' \\) -print 2>/dev/null | sort -u | head -240",
            30.0,
        ),
        (
            "eud_sysfs_attrs",
            "for p in $(find /sys/bus/platform/devices /sys/devices/platform /sys/devices "
            "\\( -iname '*eud*' -o -path '*/eud/*' \\) -print 2>/dev/null | sort -u | head -80); do "
            "  [ -d \"$p\" ] || continue; "
            "  for f in \"$p\"/enable \"$p\"/enabled \"$p\"/state \"$p\"/mode \"$p\"/secure \"$p\"/status \"$p\"/uevent \"$p\"/modalias; do "
            "    [ -e \"$f\" ] || continue; "
            "    v=$(cat \"$f\" 2>/dev/null | tr '\\000' ' ' | head -c 512); "
            "    printf 'ATTR %s %s %s\\n' \"$p\" \"${f##*/}\" \"$v\"; "
            "  done; "
            "done",
            30.0,
        ),
        (
            "eud_device_tree_paths",
            "printf 'name_matches\\n'; "
            "find /sys/firmware/devicetree/base /proc/device-tree -maxdepth 10 "
            "\\( -iname '*eud*' -o -iname '*usb*debug*' \\) -print 2>/dev/null | sort -u | head -160; "
            "printf 'compatible_hits\\n'; "
            "grep -R -a -l -E 'qcom,msm-eud|qcom,eud|eud' /sys/firmware/devicetree/base /proc/device-tree 2>/dev/null | head -160",
            45.0,
        ),
        (
            "eud_device_tree_node_dump",
            "for p in $(find /sys/firmware/devicetree/base /proc/device-tree -maxdepth 10 "
            "\\( -iname '*eud*' -o -iname '*usb*debug*' \\) -print 2>/dev/null | sort -u | head -80); do "
            "  d=\"$p\"; [ -f \"$d\" ] && d=$(dirname \"$d\"); [ -d \"$d\" ] || continue; "
            "  echo NODE \"$d\"; "
            "  for f in compatible status reg interrupts interrupt-names qcom,secure qcom,eud-mode; do "
            "    [ -e \"$d/$f\" ] || continue; "
            "    printf 'PROP %s ' \"$f\"; "
            "    if [ \"$f\" = reg ] || [ \"$f\" = interrupts ]; then od -An -tx4 \"$d/$f\" 2>/dev/null | head -4; "
            "    else tr '\\000' ' ' < \"$d/$f\" 2>/dev/null | head -c 512; echo; fi; "
            "  done; "
            "done",
            45.0,
        ),
        (
            "eud_tty_state",
            "printf 'dev_tty\\n'; ls -l /dev/ttyEUD* 2>&1 || true; "
            "printf 'proc_tty_drivers\\n'; cat /proc/tty/drivers 2>/dev/null | grep -Ei 'EUD|ttyEUD|msm' || true; "
            "printf 'tty_attrs\\n'; "
            "for f in /sys/devices/platform/soc/88e0000.qcom,msm-eud/extcon/extcon0/name "
            "/sys/devices/platform/soc/88e0000.qcom,msm-eud/extcon/extcon0/state "
            "/sys/devices/platform/soc/88e0000.qcom,msm-eud/power/runtime_status "
            "/sys/devices/platform/soc/88e0000.qcom,msm-eud/tty/ttyEUD0/console "
            "/sys/devices/platform/soc/88e0000.qcom,msm-eud/tty/ttyEUD0/dev "
            "/sys/devices/platform/soc/88e0000.qcom,msm-eud/tty/ttyEUD0/irq "
            "/sys/devices/platform/soc/88e0000.qcom,msm-eud/tty/ttyEUD0/uartclk; do "
            "  echo ===$f; cat \"$f\" 2>&1 | head -20; "
            "done",
            30.0,
        ),
        (
            "eud_dmesg",
            "dmesg | grep -Ei '(^|[^A-Za-z])eud([^A-Za-z]|$)|embedded usb|usb debug|qcom,msm-eud|jtag|swd|ttyEUD' | tail -240 || true",
            30.0,
        ),
        (
            "eud_kernel_config",
            "zcat /proc/config.gz 2>/dev/null | grep -Ei '(^CONFIG_.*EUD|MSM_EUD|USB_DEBUG|JTAG|QCOM.*DEBUG)' || true",
            30.0,
        ),
    )

    outputs: dict[str, str] = {}
    command_summaries: dict[str, dict[str, Any]] = {}
    for label, command, timeout in commands:
        meta, text = collect_command(run_dir, serial, label, command, timeout=timeout)
        outputs[label] = text
        command_summaries[label] = meta

    module_text = outputs["eud_module_state"]
    sysfs_text = outputs["eud_sysfs_paths"]
    attrs_text = outputs["eud_sysfs_attrs"]
    dt_text = outputs["eud_device_tree_paths"]
    tty_text = outputs["eud_tty_state"]
    dmesg_text = outputs["eud_dmesg"]
    config_text = outputs["eud_kernel_config"]
    attrs = parse_enable_attrs(attrs_text)
    enable_attrs = [item for item in attrs if item["name"] in ("enable", "enabled")]
    tty_present = "/dev/ttyEUD0" in tty_text or "ttyEUD0" in sysfs_text
    platform_bound = "DRIVER=msm-eud" in attrs_text or "88e0000.qcom,msm-eud" in sysfs_text

    summary = {
        "commands": command_summaries,
        "eud_module_loaded": bool(re.search(r"(?m)^eud\s", module_text, re.IGNORECASE)),
        "eud_module_file_found": ".ko" in module_text or re.search(r"/eud[^\s]*", module_text, re.IGNORECASE) is not None,
        "eud_platform_bound": platform_bound,
        "eud_sysfs_path_count": len([line for line in sysfs_text.splitlines() if line.startswith("/sys/")]),
        "eud_attrs": attrs,
        "eud_enable_attr_count": len(enable_attrs),
        "eud_enable_attrs": enable_attrs,
        "eud_tty_present": tty_present,
        "eud_dt_path_count": len(
            [line for line in dt_text.splitlines() if line.startswith("/proc/device-tree") or line.startswith("/sys/firmware/devicetree")]
        ),
        "eud_dt_compatible_hit": bool(re.search(r"qcom,msm-eud|qcom,eud|eud", dt_text, re.IGNORECASE)),
        "eud_dmesg_hit_count": len([line for line in dmesg_text.splitlines() if line.strip()]),
        "eud_kernel_config_hit_count": len([line for line in config_text.splitlines() if line.strip()]),
    }
    summary["phase_b_enable_candidate"] = bool(summary["eud_enable_attr_count"])
    summary["console_route_candidate"] = bool(summary["eud_tty_present"] and summary["eud_platform_bound"])
    summary["phase_b_candidate"] = bool(summary["phase_b_enable_candidate"] or summary["console_route_candidate"])
    append_log(log_path, f"android_inventory={json.dumps(summary, sort_keys=True)}")
    return summary


def print_plan() -> None:
    script = "workspace/public/src/scripts/revalidation/s22plus_eud_phase_a_readonly_probe.py"
    print("S22+ EUD Phase-A read-only probe")
    print("state: host/adb read-only; no EUD enable, no sysfs write, no reboot, no flash")
    print()
    print("host-only validation:")
    print(f"  PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 {script} --offline-check")
    print(f"  PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 {script} --print-plan")
    print()
    print("live read-only inventory:")
    print(f"  PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 {script}")
    print()
    print("Phase-B enable is intentionally not implemented here; make a separate ack-gated helper if Phase A finds an enable attr.")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--serial")
    parser.add_argument("--android-stability-samples", type=int, default=4)
    parser.add_argument("--android-stability-interval-sec", type=float, default=3.0)
    parser.add_argument("--offline-check", action="store_true")
    parser.add_argument("--print-plan", action="store_true")
    args = parser.parse_args(argv)

    if args.offline_check and args.print_plan:
        raise SystemExit("--offline-check and --print-plan are mutually exclusive")

    root = repo_root()
    run_dir = resolve_run_dir(root, args.run_dir)
    log_path = run_dir / "s22plus_eud_phase_a_readonly_probe.txt"
    append_log(log_path, f"=== {utc_now()} s22plus EUD Phase-A read-only probe ===")
    append_log(log_path, f"target={EXPECTED_TARGET}")

    if args.print_plan:
        append_log(log_path, "print_plan=ok device_action=0")
        print_plan()
        print(f"log={display_path(log_path)}")
        return 0

    if args.offline_check:
        missing = [str(path) for path in (root / STEER_PATH,) if not path.is_file()]
        if missing:
            raise SystemExit(f"missing expected files: {missing}")
        append_log(log_path, "offline_check=ok device_action=0")
        print(f"offline-check ok: EUD Phase-A helper imports and path constants are valid; log={display_path(log_path)}")
        return 0

    odin = resolve(root, args.odin)
    selected_serial = require_current_android(log_path, args.serial)
    verify_android_stability(
        log_path,
        selected_serial,
        args.android_stability_samples,
        args.android_stability_interval_sec,
    )
    verify_current_boot_hash(log_path, selected_serial)
    host = collect_host_baseline(run_dir, log_path, odin)
    android = collect_android_inventory(run_dir, log_path, selected_serial)
    summary = {
        "mode": "eud_phase_a_readonly_probe",
        "target": EXPECTED_TARGET,
        "generated_at_utc": utc_now(),
        "writes_performed": False,
        "reboots_performed": False,
        "flashes_performed": False,
        "sysfs_writes_performed": False,
        "modules_inserted": False,
        "eud_enable_attempted": False,
        "host": host,
        "android": android,
    }
    write_text(run_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    append_log(log_path, f"summary={json.dumps(summary, sort_keys=True)}")
    print(
        "EUD Phase-A read-only probe ok: "
        f"module_file={int(android['eud_module_file_found'])} "
        f"loaded={int(android['eud_module_loaded'])} "
        f"sysfs_paths={android['eud_sysfs_path_count']} "
        f"enable_attrs={android['eud_enable_attr_count']} "
        f"ttyEUD0={int(android['eud_tty_present'])} "
        f"dt_paths={android['eud_dt_path_count']} "
        f"phase_b_candidate={int(android['phase_b_candidate'])} "
        f"log={display_path(log_path)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
