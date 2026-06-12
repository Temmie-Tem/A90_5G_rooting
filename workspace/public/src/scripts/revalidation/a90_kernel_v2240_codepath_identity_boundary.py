#!/usr/bin/env python3
"""V2240 code-path identity boundary audit.

This host-only audit prevents a common interpretation error after V2239: kernel
exact-slide symbolization applies to kernel addresses, not to helper-owned a90*
trace_uprobe __probe_ip values. The a90* values are user-space PC values from
cnss-daemon, pm-service, and libqmi mappings; their stable identity is the event
name plus intra-binary relative offset signature.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter, defaultdict
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
DEFAULT_EXACT_SLIDE = PRIVATE_RUNS / "v2217-exact-slide-resymbolization-audit/result.json"
DEFAULT_V2239 = PRIVATE_RUNS / "v2239-scalar-uprobe-timeline-20260612-105944/summary.json"

ADDRESS_RE = re.compile(r"\((0x[0-9a-fA-F]+)\)")
A90_GROUPS = {"a90cnss", "a90libqmi", "a90pmsrv"}
A90CNSS_ANCHOR = "wlfw_start"
KEY_A90CNSS_EVENTS = [
    "wlfw_start",
    "wlfw_service_request",
    "wlfw_cap_qmi",
    "wlfw_bdf_entry",
    "wlfw_bdf_send_ret",
    "wlfw_bdf_result_log",
    "wlfw_worker_done_signal",
    "wlfw_worker_post_done_wait",
]


@dataclass(frozen=True)
class ProbeSample:
    run_id: str
    event: str
    group: str
    surface: str | None
    ts: float | None
    address: int
    address_hex: str
    domain: str
    low12_hex: str
    line: str


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
    return json.loads(path.read_text(encoding="utf-8"))


def infer_run_id(path: Path) -> str:
    for part in path.parts:
        if part.startswith("v") and "-" in part:
            return part.split("-", 1)[0]
    return path.parent.name


def classify_domain(address: int) -> str:
    if address >= 0xFFFFFF8000000000:
        return "kernel_canonical"
    if 0x0000007F00000000 <= address < 0x0000008000000000:
        return "user_shared_library"
    if 0x0000005500000000 <= address < 0x0000005700000000:
        return "user_pie_executable"
    if address < 0x0000008000000000:
        return "user_or_low_va"
    return "unknown_noncanonical"


def extract_samples(path: Path) -> list[ProbeSample]:
    data = read_json(path)
    timeline = data.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        raise ValueError(f"missing timeline in {path}")
    run_id = infer_run_id(path)
    seen: set[tuple[str, str]] = set()
    samples: list[ProbeSample] = []
    for item in timeline:
        group = str(item.get("group") or "")
        event = str(item.get("event") or "")
        if group not in A90_GROUPS or event.startswith("_surface_"):
            continue
        key = (group, event)
        if key in seen:
            continue
        seen.add(key)
        line = str(item.get("line") or "")
        match = ADDRESS_RE.search(line)
        if not match:
            continue
        address = int(match.group(1), 16)
        samples.append(
            ProbeSample(
                run_id=run_id,
                event=event,
                group=group,
                surface=item.get("surface"),
                ts=round(float(item["ts"]), 6) if item.get("ts") is not None else None,
                address=address,
                address_hex=f"0x{address:x}",
                domain=classify_domain(address),
                low12_hex=f"0x{address & 0xfff:x}",
                line=line,
            )
        )
    if not samples:
        raise ValueError(f"no a90 probe samples with addresses in {path}")
    return samples


def group_samples(samples: list[ProbeSample]) -> dict[str, list[ProbeSample]]:
    output: dict[str, list[ProbeSample]] = defaultdict(list)
    for sample in samples:
        output[sample.run_id].append(sample)
    return dict(output)


def first_sample_by_event(samples: list[ProbeSample]) -> dict[str, ProbeSample]:
    out: dict[str, ProbeSample] = {}
    for sample in samples:
        out.setdefault(sample.event, sample)
    return out


def build_a90cnss_relative_signature(samples: list[ProbeSample]) -> dict[str, Any]:
    by_run = group_samples([sample for sample in samples if sample.group == "a90cnss"])
    per_run: dict[str, dict[str, Any]] = {}
    event_deltas: dict[str, list[int]] = defaultdict(list)
    event_low12: dict[str, list[str]] = defaultdict(list)
    for run_id, run_samples in sorted(by_run.items()):
        by_event = first_sample_by_event(run_samples)
        anchor = by_event.get(A90CNSS_ANCHOR)
        if anchor is None:
            per_run[run_id] = {"anchor_present": False, "events": {}}
            continue
        events: dict[str, dict[str, Any]] = {}
        for event in KEY_A90CNSS_EVENTS:
            sample = by_event.get(event)
            if sample is None:
                continue
            delta = sample.address - anchor.address
            events[event] = {
                "address": sample.address_hex,
                "delta_from_wlfw_start": delta,
                "delta_from_wlfw_start_hex": hex(delta),
                "low12": sample.low12_hex,
            }
            event_deltas[event].append(delta)
            event_low12[event].append(sample.low12_hex)
        per_run[run_id] = {
            "anchor_present": True,
            "anchor_address": anchor.address_hex,
            "events": events,
        }
    stability: dict[str, dict[str, Any]] = {}
    for event in KEY_A90CNSS_EVENTS:
        deltas = event_deltas.get(event, [])
        low12_values = event_low12.get(event, [])
        stability[event] = {
            "observed_runs": len(deltas),
            "stable_delta": len(set(deltas)) == 1 and bool(deltas),
            "delta_hex": hex(deltas[0]) if deltas and len(set(deltas)) == 1 else None,
            "stable_low12": len(set(low12_values)) == 1 and bool(low12_values),
            "low12": low12_values[0] if low12_values and len(set(low12_values)) == 1 else None,
        }
    return {"per_run": per_run, "stability": stability}


def summarize_low12_by_event(samples: list[ProbeSample]) -> dict[str, dict[str, Any]]:
    grouped: dict[tuple[str, str], list[ProbeSample]] = defaultdict(list)
    for sample in samples:
        grouped[(sample.group, sample.event)].append(sample)
    out: dict[str, dict[str, Any]] = {}
    for (group, event), event_samples in sorted(grouped.items()):
        values = [sample.low12_hex for sample in event_samples]
        domains = sorted({sample.domain for sample in event_samples})
        out[f"{group}:{event}"] = {
            "observed_runs": len({sample.run_id for sample in event_samples}),
            "stable_low12": len(set(values)) == 1,
            "low12": values[0] if values and len(set(values)) == 1 else None,
            "domains": domains,
        }
    return out


def plain_sample(sample: ProbeSample) -> dict[str, Any]:
    data = asdict(sample)
    data.pop("line", None)
    return data


def build_summary(parser_paths: list[Path], exact_slide_path: Path, v2239_path: Path, out_dir: Path, label: str) -> dict[str, Any]:
    exact = read_json(exact_slide_path)
    v2239 = read_json(v2239_path)
    samples: list[ProbeSample] = []
    for path in parser_paths:
        samples.extend(extract_samples(path))
    domain_counts = Counter(sample.domain for sample in samples)
    group_counts = Counter(sample.group for sample in samples)
    kernel_samples = [sample for sample in samples if sample.domain == "kernel_canonical"]
    a90cnss_signature = build_a90cnss_relative_signature(samples)
    stable_cnss_events = [
        event for event, row in a90cnss_signature["stability"].items()
        if row["observed_runs"] == len(parser_paths) and row["stable_delta"] and row["stable_low12"]
    ]
    decision = "v2240-codepath-identity-boundary-pass"
    if kernel_samples:
        decision = "v2240-codepath-identity-boundary-unexpected-kernel-a90-probe-ip"
    return {
        "label": label,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "decision": decision,
        "pass": decision.endswith("-pass"),
        "out_dir": rel(out_dir),
        "safety": {
            "host_only": True,
            "device_io": False,
            "bpf_attach": False,
            "tracefs_control_write": False,
            "probe_write_user_executed": False,
            "wifi_scan_connect": False,
            "network_route_change": False,
            "flash_reboot": False,
            "partition_write": False,
            "private_raw_log_copied_to_public": False,
        },
        "inputs": {
            "parser_summaries": [rel(path) for path in parser_paths],
            "exact_slide_result": rel(exact_slide_path),
            "v2239_contract": rel(v2239_path),
        },
        "kernel_exact_slide": {
            "available": bool(exact.get("exact_slide_hex")),
            "slide_hex": exact.get("exact_slide_hex"),
            "source_decision": exact.get("decision"),
            "applies_to": [
                "kernel canonical PC/LR samples",
                "kernel function-pointer anchors",
                "stock kernel addresses from BPF/perf read paths",
            ],
            "does_not_apply_to": [
                "a90cnss/a90libqmi/a90pmsrv user-space trace_uprobe __probe_ip values",
                "scalar-only static tracepoint records",
            ],
        },
        "v2239_contract_decision": v2239.get("decision"),
        "a90_probe_ip_domain_counts": dict(sorted(domain_counts.items())),
        "a90_probe_group_counts": dict(sorted(group_counts.items())),
        "a90_probe_samples_total": len(samples),
        "a90_kernel_canonical_probe_ips": [plain_sample(sample) for sample in kernel_samples],
        "a90cnss_relative_signature": a90cnss_signature,
        "stable_a90cnss_signature_events": stable_cnss_events,
        "a90_event_low12_summary": summarize_low12_by_event(samples),
        "identity_contract": {
            "kernel_side": "Use V2216/V2217 exact slide only for kernel canonical addresses and kernel function pointers.",
            "a90_user_uprobe_side": "Use event names plus stable intra-binary relative offset signatures; do not subtract the kernel KASLR slide from user-space __probe_ip values.",
            "static_tracepoint_side": "Use scalar fields for lifecycle correlation; V2238 found no raw object-pointer anchor in these records.",
            "future_symbolization_gap": "If finer a90 user-space names are required, build a user-ELF ASLR/base mapper for cnss-daemon, pm-service, and libqmi, not a kernel System.map mapper.",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="v2240-codepath-identity-boundary")
    parser.add_argument("--parser-summary", action="append", type=Path, dest="parser_summaries")
    parser.add_argument("--exact-slide", type=Path, default=DEFAULT_EXACT_SLIDE)
    parser.add_argument("--v2239", type=Path, default=DEFAULT_V2239)
    parser.add_argument("--out-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parser_paths = args.parser_summaries or DEFAULT_PARSER_SUMMARIES
    out_dir = args.out_dir or PRIVATE_RUNS / f"{args.label}-{now_label()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary(parser_paths, args.exact_slide, args.v2239, out_dir, args.label)
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": summary["decision"],
        "pass": summary["pass"],
        "out_dir": rel(out_dir),
        "summary": rel(summary_path),
        "kernel_exact_slide": summary["kernel_exact_slide"]["slide_hex"],
        "a90_probe_ip_domain_counts": summary["a90_probe_ip_domain_counts"],
        "stable_a90cnss_signature_events": summary["stable_a90cnss_signature_events"],
    }, indent=2, sort_keys=True))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
