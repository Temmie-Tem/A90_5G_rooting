#!/usr/bin/env python3
"""Host side of the read-only boot-target auditor (§7.1).

Parses the device `boot-audit` command's `A90BOOTAUDIT key=value` output into the boot-target
guard's BlockIdentity, evaluates it (discovery/auditor mode — unconfirmed pin allowed), and emits a
proposed auditor-confirmed BootTargetPin (rdev + canonical + diskseq) for the operator to adopt into
the eventual write path. Read-only: this never triggers a write; it only reads and decides.

Pure-function core (parse_audit_output / audit_to_identity / assess) is offline-testable; --run
sends the command over the serial bridge and assesses the live output.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict

from a90_boot_target_guard import (
    BlockIdentity,
    BootTargetPin,
    evaluate_boot_target,
)

AUDIT_PREFIX = "A90BOOTAUDIT"


def parse_audit_output(text: str) -> dict:
    """Extract A90BOOTAUDIT key=value pairs from device output into a dict."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith(AUDIT_PREFIX):
            continue
        rest = line[len(AUDIT_PREFIX):].strip()
        if "=" not in rest:
            # markers like "begin" / "end rc=0"
            out.setdefault("_markers", "")
            out["_markers"] += rest + ";"
            continue
        key, _, val = rest.partition("=")
        out[key.strip()] = val.strip()
    return out


def audit_to_identity(parsed: dict) -> BlockIdentity:
    """Build the guard's BlockIdentity from parsed audit fields. Raises on missing essentials."""
    if parsed.get("open") != "ok":
        raise ValueError(f"boot-audit did not open the target (open={parsed.get('open')!r})")
    rdev = parsed.get("rdev", "")
    if ":" not in rdev:
        raise ValueError(f"missing/invalid rdev: {rdev!r}")
    major_s, _, minor_s = rdev.partition(":")
    size_field = parsed.get("size_bytes", "")
    if not size_field.isdigit():
        raise ValueError(f"missing/invalid size_bytes: {size_field!r}")
    diskseq = parsed.get("diskseq")
    diskseq_val = int(diskseq) if (diskseq and diskseq.isdigit()) else None
    return BlockIdentity(
        canonical_path=parsed.get("canonical", ""),
        rdev_major=int(major_s),
        rdev_minor=int(minor_s),
        partname=parsed.get("partname", ""),
        size_bytes=int(size_field),
        is_block=parsed.get("is_block") == "1",
        diskseq=diskseq_val,
    )


def proposed_pin(identity: BlockIdentity) -> BootTargetPin:
    """The auditor-confirmed pin an operator would adopt for the write path (§2)."""
    return BootTargetPin(
        canonical_path=identity.canonical_path,
        rdev_major=identity.rdev_major,
        rdev_minor=identity.rdev_minor,
        diskseq=identity.diskseq,
    )


def assess(text: str) -> dict:
    """Full offline assessment of raw device output. Returns a report dict."""
    parsed = parse_audit_output(text)
    report: dict = {"parsed": parsed}
    try:
        identity = audit_to_identity(parsed)
    except ValueError as exc:
        report["ok"] = False
        report["error"] = str(exc)
        return report
    result = evaluate_boot_target(identity)  # discovery mode (unconfirmed pin allowed)
    report["identity"] = asdict(identity)
    report["evaluate_ok"] = result.ok
    report["evaluate_reason"] = result.reason
    report["proposed_pin"] = asdict(proposed_pin(identity))
    report["ok"] = result.ok
    return report


def _run_live(args) -> str:
    """Send `boot-audit` over the serial bridge and return raw output."""
    from a90_transport import run_cmdv1_command  # local import; live-only
    result = run_cmdv1_command(args.bridge_host, args.bridge_port, args.bridge_timeout,
                               ["boot-audit"] + ([args.target] if args.target else []))
    return result.text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true", help="send boot-audit over the bridge (live)")
    ap.add_argument("--target", default=None, help="optional target path to audit read-only")
    ap.add_argument("--from-file", type=str, help="assess captured output from a file instead")
    ap.add_argument("--bridge-host", default="127.0.0.1")
    ap.add_argument("--bridge-port", type=int, default=54321)
    ap.add_argument("--bridge-timeout", type=float, default=20.0)
    args = ap.parse_args()

    if args.from_file:
        text = open(args.from_file).read()
    elif args.run:
        text = _run_live(args)
    else:
        text = sys.stdin.read()

    import json
    report = assess(text)
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
