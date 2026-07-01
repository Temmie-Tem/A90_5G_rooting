#!/usr/bin/env python3
"""Aggregate REPL live-call-proof run timings to find average phase times + the bottleneck.

Host-only. Reads the private `timeline.json` evidence emitted by the device-touching
V-iterations (per the GOAL.md 2026-07-01 timing rule) and reports per-phase mean / median /
min / max / p95 across runs, plus which phase dominates (the bottleneck) and the flash-vs-work
split that sizes a batching win. NO device action.

Handles both observed schemas:
  - events schema:   {"events": [{"name": ..., "timestamp_utc": ...}, ...]}
  - timeline schema: {"timeline": {"candidate_flash_start": ..., ...}}  (nested named phases)

Usage:
  python3 workspace/public/src/scripts/analysis/analyze_repl_run_timing.py \
    [--runs-dir workspace/private/runs/kernel] [--json]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_RUNS = REPO_ROOT / "workspace/private/runs/kernel"

# Canonical phases: (label, start-name-candidates, end-name-candidates). First present pair wins.
PHASES = [
    ("candidate flash", ["candidate_flash_start"], ["candidate_flash_done"]),
    ("candidate boot/health",
     ["candidate_flash_done"],
     ["candidate_boot_ready", "candidate_health_done", "candidate_health_start"]),
    ("live session (work)", ["live_session_start"], ["live_session_end"]),
    ("rollback flash", ["rollback_flash_start"], ["rollback_flash_done"]),
    ("rollback boot/health",
     ["rollback_flash_done"],
     ["rollback_boot_ready", "final_health_done", "final_selftest_done"]),
]


def parse_ts(s: str) -> dt.datetime | None:
    if not isinstance(s, str):
        return None
    s = s.strip().replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def extract_names(doc) -> dict[str, dt.datetime]:
    """Return {phase_name: earliest timestamp} from either schema."""
    out: dict[str, dt.datetime] = {}
    if isinstance(doc, list):
        doc = {"events": doc}
    if not isinstance(doc, dict):
        return out

    def put(name: str, ts: dt.datetime | None) -> None:
        if ts is None or not name:
            return
        # keep the first occurrence (start/first-response semantics)
        if name not in out or ts < out[name]:
            out[name] = ts

    if isinstance(doc.get("events"), list):
        for ev in doc["events"]:
            if isinstance(ev, dict):
                put(ev.get("name", ""), parse_ts(ev.get("timestamp_utc") or ev.get("timestamp") or ""))
    tl = doc.get("timeline")
    if isinstance(tl, dict):
        for name, val in tl.items():
            put(name, parse_ts(val))
    return out


def first_pair(names: dict[str, dt.datetime], starts: list[str], ends: list[str]):
    s = next((names[n] for n in starts if n in names), None)
    e = next((names[n] for n in ends if n in names), None)
    if s is not None and e is not None and (e - s).total_seconds() >= 0:
        return (e - s).total_seconds()
    return None


def fmt(x: float) -> str:
    return f"{x:6.1f}s"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS)
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    tls = sorted(args.runs_dir.glob("*/timeline.json"))
    per_phase: dict[str, list[float]] = {label: [] for label, _, _ in PHASES}
    runs_used = 0
    for tl in tls:
        try:
            doc = json.loads(tl.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        names = extract_names(doc)
        if not names:
            continue
        runs_used += 1
        for label, starts, ends in PHASES:
            d = first_pair(names, starts, ends)
            if d is not None:
                per_phase[label].append(d)

    def stats(v: list[float]) -> dict:
        if not v:
            return {}
        sv = sorted(v)
        p95 = sv[min(len(sv) - 1, int(round(0.95 * (len(sv) - 1))))]
        return {"n": len(v), "mean": statistics.mean(v), "median": statistics.median(v),
                "min": min(v), "max": max(v), "p95": p95}

    summary = {label: stats(v) for label, v in per_phase.items()}

    if args.json:
        print(json.dumps({"runs_dir": str(args.runs_dir), "timelines_found": len(tls),
                          "runs_used": runs_used, "phases": summary}, indent=2))
        return 0

    print(f"REPL run timing — {runs_used}/{len(tls)} timelines parsed from {args.runs_dir}\n")
    print(f"{'phase':24} {'n':>3} {'mean':>7} {'median':>7} {'min':>7} {'max':>7} {'p95':>7}")
    print("-" * 68)
    flash_total = 0.0
    work = 0.0
    for label, _, _ in PHASES:
        s = summary[label]
        if not s:
            print(f"{label:24} {'--':>3} {'(no data)':>7}")
            continue
        print(f"{label:24} {s['n']:>3} {fmt(s['mean'])} {fmt(s['median'])} "
              f"{fmt(s['min'])} {fmt(s['max'])} {fmt(s['p95'])}")
        if "flash" in label:
            flash_total += s["mean"]
        if "work" in label:
            work = s["mean"]

    # bottleneck + batching-win sizing
    means = {label: summary[label]["mean"] for label, _, _ in PHASES if summary[label]}
    if means:
        bott = max(means, key=means.get)
        print(f"\nBOTTLENECK: '{bott}' (mean {fmt(means[bott]).strip()}) dominates the iteration.")
    if flash_total and work:
        per_target_now = flash_total + work
        for n in (5, 10):
            batched = (flash_total + n * work) / n
            print(f"  flash overhead ~{flash_total:.0f}s vs work ~{work:.0f}s → "
                  f"batch {n}/boot ≈ {batched:.0f}s/target "
                  f"({per_target_now / batched:.1f}x vs {per_target_now:.0f}s now)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
