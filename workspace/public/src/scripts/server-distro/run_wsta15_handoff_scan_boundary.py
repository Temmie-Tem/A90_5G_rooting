#!/usr/bin/env python3
"""Run the WSTA15 native handoff / WLAN scan boundary diagnostic.

This diagnostic stays below association.  It compares a STA-only native
``wifi scan`` window with a second scan window after the already-bounded WSTA2
AP-iftype add/delete probe.  The result answers whether the AP-iftype probe
poisons native scan state before chasing Debian handoff reset logic.

The runner assumes a resident V3384 native-init and never flashes.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_wsta2_native_materialization as wsta2  # noqa: E402


REPO_ROOT = wsta2.REPO_ROOT
DEFAULT_RUN_BASE = wsta2.DEFAULT_RUN_BASE
SCAN_ENGINE_OK_DECISIONS = {"wifi-scan-pass", "wifi-scan-zero-bss"}


def parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def scan_summary(record: dict[str, Any]) -> dict[str, Any]:
    text = str(record.get("text", ""))
    kv = wsta2.parse_kv(text)
    decision = kv.get("decision", "")
    count = parse_int(kv.get("scan_result_count"))
    return {
        "transport_ok": bool(record.get("transport_ok", True)),
        "cmd_status": record.get("status"),
        "cmd_rc": record.get("rc"),
        "decision": decision,
        "scan_result_count": count,
        "scan_engine_ok": decision in SCAN_ENGINE_OK_DECISIONS,
        "scan_has_bss": bool(count is not None and count > 0),
        "link_up_rc": parse_int(kv.get("link_up_rc")),
        "link_up_errno": parse_int(kv.get("link_up_errno")),
        "ifindex": parse_int(kv.get("ifindex")),
        "netlink_open": parse_int(kv.get("netlink_open")),
        "family_id": parse_int(kv.get("family_id")),
        "trigger_rc": parse_int(kv.get("trigger_rc")),
        "trigger_errno": parse_int(kv.get("trigger_errno")),
        "errno": parse_int(kv.get("errno")),
    }


def scan_score(summary: dict[str, Any]) -> int:
    if summary.get("scan_has_bss"):
        return 4
    if summary.get("scan_engine_ok"):
        return 3
    if summary.get("transport_ok"):
        return 1
    return 0


def best_scan(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {}
    return max((record["scan_summary"] for record in records), key=scan_score)


def run_scan_attempt(args: argparse.Namespace, label: str, attempt: int) -> dict[str, Any]:
    timeout = max(args.timeout, (args.scan_delay_ms / 1000.0) + args.scan_slack_sec)
    record = wsta2.try_cmdv1(
        args,
        ["wifi", "scan", str(args.scan_delay_ms)],
        timeout=timeout,
    )
    record["label"] = label
    record["attempt"] = attempt
    record["scan_summary"] = scan_summary(record)
    return record


def try_cmdv1_retry(args: argparse.Namespace,
                    command: list[str],
                    *,
                    timeout: float | None = None,
                    attempts: int = 2) -> dict[str, Any]:
    last: dict[str, Any] = {}
    for attempt in range(1, max(1, attempts) + 1):
        record = wsta2.try_cmdv1(args, command, timeout=timeout)
        record["attempt"] = attempt
        if record.get("transport_ok"):
            return record
        last = record
        if attempt < attempts:
            time.sleep(1.0)
    return last


def run_scan_window(args: argparse.Namespace,
                    result: dict[str, Any],
                    out_path: Path,
                    label: str,
                    attempts: int) -> dict[str, Any]:
    window: dict[str, Any] = {
        "label": label,
        "scan_delay_ms": args.scan_delay_ms,
        "attempts_requested": attempts,
        "attempt_interval_sec": args.scan_interval_sec,
        "attempts": [],
    }
    result[label] = window
    wsta2.write_json(out_path, result)

    for attempt in range(1, attempts + 1):
        record = run_scan_attempt(args, label, attempt)
        window["attempts"].append(record)
        window["best"] = best_scan(window["attempts"])
        wsta2.write_json(out_path, result)
        if record["scan_summary"]["scan_engine_ok"]:
            break
        if attempt < attempts:
            time.sleep(args.scan_interval_sec)

    window["attempts_completed"] = len(window["attempts"])
    window["best"] = best_scan(window["attempts"])
    wsta2.write_json(out_path, result)
    return window


def classify_boundary(result: dict[str, Any]) -> str:
    checks = result.get("checks", {})
    if not checks.get("native_v3384"):
        return "wsta15-blocked-v3384-not-resident"
    if not checks.get("selftest_fail_zero") or not checks.get("hardware_contract_ok"):
        return "wsta15-blocked-native-health"
    if not checks.get("process_table_ok"):
        return "wsta15-blocked-native-process-table"
    if checks.get("forbidden_native_workers"):
        return "wsta15-blocked-forbidden-native-worker"

    pre = result.get("pre_sta_only_scan_window", {}).get("best", {})
    post = result.get("post_iftype_scan_window", {}).get("best", {})
    pre_ok = bool(pre.get("scan_engine_ok"))
    post_ok = bool(post.get("scan_engine_ok"))

    if not result.get("iftype_probe_requested"):
        if pre_ok:
            return "wsta15-native-sta-only-scan-engine-ok"
        return "wsta15-native-sta-only-scan-engine-blocked"
    if pre_ok and post_ok:
        return "wsta15-native-scan-engine-survives-iftype"
    if pre_ok and not post_ok:
        return "wsta15-native-post-iftype-scan-regressed"
    if not pre_ok and post_ok:
        return "wsta15-native-sta-only-scan-blocked-iftype-recovers"
    return "wsta15-native-scan-engine-blocked"


def run_gate(args: argparse.Namespace, result: dict[str, Any], out_path: Path) -> dict[str, Any]:
    result["bridge_status"] = wsta2.run_host([sys.executable, str(wsta2.BRIDGE), "status", "--json"], timeout=10.0)
    wsta2.write_json(out_path, result)

    version = try_cmdv1_retry(args, ["version"], timeout=args.timeout)
    result["version"] = version
    wsta2.write_json(out_path, result)
    if not version.get("transport_ok"):
        result["decision"] = "wsta15-blocked-native-cmdv1-unavailable"
        wsta2.write_json(out_path, result)
        return result

    status = try_cmdv1_retry(args, ["status"], timeout=args.timeout)
    selftest = try_cmdv1_retry(args, ["selftest"], timeout=args.timeout)
    contract = try_cmdv1_retry(args, ["server-distro", "hardware-contract"], timeout=args.timeout)
    wifi_status_pre = try_cmdv1_retry(args, ["wifi", "status"], timeout=args.timeout)
    result.update({
        "status": status,
        "selftest": selftest,
        "hardware_contract": contract,
        "wifi_status_pre": wifi_status_pre,
    })
    wsta2.write_json(out_path, result)

    run_scan_window(args, result, out_path, "pre_sta_only_scan_window", args.sta_scan_attempts)

    if args.run_iftype_probe:
        probe_timeout = max(args.timeout, (args.probe_timeout_ms / 1000.0) + 30.0)
        result["iftype_probe"] = wsta2.try_cmdv1(
            args,
            ["wifi", "softap", "iftype-probe", str(args.probe_timeout_ms)],
            timeout=probe_timeout,
        )
        result["wifi_status_after_iftype"] = try_cmdv1_retry(
            args,
            ["wifi", "status"],
            timeout=args.timeout,
        )
        wsta2.write_json(out_path, result)
        run_scan_window(args, result, out_path, "post_iftype_scan_window", args.post_iftype_scan_attempts)

    ps = try_cmdv1_retry(args, ["run", "/bin/busybox", "sh", "-c", wsta2.PS_SCRIPT], timeout=args.timeout)
    result["process_table"] = ps
    result["checks"] = {
        "native_v3384": wsta2.native_is_v3384(version.get("text", "")),
        "selftest_fail_zero": wsta2.selftest_passed(selftest.get("text", "")),
        "hardware_contract_ok": wsta2.contract_passed(contract.get("text", "")),
        "process_table_ok": bool(ps.get("transport_ok") and "A90WSTA2_PS_END" in ps.get("text", "")),
        "forbidden_native_workers": wsta2.forbidden_workers(ps.get("text", "")),
        "pre_scan_engine_ok": bool(result.get("pre_sta_only_scan_window", {}).get("best", {}).get("scan_engine_ok")),
        "pre_scan_has_bss": bool(result.get("pre_sta_only_scan_window", {}).get("best", {}).get("scan_has_bss")),
        "post_scan_engine_ok": bool(result.get("post_iftype_scan_window", {}).get("best", {}).get("scan_engine_ok")),
        "post_scan_has_bss": bool(result.get("post_iftype_scan_window", {}).get("best", {}).get("scan_has_bss")),
    }
    result["decision"] = classify_boundary(result)
    wsta2.write_json(out_path, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--scan-delay-ms", type=int, default=5000)
    parser.add_argument("--scan-slack-sec", type=float, default=20.0)
    parser.add_argument("--scan-interval-sec", type=float, default=10.0)
    parser.add_argument("--sta-scan-attempts", type=int, default=6)
    parser.add_argument("--post-iftype-scan-attempts", type=int, default=3)
    parser.add_argument("--probe-timeout-ms", type=int, default=220000)
    parser.add_argument("--skip-iftype-probe", dest="run_iftype_probe", action="store_false")
    parser.set_defaults(run_iftype_probe=True)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.run_dir or (DEFAULT_RUN_BASE / f"wsta15-handoff-scan-boundary-{ts}")
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = run_dir / "wsta15_result.json"
    result: dict[str, Any] = {
        "scope": "WSTA15 native handoff / WLAN scan boundary",
        "started_utc": ts,
        "run_dir": wsta2.rel(run_dir),
        "flash_requested": False,
        "iftype_probe_requested": bool(args.run_iftype_probe),
        "resident_required": {
            "version": wsta2.V3384_VERSION,
            "build": wsta2.V3384_BUILD,
        },
        "safety": {
            "boot_flash": False,
            "no_wifi_association": True,
            "no_dhcp": True,
            "no_ping": True,
            "no_public_tunnel": True,
            "no_forbidden_partition_write": True,
        },
    }
    try:
        result = run_gate(args, result, out_path)
    except Exception as exc:  # noqa: BLE001 - record partial state for handoff.
        result["decision"] = "wsta15-runner-error"
        result["error"] = str(exc)
        wsta2.write_json(out_path, result)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if str(result.get("decision", "")).startswith("wsta15-native-") else 2


if __name__ == "__main__":
    raise SystemExit(main())
