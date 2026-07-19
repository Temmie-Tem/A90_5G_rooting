#!/usr/bin/env python3
"""Read-only connected qualification for the FYG8 R4W1-C carrier.

This helper has no transfer, reboot, Download-mode, or flash implementation.
It pins the host artifacts and records the exact rooted Android baseline that a
later, separately reviewed one-shot live helper may consume.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any

import s22plus_boot_only_live_core as core
import s22plus_fyg8_r3c0_live_gate as transport
import s22plus_odin_transition_core as odin_core


SCHEMA = "s22plus_fyg8_r4w1c_connected_gate_v1"
PASS_SCHEMA = "s22plus_fyg8_r4w1c_connected_pass_v1"
TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
VERDICT = "PASS_R4W1C_CONNECTED_BASELINE_READ_ONLY"
OFFLINE_VERDICT = "PASS_R4W1C_CONNECTED_GATE_OFFLINE_CHECK"
ACK_TOKEN = "S22PLUS-FYG8-R4W1C-CONNECTED-READ-ONLY-DRY-RUN"
ACTIVE_SENTINEL = "S22PLUS_FYG8_R4W1C_CONNECTED_POLICY_STATE=ACTIVE"
POLICY_MARKER = "S22+ FYG8 R4W1-C connected read-only qualification gate"
POLICY_CLAUSE_BEGIN = "BEGIN_S22PLUS_FYG8_R4W1C_CONNECTED_POLICY_V1"
POLICY_CLAUSE_END = "END_S22PLUS_FYG8_R4W1C_CONNECTED_POLICY_V1"

SCRIPT_RELATIVE = Path(
    "workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1c_connected_gate.py"
)
TEST_RELATIVE = Path("tests/test_s22plus_fyg8_r4w1c_connected_gate.py")
LIVE_CORE_RELATIVE = Path(
    "workspace/public/src/scripts/revalidation/s22plus_boot_only_live_core.py"
)
LIVE_CORE_TEST_RELATIVE = Path("tests/test_s22plus_boot_only_live_core.py")
ODIN_CORE_RELATIVE = Path(
    "workspace/public/src/scripts/revalidation/s22plus_odin_transition_core.py"
)
ODIN_CORE_TEST_RELATIVE = Path("tests/test_s22plus_odin_transition_core.py")
STATIC_CHECKER_RELATIVE = Path(
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_r4w1c_watchdog_carrier_static_checker.py"
)
STATIC_CHECKER_TEST_RELATIVE = Path(
    "tests/test_s22plus_fyg8_r4w1c_watchdog_carrier_static_checker.py"
)
BUILDER_RELATIVE = Path(
    "workspace/public/src/scripts/revalidation/"
    "build_s22plus_fyg8_r4w1c_watchdog_carrier.py"
)
BUILDER_TEST_RELATIVE = Path(
    "tests/test_build_s22plus_fyg8_r4w1c_watchdog_carrier.py"
)
TRANSPORT_RELATIVE = Path(
    "workspace/public/src/scripts/revalidation/s22plus_fyg8_r3c0_live_gate.py"
)
POLICY_DRAFT = Path(
    "docs/operations/S22PLUS_FYG8_R4W1C_CONNECTED_EXCEPTION_DRAFT_2026-07-20.md"
)

EXPECTED_CANDIDATE_BOOT_SIZE = 100_663_296
EXPECTED_CANDIDATE_BOOT_SHA256 = (
    "1d394028714c48cfc0fd220acade9ead9a49ea21a81c59b2b87f88e61de704b0"
)
EXPECTED_CANDIDATE_LZ4_SIZE = 27_057_849
EXPECTED_CANDIDATE_LZ4_SHA256 = (
    "abe6b9069b1bfd04c0aeac4b022e367d5d8450101302d623ea2c9efe3b0c0d66"
)
EXPECTED_CANDIDATE_AP_SIZE = 27_064_361
EXPECTED_CANDIDATE_AP_SHA256 = (
    "85514e79e3400de30b7146606a9e86c3655fc7a8766daba5f054ae1bd54fd42f"
)
EXPECTED_MANIFEST_SIZE = 15_635
EXPECTED_MANIFEST_SHA256 = (
    "bfb932fd840104b54d41a957b13d56459c635d8939899c6f50d773aa7474ab76"
)
EXPECTED_STATIC_RESULT_SIZE = 8_306
EXPECTED_STATIC_RESULT_SHA256 = (
    "14786803582b62b88db9a3791ac49364a580fe9c5c8459d0e11b66e0f8215c94"
)
EXPECTED_STATIC_SCHEMA = "s22plus_fyg8_r4w1c_watchdog_carrier_static_checker_v1"
EXPECTED_STATIC_VERDICT = "PASS_R4W1C_WATCHDOG_CARRIER_TWO_REPRO_STATIC_CONTRACT"

EXPECTED_STATIC_CHECKER_SIZE = 25_149
EXPECTED_STATIC_CHECKER_SHA256 = (
    "eafd019f8e527d3ece6c632a52fb518c3317f62e187031c4dc4a7970c9446fff"
)
EXPECTED_STATIC_CHECKER_TEST_SIZE = 4_817
EXPECTED_STATIC_CHECKER_TEST_SHA256 = (
    "f1d158952e5912ed484479521be42e69d4fd40b9994118dd0615aa85ce3f3f8a"
)
EXPECTED_BUILDER_SIZE = 27_568
EXPECTED_BUILDER_SHA256 = (
    "869a2df317b0ff803f4129342a1e99b989c67a4ae79adfe45a520f471bd7dd0c"
)
EXPECTED_BUILDER_TEST_SIZE = 7_650
EXPECTED_BUILDER_TEST_SHA256 = (
    "5f154ee44b9cd0ce41af132d9b39fb046e10b0664dc07f901e9235e03fbf3147"
)
EXPECTED_LIVE_CORE_SIZE = 12_524
EXPECTED_LIVE_CORE_SHA256 = (
    "9bcade2532e77d538112836ebe9903bab832c1f2250151d3635260b6fd013725"
)
EXPECTED_LIVE_CORE_TEST_SIZE = 6_539
EXPECTED_LIVE_CORE_TEST_SHA256 = (
    "b55db8579115ec437e7fe63b6a3b6ecef0d8cbcac54110599e85f310f3b2fd9d"
)
EXPECTED_ODIN_CORE_SIZE = 52_557
EXPECTED_ODIN_CORE_SHA256 = (
    "ab418aac5ce4c854f433e2132bd9536a610991384ec82c50dc0ba063f1888a9b"
)
EXPECTED_ODIN_CORE_TEST_SIZE = 63_492
EXPECTED_ODIN_CORE_TEST_SHA256 = (
    "560a6cefd2b4a6fcbe63be27fa06073a4c57eba0a95e9f7e7f2c81792f9ac376"
)
EXPECTED_TRANSPORT_SIZE = 35_401
EXPECTED_TRANSPORT_SHA256 = (
    "f10a30735882bbd59453471fe901b1cef11fdf42bcf3560a8ae61b4af361c4f4"
)

EXPECTED_MAGISK_AP_SIZE = 23_367_721
EXPECTED_MAGISK_AP_SHA256 = (
    "d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56"
)
EXPECTED_STOCK_AP_SIZE = 100_669_481
EXPECTED_STOCK_AP_SHA256 = (
    "2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94"
)
EXPECTED_FULL_FIRMWARE_SIZE = 9_680_091_538
EXPECTED_FULL_FIRMWARE_SHA256 = (
    "f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8"
)
EXPECTED_ODIN_SIZE = 3_746_744
EXPECTED_ODIN_SHA256 = (
    "6754aa54f2abe6e99ece32414cd34c8b23b28dbddde537a33203036813637c3b"
)

EXPECTED_MAGISK_BOOT_SHA256 = (
    "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e"
)
EXPECTED_VENDOR_BOOT_SHA256 = (
    "096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7"
)
EXPECTED_DTBO_SHA256 = (
    "97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c"
)
EXPECTED_RECOVERY_SHA256 = (
    "93fac06ca79bf4b365b25a8d49902bc41aba112ea253c30880c90e314d7895d4"
)

MARKER = (
    b"\n[[S22R4W1B|id=36dc5462adedcf136176f2ddcfee08a8|"
    b"phase=DIRECT_INIT_EXEC_ACCEPTED|pid=1|path=/init]]\n"
)
MARKER_FAMILY = b"[[S22R4W1B|"
HISTORICAL_FAMILY = b"[[S22R4W1|"
EXPECTED_BIND = (
    "/sys/bus/platform/drivers/samsung,kernel_log_buf/"
    "8.samsung,kernel_log_buf"
)
PSTORE_PATHS = (
    "/sys/fs/pstore/console-ramoops",
    "/sys/fs/pstore/console-ramoops-0",
)
MAX_OBSERVER_BYTES = 64 * 1024 * 1024

DEFAULT_REPRO = Path(
    "workspace/private/outputs/s22plus_fyg8_r4w1c_watchdog_carrier/reproduction-h"
)
DEFAULT_CANDIDATE_BOOT = DEFAULT_REPRO / "boot.img"
DEFAULT_CANDIDATE_LZ4 = DEFAULT_REPRO / "boot.img.lz4"
DEFAULT_CANDIDATE_AP = DEFAULT_REPRO / "odin4/AP.tar.md5"
DEFAULT_MANIFEST = DEFAULT_REPRO / "manifest.json"
DEFAULT_STATIC_RESULT = Path(
    "workspace/private/outputs/s22plus_fyg8_r4w1c_watchdog_carrier/"
    "static-check-result-v3.json"
)
DEFAULT_MAGISK_AP = transport.DEFAULT_MAGISK_ROLLBACK_AP
DEFAULT_STOCK_AP = transport.DEFAULT_STOCK_ROLLBACK_AP
DEFAULT_FULL_FIRMWARE = Path(
    "workspace/private/inputs/firmware/SAMFW.COM_SM-S906N_SKC_"
    "S906NKSS7FYG8_fac.zip"
)
DEFAULT_ODIN = transport.DEFAULT_ODIN
RUN_ROOT = Path("workspace/private/runs")
PASS_STATE = Path(
    "workspace/private/state/s22plus_fyg8_r4w1c_connected_read_only_pass.json"
)


class GateError(RuntimeError):
    pass


def repo_root() -> Path:
    return transport.repo_root()


def resolve(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else (root / value).resolve()


def helper_sha256(root: Path) -> str:
    return core.sha256_file(root / SCRIPT_RELATIVE)


def test_sha256(root: Path) -> str:
    return core.sha256_file(root / TEST_RELATIVE)


def require_identity(
    path: Path, size: int, digest: str, label: str
) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise GateError(f"{label} is missing or indirect: {path}")
    identity = core.hash_stable_file(path)
    if identity != {"size": size, "sha256": digest}:
        raise GateError(f"{label} identity mismatch: {identity}")
    return identity


def tar_members(path: Path) -> list[str]:
    with tarfile.open(path) as archive:
        members = archive.getmembers()
    if any(not member.isfile() for member in members):
        raise GateError(f"AP contains a non-regular member: {path}")
    return [member.name for member in members]


def classify_marker(payload: bytes) -> dict[str, Any]:
    return core.classify_marker_family(
        payload,
        exact_marker=MARKER,
        family_prefix=MARKER_FAMILY,
        historical_family=HISTORICAL_FAMILY,
    )


def run_fresh_static_checker(root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="s22-r4w1c-connected-static-") as temporary:
        output = Path(temporary) / "result.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(root / STATIC_CHECKER_RELATIVE),
                "--out",
                str(output),
            ],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300,
            check=False,
        )
        if completed.returncode != 0 or completed.stderr:
            raise GateError(
                f"fresh static checker failed rc={completed.returncode}: "
                f"{completed.stderr.strip()}"
            )
        identity = require_identity(
            output,
            EXPECTED_STATIC_RESULT_SIZE,
            EXPECTED_STATIC_RESULT_SHA256,
            "fresh static result",
        )
        try:
            result = json.loads(output.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise GateError("fresh static result is invalid") from exc
        if (
            result.get("schema") != EXPECTED_STATIC_SCHEMA
            or result.get("verdict") != EXPECTED_STATIC_VERDICT
            or result.get("reproducible") is not True
            or result.get("device_contact") is not False
            or result.get("device_write") is not False
            or result.get("flash") is not False
            or result.get("live_authorized") is not False
        ):
            raise GateError("fresh static result contract mismatch")
        return {**identity, "schema": result["schema"], "verdict": result["verdict"]}


def verify_artifacts(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    odin = resolve(root, args.odin)
    identities = {
        "candidate_boot": require_identity(
            resolve(root, args.candidate_boot), EXPECTED_CANDIDATE_BOOT_SIZE,
            EXPECTED_CANDIDATE_BOOT_SHA256, "candidate boot"
        ),
        "candidate_lz4": require_identity(
            resolve(root, args.candidate_lz4), EXPECTED_CANDIDATE_LZ4_SIZE,
            EXPECTED_CANDIDATE_LZ4_SHA256, "candidate LZ4"
        ),
        "candidate_ap": require_identity(
            resolve(root, args.candidate_ap), EXPECTED_CANDIDATE_AP_SIZE,
            EXPECTED_CANDIDATE_AP_SHA256, "candidate AP"
        ),
        "manifest": require_identity(
            resolve(root, args.manifest), EXPECTED_MANIFEST_SIZE,
            EXPECTED_MANIFEST_SHA256, "candidate manifest"
        ),
        "static_result": require_identity(
            resolve(root, args.static_result), EXPECTED_STATIC_RESULT_SIZE,
            EXPECTED_STATIC_RESULT_SHA256, "static result"
        ),
        "magisk_rollback_ap": require_identity(
            resolve(root, args.magisk_ap), EXPECTED_MAGISK_AP_SIZE,
            EXPECTED_MAGISK_AP_SHA256, "Magisk rollback AP"
        ),
        "stock_cleanup_ap": require_identity(
            resolve(root, args.stock_ap), EXPECTED_STOCK_AP_SIZE,
            EXPECTED_STOCK_AP_SHA256, "stock cleanup AP"
        ),
        "full_firmware": require_identity(
            resolve(root, args.full_firmware), EXPECTED_FULL_FIRMWARE_SIZE,
            EXPECTED_FULL_FIRMWARE_SHA256, "full FYG8 firmware"
        ),
        "odin": require_identity(
            odin, EXPECTED_ODIN_SIZE, EXPECTED_ODIN_SHA256, "Odin4"
        ),
    }
    for label, path in (
        ("candidate AP", resolve(root, args.candidate_ap)),
        ("Magisk rollback AP", resolve(root, args.magisk_ap)),
        ("stock cleanup AP", resolve(root, args.stock_ap)),
    ):
        if tar_members(path) != ["boot.img.lz4"]:
            raise GateError(f"{label} is not exactly boot-only")
    expected_sources = {
        "static_checker": (
            STATIC_CHECKER_RELATIVE,
            EXPECTED_STATIC_CHECKER_SIZE,
            EXPECTED_STATIC_CHECKER_SHA256,
        ),
        "static_checker_test": (
            STATIC_CHECKER_TEST_RELATIVE,
            EXPECTED_STATIC_CHECKER_TEST_SIZE,
            EXPECTED_STATIC_CHECKER_TEST_SHA256,
        ),
        "builder": (
            BUILDER_RELATIVE,
            EXPECTED_BUILDER_SIZE,
            EXPECTED_BUILDER_SHA256,
        ),
        "builder_test": (
            BUILDER_TEST_RELATIVE,
            EXPECTED_BUILDER_TEST_SIZE,
            EXPECTED_BUILDER_TEST_SHA256,
        ),
        "live_core": (
            LIVE_CORE_RELATIVE,
            EXPECTED_LIVE_CORE_SIZE,
            EXPECTED_LIVE_CORE_SHA256,
        ),
        "live_core_test": (
            LIVE_CORE_TEST_RELATIVE,
            EXPECTED_LIVE_CORE_TEST_SIZE,
            EXPECTED_LIVE_CORE_TEST_SHA256,
        ),
        "odin_core": (
            ODIN_CORE_RELATIVE,
            EXPECTED_ODIN_CORE_SIZE,
            EXPECTED_ODIN_CORE_SHA256,
        ),
        "odin_core_test": (
            ODIN_CORE_TEST_RELATIVE,
            EXPECTED_ODIN_CORE_TEST_SIZE,
            EXPECTED_ODIN_CORE_TEST_SHA256,
        ),
        "transport": (
            TRANSPORT_RELATIVE,
            EXPECTED_TRANSPORT_SIZE,
            EXPECTED_TRANSPORT_SHA256,
        ),
    }
    source_pins = {
        label: require_identity(root / path, size, digest, label)
        for label, (path, size, digest) in expected_sources.items()
    }
    return {
        "target": TARGET,
        "identities": identities,
        "source_pins": source_pins,
        "fresh_static_checker": run_fresh_static_checker(root),
        "ap_members": ["boot.img.lz4"],
    }


def policy_required_values(root: Path) -> tuple[str, ...]:
    return (
        POLICY_CLAUSE_BEGIN,
        POLICY_CLAUSE_END,
        POLICY_MARKER,
        ACTIVE_SENTINEL,
        str(SCRIPT_RELATIVE),
        helper_sha256(root),
        str(TEST_RELATIVE),
        test_sha256(root),
        EXPECTED_CANDIDATE_BOOT_SHA256,
        EXPECTED_CANDIDATE_AP_SHA256,
        EXPECTED_STATIC_RESULT_SHA256,
        EXPECTED_MAGISK_AP_SHA256,
        EXPECTED_STOCK_AP_SHA256,
        EXPECTED_FULL_FIRMWARE_SHA256,
        EXPECTED_ODIN_CORE_SHA256,
        ACK_TOKEN,
    )


def policy_clause(root: Path) -> str:
    try:
        text = (root / "AGENTS.md").read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError("AGENTS.md is unavailable") from exc
    pattern = re.compile(
        rf"(?ms)^`?{re.escape(POLICY_CLAUSE_BEGIN)}`?\s*$"
        rf"(?P<body>.*?)"
        rf"^`?{re.escape(POLICY_CLAUSE_END)}`?\s*$"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise GateError("R4W1-C connected policy clause is not unique")
    clause = matches[0].group(0)
    active = re.compile(rf"(?m)^\s*`?{re.escape(ACTIVE_SENTINEL)}`?\s*$")
    if len(active.findall(clause)) != 1:
        raise GateError("R4W1-C connected ACTIVE sentinel is not unique in clause")
    if "DRAFT_INACTIVE" in clause or "POLICY_STATE=RETIRED" in clause:
        raise GateError("R4W1-C connected policy clause is inactive or retired")
    missing = [value for value in policy_required_values(root) if value not in clause]
    draft_sha256 = core.sha256_file(root / POLICY_DRAFT)
    if draft_sha256 not in clause:
        missing.append(draft_sha256)
    if missing:
        raise GateError(f"R4W1-C connected policy clause missing pins: {missing}")
    return clause


def policy_active(root: Path) -> bool:
    try:
        policy_clause(root)
    except (GateError, OSError):
        return False
    return True


def verify_policy_draft(root: Path) -> dict[str, Any]:
    path = root / POLICY_DRAFT
    if path.is_symlink() or not path.is_file():
        raise GateError("R4W1-C connected policy draft is missing")
    text = path.read_text(encoding="utf-8")
    required = ("DRAFT_INACTIVE", ACTIVE_SENTINEL, *policy_required_values(root))
    missing = [value for value in required if value not in text]
    if missing:
        raise GateError(f"R4W1-C connected policy draft missing pins: {missing}")
    try:
        clause = policy_clause(root)
    except GateError:
        clause = None
    return {
        "path": str(POLICY_DRAFT),
        "sha256": core.sha256_file(path),
        "helper_sha256": helper_sha256(root),
        "test_sha256": test_sha256(root),
        "active": clause is not None,
        "policy_clause_sha256": (
            core.sha256_bytes(clause.encode("utf-8")) if clause is not None else None
        ),
    }


def remote_text(serial: str, command: str, *, root: bool = False) -> str:
    return transport.adb_shell(serial, command, root=root, timeout=90).strip()


def sha256_output(value: str, label: str) -> str:
    fields = value.split()
    if not fields or re.fullmatch(r"[0-9a-f]{64}", fields[0]) is None:
        raise GateError(f"malformed remote SHA output: {label}")
    return fields[0]


def current_android_exact() -> tuple[str, dict[str, str]]:
    serial, values = transport.current_android()
    vendor_boot = sha256_output(
        remote_text(serial, "sha256sum /dev/block/by-name/vendor_boot", root=True),
        "vendor_boot",
    )
    if values.get("boot_sha256") != EXPECTED_MAGISK_BOOT_SHA256:
        raise GateError("Android Magisk boot identity mismatch")
    if values.get("dtbo_sha256") != EXPECTED_DTBO_SHA256:
        raise GateError("Android DTBO identity mismatch")
    if values.get("recovery_sha256") != EXPECTED_RECOVERY_SHA256:
        raise GateError("Android recovery identity mismatch")
    if vendor_boot != EXPECTED_VENDOR_BOOT_SHA256:
        raise GateError("Android vendor_boot identity mismatch")
    values["vendor_boot_sha256"] = vendor_boot
    return serial, values


def pstore_console_absent(serial: str) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for path in PSTORE_PATHS:
        value = remote_text(
            serial,
            f"if test -e {shlex.quote(path)}; then echo present; else echo absent; fi",
        )
        if value not in {"present", "absent"}:
            raise GateError(f"ambiguous pstore state: {path}")
        result[path] = value == "absent"
    if not all(result.values()):
        raise GateError(f"pstore console would shadow retained observer: {result}")
    return result


def capture_observers(serial: str, run_dir: Path) -> dict[str, Any]:
    captures: dict[str, Any] = {}
    for name, command, count in (
        ("ap_klog", "cat /proc/ap_klog", 1),
        ("last_kmsg", "cat /proc/last_kmsg", 2),
    ):
        receipts: list[dict[str, Any]] = []
        payloads: list[bytes] = []
        for index in range(count):
            suffix = f"_{index + 1}" if count > 1 else ""
            path = run_dir / f"baseline_{name}{suffix}.bin"
            receipt = core.capture_adb_exec_out(
                serial,
                command,
                path,
                root=True,
                timeout=120,
                maximum=MAX_OBSERVER_BYTES,
            )
            payload = core.read_stable_file(path, maximum=MAX_OBSERVER_BYTES)
            if not payload:
                raise GateError(f"baseline observer is empty: {name}")
            receipts.append(receipt)
            payloads.append(payload)
            if count > 1:
                time.sleep(0.25)
        if any(payload != payloads[0] for payload in payloads[1:]):
            raise GateError(f"baseline observer reads differ: {name}")
        marker = classify_marker(payloads[0])
        if marker["baseline_absent"] is not True or marker["integrity_issue"] is not False:
            raise GateError(f"R4W1-B marker family contaminates baseline: {name}")
        captures[name] = {
            "reads": receipts,
            "read_count": count,
            "byte_identical": True,
            "read_to_eof": all(receipt["read_to_eof"] for receipt in receipts),
            "stderr_bytes": sum(receipt["stderr_bytes"] for receipt in receipts),
            "bytes": len(payloads[0]),
            "sha256": core.sha256_bytes(payloads[0]),
            "marker": marker,
        }
    return captures


def require_clean_odin_snapshot(record: dict[str, Any], label: str) -> None:
    if (
        record.get("live_devices") != []
        or record.get("live_device_identities") != []
        or record.get("stale_devices") != []
    ):
        raise GateError(f"{label} Odin snapshot is not clean-empty: {record}")


def expected_phase_payload(baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "connected-read-only",
        "no_odin_endpoint": True,
        "initial_snapshot_sequence": 0,
        "final_snapshot_sequence": 1,
        "android_serial": baseline.get("android_serial"),
        "boot_id": baseline.get("boot_id"),
    }


def require_direct_path(
    root: Path,
    path: Path,
    label: str,
    *,
    directory: bool = False,
) -> Path:
    root_path = root.resolve()
    if ".." in path.parts:
        raise GateError(f"{label} path contains parent traversal")
    candidate = path if path.is_absolute() else root_path / path
    try:
        relative = candidate.relative_to(root_path)
    except ValueError as exc:
        raise GateError(f"{label} path escaped the repository") from exc
    current = root_path
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise GateError(f"{label} path contains a symlink")
    if directory:
        if not candidate.is_dir():
            raise GateError(f"{label} is not a direct directory")
    elif not candidate.is_file():
        raise GateError(f"{label} is not a direct regular file")
    resolved = candidate.resolve()
    if resolved != candidate:
        raise GateError(f"{label} path did not resolve directly")
    return resolved


def canonical_run_relative(root: Path, run_dir: Path, value: str, label: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        raise GateError(f"{label} path is not absolute")
    resolved = require_direct_path(root, path, label)
    if resolved.parent != run_dir.resolve() and run_dir.resolve() not in resolved.parents:
        raise GateError(f"{label} path escaped the run directory")
    return str(resolved.relative_to(root.resolve()))


def collect_odin_evidence(
    root: Path,
    run_dir: Path,
    *,
    expected_phase_payload: dict[str, Any],
) -> dict[str, Any]:
    snapshots = odin_core.list_snapshot_receipts(run_dir)
    phases = odin_core.list_phase_receipts(run_dir)
    indexed = odin_core.read_transaction_segments(run_dir)
    if len(snapshots) != 2 or [record["sequence"] for record in snapshots] != [0, 1]:
        raise GateError("connected gate requires exactly two Odin snapshots")
    for index, snapshot in enumerate(snapshots):
        require_clean_odin_snapshot(snapshot, f"snapshot-{index}")
    if [record.get("phase") for record in phases] != ["prepared"]:
        raise GateError("connected gate requires exactly one prepared phase receipt")

    phase_path = Path(str(phases[0]["path"]))
    phase_bytes = core.read_stable_file(phase_path, maximum=1024 * 1024)
    if {
        "size": len(phase_bytes),
        "sha256": core.sha256_bytes(phase_bytes),
    } != {"size": phases[0]["size"], "sha256": phases[0]["sha256"]}:
        raise GateError("prepared phase receipt identity mismatch")
    try:
        phase_value = json.loads(phase_bytes)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GateError("prepared phase receipt is invalid JSON") from exc
    if (
        not isinstance(phase_value, dict)
        or set(phase_value) != {"schema", "phase", "timestamp_utc", "payload"}
        or phase_value.get("schema") != odin_core.PHASE_SCHEMA
        or phase_value.get("phase") != "prepared"
        or phase_value.get("timestamp_utc") != phases[0].get("timestamp_utc")
        or phase_value.get("payload") != expected_phase_payload
    ):
        raise GateError("prepared phase receipt semantic mismatch")

    summaries: list[dict[str, Any]] = []
    known: dict[str, dict[str, Any]] = {}
    for kind, records in (("odin_snapshot", snapshots), ("phase_receipt", phases)):
        for record in records:
            path = str(record["path"])
            relative = canonical_run_relative(root, run_dir, path, f"{kind} receipt")
            summary = {**record, "path": relative, "record": kind}
            summaries.append(summary)
            known[path] = record

    records = indexed.get("records")
    if not isinstance(records, list) or len(records) != len(known):
        raise GateError("Odin transaction index record count mismatch")
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise GateError("Odin transaction index record is malformed")
        receipt_path = record.get("receipt")
        if not isinstance(receipt_path, str) or receipt_path in seen:
            raise GateError("Odin transaction index receipt reference is invalid")
        seen.add(receipt_path)
        expected = known.get(receipt_path)
        if expected is None:
            raise GateError("Odin transaction index references unknown receipt")
        if (
            record.get("receipt_size") != expected["size"]
            or record.get("receipt_sha256") != expected["sha256"]
        ):
            raise GateError("Odin transaction index receipt identity mismatch")
    if seen != set(known):
        raise GateError("Odin transaction index omits a receipt")

    segment_summaries: list[dict[str, Any]] = []
    segments = indexed.get("segments")
    if not isinstance(segments, list) or not segments:
        raise GateError("Odin transaction index segment is missing")
    for segment in segments:
        if (
            not isinstance(segment, dict)
            or segment.get("complete") is not True
            or segment.get("partial_tail_bytes") != 0
        ):
            raise GateError("Odin transaction index segment is incomplete")
        path = Path(str(segment.get("path", "")))
        relative = canonical_run_relative(root, run_dir, str(path), "Odin index")
        identity = core.hash_stable_file(path)
        segment_summaries.append({**segment, **identity, "path": relative})
    summaries.sort(key=lambda value: value["path"])
    return {
        "snapshots": [
            {**record, "path": canonical_run_relative(root, run_dir, record["path"], "snapshot")}
            for record in snapshots
        ],
        "phases": [
            {
                **record,
                "path": canonical_run_relative(root, run_dir, record["path"], "phase"),
                "payload": expected_phase_payload,
            }
            for record in phases
        ],
        "index_segments": segment_summaries,
        "indexed_receipts": summaries,
        "record_count": len(records),
    }


def connected_preflight(
    root: Path,
    run_dir: Path,
    odin: Path,
    *,
    odin_absence_wait_sec: float,
    lease: Any,
) -> dict[str, Any]:
    initial_absence = odin_core.wait_for_no_live_endpoint(
        odin,
        run_dir,
        timeout_sec=odin_absence_wait_sec,
        poll_sec=0.1,
        lease=lease,
    )
    if not initial_absence.absent or initial_absence.timed_out:
        raise GateError("normal Android baseline has an Odin endpoint")
    initial_snapshots = odin_core.list_snapshot_receipts(run_dir)
    if len(initial_snapshots) != 1:
        raise GateError("initial Odin absence did not produce one snapshot")
    require_clean_odin_snapshot(initial_snapshots[0], "initial")

    serial, android = current_android_exact()
    boot_id = remote_text(serial, "cat /proc/sys/kernel/random/boot_id")
    if re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", boot_id) is None:
        raise GateError("Android boot_id is malformed")
    state = remote_text(
        serial,
        "printf 'osrelease='; cat /proc/sys/kernel/osrelease; "
        "grep '^sec_log_buf ' /proc/modules; "
        f"test -L {shlex.quote(EXPECTED_BIND)} && echo bind_ok=1 || echo bind_ok=0; "
        "stat -c '%n:%s:%a' /proc/ap_klog /proc/last_kmsg",
        root=True,
    )
    required = (
        f"osrelease={transport.EXPECTED_RELEASE}",
        "sec_log_buf ",
        " Live ",
        "bind_ok=1",
        "/proc/ap_klog:",
        "/proc/last_kmsg:",
    )
    missing = [value for value in required if value not in state]
    if missing:
        raise GateError(f"retained observer baseline mismatch: {missing}")
    pstore = pstore_console_absent(serial)
    observers = capture_observers(serial, run_dir)
    final_serial, final_android = current_android_exact()
    final_boot_id = remote_text(final_serial, "cat /proc/sys/kernel/random/boot_id")
    if final_serial != serial or final_android != android or final_boot_id != boot_id:
        raise GateError("Android baseline changed during connected collection")
    final_absence = odin_core.wait_for_no_live_endpoint(
        odin,
        run_dir,
        timeout_sec=odin_absence_wait_sec,
        poll_sec=0.1,
        sequence_start=initial_absence.next_sequence,
        lease=lease,
    )
    if not final_absence.absent or final_absence.timed_out:
        raise GateError("final connected baseline has an Odin endpoint")
    snapshots = odin_core.list_snapshot_receipts(run_dir)
    if len(snapshots) != 2:
        raise GateError("final Odin absence did not produce exactly two snapshots")
    require_clean_odin_snapshot(snapshots[1], "final")
    phase_payload = {
        "mode": "connected-read-only",
        "no_odin_endpoint": True,
        "initial_snapshot_sequence": 0,
        "final_snapshot_sequence": 1,
        "android_serial": serial,
        "boot_id": boot_id,
    }
    odin_core.create_phase_receipt(
        run_dir,
        "prepared",
        phase_payload,
        lease=lease,
    )
    odin_evidence = collect_odin_evidence(
        root,
        run_dir,
        expected_phase_payload=phase_payload,
    )
    baseline = {
        "target": TARGET,
        "android": android,
        "final_android": final_android,
        "android_serial": serial,
        "boot_id": boot_id,
        "sec_log_buf_live": True,
        "bind": EXPECTED_BIND,
        "pstore_console_absent": pstore,
        "observers": observers,
        "no_odin_endpoint": True,
        "odin_evidence": odin_evidence,
        "device_writes": False,
    }
    core.durable_write_json(run_dir / "connected_preflight.json", baseline)
    return baseline


def validate_connected_result(
    result: Any,
    artifacts: dict[str, Any],
    *,
    root: Path | None = None,
    result_path: Path | None = None,
) -> dict[Path, bytes]:
    if (root is None) != (result_path is None):
        raise GateError("connected validation context is incomplete")
    expected = {
        "schema": SCHEMA,
        "mode": "connected-read-only-dry-run",
        "target": TARGET,
        "device_contact": True,
        "device_writes": False,
        "reboot": False,
        "download_transition": False,
        "odin_transfer": False,
        "flash": False,
        "verdict": VERDICT,
    }
    if not isinstance(result, dict) or any(
        result.get(key) != value for key, value in expected.items()
    ):
        raise GateError("connected result envelope mismatch")
    if result.get("artifacts") != artifacts:
        raise GateError("connected result artifact contract mismatch")
    runtime_pins = result.get("runtime_pins")
    if (
        not isinstance(runtime_pins, dict)
        or set(runtime_pins)
        != {
            "helper_sha256",
            "test_sha256",
            "policy_draft_sha256",
            "policy_clause_sha256",
        }
        or runtime_pins.get("helper_sha256") is None
        or runtime_pins.get("test_sha256") is None
        or runtime_pins.get("policy_draft_sha256") is None
        or runtime_pins.get("policy_clause_sha256") is None
    ):
        raise GateError("connected runtime pin contract mismatch")
    if root is not None:
        clause = policy_clause(root)
        if runtime_pins != {
            "helper_sha256": helper_sha256(root),
            "test_sha256": test_sha256(root),
            "policy_draft_sha256": core.sha256_file(root / POLICY_DRAFT),
            "policy_clause_sha256": core.sha256_bytes(clause.encode("utf-8")),
        }:
            raise GateError("connected runtime pins do not match current policy")
    baseline = result.get("baseline")
    if not isinstance(baseline, dict):
        raise GateError("connected result baseline is missing")
    if (
        baseline.get("target") != TARGET
        or baseline.get("device_writes") is not False
        or baseline.get("no_odin_endpoint") is not True
        or baseline.get("sec_log_buf_live") is not True
        or baseline.get("bind") != EXPECTED_BIND
        or not isinstance(baseline.get("android_serial"), str)
        or re.fullmatch(
            r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}",
            str(baseline.get("boot_id", "")),
        )
        is None
    ):
        raise GateError("connected baseline contract mismatch")
    expected_android = {
        "model": "SM-S906N",
        "device": "g0q",
        "bootloader": "S906NKSS7FYG8",
        "incremental": "S906NKSS7FYG8",
        "boot_completed": "1",
        "bootanim": "stopped",
        "verified_boot_state": "orange",
        "root": "uid=0(root)",
        "boot_sha256": EXPECTED_MAGISK_BOOT_SHA256,
        "dtbo_sha256": EXPECTED_DTBO_SHA256,
        "recovery_sha256": EXPECTED_RECOVERY_SHA256,
        "vendor_boot_sha256": EXPECTED_VENDOR_BOOT_SHA256,
    }
    if (
        baseline.get("android") != expected_android
        or baseline.get("final_android") != expected_android
    ):
        raise GateError("connected Android contract mismatch")
    observers = baseline.get("observers")
    if not isinstance(observers, dict) or set(observers) != {"ap_klog", "last_kmsg"}:
        raise GateError("observer contract mismatch")
    expected_names = {
        "ap_klog": ["baseline_ap_klog.bin"],
        "last_kmsg": ["baseline_last_kmsg_1.bin", "baseline_last_kmsg_2.bin"],
    }
    reopened: dict[Path, bytes] = {}
    for name, observer in observers.items():
        expected_reads = 2 if name == "last_kmsg" else 1
        if (
            not isinstance(observer, dict)
            or observer.get("read_count") != expected_reads
            or observer.get("byte_identical") is not True
            or observer.get("read_to_eof") is not True
            or observer.get("stderr_bytes") != 0
            or type(observer.get("bytes")) is not int
            or observer["bytes"] <= 0
            or observer["bytes"] > MAX_OBSERVER_BYTES
            or re.fullmatch(r"[0-9a-f]{64}", str(observer.get("sha256", ""))) is None
            or not isinstance(observer.get("reads"), list)
            or len(observer["reads"]) != expected_reads
        ):
            raise GateError(f"observer receipt mismatch: {name}")
        marker = observer.get("marker")
        if (
            not isinstance(marker, dict)
            or marker.get("baseline_absent") is not True
            or marker.get("integrity_issue") is not False
            or marker.get("family_count") != 0
        ):
            raise GateError(f"observer marker mismatch: {name}")
        identities: list[dict[str, Any]] = []
        for index, receipt in enumerate(observer["reads"]):
            if (
                not isinstance(receipt, dict)
                or receipt.get("read_to_eof") is not True
                or receipt.get("returncode") != 0
                or receipt.get("stderr_bytes") != 0
                or type(receipt.get("bytes")) is not int
                or receipt["bytes"] <= 0
                or receipt["bytes"] > MAX_OBSERVER_BYTES
                or re.fullmatch(
                    r"[0-9a-f]{64}", str(receipt.get("sha256", ""))
                )
                is None
            ):
                raise GateError(f"observer read receipt mismatch: {name}")
            path = Path(str(receipt.get("path", "")))
            if not path.is_absolute() or path.name != expected_names[name][index]:
                raise GateError(f"observer read path mismatch: {name}")
            identity = {"size": receipt["bytes"], "sha256": receipt["sha256"]}
            identities.append(identity)
            if root is not None and result_path is not None:
                run_dir = require_direct_path(
                    root,
                    result_path.parent,
                    "connected run directory",
                    directory=True,
                )
                direct_path = require_direct_path(root, path, f"observer read {name}")
                if direct_path.parent != run_dir:
                    raise GateError(f"observer read escaped result directory: {name}")
                payload = core.read_stable_file(direct_path, maximum=MAX_OBSERVER_BYTES)
                if {
                    "size": len(payload),
                    "sha256": core.sha256_bytes(payload),
                } != identity:
                    raise GateError(f"observer read identity mismatch: {name}")
                if classify_marker(payload) != marker:
                    raise GateError(f"observer marker recomputation mismatch: {name}")
                stderr_path = path.with_suffix(path.suffix + ".stderr")
                direct_stderr = require_direct_path(
                    root,
                    stderr_path,
                    f"observer stderr {name}",
                )
                if core.read_stable_file(direct_stderr, maximum=1) != b"":
                    raise GateError(f"observer stderr evidence mismatch: {name}")
                reopened[direct_path] = payload
                reopened[direct_stderr] = b""
        if (
            observer["bytes"] != identities[0]["size"]
            or observer["sha256"] != identities[0]["sha256"]
            or any(identity != identities[0] for identity in identities[1:])
        ):
            raise GateError(f"observer summary identity mismatch: {name}")
    pstore = baseline.get("pstore_console_absent")
    if (
        not isinstance(pstore, dict)
        or set(pstore) != set(PSTORE_PATHS)
        or not all(pstore.values())
    ):
        raise GateError("pstore absence contract mismatch")
    odin_evidence = baseline.get("odin_evidence")
    if not isinstance(odin_evidence, dict):
        raise GateError("Odin evidence is missing")
    evidence = result.get("evidence")
    if not isinstance(evidence, dict) or set(evidence) != {"timeline", "preflight"}:
        raise GateError("connected file evidence contract mismatch")
    for label in ("timeline", "preflight"):
        item = evidence[label]
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "size", "sha256"}
            or type(item.get("size")) is not int
            or item["size"] <= 0
            or re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))) is None
        ):
            raise GateError(f"connected {label} evidence identity is malformed")
    if root is not None and result_path is not None:
        run_dir = require_direct_path(
            root,
            result_path.parent,
            "connected run directory",
            directory=True,
        )
        fresh_odin = collect_odin_evidence(
            root,
            run_dir,
            expected_phase_payload=expected_phase_payload(baseline),
        )
        if fresh_odin != odin_evidence:
            raise GateError("Odin evidence changed after collection")
        for collection in ("snapshots", "phases", "index_segments"):
            entries = odin_evidence.get(collection)
            if not isinstance(entries, list) or not entries:
                raise GateError(f"Odin {collection} evidence is missing")
            for item in entries:
                if (
                    not isinstance(item, dict)
                    or type(item.get("size")) is not int
                    or item["size"] <= 0
                    or re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")))
                    is None
                ):
                    raise GateError(f"Odin {collection} identity is malformed")
                relative = Path(str(item.get("path", "")))
                if relative.is_absolute() or ".." in relative.parts:
                    raise GateError(f"Odin {collection} path is not canonical")
                path = require_direct_path(
                    root,
                    root / relative,
                    f"Odin {collection}",
                )
                if path.parent not in {
                    run_dir,
                    run_dir / "receipts",
                }:
                    raise GateError(f"Odin {collection} path escaped the run")
                payload = core.read_stable_file(path, maximum=8 * 1024 * 1024)
                if {"size": len(payload), "sha256": core.sha256_bytes(payload)} != {
                    "size": item["size"],
                    "sha256": item["sha256"],
                }:
                    raise GateError(f"Odin {collection} identity changed")
                reopened[path] = payload
        for label, expected_name in (
            ("timeline", "timeline.json"),
            ("preflight", "connected_preflight.json"),
        ):
            item = evidence[label]
            path = require_direct_path(
                root,
                root / Path(str(item["path"])),
                f"connected {label} evidence",
            )
            if path.parent != run_dir or path.name != expected_name:
                raise GateError(f"connected {label} evidence path mismatch")
            payload = core.read_stable_file(path, maximum=8 * 1024 * 1024)
            if {"size": len(payload), "sha256": core.sha256_bytes(payload)} != {
                "size": item["size"],
                "sha256": item["sha256"],
            }:
                raise GateError(f"connected {label} evidence identity mismatch")
            try:
                parsed = json.loads(payload)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise GateError(f"connected {label} evidence is invalid JSON") from exc
            if label == "timeline":
                events = parsed.get("events") if isinstance(parsed, dict) else None
                if not isinstance(events, list) or not core.timeline_complete(events):
                    raise GateError("connected timeline is not canonical and complete")
            elif parsed != baseline:
                raise GateError("connected preflight file differs from result baseline")
            reopened[path] = payload
    return reopened


def validate_connected_pass(
    root: Path, *, expected_artifacts: dict[str, Any] | None = None
) -> dict[str, Any]:
    path = require_direct_path(
        root,
        root / PASS_STATE,
        "R4W1-C connected PASS record",
    )
    pass_payload = core.read_stable_file(path, maximum=1024 * 1024)
    try:
        record = json.loads(pass_payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GateError("R4W1-C connected PASS record is invalid") from exc
    clause = policy_clause(root)
    expected = {
        "schema": PASS_SCHEMA,
        "target": TARGET,
        "helper_sha256": helper_sha256(root),
        "test_sha256": test_sha256(root),
        "live_core_sha256": EXPECTED_LIVE_CORE_SHA256,
        "odin_core_sha256": EXPECTED_ODIN_CORE_SHA256,
        "policy_draft_sha256": core.sha256_file(root / POLICY_DRAFT),
        "policy_clause_sha256": core.sha256_bytes(clause.encode("utf-8")),
        "verdict": VERDICT,
        "device_writes": False,
    }
    required_keys = {
        *expected,
        "created_at_utc",
        "result_path",
        "result_size",
        "result_sha256",
    }
    if (
        not isinstance(record, dict)
        or set(record) != required_keys
        or any(record.get(key) != value for key, value in expected.items())
        or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z",
            str(record.get("created_at_utc", "")),
        )
        is None
        or type(record.get("result_size")) is not int
        or record["result_size"] <= 0
        or re.fullmatch(r"[0-9a-f]{64}", str(record.get("result_sha256", ""))) is None
    ):
        raise GateError("R4W1-C connected PASS contract mismatch")
    result_relative = Path(str(record.get("result_path", "")))
    if (
        result_relative.is_absolute()
        or ".." in result_relative.parts
        or tuple(result_relative.parts[:3]) != ("workspace", "private", "runs")
        or result_relative.name != "result.json"
    ):
        raise GateError("R4W1-C connected result path is not canonical")
    claimed_result_path = root / result_relative
    run_root = (root / RUN_ROOT).resolve()
    result_path = require_direct_path(
        root,
        claimed_result_path,
        "R4W1-C connected result",
    )
    if not result_path.is_relative_to(run_root):
        raise GateError("R4W1-C connected result escaped private runs")
    result_payload = core.read_stable_file(result_path, maximum=8 * 1024 * 1024)
    if {"size": len(result_payload), "sha256": core.sha256_bytes(result_payload)} != {
        "size": record["result_size"],
        "sha256": record["result_sha256"],
    }:
        raise GateError("R4W1-C connected result identity mismatch")
    try:
        result = json.loads(result_payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GateError("R4W1-C connected result is invalid") from exc
    artifacts = result.get("artifacts")
    if expected_artifacts is not None and artifacts != expected_artifacts:
        raise GateError("R4W1-C connected artifacts changed")
    reopened = validate_connected_result(
        result,
        artifacts,
        root=root,
        result_path=result_path,
    )
    if (
        core.read_stable_file(path, maximum=1024 * 1024) != pass_payload
        or core.read_stable_file(result_path, maximum=8 * 1024 * 1024)
        != result_payload
        or any(
            core.read_stable_file(
                evidence_path,
                maximum=MAX_OBSERVER_BYTES if payload else 8 * 1024 * 1024,
            )
            != payload
            for evidence_path, payload in reopened.items()
        )
    ):
        raise GateError("R4W1-C connected evidence changed during reopen")
    return record


def _connected_dry_run_locked(
    root: Path,
    args: argparse.Namespace,
    artifacts: dict[str, Any],
    policy: dict[str, Any],
    run_dir: Path,
    lease: Any,
) -> int:
    pass_path = root / PASS_STATE
    timeline_path = run_dir / "timeline.json"
    timeline: list[dict[str, str]] = []
    core.append_event(timeline_path, timeline, "live_session_start")
    baseline = connected_preflight(
        root,
        run_dir,
        resolve(root, args.odin),
        odin_absence_wait_sec=args.odin_absence_wait_sec,
        lease=lease,
    )
    core.append_remaining_events(timeline_path, timeline)
    current_policy = verify_policy_draft(root)
    if current_policy != policy:
        raise GateError("R4W1-C connected policy identity changed during run")
    if helper_sha256(root) != policy["helper_sha256"] or test_sha256(root) != policy[
        "test_sha256"
    ]:
        raise GateError("R4W1-C connected source identity changed during run")
    preflight_path = run_dir / "connected_preflight.json"
    evidence = {
        "timeline": {
            "path": str(timeline_path.relative_to(root)),
            **core.hash_stable_file(timeline_path),
        },
        "preflight": {
            "path": str(preflight_path.relative_to(root)),
            **core.hash_stable_file(preflight_path),
        },
    }
    result = {
        "schema": SCHEMA,
        "mode": "connected-read-only-dry-run",
        "target": TARGET,
        "artifacts": artifacts,
        "baseline": baseline,
        "runtime_pins": {
            "helper_sha256": policy["helper_sha256"],
            "test_sha256": policy["test_sha256"],
            "policy_draft_sha256": policy["sha256"],
            "policy_clause_sha256": policy["policy_clause_sha256"],
        },
        "evidence": evidence,
        "timeline_semantics": {
            "candidate_flash_start": "zero-action phase; no candidate transfer",
            "candidate_flash_done": "zero-action phase; no candidate transfer",
            "candidate_boot_ready": "normal Magisk Android baseline observed",
            "rollback_flash_start": "zero-action phase; no rollback transfer",
            "rollback_flash_done": "zero-action phase; no rollback transfer",
            "rollback_boot_ready": "same normal Magisk Android baseline retained",
        },
        "device_contact": True,
        "device_writes": False,
        "reboot": False,
        "download_transition": False,
        "odin_transfer": False,
        "flash": False,
        "verdict": VERDICT,
    }
    result_path = run_dir / "result.json"
    validate_connected_result(
        result,
        artifacts,
        root=root,
        result_path=result_path,
    )
    core.durable_write_json(result_path, result)
    record = {
        "schema": PASS_SCHEMA,
        "target": TARGET,
        "created_at_utc": core.utc_now(),
        "helper_sha256": helper_sha256(root),
        "test_sha256": test_sha256(root),
        "live_core_sha256": EXPECTED_LIVE_CORE_SHA256,
        "odin_core_sha256": EXPECTED_ODIN_CORE_SHA256,
        "policy_draft_sha256": policy["sha256"],
        "policy_clause_sha256": policy["policy_clause_sha256"],
        "result_path": str(result_path.relative_to(root)),
        "result_size": result_path.stat().st_size,
        "result_sha256": core.sha256_file(result_path),
        "verdict": VERDICT,
        "device_writes": False,
    }
    require_direct_path(
        root,
        pass_path.parent,
        "R4W1-C connected PASS state directory",
        directory=True,
    )
    core.durable_create_json(pass_path, record)
    validate_connected_pass(root, expected_artifacts=artifacts)
    print(json.dumps({"run_dir": str(run_dir), "verdict": VERDICT}, indent=2))
    return 0


def connected_dry_run(
    root: Path,
    args: argparse.Namespace,
    artifacts: dict[str, Any],
    policy: dict[str, Any],
) -> int:
    current_policy = verify_policy_draft(root)
    if current_policy != policy:
        raise GateError("R4W1-C connected policy identity changed before run")
    if not policy_active(root) or policy.get("active") is not True:
        raise GateError("R4W1-C connected policy is inactive")
    if policy.get("policy_clause_sha256") is None:
        raise GateError("R4W1-C connected policy identity is missing")
    if args.ack != ACK_TOKEN:
        raise GateError("R4W1-C connected acknowledgement mismatch")
    pass_path = root / PASS_STATE
    require_direct_path(
        root,
        pass_path.parent,
        "R4W1-C connected PASS state directory",
        directory=True,
    )
    if pass_path.exists() or pass_path.is_symlink():
        raise GateError("R4W1-C connected PASS state already exists")
    run_dir = core.allocate_run_dir(root, RUN_ROOT, "s22plus-r4w1c-connected", args.run_dir)
    with odin_core.transaction_session(run_dir) as lease:
        return _connected_dry_run_locked(
            root,
            args,
            artifacts,
            policy,
            run_dir,
            lease,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--offline-check", action="store_true")
    modes.add_argument("--connected-read-only-dry-run", action="store_true")
    parser.add_argument("--ack")
    parser.add_argument("--candidate-boot", type=Path, default=DEFAULT_CANDIDATE_BOOT)
    parser.add_argument("--candidate-lz4", type=Path, default=DEFAULT_CANDIDATE_LZ4)
    parser.add_argument("--candidate-ap", type=Path, default=DEFAULT_CANDIDATE_AP)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--static-result", type=Path, default=DEFAULT_STATIC_RESULT)
    parser.add_argument("--magisk-ap", type=Path, default=DEFAULT_MAGISK_AP)
    parser.add_argument("--stock-ap", type=Path, default=DEFAULT_STOCK_AP)
    parser.add_argument("--full-firmware", type=Path, default=DEFAULT_FULL_FIRMWARE)
    parser.add_argument("--odin", type=Path, default=DEFAULT_ODIN)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--odin-absence-wait-sec", type=float, default=15.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root()
    try:
        if not (0.1 <= args.odin_absence_wait_sec <= 30.0):
            raise GateError("Odin absence wait must be between 0.1 and 30 seconds")
        artifacts = verify_artifacts(root, args)
        policy = verify_policy_draft(root)
        if args.offline_check:
            print(json.dumps({
                "schema": SCHEMA,
                "mode": "offline-check",
                "target": TARGET,
                "artifacts": artifacts,
                "policy": policy,
                "connected_pass_present": (root / PASS_STATE).is_file(),
                "device_contact": False,
                "device_writes": False,
                "reboot": False,
                "download_transition": False,
                "odin_transfer": False,
                "flash": False,
                "verdict": OFFLINE_VERDICT,
            }, indent=2))
            return 0
        return connected_dry_run(root, args, artifacts, policy)
    except (
        GateError,
        core.LiveCoreError,
        odin_core.OdinTransitionError,
        transport.GateError,
        OSError,
        subprocess.SubprocessError,
        tarfile.TarError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        print(
            json.dumps(
                {"schema": SCHEMA, "verdict": "FAIL_CLOSED", "error": str(exc)},
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
