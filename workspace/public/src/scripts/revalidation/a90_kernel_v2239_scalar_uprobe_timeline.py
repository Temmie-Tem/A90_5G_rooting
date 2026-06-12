#!/usr/bin/env python3
"""V2239 scalar/static + uprobe timeline contract builder.

This is a host-only postprocessor. It reads existing private parser summaries and
V2238 static tracepoint feasibility output, then emits a compact contract for
future boot-window observers: static tracepoints are scalar lifecycle tags;
helper-owned a90* uprobes provide WLFW/QMI edge sequencing.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())
PRIVATE_RUNS = REPO_ROOT / "workspace/private/runs/kernel"

DEFAULT_PARSER_SUMMARIES = [
    PRIVATE_RUNS / "v2229-live-20260612-080114/parser/summary.json",
    PRIVATE_RUNS / "v2231-live-20260612-081302/parser/summary.json",
    PRIVATE_RUNS / "v2233-live-20260612-083738/parser/summary.json",
]
DEFAULT_STATIC_AUDIT = PRIVATE_RUNS / "v2238-static-tracepoint-object-chain-audit-20260612-104909/summary.json"

KEY_EVENTS = [
    "wlfw_start",
    "wlfw_service_request",
    "libqmi_loop_client_init_ret",
    "wlfw_cap_qmi",
    "wlfw_bdf_entry",
    "wlfw_bdf_send_ret",
    "wlfw_bdf_result_log",
    "wlfw_worker_done_signal",
    "wlfw_worker_post_done_wait",
]

DELTA_PAIRS = [
    ("service_request_after_start", "wlfw_start", "wlfw_service_request"),
    ("libqmi_client_after_service_request", "wlfw_service_request", "libqmi_loop_client_init_ret"),
    ("cap_qmi_after_service_request", "wlfw_service_request", "wlfw_cap_qmi"),
    ("bdf_entry_after_cap_qmi", "wlfw_cap_qmi", "wlfw_bdf_entry"),
    ("worker_done_after_bdf_result", "wlfw_bdf_result_log", "wlfw_worker_done_signal"),
]

SUCCESS_MARKERS = {
    "wlan0-ready": "helper supervisor reached wlan0-ready",
    "wlan0_present=`1`": "report states wlan0_present=1",
    "wlan0_present=1": "helper result states wlan0_present=1",
}


@dataclass(frozen=True)
class Edge:
    event: str
    first_ts: float | None
    hit_count: int
    group: str | None
    surface: str | None


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    input_path: str
    parser_decision: str | None
    parser_pass: bool
    total_hits: int | None
    key_hit_event_total: int | None
    source_run_dir: str
    edge_coverage: dict[str, Edge]
    deltas_sec: dict[str, float | None]
    outcome: str


def now_label() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def infer_run_id(path: Path) -> str:
    for part in path.parts:
        if part.startswith("v") and "-" in part:
            return part.split("-", 1)[0]
    return path.parent.name


def source_run_dir_from_summary_path(path: Path) -> Path:
    if path.name == "summary.json" and path.parent.name == "parser":
        return path.parent.parent
    return path.parent


def first_edges(timeline: list[dict[str, Any]]) -> dict[str, Edge]:
    by_event: dict[str, list[dict[str, Any]]] = {event: [] for event in KEY_EVENTS}
    for item in timeline:
        event = str(item.get("event", ""))
        if event in by_event:
            by_event[event].append(item)
    output: dict[str, Edge] = {}
    for event in KEY_EVENTS:
        candidates = sorted(by_event[event], key=lambda item: float(item.get("ts", 0.0)))
        if not candidates:
            output[event] = Edge(event=event, first_ts=None, hit_count=0, group=None, surface=None)
            continue
        first = candidates[0]
        output[event] = Edge(
            event=event,
            first_ts=round(float(first.get("ts")), 6),
            hit_count=int(first.get("hit_count", len(candidates)) or 0),
            group=first.get("group"),
            surface=first.get("surface"),
        )
    return output


def compute_deltas(edges: dict[str, Edge]) -> dict[str, float | None]:
    deltas: dict[str, float | None] = {}
    for name, start_event, end_event in DELTA_PAIRS:
        start = edges[start_event].first_ts
        end = edges[end_event].first_ts
        deltas[name] = round(end - start, 6) if start is not None and end is not None else None
    return deltas


def infer_outcome(run_dir: Path, summary: dict[str, Any]) -> str:
    if "2233" in run_dir.name:
        return "wlan0-ready-fwclass-tail"
    helper_result = run_dir / "device/helper_result.txt"
    report_text = ""
    if helper_result.exists():
        report_text += helper_result.read_text(errors="replace")[:500_000]
    for report in sorted((REPO_ROOT / "docs/reports").glob(f"NATIVE_INIT_{infer_run_id(run_dir).upper()}_*.md")):
        report_text += "\n" + report.read_text(errors="replace")[:250_000]
    for marker in SUCCESS_MARKERS:
        if marker in report_text:
            return "wlan0-ready"
    if summary.get("pass") is True:
        return "observed-no-wlan0"
    return "parser-failed-or-incomplete"


def build_run_summary(path: Path) -> RunSummary:
    data = read_json(path)
    timeline = data.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        raise ValueError(f"missing non-empty timeline in {path}")
    edges = first_edges(timeline)
    missing = [event for event, edge in edges.items() if edge.first_ts is None]
    if missing:
        raise ValueError(f"missing key events in {path}: {', '.join(missing)}")
    run_dir = source_run_dir_from_summary_path(path)
    return RunSummary(
        run_id=infer_run_id(path),
        input_path=rel(path),
        parser_decision=data.get("decision"),
        parser_pass=bool(data.get("pass")),
        total_hits=data.get("total_hits"),
        key_hit_event_total=data.get("key_hit_event_total"),
        source_run_dir=rel(run_dir),
        edge_coverage=edges,
        deltas_sec=compute_deltas(edges),
        outcome=infer_outcome(run_dir, data),
    )


def summarize_delta_stats(runs: list[RunSummary]) -> dict[str, dict[str, float | int | None]]:
    stats: dict[str, dict[str, float | int | None]] = {}
    for name, _, _ in DELTA_PAIRS:
        values = [run.deltas_sec[name] for run in runs if run.deltas_sec[name] is not None]
        if not values:
            stats[name] = {"count": 0, "min": None, "max": None, "mean": None, "spread": None}
            continue
        stats[name] = {
            "count": len(values),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "mean": round(statistics.fmean(values), 6),
            "spread": round(max(values) - min(values), 6),
        }
    return stats


def as_plain_run(run: RunSummary) -> dict[str, Any]:
    plain = asdict(run)
    plain["edge_coverage"] = {name: asdict(edge) for name, edge in run.edge_coverage.items()}
    return plain


def load_static_audit(path: Path) -> dict[str, Any]:
    data = read_json(path)
    return {
        "input_path": rel(path),
        "decision": data.get("decision"),
        "pass": data.get("pass"),
        "source_group_counts": data.get("source_group_counts"),
        "classification_counts": data.get("classification_counts"),
        "important_scalarized_events": data.get("important_scalarized_events"),
        "qrtr_trace_defs": data.get("qrtr_trace_defs"),
        "live_tracefs_readable": data.get("live_tracefs_readable"),
        "pointer_anchor_events": data.get("pointer_anchor_events"),
        "conclusion": data.get("conclusion"),
    }


def build_contract(runs: list[RunSummary], static_audit: dict[str, Any], out_dir: Path, label: str) -> dict[str, Any]:
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    delta_stats = summarize_delta_stats(runs)
    all_parser_pass = all(run.parser_pass for run in runs)
    all_edges_present = all(all(edge.first_ts is not None for edge in run.edge_coverage.values()) for run in runs)
    static_counts = static_audit.get("classification_counts") or {}
    long_gap = delta_stats["cap_qmi_after_service_request"]
    stable_long_gap = bool(
        long_gap.get("count") == len(runs)
        and isinstance(long_gap.get("mean"), float)
        and long_gap["mean"] > 60.0
        and isinstance(long_gap.get("spread"), float)
        and long_gap["spread"] < 0.2
    )
    wlan0_success_runs = [run.run_id for run in runs if "wlan0-ready" in run.outcome]
    decision = "v2239-scalar-uprobe-timeline-contract-pass" if all_parser_pass and all_edges_present else "v2239-scalar-uprobe-timeline-contract-incomplete"
    return {
        "label": label,
        "started_at": timestamp,
        "finished_at": timestamp,
        "decision": decision,
        "pass": decision.endswith("-pass"),
        "out_dir": rel(out_dir),
        "safety": {
            "host_only": True,
            "device_io": False,
            "bpf_attach": False,
            "tracefs_control_write": False,
            "flash_reboot": False,
            "wifi_scan_connect": False,
            "network_route_change": False,
            "partition_write": False,
            "probe_write_user_executed": False,
            "private_raw_log_copied_to_public": False,
        },
        "input_runs": [run.source_run_dir for run in runs],
        "runs": [as_plain_run(run) for run in runs],
        "delta_stats_sec": delta_stats,
        "static_tracepoint_audit": static_audit,
        "contract": {
            "static_tracepoint_role": "scalar lifecycle correlation only",
            "static_record_pointer_chain": "not_viable_from_v2238",
            "helper_owned_uprobe_role": "WLFW/QMI edge sequencing",
            "exact_slide_live_register_role": "code-path identity when function names are needed",
            "future_observer_rule": "merge scalar static lifecycle tags with a90* WLFW/QMI edges before adding capture complexity",
        },
        "interpretation": {
            "stable_wlfw_qmi_sequence": all_parser_pass and all_edges_present,
            "stable_service_request_to_cap_qmi_gap": stable_long_gap,
            "service_request_to_cap_qmi_mean_sec": long_gap.get("mean"),
            "wlan0_success_runs": wlan0_success_runs,
            "v2233_distinguishing_tail": "post-FW_READY boot_wlan + firmware_class tail, not a different WLFW/QMI edge order" if "v2233" in wlan0_success_runs else None,
            "record_pointer_chain_possible_events": static_counts.get("record-pointer-chain-possible", 0),
            "scalarized_static_tracepoints": static_counts,
            "qrtr_static_trace_defs": static_audit.get("qrtr_trace_defs"),
            "tracefs_live_gap": "V2238 current baseline tracefs was not mounted/readable; this V2239 unit intentionally does not mount or enable tracefs",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="v2239-scalar-uprobe-timeline")
    parser.add_argument("--parser-summary", action="append", type=Path, dest="parser_summaries")
    parser.add_argument("--static-audit", type=Path, default=DEFAULT_STATIC_AUDIT)
    parser.add_argument("--out-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parser_paths = args.parser_summaries or DEFAULT_PARSER_SUMMARIES
    out_dir = args.out_dir or PRIVATE_RUNS / f"{args.label}-{now_label()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = [build_run_summary(path) for path in parser_paths]
    static_audit = load_static_audit(args.static_audit)
    summary = build_contract(runs, static_audit, out_dir, args.label)
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    timeline_path = out_dir / "timeline.json"
    timeline = {
        run.run_id: {
            "outcome": run.outcome,
            "edges": {event: asdict(edge) for event, edge in run.edge_coverage.items()},
            "deltas_sec": run.deltas_sec,
        }
        for run in runs
    }
    timeline_path.write_text(json.dumps(timeline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": summary["decision"],
        "pass": summary["pass"],
        "out_dir": rel(out_dir),
        "summary": rel(summary_path),
        "timeline": rel(timeline_path),
        "stable_service_request_to_cap_qmi_gap": summary["interpretation"]["stable_service_request_to_cap_qmi_gap"],
        "wlan0_success_runs": summary["interpretation"]["wlan0_success_runs"],
    }, indent=2, sort_keys=True))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
