#!/usr/bin/env python3
"""V2245 post-FWREADY tail inventory.

Host-only postprocessor for the V2229/V2231/V2233 helper results. V2244
closed the WLFW/QMI semantic-order loop; this script inventories the downstream
post-FWREADY boot_wlan/firmware_class/qcacld-HDD tail that distinguishes the
V2233 wlan0 success from the earlier no-wlan0 runs.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from a90_kernel_v2241_user_uprobe_offset_base_map import PRIVATE_RUNS, rel

DEFAULT_RUNS = [
    PRIVATE_RUNS / "v2229-live-20260612-080114",
    PRIVATE_RUNS / "v2231-live-20260612-081302",
    PRIVATE_RUNS / "v2233-live-20260612-083738",
]
DEFAULT_V2244_SUMMARY = PRIVATE_RUNS / "v2244-semantic-timeline-merge-20260612-113706/summary.json"

TAIL_PREFIXES = (
    "post_fw_ready_boot_wlan_trigger.",
    "firmware_class_fallback_sampler.after_boot_wlan_trigger.",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_trigger.",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.",
    "icnss_register_probe_stack_sampler.after_boot_wlan_trigger.",
    "icnss_register_probe_stack_sampler.after_boot_wlan_long_window.",
)

TAIL_KEYS = [
    "post_fw_ready_boot_wlan_trigger.begin",
    "post_fw_ready_boot_wlan_trigger.allowed",
    "post_fw_ready_boot_wlan_trigger.active_driver_start",
    "post_fw_ready_boot_wlan_trigger.pre.fw_ready_processed",
    "post_fw_ready_boot_wlan_trigger.final.fw_ready_processed",
    "post_fw_ready_boot_wlan_trigger.final.register_driver_posted",
    "post_fw_ready_boot_wlan_trigger.final.register_driver_processed",
    "post_fw_ready_boot_wlan_trigger.path.exists",
    "post_fw_ready_boot_wlan_trigger.path.writable",
    "post_fw_ready_boot_wlan_trigger.gate_ready",
    "post_fw_ready_boot_wlan_trigger.executed",
    "post_fw_ready_boot_wlan_trigger.write_rc",
    "post_fw_ready_boot_wlan_trigger.wait_elapsed_ms",
    "post_fw_ready_boot_wlan_trigger.reason",
    "firmware_class_fallback_sampler.after_boot_wlan_trigger.request_0.dir",
    "firmware_class_fallback_sampler.after_boot_wlan_trigger.request_0.uevent_preview",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_count",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.seen_count",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.fed_count",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.timed_out",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.firmware",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.source_bytes",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.fed",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.data_rc",
    "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.loading_done_rc",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_trigger.icnss_stats.event.fw_ready.processed",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_trigger.icnss_stats.event.register_driver.posted",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_trigger.icnss_stats.event.register_driver.processed",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_trigger.icnss_stats.state.hex",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_trigger.icnss_stats.state.line",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.event.fw_ready.processed",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.event.register_driver.posted",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.event.register_driver.processed",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.cfg_req",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.cfg_resp",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.mode_req",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.mode_resp",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.ini_req",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.ini_resp",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.state.hex",
    "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.state.line",
    "icnss_register_probe_stack_sampler.after_boot_wlan_trigger.target_hits",
    "icnss_register_probe_stack_sampler.after_boot_wlan_long_window.target_hits",
]

STACK_LINE_RE = re.compile(r"^(?P<prefix>icnss_register_probe_stack_sampler\.after_boot_wlan_trigger\.sample_\d+)\.stack_\d+=(?P<value>.+)$")
TARGET_RE = re.compile(r"^(?P<prefix>icnss_register_probe_stack_sampler\.after_boot_wlan_trigger\.sample_\d+)\.target=1$")
META_RE = re.compile(r"^(?P<prefix>icnss_register_probe_stack_sampler\.after_boot_wlan_trigger\.sample_\d+)\.(?P<key>comm|wchan)=(?P<value>.*)$")


def now_label() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def read_text_lossy(path: Path) -> str:
    return path.read_bytes().replace(b"\0", b"\n").decode("utf-8", errors="replace")


def read_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in read_text_lossy(path).splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key:
            values[key] = value
    return values


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def as_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def value_is_one(values: dict[str, str], key: str) -> bool:
    return values.get(key) == "1"


def infer_run_id(run_dir: Path) -> str:
    name = run_dir.name
    if name.startswith("v") and "-" in name:
        return name.split("-", 1)[0]
    return name


def count_tail_keys(helper_values: dict[str, str]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for key in helper_values:
        for prefix in TAIL_PREFIXES:
            if key.startswith(prefix):
                counts[prefix.rstrip(".")] += 1
                break
    return dict(sorted(counts.items()))


def collect_target_stacks(helper_path: Path) -> list[dict[str, Any]]:
    if not helper_path.exists():
        return []
    targets: set[str] = set()
    meta: dict[str, dict[str, str]] = {}
    stacks: dict[str, list[str]] = {}
    for line in read_text_lossy(helper_path).splitlines():
        target = TARGET_RE.match(line)
        if target:
            targets.add(target.group("prefix"))
            continue
        meta_match = META_RE.match(line)
        if meta_match:
            prefix = meta_match.group("prefix")
            meta.setdefault(prefix, {})[meta_match.group("key")] = meta_match.group("value")
            continue
        stack_match = STACK_LINE_RE.match(line)
        if stack_match:
            stacks.setdefault(stack_match.group("prefix"), []).append(stack_match.group("value"))
    rows = []
    for prefix in sorted(targets):
        frame_values = stacks.get(prefix, [])
        rows.append({
            "sample": prefix.rsplit(".", 1)[-1],
            "comm": meta.get(prefix, {}).get("comm"),
            "wchan": meta.get(prefix, {}).get("wchan"),
            "stack_depth": len(frame_values),
            "stack_functions": frame_values[:12],
        })
    return rows


def classify_stage(helper_values: dict[str, str], summary_values: dict[str, str]) -> str:
    if not value_is_one(helper_values, "post_fw_ready_boot_wlan_trigger.begin"):
        return "tail_absent"
    if not value_is_one(helper_values, "post_fw_ready_boot_wlan_trigger.executed"):
        return "boot_wlan_not_executed"
    if helper_values.get("post_fw_ready_boot_wlan_trigger.write_rc") not in {"0", None}:
        return "boot_wlan_write_failed"
    fed_count = as_int(helper_values.get("qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.fed_count")) or 0
    if fed_count <= 0:
        return "boot_wlan_executed_no_fwclass_feed"
    long_register_processed = value_is_one(helper_values, "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.event.register_driver.processed")
    cfg_ok = value_is_one(helper_values, "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.cfg_req") and value_is_one(helper_values, "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.cfg_resp")
    mode_ok = (as_int(helper_values.get("wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.mode_req")) or 0) >= 1 and (as_int(helper_values.get("wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.mode_resp")) or 0) >= 1
    ini_ok = value_is_one(helper_values, "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.ini_req") and value_is_one(helper_values, "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.ini_resp")
    wlan0_ready = summary_values.get("wlan0_present") == "1"
    if long_register_processed and cfg_ok and mode_ok and ini_ok and wlan0_ready:
        return "tail_complete_wlan0_ready"
    if long_register_processed:
        return "driver_probe_tail_partial"
    return "fwclass_fed_no_driver_probe"


def summarize_run(run_dir: Path) -> dict[str, Any]:
    run_id = infer_run_id(run_dir)
    helper_path = run_dir / "device/helper_result.txt"
    summary_path = run_dir / "device/summary.txt"
    helper_values = read_key_values(helper_path)
    summary_values = read_key_values(summary_path)
    selected = {key: helper_values[key] for key in TAIL_KEYS if key in helper_values}
    target_stacks = collect_target_stacks(helper_path)
    return {
        "run_id": run_id,
        "run_dir": rel(run_dir),
        "helper_result_present": helper_path.exists(),
        "summary_present": summary_path.exists(),
        "helper_result_bytes": helper_path.stat().st_size if helper_path.exists() else 0,
        "summary": {
            "wlan0_present": summary_values.get("wlan0_present"),
            "supervisor_result": summary_values.get("supervisor_result"),
            "supervisor_timeout_sec": summary_values.get("supervisor_timeout_sec"),
        },
        "tail_stage": classify_stage(helper_values, summary_values),
        "tail_key_counts": count_tail_keys(helper_values),
        "signals": selected,
        "target_stack_samples": target_stacks,
        "target_stack_sample_count": len(target_stacks),
    }


def compare_runs(runs: dict[str, dict[str, Any]], v2244: dict[str, Any]) -> dict[str, Any]:
    stages = {run_id: run["tail_stage"] for run_id, run in runs.items()}
    successes = [run_id for run_id, run in runs.items() if run["tail_stage"] == "tail_complete_wlan0_ready"]
    no_tail = [run_id for run_id, run in runs.items() if run["tail_stage"] == "tail_absent"]
    wl_fw_qmi_identical = bool((v2244.get("comparison") or {}).get("edge_sets_identical_across_runs"))
    semantic_signatures_identical = bool((v2244.get("comparison") or {}).get("semantic_signatures_identical_across_runs"))
    diff_is_tail = bool(successes and no_tail and wl_fw_qmi_identical and semantic_signatures_identical)
    return {
        "tail_stages": stages,
        "tail_complete_runs": successes,
        "tail_absent_runs": no_tail,
        "v2244_wlfw_qmi_edge_sets_identical": wl_fw_qmi_identical,
        "v2244_semantic_signatures_identical": semantic_signatures_identical,
        "post_fwready_tail_explains_success_delta": diff_is_tail,
    }


def build_summary(args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    v2244 = read_json(args.v2244_summary)
    runs = {infer_run_id(path): summarize_run(path) for path in args.run_dir}
    comparison = compare_runs(runs, v2244)
    inventory_path = out_dir / "post_fwready_tail_inventory.json"
    inventory_path.write_text(json.dumps({
        "warning": "Public-safe derived inventory. Raw helper_result content remains under workspace/private.",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "runs": runs,
        "comparison": comparison,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    decision = "v2245-post-fwready-tail-inventory-pass"
    if not comparison["post_fwready_tail_explains_success_delta"]:
        decision = "v2245-post-fwready-tail-inventory-review-needed"
    return {
        "label": args.label,
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
            "run_dirs": [rel(path) for path in args.run_dir],
            "v2244_summary": rel(args.v2244_summary),
        },
        "run_count": len(runs),
        "tail_stage_counts": dict(sorted(Counter(run["tail_stage"] for run in runs.values()).items())),
        "runs": {
            run_id: {
                "summary": run["summary"],
                "tail_stage": run["tail_stage"],
                "tail_key_counts": run["tail_key_counts"],
                "target_stack_sample_count": run["target_stack_sample_count"],
                "key_signals": {
                    key: value
                    for key, value in run["signals"].items()
                    if key in {
                        "post_fw_ready_boot_wlan_trigger.executed",
                        "post_fw_ready_boot_wlan_trigger.write_rc",
                        "post_fw_ready_boot_wlan_trigger.reason",
                        "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.firmware",
                        "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.fed",
                        "qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.source_bytes",
                        "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.event.register_driver.processed",
                        "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.cfg_req",
                        "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.cfg_resp",
                        "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.mode_req",
                        "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.mode_resp",
                        "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.ini_req",
                        "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.ini_resp",
                        "wlan_pd_icnss_ipc_snapshot.after_boot_wlan_long_window.icnss_stats.state.hex",
                    }
                },
                "target_stack_samples": run["target_stack_samples"],
            }
            for run_id, run in runs.items()
        },
        "comparison": comparison,
        "inventory": {
            "path": rel(inventory_path),
            "raw_helper_result_published": False,
        },
        "interpretation": {
            "result": "V2229/V2231 lack the post-FWREADY tail instrumentation, while V2233 executes boot_wlan, feeds the WCNSS_qcom_cfg.ini firmware_class fallback, observes the qcacld probe stack, and reaches ICNSS register/cfg/mode/ini completion plus wlan0.",
            "not_the_next_target": "Do not re-run WLFW/QMI semantic-order captures; V2244 already showed the edge sets are identical across no-wlan0 and wlan0 runs.",
            "next_if_live_needed": "Attach exact-slide kernel PC/LR or tracepoint sampling to the post-FWREADY firmware_class/qcacld probe tail around boot_wlan, not to PerMgr/WLFW order.",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="v2245-post-fwready-tail-inventory")
    parser.add_argument("--run-dir", type=Path, action="append")
    parser.add_argument("--v2244-summary", type=Path, default=DEFAULT_V2244_SUMMARY)
    parser.add_argument("--out-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.run_dir is None:
        args.run_dir = list(DEFAULT_RUNS)
    out_dir = args.out_dir or PRIVATE_RUNS / f"{args.label}-{now_label()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary(args, out_dir)
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": summary["decision"],
        "pass": summary["pass"],
        "out_dir": summary["out_dir"],
        "summary": rel(summary_path),
        "run_count": summary["run_count"],
        "tail_stage_counts": summary["tail_stage_counts"],
        "post_fwready_tail_explains_success_delta": summary["comparison"]["post_fwready_tail_explains_success_delta"],
    }, indent=2, sort_keys=True))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
