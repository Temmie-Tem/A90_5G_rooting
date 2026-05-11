#!/usr/bin/env python3
"""v195 broker soak suite that composes smoke, mixed-soak, and recovery gates."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from a90harness.evidence import EvidenceStore  # noqa: E402


DEFAULT_EXPECT_VERSION = "A90 Linux init 0.9.59 (v159)"


@dataclass
class SuiteStep:
    name: str
    ok: bool
    rc: int
    duration_sec: float
    command: list[str]
    output_file: str


def timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the broker-backed soak suite for A90B1 host tooling.",
    )
    parser.add_argument("--run-dir", type=Path,
                        default=Path("tmp") / f"a90-v195-broker-soak-{timestamp()}")
    parser.add_argument("--expect-version", default=DEFAULT_EXPECT_VERSION)
    parser.add_argument("--duration-sec", type=float, default=300.0)
    parser.add_argument("--observer-interval", type=float, default=15.0)
    parser.add_argument("--dry-run", action="store_true",
                        help="keep mixed-soak in dry-run mode; no live device commands required")
    parser.add_argument("--include-live-recovery", action="store_true",
                        help="run live v192 recovery cases in addition to fake recovery")
    parser.add_argument("--stop-on-failure", action="store_true")
    return parser


def script(name: str) -> Path:
    return SCRIPT_DIR / name


def run_step(store: EvidenceStore,
             name: str,
             command: list[str],
             *,
             timeout_sec: float) -> SuiteStep:
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_sec,
    )
    duration_sec = time.monotonic() - started
    output_name = f"{name}.txt"
    store.write_text(output_name, result.stdout)
    return SuiteStep(
        name=name,
        ok=result.returncode == 0,
        rc=result.returncode,
        duration_sec=duration_sec,
        command=command,
        output_file=output_name,
    )


def build_steps(args: argparse.Namespace, store: EvidenceStore) -> list[tuple[str, list[str], float]]:
    fake_smoke_dir = store.mkdir("fake-concurrent-smoke")
    mixed_dir = store.mkdir("mixed-soak")
    recovery_dir = store.mkdir("recovery-tests")

    steps: list[tuple[str, list[str], float]] = [
        (
            "fake-concurrent-smoke",
            [
                sys.executable,
                str(script("a90_broker_concurrent_smoke.py")),
                "--backend",
                "fake",
                "--clients",
                "4",
                "--rounds",
                "3",
                "--include-blocked",
                "--run-dir",
                str(fake_smoke_dir),
            ],
            60.0,
        ),
        (
            "broker-mixed-soak",
            [
                sys.executable,
                str(script("a90_broker_mixed_soak_gate.py")),
                "--run-dir",
                str(mixed_dir),
                "--duration-sec",
                str(args.duration_sec),
                "--observer-interval",
                str(args.observer_interval),
                "--workload-profile",
                "smoke",
                "--seed",
                "195",
                "--expect-version",
                args.expect_version,
                *(["--dry-run"] if args.dry_run else []),
            ],
            max(args.duration_sec + 360.0, 120.0),
        ),
        (
            "broker-recovery-tests",
            [
                sys.executable,
                str(script("a90_broker_recovery_tests.py")),
                "--run-dir",
                str(recovery_dir),
                *(["--include-live"] if args.include_live_recovery else []),
            ],
            120.0,
        ),
    ]
    return steps


def render_report(steps: list[SuiteStep], pass_ok: bool, args: argparse.Namespace) -> str:
    lines = [
        "# v195 Broker Soak Suite\n\n",
        f"- result: `{'PASS' if pass_ok else 'FAIL'}`\n",
        f"- run_dir: `{args.run_dir}`\n",
        f"- dry_run: `{args.dry_run}`\n",
        f"- include_live_recovery: `{args.include_live_recovery}`\n",
        f"- duration_sec: `{args.duration_sec}`\n\n",
        "## Steps\n\n",
    ]
    for step in steps:
        lines.append(
            f"- {'PASS' if step.ok else 'FAIL'} `{step.name}` "
            f"rc={step.rc} duration={step.duration_sec:.3f}s output=`{step.output_file}`\n"
        )
    return "".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    store = EvidenceStore(args.run_dir)
    planned_steps = build_steps(args, store)
    steps: list[SuiteStep] = []
    for name, command, timeout_sec in planned_steps:
        step = run_step(store, name, command, timeout_sec=timeout_sec)
        steps.append(step)
        if args.stop_on_failure and not step.ok:
            break

    pass_ok = all(step.ok for step in steps) and len(steps) == len(planned_steps)
    payload: dict[str, Any] = {
        "pass": pass_ok,
        "run_dir": str(args.run_dir),
        "dry_run": args.dry_run,
        "include_live_recovery": args.include_live_recovery,
        "duration_sec": args.duration_sec,
        "steps": [asdict(step) for step in steps],
    }
    store.write_json("broker-soak-suite-summary.json", payload)
    store.write_text("broker-soak-suite-report.md", render_report(steps, pass_ok, args))
    print(f"{'PASS' if pass_ok else 'FAIL'} run_dir={args.run_dir} steps={len(steps)}")
    return 0 if pass_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
