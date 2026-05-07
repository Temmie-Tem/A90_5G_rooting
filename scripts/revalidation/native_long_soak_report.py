#!/usr/bin/env python3
"""Build a host/device correlation report from native long-soak JSONL files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-jsonl", default="tmp/soak/native-long-soak-v150-host.jsonl")
    parser.add_argument("--device-jsonl", default="tmp/soak/native-long-soak-v150-device.jsonl")
    parser.add_argument("--out-md", default="tmp/soak/native-long-soak-v150-report.md")
    parser.add_argument("--out-json", default="tmp/soak/native-long-soak-v150-report.json")
    parser.add_argument("--min-device-samples", type=int, default=2)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def device_sequence_ok(samples: list[dict[str, Any]]) -> bool:
    expected = None

    for row in samples:
        seq = int(row.get("seq", 0))
        if expected is None:
            expected = seq
        if seq != expected:
            return False
        expected += 1
    return True


def monotonic_non_decreasing(rows: list[dict[str, Any]], key: str) -> bool:
    previous = None

    for row in rows:
        value = row.get(key)
        if value is None:
            continue
        value_f = float(value)
        if previous is not None and value_f < previous:
            return False
        previous = value_f
    return True


def main() -> int:
    args = parse_args()
    host_path = Path(args.host_jsonl)
    device_path = Path(args.device_jsonl)
    out_md = Path(args.out_md)
    out_json = Path(args.out_json)
    host_rows = read_jsonl(host_path)
    device_rows = read_jsonl(device_path)
    host_failures = [row for row in host_rows if not bool(row.get("ok"))]
    durations = [float(row.get("duration_sec", 0.0)) for row in host_rows]
    device_samples = [row for row in device_rows if row.get("type") == "sample"]
    device_stop = [row for row in device_rows if row.get("type") == "stop"]
    seq_ok = device_sequence_ok(device_samples)
    ts_ok = monotonic_non_decreasing(device_rows, "ts_ms")
    uptime_ok = monotonic_non_decreasing(device_samples, "uptime_sec")
    pass_ok = (
        len(host_rows) > 0 and
        len(host_failures) == 0 and
        len(device_samples) >= args.min_device_samples and
        seq_ok and
        ts_ok and
        uptime_ok
    )

    summary = {
        "pass": pass_ok,
        "host_jsonl": str(host_path),
        "device_jsonl": str(device_path),
        "host_events": len(host_rows),
        "host_failures": len(host_failures),
        "host_duration_avg_sec": mean(durations) if durations else 0.0,
        "host_duration_max_sec": max(durations) if durations else 0.0,
        "device_events": len(device_rows),
        "device_samples": len(device_samples),
        "device_stop_events": len(device_stop),
        "device_seq_contiguous": seq_ok,
        "device_ts_monotonic": ts_ok,
        "device_uptime_monotonic": uptime_ok,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Native Long Soak Correlation Report\n\n",
        f"- result: {'PASS' if pass_ok else 'FAIL'}\n",
        f"- host events: {summary['host_events']}\n",
        f"- host failures: {summary['host_failures']}\n",
        f"- host max duration: {summary['host_duration_max_sec']:.3f}s\n",
        f"- device events: {summary['device_events']}\n",
        f"- device samples: {summary['device_samples']}\n",
        f"- device stop events: {summary['device_stop_events']}\n",
        f"- device seq contiguous: {summary['device_seq_contiguous']}\n",
        f"- device ts monotonic: {summary['device_ts_monotonic']}\n",
        f"- device uptime monotonic: {summary['device_uptime_monotonic']}\n",
    ]
    out_md.write_text("".join(lines), encoding="utf-8")

    print(f"{'PASS' if pass_ok else 'FAIL'} host_events={len(host_rows)} device_samples={len(device_samples)}")
    print(out_md)
    print(out_json)
    return 0 if pass_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
