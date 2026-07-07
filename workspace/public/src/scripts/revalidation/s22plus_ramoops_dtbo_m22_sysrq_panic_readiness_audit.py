#!/usr/bin/env python3
"""Host-only readiness audit for the S22+ ramoops DTBO + M22 sysrq-panic gate.

This script performs no Android, Odin live, flash, reboot, partition, or sysfs
action. It checks that the inert M22 policy draft is complete, the active
AGENTS.md state is in the expected inactive/active state, and the guarded gate's
offline/plan/fail-closed paths still behave as designed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate as gate


DEFAULT_DRAFT = Path("docs/operations/S22PLUS_RAMOOPS_DTBO_M22_SYSRQ_PANIC_AGENTS_EXCEPTION_DRAFT_2026-07-08.md")
DEFAULT_AGENTS = Path("AGENTS.md")
DEFAULT_GATE = Path("workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py")


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").is_dir():
            return parent
    raise RuntimeError(f"could not locate repo root from {current}")


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def required_markers() -> list[str]:
    return [
        "S22+ ramoops DTBO + M22 sysrq-panic retained-console",
        "workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py",
        gate.EXPECTED_DTBO_CANDIDATE_AP_SHA256,
        gate.EXPECTED_DTBO_ROLLBACK_AP_SHA256,
        gate.EXPECTED_PATCHED_DTBO_RAW_SHA256,
        gate.EXPECTED_STOCK_DTBO_RAW_SHA256,
        gate.EXPECTED_M22_AP_SHA256,
        gate.EXPECTED_M22_BOOT_SHA256,
        gate.EXPECTED_M22_BASE_BOOT_SHA256,
        gate.EXPECTED_M22_KERNEL_SHA256,
        gate.EXPECTED_M22_INIT_SHA256,
        gate.EXPECTED_M22_SOURCE_SHA256,
        gate.EXPECTED_MAGISK_AP_SHA256,
        gate.EXPECTED_STOCK_BOOT_AP_SHA256,
        gate.LIVE_ACK_TOKEN,
        gate.ROLLBACK_BOOT_ACK_TOKEN,
        gate.RESTORE_DTBO_ACK_TOKEN,
        "dtbo.img.lz4",
        "boot.img.lz4",
        "ramoops_region/status=okay",
        gate.EXPECTED_M22_LABEL,
        gate.EXPECTED_M22_MARKER,
        "intentional kernel crash",
        "sysrq-trigger-c",
        "restore stock DTBO",
        "manual download-mode",
        "no vendor_boot",
    ]


def normalized_text(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"required file missing: {path}")
    return " ".join(path.read_text(encoding="utf-8").split())


def marker_status(path: Path, markers: list[str]) -> dict[str, Any]:
    text = normalized_text(path)
    missing = [marker for marker in markers if marker not in text]
    return {
        "path": str(path),
        "required_count": len(markers),
        "missing": missing,
        "complete": missing == [],
    }


def run_command(root: Path, argv: list[str | Path], timeout: float) -> dict[str, Any]:
    completed = subprocess.run(
        [str(part) for part in argv],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "argv": [str(part) for part in argv],
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def add_failure(report: dict[str, Any], message: str) -> None:
    report.setdefault("failures", []).append(message)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--agents", type=Path, default=DEFAULT_AGENTS)
    parser.add_argument("--gate", type=Path, default=DEFAULT_GATE)
    parser.add_argument("--out", type=Path, help="optional JSON output path")
    parser.add_argument("--expect-agents-active", action="store_true")
    parser.add_argument("--no-default-fail-closed-check", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root()
    draft = resolve(root, args.draft)
    agents = resolve(root, args.agents)
    gate_script = resolve(root, args.gate)
    markers = required_markers()

    report: dict[str, Any] = {
        "generated_at_utc": utc_now(),
        "purpose": "host-only readiness audit for S22+ ramoops DTBO + M22 sysrq-panic retained-console gate",
        "device_action": False,
        "live_action": False,
        "required_markers": markers,
        "draft": marker_status(draft, markers),
        "agents": marker_status(agents, markers),
        "commands": {},
        "failures": [],
    }

    if not report["draft"]["complete"]:
        add_failure(report, f"M22 exception draft missing markers: {report['draft']['missing']}")
    if args.expect_agents_active:
        if not report["agents"]["complete"]:
            add_failure(report, f"AGENTS.md missing active M22 markers: {report['agents']['missing']}")
    elif report["agents"]["complete"]:
        add_failure(report, "AGENTS.md already contains complete active M22 markers; expected inactive policy")

    offline = run_command(root, ["python3", gate_script, "--offline-check"], timeout=30.0)
    report["commands"]["offline_check"] = offline
    if offline["returncode"] != 0:
        add_failure(report, f"M22 gate --offline-check failed rc={offline['returncode']}")

    plan = run_command(root, ["python3", gate_script, "--print-plan"], timeout=30.0)
    report["commands"]["print_plan"] = plan
    plan_output = f"{plan['stdout']}\n{plan['stderr']}"
    if plan["returncode"] != 0:
        add_failure(report, f"M22 gate --print-plan failed rc={plan['returncode']}")
    for expected in [
        gate.LIVE_ACK_TOKEN,
        gate.ROLLBACK_BOOT_ACK_TOKEN,
        gate.RESTORE_DTBO_ACK_TOKEN,
        "--rollback-boot-from-download",
        "--restore-dtbo-from-android",
        "--restore-dtbo-from-download",
        gate.EXPECTED_M22_MARKER,
        "sysrq-trigger-c",
    ]:
        if expected not in plan_output:
            add_failure(report, f"M22 gate --print-plan missing expected text: {expected}")

    if not args.no_default_fail_closed_check and not args.expect_agents_active:
        dryrun = run_command(root, ["python3", gate_script], timeout=30.0)
        report["commands"]["default_fail_closed"] = dryrun
        combined = f"{dryrun['stdout']}\n{dryrun['stderr']}"
        expected_message = "AGENTS.md missing ramoops DTBO + M22 authorization markers"
        if dryrun["returncode"] == 0:
            add_failure(report, "M22 default run unexpectedly passed with inactive policy")
        if expected_message not in combined:
            add_failure(report, "M22 default run did not fail at the expected AGENTS marker gate")

    report["result"] = "pass" if not report["failures"] else "fail"
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        out = resolve(root, args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
