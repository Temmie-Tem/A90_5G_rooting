#!/usr/bin/env python3
"""V2275 rollbackable live validation for the V2274 workqueue/codeword combined oracle.

Default mode is host-only dry-run. Live mode flashes the V2274 combined
workqueue+codeword boot image, waits for the helper-owned firmware_class feeder
window, collects both sampler logs, classifies workqueue function pointers with
the same-boot codeword slide, then rolls back to V2237 and verifies selftest
fail=0.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import (
    EvidenceStore,
    artifact_timestamp,
    read_bounded_json,
    safe_artifact_label,
    workspace_private_input_path,
    write_public_text,
)
import a90_transport as transport
import native_kernel_perf_regs_codeword_sample_ring_v2216 as codeword_v2216


REPO_ROOT = repo_root()
RUN_ROOT = REPO_ROOT / "workspace" / "private" / "runs" / "kernel"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2275_WORKQUEUE_CODEWORD_LIVE_2026-06-12.md"
)
BUILD_MANIFEST = (
    REPO_ROOT
    / "workspace"
    / "private"
    / "builds"
    / "native-init"
    / "v2274-workqueue-codeword-combined"
    / "manifest.json"
)
TEST_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2274_workqueue_codeword_combined.img", legacy_fallback=False
)
ROLLBACK_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v2237_supplicant_terminate_poll.img", legacy_fallback=False
)
TEST_EXPECT_VERSION = "A90 Linux init 0.9.274 (v2274-workqueue-codeword-combined)"
ROLLBACK_EXPECT_VERSION = "A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)"
REQUIRED_CONFIRM = "I_UNDERSTAND_V2275_FLASHES_V2274_AND_ROLLS_BACK_TO_V2237"
REMOTE_ARTIFACTS = {
    "helper_result": "/cache/native-init-wifi-test-boot-v2274-helper.result",
    "summary": "/cache/native-init-wifi-test-boot-v2274.summary",
    "log": "/cache/native-init-wifi-test-boot-v2274.log",
    "workqueue_log": "/cache/native-init-v2274-workqueue-fwclass.log",
    "codeword_log": "/cache/native-init-v2274-tail-perf-regs-codeword.log",
}
TARGET_SYMBOLS = [
    "request_firmware_work_func",
    "_request_firmware",
    "request_firmware",
    "qdf_file_read",
    "qdf_ini_parse",
    "cfg_parse",
    "hdd_context_create",
    "wlan_hdd_pld_probe",
]


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: list[object], *, timeout: float) -> dict[str, Any]:
    rendered = [str(item) for item in command]
    print("+ " + shlex.join(rendered), flush=True)
    started = now_iso()
    try:
        completed = subprocess.run(
            rendered,
            cwd=str(REPO_ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": rendered,
            "started": started,
            "ended": now_iso(),
            "timeout": False,
            "rc": completed.returncode,
            "ok": completed.returncode == 0,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": rendered,
            "started": started,
            "ended": now_iso(),
            "timeout": True,
            "rc": None,
            "ok": False,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def write_step(store: EvidenceStore, steps: list[dict[str, Any]], name: str, result: dict[str, Any]) -> dict[str, Any]:
    stdout_path = store.write_log("host", f"{name}.stdout.txt", str(result.get("stdout") or ""))
    stderr_path = store.write_log("host", f"{name}.stderr.txt", str(result.get("stderr") or ""))
    step = {
        "name": name,
        "command": result["command"],
        "started": result["started"],
        "ended": result["ended"],
        "timeout": result["timeout"],
        "rc": result["rc"],
        "ok": result["ok"],
        "stdout_file": str(stdout_path.relative_to(store.run_dir)),
        "stderr_file": str(stderr_path.relative_to(store.run_dir)),
    }
    steps.append(step)
    return step



def run_a90ctl_step(store: EvidenceStore,
                    steps: list[dict[str, Any]],
                    name: str,
                    args: argparse.Namespace,
                    command: list[str],
                    *,
                    allow_error: bool = True,
                    timeout: float = 90.0,
                    attempts: int = 3,
                    delay_sec: float = 4.0) -> dict[str, Any]:
    last_result: dict[str, Any] | None = None
    for attempt in range(1, max(1, attempts) + 1):
        result = run_command(a90ctl_command(args, command, allow_error=allow_error), timeout=timeout)
        write_step(store, steps, f"{name}-attempt-{attempt}", result)
        if result.get("ok"):
            result = dict(result)
            result["attempt"] = attempt
            return result
        last_result = result
        if attempt < attempts:
            time.sleep(delay_sec)
    assert last_result is not None
    last_result = dict(last_result)
    last_result["attempt"] = attempts
    return last_result

def a90ctl_command(args: argparse.Namespace, command: list[str], *, allow_error: bool = False) -> list[object]:
    rendered: list[object] = [
        "python3",
        "workspace/public/src/scripts/revalidation/a90ctl.py",
        "--host",
        args.bridge_host,
        "--port",
        str(args.bridge_port),
        "--timeout",
        str(args.timeout),
        "--input-mode",
        "slow",
        "--hide-on-busy",
    ]
    if allow_error:
        rendered.append("--allow-error")
    rendered.extend(command)
    return rendered


def flash_command(image: Path, expect_version: str, expect_sha: str, *, from_native: bool) -> list[object]:
    command: list[object] = [
        "python3",
        "workspace/public/src/scripts/revalidation/native_init_flash.py",
        image,
        "--expect-version",
        expect_version,
        "--expect-sha256",
        expect_sha,
        "--verify-protocol",
        "selftest",
        "--bridge-timeout",
        "260",
        "--recovery-timeout",
        "260",
    ]
    if from_native:
        command.append("--from-native")
    return command


def load_build_manifest() -> dict[str, Any]:
    if not BUILD_MANIFEST.exists():
        return {}
    return read_bounded_json(BUILD_MANIFEST)


def preflight() -> dict[str, Any]:
    build_manifest = load_build_manifest()
    expected_test_sha = str(build_manifest.get("boot_sha256") or "") if build_manifest else ""
    test_sha = sha256(TEST_IMAGE) if TEST_IMAGE.exists() else ""
    rollback_sha = sha256(ROLLBACK_IMAGE) if ROLLBACK_IMAGE.exists() else ""
    return {
        "build_manifest": rel(BUILD_MANIFEST),
        "build_manifest_exists": BUILD_MANIFEST.exists(),
        "build_manifest_decision": build_manifest.get("decision"),
        "test_image": rel(TEST_IMAGE),
        "test_image_exists": TEST_IMAGE.exists(),
        "test_image_sha256": test_sha,
        "test_image_expected_sha256": expected_test_sha,
        "test_image_sha_matches_manifest": bool(expected_test_sha and test_sha == expected_test_sha),
        "rollback_image": rel(ROLLBACK_IMAGE),
        "rollback_image_exists": ROLLBACK_IMAGE.exists(),
        "rollback_image_sha256": rollback_sha,
        "test_expect_version": TEST_EXPECT_VERSION,
        "rollback_expect_version": ROLLBACK_EXPECT_VERSION,
        "remote_artifacts": REMOTE_ARTIFACTS,
        "recovery_twrp_available_source": "docs/operations/NATIVE_INIT_FLASH_AND_BRIDGE_GUIDE.md",
        "flash_helper": "workspace/public/src/scripts/revalidation/native_init_flash.py",
    }


def dry_run_commands(preflight_result: dict[str, Any]) -> dict[str, Any]:
    test_sha = str(preflight_result.get("test_image_sha256") or "")
    rollback_sha = str(preflight_result.get("rollback_image_sha256") or "")
    return json.loads(json.dumps({
        "current_verify": [
            "python3",
            "workspace/public/src/scripts/revalidation/native_init_flash.py",
            "--verify-only",
            "--verify-protocol",
            "selftest",
            "--expect-version",
            ROLLBACK_EXPECT_VERSION,
        ],
        "flash_test_boot": flash_command(Path(rel(TEST_IMAGE)), TEST_EXPECT_VERSION, test_sha, from_native=True),
        "collect": [
            ["python3", "workspace/public/src/scripts/revalidation/a90ctl.py", "cat", path]
            for path in REMOTE_ARTIFACTS.values()
        ],
        "rollback": flash_command(Path(rel(ROLLBACK_IMAGE)), ROLLBACK_EXPECT_VERSION, rollback_sha, from_native=True),
        "post_rollback": [
            ["python3", "workspace/public/src/scripts/revalidation/a90ctl.py", "version"],
            ["python3", "workspace/public/src/scripts/revalidation/a90ctl.py", "status"],
            ["python3", "workspace/public/src/scripts/revalidation/a90ctl.py", "selftest"],
        ],
    }, default=str))


def parse_key_values(text: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for raw_line in text.replace("\r", "").splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if not key or key.startswith("A90P1 "):
            continue
        values.setdefault(key, []).append(value.strip())
    return values


def parse_int(value: str) -> int:
    return int(value, 16) if value.startswith(("0x", "0X")) else int(value, 10)


def last_value(values: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    items = values.get(key)
    if not items:
        return default
    return items[-1]


def int_value(values: dict[str, list[str]], key: str) -> int | None:
    value = last_value(values, key)
    if value is None:
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


WORKQUEUE_SAMPLE_RE = re.compile(r"^sample\s+(?P<body>.+)$", re.MULTILINE)
WORKQUEUE_STATS_RE = re.compile(r"^stats\s+(?P<body>.+)$", re.MULTILINE)
WORKQUEUE_RESULT_RE = re.compile(r"^result=(?P<result>.+)$", re.MULTILINE)


def parse_workqueue_log(text: str) -> dict[str, Any]:
    stats_match = WORKQUEUE_STATS_RE.search(text)
    def scalar_fields(body: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for item in shlex.split(body):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            out[key] = value
        return out

    stats = {
        key: parse_int(value)
        for key, value in scalar_fields(stats_match.group("body")).items()
    } if stats_match else {}
    samples: list[dict[str, Any]] = []
    for match in WORKQUEUE_SAMPLE_RE.finditer(text):
        fields = scalar_fields(match.group("body"))
        row: dict[str, Any] = {}
        for key, value in fields.items():
            if key == "kind":
                row[key] = value
            else:
                row[key] = parse_int(value)
        if "function" in row:
            samples.append(row)
    result_match = WORKQUEUE_RESULT_RE.search(text)
    return {
        "stats": stats,
        "samples": samples,
        "result": result_match.group("result") if result_match else None,
    }


def load_symbol_map() -> tuple[list[int], list[str], dict[str, int]]:
    symbols = codeword_v2216.load_text_symbols()
    return [addr for addr, _ in symbols], [name for _, name in symbols], dict((name, addr) for addr, name in symbols)


def resolve_symbol(static_addr: int, addrs: list[int], names: list[str]) -> dict[str, Any]:
    index = bisect.bisect_right(addrs, static_addr) - 1
    if index < 0:
        return {"symbol": None, "offset": None, "static_hex": f"0x{static_addr:016x}"}
    symbol_addr = addrs[index]
    next_addr = addrs[index + 1] if index + 1 < len(addrs) else None
    in_range = next_addr is None or static_addr < next_addr
    return {
        "symbol": names[index] if in_range else None,
        "symbol_addr": f"0x{symbol_addr:016x}",
        "offset": static_addr - symbol_addr if in_range else None,
        "static_hex": f"0x{static_addr:016x}",
    }


def classify_combined_artifacts(paths: dict[str, Path]) -> dict[str, Any]:
    workqueue_text = paths.get("workqueue_log", Path()).read_text(encoding="utf-8", errors="replace") if paths.get("workqueue_log") and paths["workqueue_log"].exists() else ""
    codeword_text = paths.get("codeword_log", Path()).read_text(encoding="utf-8", errors="replace") if paths.get("codeword_log") and paths["codeword_log"].exists() else ""
    helper_text = "\n".join(
        paths[name].read_text(encoding="utf-8", errors="replace")
        for name in ("helper_result", "summary", "log")
        if name in paths and paths[name].exists()
    )
    helper_values = parse_key_values(helper_text)

    workqueue = parse_workqueue_log(workqueue_text)
    codeword_probe = codeword_v2216.parse_helper_stdout(codeword_text)
    codeword_analysis = codeword_v2216.analyze_probe(codeword_probe)
    codeword = codeword_analysis.get("codeword") or {}
    slide = codeword_v2216.parse_int(str((codeword.get("best") or {}).get("slide", "0"))) if (codeword.get("best") or {}).get("slide") is not None else None
    accepted_slide = bool(codeword.get("accepted_symbolization_slide") or codeword.get("accepted_exact_codeword_slide"))

    addrs, names, symbol_index = load_symbol_map()
    target_static = {name: symbol_index[name] for name in TARGET_SYMBOLS if name in symbol_index}
    target_hits: list[dict[str, Any]] = []
    symbol_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    samples_out: list[dict[str, Any]] = []
    if slide is not None:
        for sample in workqueue.get("samples") or []:
            function = int(sample.get("function", 0))
            static_addr = function - slide
            resolved = resolve_symbol(static_addr, addrs, names)
            symbol = resolved.get("symbol")
            kind = str(sample.get("kind") or "")
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
            if symbol:
                symbol_counts[str(symbol)] = symbol_counts.get(str(symbol), 0) + 1
            row = {
                "index": sample.get("index"),
                "kind": kind,
                "function": f"0x{function:016x}",
                "static": resolved.get("static_hex"),
                "symbol": symbol,
                "offset": resolved.get("offset"),
                "work": f"0x{int(sample.get('work', 0)):016x}",
                "workqueue": f"0x{int(sample.get('workqueue', 0)):016x}",
                "pid": sample.get("pid"),
                "tgid": sample.get("tgid"),
            }
            if len(samples_out) < 64:
                samples_out.append(row)
            if symbol in target_static:
                target_hits.append(row)

    total = int((workqueue.get("stats") or {}).get("total", 0))
    stored = int((workqueue.get("stats") or {}).get("stored", 0))
    if not workqueue_text:
        classification = "workqueue-log-missing"
    elif workqueue.get("result") != "v2273-workqueue-func-sample-ring-complete":
        classification = "workqueue-sampler-incomplete"
    elif not codeword_text:
        classification = "codeword-log-missing"
    elif not accepted_slide:
        classification = "codeword-slide-unusable"
    elif total <= 0 or stored <= 0:
        classification = "workqueue-no-activity"
    elif target_hits:
        classification = "workqueue-target-hit"
    else:
        classification = "workqueue-no-target-hit"

    return {
        "classification": classification,
        "target_symbols": TARGET_SYMBOLS,
        "target_symbol_static": {name: f"0x{addr:016x}" for name, addr in target_static.items()},
        "target_hit_count": len(target_hits),
        "target_hits": target_hits[:32],
        "workqueue": {
            "result": workqueue.get("result"),
            "stats": workqueue.get("stats"),
            "sample_count": len(workqueue.get("samples") or []),
            "symbol_counts_top": sorted(symbol_counts.items(), key=lambda item: (-item[1], item[0]))[:24],
            "kind_counts": kind_counts,
            "sample_preview": samples_out,
        },
        "codeword": {
            "printed_samples": len(codeword_probe.get("samples") or []),
            "occupied_samples": codeword_analysis.get("occupied_samples"),
            "capacity": codeword_analysis.get("capacity"),
            "accepted_symbolization_slide": accepted_slide,
            "accepted_exact_codeword_slide": codeword.get("accepted_exact_codeword_slide"),
            "accepted_near_exact_codeword_slide": codeword.get("accepted_near_exact_codeword_slide"),
            "acceptance_reason": codeword.get("acceptance_reason"),
            "slide": slide,
            "slide_hex": (codeword.get("best") or {}).get("slide_hex"),
            "best": codeword.get("best"),
        },
        "helper": {
            "wlan0_present": last_value(helper_values, "wlan0_present"),
            "supervisor_result": last_value(helper_values, "supervisor_result"),
            "helper_exit_code": last_value(helper_values, "helper_exit_code") or last_value(helper_values, "child_exit_code"),
            "helper_timed_out": last_value(helper_values, "helper_timed_out") or last_value(helper_values, "timed_out"),
        },
    }


def collect_artifacts(args: argparse.Namespace, store: EvidenceStore, steps: list[dict[str, Any]]) -> dict[str, Any]:
    device_dir = store.mkdir("device")
    paths: dict[str, Path] = {}
    collected: dict[str, Any] = {}
    for name, remote_path in REMOTE_ARTIFACTS.items():
        result = run_command(a90ctl_command(args, ["cat", remote_path], allow_error=True), timeout=args.collect_timeout)
        write_step(store, steps, f"collect-{name}", result)
        local_path = device_dir / f"{name}.cmdv1.txt"
        local_path.write_text(str(result.get("stdout") or ""), encoding="utf-8")
        local_path.chmod(0o600)
        paths[name] = local_path
        collected[name] = {
            "remote_path": remote_path,
            "local_path": rel(local_path),
            "ok": bool(result.get("ok")),
            "bytes": local_path.stat().st_size,
        }
    return {
        "artifacts": collected,
        "classification": classify_combined_artifacts(paths),
    }


def verify_current(args: argparse.Namespace, store: EvidenceStore, steps: list[dict[str, Any]], expected_sha: str) -> dict[str, Any]:
    verify = run_command([
        "python3",
        "workspace/public/src/scripts/revalidation/native_init_flash.py",
        "--verify-only",
        "--verify-protocol",
        "selftest",
        "--expect-version",
        ROLLBACK_EXPECT_VERSION,
        "--expect-sha256",
        expected_sha,
        str(ROLLBACK_IMAGE),
    ], timeout=args.flash_timeout)
    write_step(store, steps, "preflight-current-baseline-verify", verify)
    status = run_a90ctl_step(store, steps, "preflight-current-status", args, ["status"], timeout=120)
    selftest = run_a90ctl_step(store, steps, "preflight-current-selftest", args, ["selftest"], timeout=120)
    return {
        "verify_ok": bool(verify.get("ok")),
        "status_ok": bool(status.get("ok")),
        "selftest_ok": bool(selftest.get("ok")) and "fail=0" in str(selftest.get("stdout") or ""),
    }


def rollback(args: argparse.Namespace, store: EvidenceStore, steps: list[dict[str, Any]], rollback_sha: str) -> dict[str, Any]:
    first = run_command(flash_command(ROLLBACK_IMAGE, ROLLBACK_EXPECT_VERSION, rollback_sha, from_native=True), timeout=args.flash_timeout)
    write_step(store, steps, "rollback-v2237-from-native", first)
    attempt = "from-native"
    ok = bool(first.get("ok"))
    if not ok:
        second = run_command(flash_command(ROLLBACK_IMAGE, ROLLBACK_EXPECT_VERSION, rollback_sha, from_native=False), timeout=args.flash_timeout)
        write_step(store, steps, "rollback-v2237-from-recovery", second)
        attempt = "from-recovery"
        ok = bool(second.get("ok"))
    version = run_a90ctl_step(store, steps, "post-rollback-version", args, ["version"], timeout=120)
    status = run_a90ctl_step(store, steps, "post-rollback-status", args, ["status"], timeout=120)
    selftest = run_a90ctl_step(store, steps, "post-rollback-selftest", args, ["selftest"], timeout=120)
    return {
        "ok": ok,
        "attempt": attempt,
        "version_ok": bool(version.get("ok")) and ROLLBACK_EXPECT_VERSION in str(version.get("stdout") or ""),
        "status_ok": bool(status.get("ok")),
        "selftest_ok": bool(selftest.get("ok")) and "fail=0" in str(selftest.get("stdout") or ""),
    }


def classify_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not manifest.get("execute"):
        pre = manifest["preflight"]
        ok = all([
            pre.get("build_manifest_exists"),
            pre.get("test_image_exists"),
            pre.get("test_image_sha_matches_manifest"),
            pre.get("rollback_image_exists"),
        ])
        return {
            "decision": "v2275-workqueue-codeword-dry-run-ready" if ok else "v2275-workqueue-codeword-dry-run-blocked",
            "pass": bool(ok),
            "reason": "host-only flash/capture/rollback plan is complete; live execution requires --execute and confirmation" if ok else "required V2274 build artifact or rollback image is missing/mismatched",
        }
    rollback_result = manifest.get("rollback") or {}
    if not rollback_result.get("selftest_ok"):
        return {
            "decision": "v2275-workqueue-codeword-rollback-selftest-failed",
            "pass": False,
            "reason": "rollback did not finish with selftest fail=0",
        }
    if manifest.get("live_block") == "preflight-current-baseline-failed":
        return {
            "decision": "v2275-workqueue-codeword-preflight-failed-no-flash",
            "pass": False,
            "reason": "current baseline verification failed before flashing V2274",
        }
    if manifest.get("live_block") == "test-flash-failed":
        return {
            "decision": "v2275-workqueue-codeword-test-flash-failed-rollback-pass",
            "pass": False,
            "reason": "V2274 flash or health verification failed, but rollback selftest fail=0 passed",
        }
    collect = manifest.get("collect") or {}
    classification = collect.get("classification") or {}
    classification_name = str(classification.get("classification") or "unknown")
    if classification_name in {"workqueue-log-missing", "workqueue-sampler-incomplete", "codeword-log-missing", "codeword-slide-unusable"}:
        return {
            "decision": f"v2275-workqueue-codeword-live-{classification_name}-rollback-pass",
            "pass": False,
            "reason": "V2274 booted and rollback passed, but the combined oracle did not produce classifiable paired workqueue/codeword evidence",
        }
    return {
        "decision": f"v2275-workqueue-codeword-live-pass-{classification_name}",
        "pass": True,
        "reason": "V2274 workqueue/codeword artifacts were collected and classified; rollback selftest fail=0 passed",
    }


def render_report(manifest: dict[str, Any]) -> str:
    result = manifest["result"]
    pre = manifest["preflight"]
    lines = [
        "# Native Init V2275 Workqueue Codeword Live",
        "",
        "## Summary",
        "",
        "- Cycle: `V2275`",
        "- Type: rollbackable live validation of the V2274 combined workqueue function-pointer and same-boot codeword observer.",
        f"- Decision: `{result['decision']}`",
        f"- Result: `{'PASS' if result['pass'] else 'FAIL'}`",
        f"- Reason: {result['reason']}",
        f"- Execute mode: `{manifest['execute']}`",
        f"- Evidence: `{manifest['out_dir']}`",
        "- Track: T1 kernel observation; no downgrade to T2/T3.",
        "",
        "## Images",
        "",
        f"- Test image: `{pre['test_image']}`",
        f"- Test SHA256: `{pre['test_image_sha256']}`",
        f"- Test version: `{pre['test_expect_version']}`",
        f"- Rollback image: `{pre['rollback_image']}`",
        f"- Rollback SHA256: `{pre['rollback_image_sha256']}`",
        f"- Rollback version: `{pre['rollback_expect_version']}`",
        "",
    ]
    if manifest.get("execute"):
        health = manifest.get("test_health") or {}
        rollback_result = manifest.get("rollback") or {}
        classification = ((manifest.get("collect") or {}).get("classification") or {})
        lines.extend([
            "## Live Evidence",
            "",
            f"- Preflight baseline verified: `{(manifest.get('current_preflight') or {}).get('verify_ok')}` selftest fail=0: `{(manifest.get('current_preflight') or {}).get('selftest_ok')}`",
            f"- V2274 flash OK: `{(manifest.get('test_flash') or {}).get('ok')}`",
            f"- V2274 health: version=`{health.get('version_ok')}` status=`{health.get('status_ok')}` selftest_fail0=`{health.get('selftest_ok')}`",
            f"- Rollback OK: `{rollback_result.get('ok')}` via `{rollback_result.get('attempt')}`",
            f"- Rollback health: version=`{rollback_result.get('version_ok')}` status=`{rollback_result.get('status_ok')}` selftest_fail0=`{rollback_result.get('selftest_ok')}`",
            f"- Classification: `{classification.get('classification')}`",
            f"- Workqueue samples: `{((classification.get('workqueue') or {}).get('sample_count'))}` stats=`{((classification.get('workqueue') or {}).get('stats'))}`",
            f"- Codeword slide: accepted=`{((classification.get('codeword') or {}).get('accepted_symbolization_slide'))}` slide=`{((classification.get('codeword') or {}).get('slide_hex'))}` reason=`{((classification.get('codeword') or {}).get('acceptance_reason'))}`",
            f"- Target hit count: `{classification.get('target_hit_count')}`",
            f"- Helper result: supervisor=`{((classification.get('helper') or {}).get('supervisor_result'))}` exit=`{((classification.get('helper') or {}).get('helper_exit_code'))}` timed_out=`{((classification.get('helper') or {}).get('helper_timed_out'))}` wlan0_present=`{((classification.get('helper') or {}).get('wlan0_present'))}`",
            "",
            "## Workqueue Classification",
            "",
        ])
        workqueue = classification.get("workqueue") or {}
        lines.extend([
            f"- Workqueue sampler result: `{workqueue.get('result')}`",
            f"- Kind counts: `{workqueue.get('kind_counts')}`",
            f"- Top symbols: `{workqueue.get('symbol_counts_top')}`",
            f"- Target hits: `{classification.get('target_hits')}`",
            "",
        ])
        if classification.get("classification") == "workqueue-target-hit":
            lines.extend([
                "## Interpretation",
                "",
                "- The V2274 same-boot codeword slide classified at least one target workqueue function pointer.",
                "- Treat this as code-path identity evidence for the post-FWREADY firmware_class/qcacld-HDD tail, not as a Wi-Fi network functional test.",
                "",
            ])
        elif classification.get("classification") == "workqueue-no-target-hit":
            lines.extend([
                "## Interpretation",
                "",
                "- The paired workqueue/codeword oracle was classifiable, but no target firmware_class/qcacld-HDD workqueue function pointer appeared in the captured window.",
                "- This narrows the observed tail toward a synchronous/non-workqueue path or a target window outside the V2274 sampler period.",
                "",
            ])
    else:
        lines.extend([
            "## Dry-Run Plan",
            "",
            "```json",
            json.dumps(manifest.get("dry_run_commands") or {}, indent=2, ensure_ascii=False),
            "```",
            "",
        ])
    lines.extend([
        "## Safety Scope",
        "",
        "- Flash path is limited to boot partition via `native_init_flash.py`.",
        "- Rollback target is V2237, with post-rollback `version`/`status`/`selftest fail=0` verification.",
        "- Collection uses read-only `cat` through the native bridge after the helper window.",
        "- This run does not use Wi-Fi scan/connect, credentials, DHCP/routes, external ping, `probe_write_user`, tracefs control writes, eSoC/PCIe/GDSC/PMIC/GPIO paths, platform bind/unbind, or `sda29` writes.",
        "- The only non-read-only target-side operation inside V2274 is the pre-existing bounded firmware_class userspace fallback feed for `WCNSS_qcom_cfg.ini`, `bdwlan.bin`, and `regdb.bin`.",
        "",
    ])
    return "\n".join(lines)


def residual_state(manifest: dict[str, Any]) -> dict[str, Any]:
    steps = [step for step in manifest.get("steps", []) if isinstance(step, dict)]
    test_flash = manifest.get("test_flash") if isinstance(manifest.get("test_flash"), dict) else {}
    test_flash_attempted = "ok" in test_flash
    rollback_needed = bool(manifest.get("execute") and test_flash_attempted)
    rollback_result = manifest.get("rollback") if isinstance(manifest.get("rollback"), dict) else {}
    rollback_selftest_ok = bool(rollback_result.get("selftest_ok"))
    rollback_ok = bool(rollback_result.get("ok")) and rollback_selftest_ok if rollback_needed else True
    cleanup_required = bool(rollback_needed and not rollback_ok)
    return {
        "device_touched": bool(manifest.get("execute") and steps),
        "flash_reboot": test_flash_attempted,
        "test_flash_ok": bool(test_flash.get("ok")),
        "rollback_ok": rollback_ok,
        "rollback_attempt": rollback_result.get("attempt", "not-needed-no-flash"),
        "selftest_ok": rollback_selftest_ok if rollback_needed else True,
        "cleanup_required": cleanup_required,
        "residual_risk": "rollback-or-selftest-incomplete" if cleanup_required else "none",
        "wifi_scan_connect": False,
        "credentials_used": False,
        "dhcp_routes_ping": False,
        "tracefs_control_write": False,
        "bpf_attach": bool(manifest.get("execute")),
        "read_only_bpf": True,
        "probe_write_user_executed": False,
        "partition_write": test_flash_attempted,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="v2275-workqueue-codeword-live")
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=54321)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--collect-timeout", type=float, default=180.0)
    parser.add_argument("--flash-timeout", type=float, default=900.0)
    parser.add_argument("--post-boot-wait-sec", type=float, default=125.0)
    parser.add_argument("--execute", action="store_true", help="perform the live flash/capture/rollback sequence")
    parser.add_argument("--confirm", default="", help=f"required for --execute: {REQUIRED_CONFIRM}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    label = safe_artifact_label(args.label)
    run_dir = RUN_ROOT / f"{label}-{artifact_timestamp()}"
    store = EvidenceStore(run_dir)
    steps: list[dict[str, Any]] = []
    manifest: dict[str, Any] = {
        "cycle": "V2275",
        "started_at": now_iso(),
        "out_dir": rel(run_dir),
        "execute": bool(args.execute),
        "preflight": {},
        "steps": steps,
        "phase_timer_contract": transport.PHASE_TIMER_CONTRACT,
        "phase_timers": [],
        "safety": {
            "dry_run_default": True,
            "requires_confirm_for_flash": True,
            "flash_helper_only": True,
            "partition_write_scope": "boot image flash to V2274 and rollback to V2237 only" if args.execute else "none",
            "wifi_scan_connect": False,
            "credentials": False,
            "dhcp_routes_ping": False,
            "bpf_attach": bool(args.execute),
            "read_only_bpf": True,
            "probe_write_user": False,
            "tracefs_write": False,
        },
    }
    with transport.phase(manifest, "host_preflight"):
        preflight_result = preflight()
    manifest["preflight"] = preflight_result
    if not args.execute:
        with transport.phase(manifest, "dry_run_plan"):
            manifest["dry_run_commands"] = dry_run_commands(preflight_result)
    elif args.confirm != REQUIRED_CONFIRM:
        manifest["result"] = {
            "decision": "v2275-workqueue-codeword-live-confirmation-missing",
            "pass": False,
            "reason": "live mode requires the exact confirmation token",
        }
    else:
        with transport.phase(manifest, "verify_current_baseline"):
            current = verify_current(args, store, steps, str(preflight_result["rollback_image_sha256"]))
        manifest["current_preflight"] = current
        if not (current.get("verify_ok") and current.get("selftest_ok")):
            manifest["live_block"] = "preflight-current-baseline-failed"
            manifest["rollback"] = {"ok": True, "attempt": "not-needed-pre-test-flash", "selftest_ok": True}
        else:
            with transport.phase(manifest, "test_flash"):
                test_flash = run_command(
                    flash_command(TEST_IMAGE, TEST_EXPECT_VERSION, str(preflight_result["test_image_sha256"]), from_native=True),
                    timeout=args.flash_timeout,
                )
            write_step(store, steps, "flash-v2274-from-native", test_flash)
            manifest["test_flash"] = {"ok": bool(test_flash.get("ok")), "rc": test_flash.get("rc")}
            if bool(test_flash.get("ok")):
                with transport.phase(manifest, "test_boot_health"):
                    version = run_a90ctl_step(store, steps, "test-boot-version", args, ["version"], timeout=120)
                    status = run_a90ctl_step(store, steps, "test-boot-status", args, ["status"], timeout=120)
                    selftest = run_a90ctl_step(store, steps, "test-boot-selftest", args, ["selftest"], timeout=120)
                manifest["test_health"] = {
                    "version_ok": bool(version.get("ok")) and TEST_EXPECT_VERSION in str(version.get("stdout") or ""),
                    "status_ok": bool(status.get("ok")),
                    "selftest_ok": bool(selftest.get("ok")) and "fail=0" in str(selftest.get("stdout") or ""),
                }
                with transport.phase(manifest, "post_boot_helper_window_wait"):
                    wait_started = now_iso()
                    time.sleep(max(0.0, args.post_boot_wait_sec))
                    write_step(store, steps, "post-boot-helper-window-wait", {
                        "command": ["sleep", f"{args.post_boot_wait_sec:.3f}"],
                        "started": wait_started,
                        "ended": now_iso(),
                        "timeout": False,
                        "rc": 0,
                        "ok": True,
                        "stdout": f"waited_sec={args.post_boot_wait_sec:.3f}\n",
                        "stderr": "",
                    })
                with transport.phase(manifest, "collect_artifacts"):
                    manifest["collect"] = collect_artifacts(args, store, steps)
            else:
                manifest["live_block"] = "test-flash-failed"
            with transport.phase(manifest, "rollback"):
                manifest["rollback"] = rollback(args, store, steps, str(preflight_result["rollback_image_sha256"]))
    if "result" not in manifest:
        with transport.phase(manifest, "classify"):
            manifest["result"] = classify_manifest(manifest)
    manifest["finished_at"] = now_iso()
    transport.set_residual_state(manifest, residual_state(manifest))
    transport.add_total_phase(manifest, "artifact_write", time.monotonic(), ok=True)
    store.write_json("manifest.json", manifest)
    write_public_text(REPORT_PATH, render_report(manifest))
    print(json.dumps({
        "decision": manifest["result"]["decision"],
        "pass": manifest["result"]["pass"],
        "out_dir": manifest["out_dir"],
        "execute": manifest["execute"],
    }, indent=2, ensure_ascii=False))
    return 0 if manifest["result"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
