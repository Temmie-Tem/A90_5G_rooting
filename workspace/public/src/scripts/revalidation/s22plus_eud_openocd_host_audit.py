#!/usr/bin/env python3
"""Host-only audit for the S22+ EUD OpenOCD/SWD path.

This helper performs no device action:

- no ADB, flash, reboot, partition write, sysfs write, or EUD enable;
- checks whether the host has an OpenOCD binary and EUD/Qualcomm scripts;
- snapshots host USB/TTY state for an already-attached EUD interface;
- optionally folds in the latest EUD Phase-B summary to avoid re-running the
  reversible enable write.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_RUN_ROOT = Path("workspace/private/runs")
PHASE_B_PREFIX = "s22plus_eud_phase_b_enable_"
EXPECTED_TARGET = "SM-S906N/g0q/S906NKSS7FYG8"


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
    base = resolve(root, DEFAULT_RUN_ROOT / f"s22plus_eud_openocd_host_audit_{stamp}")
    for suffix in range(100):
        run_dir = base if suffix == 0 else Path(f"{base}_{suffix:02d}")
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        return run_dir
    raise SystemExit(f"could not allocate unique run directory under {base.parent}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def redact(text: str) -> str:
    text = re.sub(r"RFCT[0-9A-Z]+", "<REDACTED_SERIAL>", text)
    text = re.sub(r"usb-SAMSUNG_SAMSUNG_Android_[^/\s]+", "usb-SAMSUNG_SAMSUNG_Android_<REDACTED_SERIAL>", text)
    text = re.sub(r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", "<REDACTED_MAC>", text)
    return text


def run_command(argv: list[str | Path], timeout: float = 10.0) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [str(part) for part in argv],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "argv": [str(part) for part in argv],
            "returncode": completed.returncode,
            "stdout": redact(completed.stdout),
            "stderr": redact(completed.stderr),
            "timeout": False,
        }
    except FileNotFoundError as exc:
        return {
            "argv": [str(part) for part in argv],
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
            "timeout": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": [str(part) for part in argv],
            "returncode": 124,
            "stdout": redact(exc.stdout or ""),
            "stderr": redact(exc.stderr or ""),
            "timeout": True,
        }


def existing_dirs(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    found: list[Path] = []
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        found.append(path)
    return found


def infer_script_dirs(openocd_path: Path | None, extra: list[Path]) -> list[Path]:
    candidates: list[Path] = []
    env_scripts = os.environ.get("OPENOCD_SCRIPTS")
    if env_scripts:
        candidates.append(Path(env_scripts))
    candidates.extend(extra)
    if openocd_path is not None:
        candidates.append(openocd_path.parent.parent / "share" / "openocd" / "scripts")
        candidates.append(openocd_path.parent.parent / "share" / "openocd")
    candidates.extend(
        [
            Path("/usr/share/openocd/scripts"),
            Path("/usr/local/share/openocd/scripts"),
            Path("/opt/openocd/share/openocd/scripts"),
        ]
    )
    return existing_dirs(candidates)


def find_named(root: Path, relative_names: list[str], patterns: list[str]) -> list[str]:
    hits: list[str] = []
    for rel in relative_names:
        path = root / rel
        if path.is_file():
            hits.append(str(path))
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                value = str(path)
                if value not in hits:
                    hits.append(value)
    return hits


def inspect_openocd(openocd: Path | None, script_dirs: list[Path]) -> dict[str, Any]:
    openocd_str = str(openocd) if openocd is not None else shutil.which("openocd")
    openocd_path = Path(openocd_str) if openocd_str else None
    version = run_command([openocd_path, "--version"], timeout=5.0) if openocd_path else None
    dirs = infer_script_dirs(openocd_path, script_dirs)
    eud_cfg: list[str] = []
    qcom_cfg: list[str] = []
    sm8450_cfg: list[str] = []
    for directory in dirs:
        eud_cfg.extend(find_named(directory, ["interface/eud.cfg"], ["interface/*eud*.cfg", "**/*eud*.cfg"]))
        qcom_cfg.extend(
            find_named(
                directory,
                ["target/qualcomm/qcom.cfg", "target/qcom.cfg"],
                ["target/**/qcom*.cfg", "target/**/qualcomm*.cfg"],
            )
        )
        sm8450_cfg.extend(find_named(directory, [], ["target/**/*sm8450*.cfg", "**/*sm8450*.cfg"]))
    return {
        "openocd_present": bool(
            openocd_path is not None and (openocd_path.is_file() or shutil.which(str(openocd_path)) is not None)
        ),
        "openocd_path": str(openocd_path) if openocd_path else None,
        "openocd_version": version,
        "script_dirs": [str(path) for path in dirs],
        "eud_cfg": sorted(set(eud_cfg)),
        "qcom_cfg": sorted(set(qcom_cfg)),
        "sm8450_cfg": sorted(set(sm8450_cfg)),
        "eud_cfg_present": bool(eud_cfg),
        "qcom_cfg_present": bool(qcom_cfg),
        "sm8450_cfg_present": bool(sm8450_cfg),
    }


def eud_hint(text: str) -> bool:
    return bool(re.search(r"\bEUD\b|Embedded USB Debug|Qualcomm.*debug|05c6:", text, re.IGNORECASE))


def tty_paths_from_text(text: str) -> list[str]:
    paths = sorted(set(re.findall(r"/dev/(?:tty(?:ACM|USB)\d+|serial/by-[^\s]+)", text)))
    return paths


def inspect_host_usb(run_dir: Path) -> dict[str, Any]:
    commands = {
        "lsusb": run_command(["lsusb"], timeout=10.0),
        "lsusb_tree": run_command(["lsusb", "-t"], timeout=10.0),
        "tty_paths": run_command(
            [
                "bash",
                "-lc",
                "find /dev/serial/by-id /dev/serial/by-path -maxdepth 1 -type l -print 2>/dev/null; "
                "ls -1 /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true",
            ],
            timeout=10.0,
        ),
    }
    for name, result in commands.items():
        write_text(run_dir / "host" / f"{name}.txt", result["stdout"] + result["stderr"])
    combined = "\n".join(result["stdout"] + result["stderr"] for result in commands.values())
    return {
        "commands": commands,
        "host_eud_usb_hint": eud_hint(combined),
        "host_tty_paths": tty_paths_from_text(combined),
    }


def is_live_phase_b_summary(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return False
    return all(key in data for key in ("restored_enable_0", "enable_result", "after_enable", "after_disable"))


def latest_phase_b_summary(root: Path) -> Path | None:
    run_root = root / DEFAULT_RUN_ROOT
    if not run_root.is_dir():
        return None
    candidates = sorted(
        (path / "summary.json" for path in run_root.iterdir() if path.is_dir() and path.name.startswith(PHASE_B_PREFIX)),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    for path in candidates:
        if path.is_file() and is_live_phase_b_summary(path):
            return path
    return None


def load_phase_b_summary(root: Path, requested: Path | None) -> dict[str, Any] | None:
    path = resolve(root, requested) if requested is not None else latest_phase_b_summary(root)
    if path is None or not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        "path": str(path),
        "restored_enable_0": bool(data.get("restored_enable_0")),
        "host_eud_usb_hint": bool(data.get("host_eud_usb_hint")),
        "host_new_serial_tty_hint": bool(data.get("host_new_serial_tty_hint")),
        "host_eud_or_new_tty_hint": bool(data.get("host_eud_or_new_tty_hint")),
        "after_enable_runtime_status": (data.get("after_enable") or {}).get("runtime_status"),
        "after_disable_runtime_status": (data.get("after_disable") or {}).get("runtime_status"),
        "secure_path_hint": bool((data.get("after_enable") or {}).get("secure_path_hint"))
        or bool((data.get("after_disable") or {}).get("secure_path_hint")),
    }


def classify(readiness: dict[str, Any]) -> dict[str, Any]:
    openocd = readiness["openocd"]
    host = readiness["host"]
    phase_b = readiness.get("phase_b")
    reasons: list[str] = []

    if not openocd["openocd_present"]:
        reasons.append("openocd-not-installed")
    if not openocd["eud_cfg_present"]:
        reasons.append("missing-interface-eud-cfg")
    if not openocd["qcom_cfg_present"]:
        reasons.append("missing-qualcomm-target-cfg")
    if not openocd["sm8450_cfg_present"]:
        reasons.append("missing-sm8450-target-cfg")
    if phase_b and phase_b["restored_enable_0"] and not phase_b["host_eud_or_new_tty_hint"]:
        reasons.append("phase-b-no-host-eud-or-new-tty")
    if not host["host_eud_usb_hint"]:
        reasons.append("no-current-host-eud-usb")

    if not openocd["openocd_present"]:
        result = "blocked_no_openocd"
    elif not openocd["eud_cfg_present"] or not openocd["qcom_cfg_present"]:
        result = "blocked_missing_openocd_eud_scripts"
    elif not openocd["sm8450_cfg_present"]:
        result = "blocked_missing_sm8450_target"
    elif not host["host_eud_usb_hint"]:
        result = "waiting_for_eud_enumeration_or_hardware"
    else:
        result = "host_openocd_eud_ready_to_probe"
    return {"result": result, "reasons": reasons}


def build_report(root: Path, args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    run_dir = resolve_run_dir(root, args.run_dir)
    openocd = inspect_openocd(args.openocd, [resolve(root, path) for path in args.script_dir])
    host = inspect_host_usb(run_dir)
    phase_b = load_phase_b_summary(root, args.phase_b_summary)
    summary: dict[str, Any] = {
        "generated_at_utc": utc_now(),
        "target": EXPECTED_TARGET,
        "device_action": False,
        "writes_performed": False,
        "reboots_performed": False,
        "flashes_performed": False,
        "sysfs_writes_performed": False,
        "openocd": openocd,
        "host": {
            "host_eud_usb_hint": host["host_eud_usb_hint"],
            "host_tty_paths": host["host_tty_paths"],
        },
        "phase_b": phase_b,
    }
    summary["classification"] = classify(summary)
    write_text(run_dir / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return run_dir, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--openocd", type=Path, help="specific OpenOCD binary to inspect")
    parser.add_argument("--script-dir", type=Path, action="append", default=[], help="additional OpenOCD scripts directory")
    parser.add_argument("--phase-b-summary", type=Path, help="specific EUD Phase-B summary.json to fold into the audit")
    parser.add_argument("--require-ready", action="store_true", help="return nonzero unless OpenOCD/EUD appears ready")
    args = parser.parse_args(argv)

    root = repo_root()
    run_dir, summary = build_report(root, args)
    result = summary["classification"]["result"]
    print(
        "S22+ EUD OpenOCD host audit: "
        f"{result}; openocd={int(summary['openocd']['openocd_present'])} "
        f"eud_cfg={int(summary['openocd']['eud_cfg_present'])} "
        f"qcom_cfg={int(summary['openocd']['qcom_cfg_present'])} "
        f"sm8450_cfg={int(summary['openocd']['sm8450_cfg_present'])} "
        f"host_eud_usb={int(summary['host']['host_eud_usb_hint'])}; "
        f"log={display_path(run_dir / 'summary.json')}"
    )
    if args.require_ready and result != "host_openocd_eud_ready_to_probe":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
