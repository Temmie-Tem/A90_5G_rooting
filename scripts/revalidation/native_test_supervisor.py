#!/usr/bin/env python3
"""A90 native-init host test supervisor."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from a90harness.device import DeviceClient  # noqa: E402
from a90harness.evidence import EvidenceStore  # noqa: E402
from a90harness.observer import run_observer  # noqa: E402
from a90harness.schema import CheckResult, CommandRecord, HarnessResult  # noqa: E402


DEFAULT_EXPECT_VERSION = "A90 Linux init 0.9.59 (v159)"


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def default_run_dir(label: str) -> Path:
    return REPO_ROOT / "tmp" / "soak" / "harness" / f"{label}-{utc_stamp()}"


def run_host_command(command: list[str], timeout: int = 10) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return result.returncode, result.stdout


def host_metadata() -> dict[str, Any]:
    rc, head = run_host_command(["git", "rev-parse", "--short", "HEAD"], timeout=5)
    rc_status, status = run_host_command(["git", "status", "--short"], timeout=5)
    return {
        "repo": str(REPO_ROOT),
        "git_head": head.strip() if rc == 0 else "unknown",
        "git_dirty": bool(rc_status == 0 and status.strip()),
        "git_status_short": status.splitlines() if rc_status == 0 and status.strip() else [],
    }


def transcript_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in name)
    return f"commands/{safe}.txt"


def record_command(store: EvidenceStore,
                   client: DeviceClient,
                   name: str,
                   command: list[str],
                   *,
                   timeout: float | None = None) -> tuple[CommandRecord, str]:
    relative = transcript_name(name)
    record, text = client.run(name, command, timeout=timeout, transcript=str(store.path(relative)))
    store.write_text(relative, text)
    return record, text


def render_summary(result: HarnessResult, manifest: dict[str, Any]) -> str:
    lines = [
        f"# {result.label}\n\n",
        f"- result: `{'PASS' if result.ok else 'FAIL'}`\n",
        f"- run_dir: `{manifest['run_dir']}`\n",
        f"- expect_version: `{manifest['expect_version']}`\n",
        f"- version_matches: `{manifest.get('version_matches')}`\n",
        f"- failed_checks: `{len([check for check in result.checks if not check.ok])}`\n",
        f"- failed_commands: `{len([command for command in result.commands if not command.ok])}`\n\n",
        "## Checks\n\n",
    ]
    for check in result.checks:
        lines.append(f"- {'PASS' if check.ok else 'FAIL'} `{check.name}`: {check.detail}\n")
    lines.append("\n## Commands\n\n")
    for command in result.commands:
        lines.append(
            f"- {'PASS' if command.ok else 'FAIL'} `{ ' '.join(command.command) }` "
            f"rc={command.rc} status={command.status} duration={command.duration_sec:.3f}s "
            f"file=`{command.transcript}`"
        )
        if command.error:
            lines.append(f" error=`{command.error}`")
        lines.append("\n")
    return "".join(lines)


def run_smoke(args: argparse.Namespace) -> int:
    run_dir = args.run_dir if args.run_dir is not None else default_run_dir("v170-smoke")
    run_dir = run_dir if run_dir.is_absolute() else REPO_ROOT / run_dir
    store = EvidenceStore(run_dir)
    store.mkdir("commands")
    client = DeviceClient(args.host, args.port, args.timeout)
    started = time.monotonic()

    commands: list[CommandRecord] = []
    checks: list[CheckResult] = []

    version_record, version_text = record_command(store, client, "version", ["version"], timeout=args.timeout)
    commands.append(version_record)
    version_matches = args.expect_version in version_text
    checks.append(CheckResult("version command", version_record.ok, f"rc={version_record.rc} status={version_record.status}"))
    checks.append(CheckResult("version matches", version_matches, args.expect_version))

    status_record, status_text = record_command(store, client, "status", ["status"], timeout=args.timeout)
    commands.append(status_record)
    checks.append(CheckResult("status command", status_record.ok, f"rc={status_record.rc} status={status_record.status}"))
    checks.append(CheckResult("status has selftest", "selftest:" in status_text, "status output contains selftest summary"))

    ok = all(check.ok for check in checks) and all(command.ok for command in commands)
    result = HarnessResult("A90 v170 Harness Foundation Smoke", ok, checks, commands)
    manifest: dict[str, Any] = {
        "label": result.label,
        "pass": ok,
        "run_dir": str(run_dir),
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "duration_sec": time.monotonic() - started,
        "expect_version": args.expect_version,
        "version_matches": version_matches,
        "host": host_metadata(),
        "result": result.to_dict(),
        "policy": "host-side smoke; cmdv1 version/status only; no device mutation",
    }
    store.write_json("manifest.json", manifest)
    store.write_text("summary.md", render_summary(result, manifest))
    print(f"{'PASS' if ok else 'FAIL'} run_dir={run_dir}")
    return 0 if ok else 1


def run_observe(args: argparse.Namespace) -> int:
    run_dir = args.run_dir if args.run_dir is not None else default_run_dir("v171-observer")
    run_dir = run_dir if run_dir.is_absolute() else REPO_ROOT / run_dir
    store = EvidenceStore(run_dir)
    client = DeviceClient(args.host, args.port, args.timeout)
    started = time.monotonic()

    observer_summary = run_observer(
        client,
        store,
        duration_sec=args.duration_sec,
        interval_sec=args.interval,
    )
    observer_text = store.path("observer.jsonl").read_text(encoding="utf-8", errors="replace")
    version_matches = args.expect_version in observer_text
    checks = [
        CheckResult("observer samples", observer_summary.samples > 0, f"samples={observer_summary.samples}"),
        CheckResult("observer failures", observer_summary.failures == 0, f"failures={observer_summary.failures}"),
        CheckResult("observer version matches", version_matches, args.expect_version),
    ]
    ok = observer_summary.ok and all(check.ok for check in checks)
    result = HarnessResult("A90 v171 Observer API", ok, checks, [])
    manifest: dict[str, Any] = {
        "label": result.label,
        "pass": ok,
        "run_dir": str(run_dir),
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "duration_sec": time.monotonic() - started,
        "expect_version": args.expect_version,
        "version_matches": version_matches,
        "host": host_metadata(),
        "observer": observer_summary.to_dict(),
        "result": result.to_dict(),
        "policy": "read-only observer; no device mutation",
    }
    store.write_json("manifest.json", manifest)
    store.write_text("summary.md", render_summary(result, manifest))
    print(f"{'PASS' if ok else 'FAIL'} run_dir={run_dir} samples={observer_summary.samples} failures={observer_summary.failures}")
    return 0 if ok else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=54321)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--expect-version", default=DEFAULT_EXPECT_VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    smoke = subparsers.add_parser("smoke", help="run v170 harness foundation smoke check")
    smoke.add_argument("--run-dir", type=Path)

    observe = subparsers.add_parser("observe", help="run v171 read-only observer")
    observe.add_argument("--run-dir", type=Path)
    observe.add_argument("--duration-sec", type=float, default=60.0)
    observe.add_argument("--interval", type=float, default=10.0)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "smoke":
        return run_smoke(args)
    if args.command == "observe":
        return run_observe(args)
    raise RuntimeError(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
