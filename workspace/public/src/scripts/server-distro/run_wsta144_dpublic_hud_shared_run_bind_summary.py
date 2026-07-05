#!/usr/bin/env python3
"""WSTA144 host-only summary for the D-public HUD handoff live proof.

The live work already happened in a private run directory: V3401 was flashed
through the checked helper, the durable native HUD presenter survived the Debian
handoff, the shared /run/a90-dpublic bind was proven, and Debian a90hud wrote a
fresh intent consumed by the preserved native presenter.  This script performs
no device action.  It re-reads private transcripts and emits a compact redacted
proof JSON that WSTA108 can consume.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prepare_wsta3_sta_rootfs as wsta3  # noqa: E402


REPO_ROOT = wsta3.REPO_ROOT
PRIVATE_ROOT = REPO_ROOT / "workspace/private"
DEFAULT_RUN_BASE = wsta3.DEFAULT_RUN_BASE
PASS_DECISION = "wsta144-dpublic-hud-shared-run-bind-live-pass"
RESULT_NAME = "wsta144_dpublic_hud_shared_run_bind_live.json"

INIT_VERSION = "0.11.157"
INIT_BUILD = "v3401-dpublic-hud-shared-run-bind"
BOOT_SHA256 = "d9496d565af554f4fb30a9064c1998356b27396163b7cc67fd693db8a3a8e418"
BOOT_IMAGE = "workspace/private/inputs/boot_images/boot_linux_v3401_dpublic_hud_shared_run_bind.img"
INTENT_SCHEMA = "a90-dpublic-hud-intent-v1"
PRE_HANDOFF_SEQUENCE = 14400
DEBIAN_SEQUENCE = 14401


def rel(path: Path) -> str:
    return wsta3.rel(path)


def utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text)
    if not match:
        return None
    return int(match.group(1), 10)


def section(text: str, begin: str, end: str) -> str:
    start = text.find(begin)
    if start < 0:
        return ""
    start += len(begin)
    finish = text.find(end, start)
    if finish < 0:
        return text[start:]
    return text[start:finish]


def drm_fd_lines(text: str, block_begin: str, block_end: str) -> list[str]:
    block = section(text, block_begin, block_end)
    return [line.strip() for line in block.splitlines() if line.startswith("DRMFD ")]


def safety() -> dict[str, Any]:
    return {
        "device_action": False,
        "boot_flash": False,
        "native_reboot": False,
        "wifi_connect": False,
        "dhcp": False,
        "public_tunnel": False,
        "public_smoke": False,
        "packet_filter_mutation": False,
        "userdata_touch": False,
        "switch_root": False,
        "debian_direct_kms": False,
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }


def collect_from_source(source_run_dir: Path) -> dict[str, Any]:
    files = {
        "flash": source_run_dir / "flash-v3401-retry.txt",
        "start": source_run_dir / "presenter-start-before-handoff.txt",
        "status": source_run_dir / "presenter-status-before-handoff.txt",
        "pre_intent": source_run_dir / "presenter-files-after-pre-intent.txt",
        "switch_root": source_run_dir / "switch-root-to-userdata.txt",
        "ssh_wait": source_run_dir / "wait-for-debian-ssh.txt",
        "debian": source_run_dir / "debian-handoff-proof.txt",
        "final_version": source_run_dir / "native-version-after-reboot.txt",
        "final_selftest": source_run_dir / "native-selftest-after-reboot.txt",
        "final_status": source_run_dir / "native-status-after-reboot.txt",
    }
    texts = {name: read_text(path) if path.is_file() else "" for name, path in files.items()}
    presenter_pid = extract_int(r"A90WSTA140 start\.pid=(\d+)", texts["start"])
    pre_sequence = extract_int(r"last_sequence=(\d+)", texts["pre_intent"])
    pre_present_rc = extract_int(r"present_rc=(-?\d+)", texts["pre_intent"])
    debian_status_before = section(texts["debian"], "status_before_begin", "status_before_end")
    debian_status_after = section(texts["debian"], "status_after_begin", "status_after_end")
    shared_devs = re.findall(r"stat_dev=([0-9a-fA-F]+)", texts["debian"])
    shared_inos = re.findall(r"stat_ino=(\d+)", texts["debian"])
    shared_fstypes = re.findall(r"fs_type=([^\s]+)", texts["debian"])
    drm_before = drm_fd_lines(texts["debian"], "drm_scan_before_begin", "drm_scan_before_end")
    drm_after = drm_fd_lines(texts["debian"], "drm_scan_after_begin", "drm_scan_after_end")

    proof = {
        "schema": "a90-wsta144-dpublic-hud-shared-run-bind-live-v1",
        "source_run_dir": rel(source_run_dir),
        "candidate": {
            "init_version": INIT_VERSION,
            "init_build": INIT_BUILD,
            "boot_image": BOOT_IMAGE,
            "boot_sha256": BOOT_SHA256,
        },
        "checked_flash": {
            "helper": "native_init_flash.py",
            "used_checked_helper": "native-init-flash" in texts["flash"],
            "local_sha_match": f"local image sha256: {BOOT_SHA256}" in texts["flash"],
            "remote_sha_match": f"remote image sha256: {BOOT_SHA256}" in texts["flash"],
            "boot_readback_sha_match": f"boot block prefix sha256: {BOOT_SHA256}" in texts["flash"],
            "booted_v3401": f"A90 Linux init {INIT_VERSION} ({INIT_BUILD})" in texts["flash"],
            "boot_ok": "boot: BOOT OK" in texts["flash"],
            "selftest_fail_zero": "selftest: pass=12 warn=1 fail=0" in texts["flash"],
            "transport_serial_ready": "transport.serial=ready" in texts["flash"],
            "transport_tcpctl_ready": "transport.tcpctl=ready" in texts["flash"],
        },
        "native_presenter_pre_handoff": {
            "pid": presenter_pid,
            "shared_run_marker": "A90WSTA144 shared_run_dir=shared-run-dir-bind-before-switch-root" in texts["start"],
            "shared_run_tmpfs_mounted": "A90WSTA144 shared_run_dir=mounted path=/run/a90-dpublic fstype=tmpfs" in texts["start"],
            "status_drm_fd": "A90WSTA140 status.drm_fd=1" in texts["status"],
            "debian_direct_kms_zero": "A90WSTA140 status.debian_direct_kms=0" in texts["status"],
            "pre_sequence": pre_sequence,
            "pre_present_rc": pre_present_rc,
        },
        "handoff": {
            "switch_root_exec_reached": "A90D4 exec_switch_root_now" in texts["switch_root"],
            "presenter_preserved": (
                presenter_pid is not None
                and f"drm_owner_pid={presenter_pid} action=preserve-dpublic-hud-presenter" in texts["switch_root"]
            ),
            "stale_drm_owners_killed": "A90D4 handoff_display=done killed=3 rc=0" in texts["switch_root"],
            "shared_run_bind_ok": "A90WSTA144 shared_run_bind=ok" in texts["switch_root"],
            "shared_run_same_dev": "same_dev=1" in texts["switch_root"],
            "shared_run_same_ino": "same_ino=1" in texts["switch_root"],
            "firstboot_intent_presented": "dpublic-hud-presenter-service: presented framebuffer 1080x2400 on crtc=133" in texts["switch_root"],
        },
        "debian": {
            "ssh_ready": "A90WSTA144_SSH_READY" in texts["ssh_wait"],
            "pid1_comm_init": "pid1_comm=init" in texts["debian"],
            "proc1_exe_usr_sbin_init": "proc1_exe=/usr/sbin/init" in texts["debian"],
            "debian_version": re.search(r"debian_version=([^\n]+)", texts["debian"]).group(1)
            if re.search(r"debian_version=([^\n]+)", texts["debian"]) else None,
            "root_is_userdata_ext4": "root_findmnt=/dev/block/a90-userdata ext4 /" in texts["debian"],
            "run_dir_root_a90hud_1770": "run_dir_stat=root a90hud 1770" in texts["debian"],
        },
        "shared_run_compare": {
            "debian_path": "/run/a90-dpublic",
            "presenter_root_path": f"/proc/{presenter_pid}/root/run/a90-dpublic" if presenter_pid else None,
            "same_dev": len(shared_devs) >= 2 and len(set(shared_devs[:2])) == 1,
            "same_ino": len(shared_inos) >= 2 and len(set(shared_inos[:2])) == 1,
            "tmpfs": shared_fstypes.count("tmpfs") >= 2,
            "root_a90hud_1770": "stat_mode=1770 stat_owner=root:a90hud" in texts["debian"],
        },
        "drm_ownership": {
            "presenter_alive": "presenter_alive=1" in texts["debian"],
            "presenter_pid": presenter_pid,
            "presenter_exe_deleted": "presenter_exe=/init (deleted)" in texts["debian"],
            "presenter_has_card0_fd": (
                presenter_pid is not None
                and f"PRESENTERFD fd=3 target=/dev/dri/card0 (deleted)" in texts["debian"]
            ),
            "drm_before_lines": drm_before,
            "drm_after_lines": drm_after,
            "sole_drm_owner_before": len(drm_before) == 1 and presenter_pid is not None and f"pid={presenter_pid}" in drm_before[0],
            "sole_drm_owner_after": len(drm_after) == 1 and presenter_pid is not None and f"pid={presenter_pid}" in drm_after[0],
        },
        "a90hud_intent_writer": {
            "identity": "a90hud_identity=a90hud:x:3904:3904" in texts["debian"],
            "launcher_exec": "a90_service_launcher_decision=exec" in texts["debian"],
            "no_network_intent": "a90_service_launcher_network_intent=no-network-intent-producer-only" in texts["debian"],
            "no_new_privs": "a90_service_launcher_no_new_privs=1" in texts["debian"],
            "uid_3904": "launched_uid=3904" in texts["debian"],
            "gid_3904": "launched_gid=3904" in texts["debian"],
            "cap_eff_zero": "launched_cap_eff=0000000000000000" in texts["debian"],
            "no_drm_fd": "A90HUDFD" in texts["debian"] and "/dev/dri" not in section(texts["debian"], "launched_fd_begin", "launched_fd_end"),
            "intent_written": "A90WSTA132_INTENT_WRITTEN=1" in texts["debian"],
            "intent_sequence": extract_int(r"A90WSTA132_INTENT_SEQUENCE=(\d+)", texts["debian"]),
            "intent_owner_a90hud": "intent_after_stat=a90hud a90hud 640" in texts["debian"],
            "intent_schema": INTENT_SCHEMA if f"\"schema\":\"{INTENT_SCHEMA}\"" in texts["debian"] else None,
        },
        "presenter_consumption": {
            "status_before_sequence": extract_int(r"last_sequence=(\d+)", debian_status_before),
            "status_before_present_rc": extract_int(r"present_rc=(-?\d+)", debian_status_before),
            "status_after_sequence": extract_int(r"last_sequence=(\d+)", debian_status_after),
            "status_after_present_rc": extract_int(r"present_rc=(-?\d+)", debian_status_after),
            "fresh_debian_intent_consumed": f"last_sequence={DEBIAN_SEQUENCE}" in debian_status_after,
        },
        "final_health": {
            "v3401_resident": f"A90 Linux init {INIT_VERSION} ({INIT_BUILD})" in texts["final_version"],
            "selftest_fail_zero": "selftest: pass=12 warn=1 fail=0" in texts["final_selftest"],
            "transport_serial_ready": "transport.serial=ready" in texts["final_status"],
            "transport_tcpctl_ready": "transport.tcpctl=ready" in texts["final_status"],
        },
        "public_url_value_logged": False,
        "secret_values_logged": 0,
    }
    proof["checks"] = validate_proof(proof)
    proof["decision"] = PASS_DECISION if all(proof["checks"].values()) else "wsta144-dpublic-hud-shared-run-bind-live-fail"
    return proof


def validate_proof(proof: dict[str, Any]) -> dict[str, bool]:
    candidate = proof.get("candidate") if isinstance(proof.get("candidate"), dict) else {}
    checked_flash = proof.get("checked_flash") if isinstance(proof.get("checked_flash"), dict) else {}
    native = proof.get("native_presenter_pre_handoff") if isinstance(proof.get("native_presenter_pre_handoff"), dict) else {}
    handoff = proof.get("handoff") if isinstance(proof.get("handoff"), dict) else {}
    debian = proof.get("debian") if isinstance(proof.get("debian"), dict) else {}
    shared = proof.get("shared_run_compare") if isinstance(proof.get("shared_run_compare"), dict) else {}
    drm = proof.get("drm_ownership") if isinstance(proof.get("drm_ownership"), dict) else {}
    writer = proof.get("a90hud_intent_writer") if isinstance(proof.get("a90hud_intent_writer"), dict) else {}
    consumption = proof.get("presenter_consumption") if isinstance(proof.get("presenter_consumption"), dict) else {}
    final_health = proof.get("final_health") if isinstance(proof.get("final_health"), dict) else {}
    return {
        "candidate_is_v3401": (
            candidate.get("init_version") == INIT_VERSION
            and candidate.get("init_build") == INIT_BUILD
            and candidate.get("boot_sha256") == BOOT_SHA256
        ),
        "checked_flash_used": bool(checked_flash.get("used_checked_helper")),
        "checked_flash_sha_matched": bool(
            checked_flash.get("local_sha_match")
            and checked_flash.get("remote_sha_match")
            and checked_flash.get("boot_readback_sha_match")
        ),
        "checked_flash_boot_health_clean": bool(
            checked_flash.get("booted_v3401")
            and checked_flash.get("boot_ok")
            and checked_flash.get("selftest_fail_zero")
            and checked_flash.get("transport_serial_ready")
            and checked_flash.get("transport_tcpctl_ready")
        ),
        "native_shared_run_mounted": bool(
            native.get("shared_run_marker")
            and native.get("shared_run_tmpfs_mounted")
            and native.get("status_drm_fd")
            and native.get("debian_direct_kms_zero")
        ),
        "native_pre_handoff_presented": bool(
            native.get("pre_sequence") == PRE_HANDOFF_SEQUENCE
            and native.get("pre_present_rc") == 0
        ),
        "handoff_preserved_presenter_and_bound_shared_run": bool(
            handoff.get("switch_root_exec_reached")
            and handoff.get("presenter_preserved")
            and handoff.get("stale_drm_owners_killed")
            and handoff.get("shared_run_bind_ok")
            and handoff.get("shared_run_same_dev")
            and handoff.get("shared_run_same_ino")
        ),
        "debian_pid1_userdata_root": bool(
            debian.get("ssh_ready")
            and debian.get("pid1_comm_init")
            and debian.get("proc1_exe_usr_sbin_init")
            and debian.get("root_is_userdata_ext4")
            and debian.get("run_dir_root_a90hud_1770")
        ),
        "shared_run_same_mount_after_handoff": bool(
            shared.get("same_dev")
            and shared.get("same_ino")
            and shared.get("tmpfs")
            and shared.get("root_a90hud_1770")
        ),
        "presenter_sole_drm_owner_after_handoff": bool(
            drm.get("presenter_alive")
            and drm.get("presenter_has_card0_fd")
            and drm.get("sole_drm_owner_before")
            and drm.get("sole_drm_owner_after")
        ),
        "a90hud_intent_writer_sandboxed": bool(
            writer.get("identity")
            and writer.get("launcher_exec")
            and writer.get("no_network_intent")
            and writer.get("no_new_privs")
            and writer.get("uid_3904")
            and writer.get("gid_3904")
            and writer.get("cap_eff_zero")
            and writer.get("no_drm_fd")
        ),
        "fresh_debian_intent_consumed": bool(
            writer.get("intent_written")
            and writer.get("intent_sequence") == DEBIAN_SEQUENCE
            and writer.get("intent_owner_a90hud")
            and writer.get("intent_schema") == INTENT_SCHEMA
            and consumption.get("status_after_sequence") == DEBIAN_SEQUENCE
            and consumption.get("status_after_present_rc") == 0
            and consumption.get("fresh_debian_intent_consumed")
        ),
        "final_health_clean": bool(
            final_health.get("v3401_resident")
            and final_health.get("selftest_fail_zero")
            and final_health.get("transport_serial_ready")
            and final_health.get("transport_tcpctl_ready")
        ),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    run_id = args.run_id or f"wsta144-dpublic-hud-shared-run-bind-summary-{utc_stamp()}"
    run_dir = resolve_path(args.run_dir or (DEFAULT_RUN_BASE / run_id))
    source_run_dir = resolve_path(args.source_run_dir)
    result: dict[str, Any] = {
        "schema": "a90-wsta144-live-summary-run-v1",
        "run_id": run_id,
        "run_dir": rel(run_dir),
        "source_run_dir": rel(source_run_dir),
        "started_utc": utc_stamp(),
        "decision": "wsta144-dpublic-hud-shared-run-bind-live-blocked",
        "safety": safety(),
    }
    if not is_under(run_dir, PRIVATE_ROOT) or not is_under(source_run_dir, PRIVATE_ROOT):
        result["decision"] = "wsta144-blocked-nonprivate-path"
        result["ended_utc"] = utc_stamp()
        return result
    if not source_run_dir.is_dir():
        result["decision"] = "wsta144-blocked-source-run-dir-missing"
        result["ended_utc"] = utc_stamp()
        return result

    proof = collect_from_source(source_run_dir)
    result.update(proof)
    result["run_id"] = run_id
    result["run_dir"] = rel(run_dir)
    result["source_run_dir"] = rel(source_run_dir)
    result["safety"] = safety()
    result["ended_utc"] = utc_stamp()
    write_json(run_dir / RESULT_NAME, result)
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--source-run-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("decision") == PASS_DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
