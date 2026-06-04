#!/usr/bin/env python3
"""V2107 rollbackable handoff for TFTP persist-RFS parent traversal parity."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import native_wifi_tftp_process_namespace_audit_handoff_v2103 as prev2103


CYCLE = "V2107"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "tmp" / "wifi" / "v2107-tftp-persist-parent-traverse-handoff"
HANDOFF_DIR = OUT_DIR / "v2106-handoff"
HANDOFF_REPORT = OUT_DIR / "v2106-handoff-report.md"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V2107_TFTP_PERSIST_PARENT_TRAVERSE_HANDOFF_2026-06-05.md"
)
V2106_OUT = REPO_ROOT / "tmp" / "wifi" / "v2106-tftp-persist-parent-traverse-test-boot"
V2106_INIT = V2106_OUT / "init_v2106_tftp_persist_parent_traverse"
V2106_BOOT = V2106_OUT / "boot_linux_v2106_tftp_persist_parent_traverse.img"
REMOTE_PROPERTY_ROOT = "/mnt/sdext/a90/private-property-v317/v2106/dev/__properties__"
TEST_EXPECT_VERSION = "A90 Linux init 0.9.229 (v2106-tftp-persist-parent-traverse)"
TEST_LOG_PATH = "/cache/native-init-wifi-test-boot-v2106.log"
TEST_SUMMARY_PATH = "/cache/native-init-wifi-test-boot-v2106.summary"
TEST_HELPER_RESULT_PATH = "/cache/native-init-wifi-test-boot-v2106-helper.result"
EXPECTED_HELPER_VERSION = "a90_android_execns_probe v413"


def rel(path: Path) -> str:
    return prev2103.rel(path)


def intish(value: object) -> int:
    return prev2103.intish(value)


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    return prev2103.markdown_table(headers, rows)


def artifact_hook_check() -> dict[str, Any]:
    init_forbidden = (
        "--allow-servloc-domain-list-probe",
        "--allow-service-notifier-listener-probe",
        "--qrtr-readback-matrix",
        "wlfw:69:0,1",
        "--pm-observer-private-cnss-daemon-sdx50m",
        "--private-cnss-daemon-path",
    )
    boot_forbidden = (
        "diag_remote_dev_poll_probe.begin=1",
        "diag_wlan_pd_memory_device_probe.begin=1",
        "diag_wlan_pd_memory_regular_mask_probe.begin=1",
        "diag_dci_register_read_probe.begin=1",
        "wlan_pd_tftp_server_trace.late_attach.begin=1",
        "wifi_companion_start.wlan_pd_producer_tftp_server_syscall_trace.compiled=1",
        "wifi_companion_start.macloader_syscall_trace.compiled=1",
        "PTRACE_ATTACH",
        "post_bdf_boot_wlan_consumer_gate.begin=1",
    )
    init_required = (
        "native-init-sibling-fwssctl-v641",
        "A90v641: sibling fwssctl proof armed",
        "wifi-v641-fwssctl",
        "A90v2106",
        "wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only",
        "--timeout-sec",
        "75",
    )
    boot_required = (
        EXPECTED_HELPER_VERSION,
        "wifi_companion_start.tftp_persist_rfs_parent_traverse_parity.enabled=%d",
        "wifi_companion_start.tftp_persist_rfs_parent_traverse_parity.paths=/mnt,/mnt/vendor,/mnt/vendor/persist",
        "wifi_companion_start.tftp_persist_rfs_parent_traverse_parity.owner=root:system",
        "wifi_companion_start.tftp_process_namespace_audit.compiled=%d",
        "persist_rfs_shared",
        "persist_rfs_msm_mpss",
        "persist_rfs_msm_adsp",
        "tftp_ready_before_wlfw_vote.mode=alive-socket-plus-android-order-settle",
        "tftp_logdw_sink.order_timestamps=1",
        "per_mgr_vote_focused.begin=1",
        "wlfw_late_msg21_focused.begin=1",
        "icnss_qcacld_post_bdf_focused",
    )
    checks: dict[str, Any] = {}
    for path, required in ((V2106_INIT, init_required), (V2106_BOOT, boot_required)):
        key = rel(path)
        forbidden_tokens = init_forbidden if path == V2106_INIT else boot_forbidden
        data = path.read_bytes() if path.exists() else b""
        missing = [token for token in required if token.encode() not in data]
        forbidden = [token for token in forbidden_tokens if token.encode() in data]
        checks[key] = {
            "exists": path.exists(),
            "ok": path.exists() and not missing and not forbidden,
            "missing": missing,
            "forbidden": forbidden,
        }
    return checks


def collect_namespace(fields: dict[str, str]) -> dict[str, Any]:
    ns = prev2103.collect_namespace(fields)
    paths = ns.get("paths") if isinstance(ns.get("paths"), dict) else {}
    parent_names = ("mnt", "mnt_vendor", "persist")
    for name in parent_names:
        paths[name] = prev2103.ns_path(fields, name)
    ns["paths"] = paths
    ns["parents_traversable_for_tftp"] = all(
        isinstance(paths.get(name), dict)
        and str(paths[name].get("mode")) == "0750"
        and intish(paths[name].get("uid")) == 0
        and intish(paths[name].get("gid")) == 1000
        for name in parent_names
    )
    ns["parent_names"] = list(parent_names)
    return ns


def collect_details(handoff: dict[str, Any]) -> dict[str, Any]:
    details = prev2103.prev2101.collect_details(handoff)
    fields = prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.prev2059.prev2057.parse_fields()
    details["tftp_process_namespace_audit"] = collect_namespace(fields)
    details["parent_traverse_marker"] = {
        "enabled": intish(fields.get("wifi_companion_start.tftp_persist_rfs_parent_traverse_parity.enabled")),
        "paths": fields.get("wifi_companion_start.tftp_persist_rfs_parent_traverse_parity.paths", ""),
        "owner": fields.get("wifi_companion_start.tftp_persist_rfs_parent_traverse_parity.owner", ""),
        "mode": fields.get("wifi_companion_start.tftp_persist_rfs_parent_traverse_parity.mode", ""),
    }
    return details


def classify(handoff: dict[str, Any],
             hook: dict[str, Any],
             steps: list[dict[str, Any]],
             details: dict[str, Any]) -> dict[str, Any]:
    base = prev2103.prev2101.classify(handoff, hook, steps, details)
    ns = details.get("tftp_process_namespace_audit") if isinstance(details.get("tftp_process_namespace_audit"), dict) else {}
    branch = details.get("tftp_tombstone_branch") if isinstance(details.get("tftp_tombstone_branch"), dict) else {}
    cascade = details.get("cascade") if isinstance(details.get("cascade"), dict) else {}
    marker = details.get("parent_traverse_marker") if isinstance(details.get("parent_traverse_marker"), dict) else {}
    hook_ok = all(bool(item.get("ok")) for item in hook.values())
    marker_enabled = intish(marker.get("enabled")) == 1
    persist_auto_dir = intish(base.get("persist_auto_dir_error_count"))
    persist_mkdir = intish(base.get("persist_mkdir_failed_count"))
    parents_ok = bool(ns.get("parents_traversable_for_tftp"))
    wlanmdsp_seen = bool(base.get("wlanmdsp_seen"))
    ota_seen = bool(base.get("ota_seen"))
    server_payload = str(branch.get("server_check", {}).get("payload", ""))
    fw_ready = intish(cascade.get("fw_ready")) > 0
    wlan0 = intish(cascade.get("wlan0")) > 0

    if not hook_ok:
        label = "persist-parent-traverse-artifact-hook-regression"
        passed = False
        reason = "V2106 artifact does not contain the bounded parent-traversal contract"
    elif not marker_enabled:
        label = "persist-parent-traverse-test-boot-not-executed"
        passed = False
        reason = "V2106 helper runtime markers are absent; the handoff failed before a valid producer-window test boot"
    elif intish(ns.get("audit_ok")) != 1:
        label = "persist-parent-traverse-audit-missing"
        passed = False
        reason = "stock tftp_server process namespace audit did not complete"
    elif not parents_ok:
        label = "persist-parent-traverse-not-applied"
        passed = False
        reason = "tftp_server process root did not show `/mnt*` parent dirs as root:system 0750"
    elif wlan0:
        label = "persist-parent-traverse-wlan0-progress"
        passed = True
        reason = "native reached wlan0; stop before scan/connect and run the dedicated connectivity gate"
    elif fw_ready:
        label = "persist-parent-traverse-fw-ready-progress"
        passed = True
        reason = "native reached FW_READY; chase wlan0 next"
    elif wlanmdsp_seen:
        label = "persist-parent-traverse-wlanmdsp-progress"
        passed = True
        reason = "parent traversal parity allowed a wlanmdsp tftp request"
    elif ota_seen:
        label = "persist-parent-traverse-ota-progress-no-wlanmdsp"
        passed = True
        reason = "parent traversal parity reached ota_firewall but not wlanmdsp"
    elif persist_auto_dir > 0 or persist_mkdir > 0:
        label = "persist-parent-traverse-eacces-persists"
        passed = True
        reason = "parent traversal parity applied, but persist-RFS auto-dir EACCES remains"
    elif server_payload == "hello":
        label = "persist-parent-traverse-clears-eacces-post-up-server-check"
        passed = True
        reason = "persist-RFS EACCES cleared, but native still only shows late post-UP server_check and no ota/wlanmdsp"
    else:
        label = "persist-parent-traverse-clears-eacces-no-early-branch"
        passed = True
        reason = "persist-RFS EACCES cleared, but Android-order tftp bootstrap still did not appear"

    return {
        **base,
        "decision": f"v2107-{label}-rollback-{'pass' if passed else 'blocked'}",
        "label": label,
        "pass": passed,
        "reason": reason,
        "hook_ok": hook_ok,
        "parent_traverse_marker_enabled": marker_enabled,
        "namespace_audit_ok": intish(ns.get("audit_ok")),
        "tftp_pid": intish(ns.get("pid")),
        "parents_traversable_for_tftp": parents_ok,
        "all_persist_targets_visible": bool(ns.get("all_persist_targets_visible")),
        "mountinfo_match_count": intish(ns.get("mountinfo_match_count")),
        "persist_auto_dir_error_count": persist_auto_dir,
        "persist_mkdir_failed_count": persist_mkdir,
        "server_check_payload": server_payload,
        "server_after_wlan_pd_ms": branch.get("server_after_wlan_pd_ms"),
    }


def render_report(manifest: dict[str, Any]) -> str:
    details = manifest["details"]
    classification = manifest["classification"]
    ns = details.get("tftp_process_namespace_audit", {}) if isinstance(details.get("tftp_process_namespace_audit"), dict) else {}
    paths = ns.get("paths", {}) if isinstance(ns.get("paths"), dict) else {}
    cascade = details.get("cascade", {}) if isinstance(details.get("cascade"), dict) else {}
    marker = details.get("parent_traverse_marker", {}) if isinstance(details.get("parent_traverse_marker"), dict) else {}
    step_lines = [
        f"- `{step['name']}` rc `{step['rc']}` ok `{step['ok']}` evidence `{step['file']}`"
        for step in manifest["steps"]
    ]
    return "\n".join([
        "# Native Init V2107 TFTP Persist Parent Traverse Handoff",
        "",
        "## Summary",
        "",
        "- Cycle: `V2107`",
        f"- Decision: `{manifest['decision']}`",
        f"- Label: `{manifest['label']}`",
        f"- Pass: `{manifest['pass']}`",
        f"- Reason: {manifest['reason']}",
        f"- Evidence: `{manifest['out_dir']}`",
        f"- Inner handoff: `{manifest['handoff_manifest']}`",
        "",
        "## Matrix",
        "",
        markdown_table(
            ["area", "value", "detail"],
            [
                ["artifact", classification.get("hook_ok"), f"helper={EXPECTED_HELPER_VERSION}"],
                ["parent_traverse", classification.get("parents_traversable_for_tftp"), f"marker={marker}"],
                ["namespace_audit", classification.get("namespace_audit_ok"), f"pid={classification.get('tftp_pid')} root={ns.get('root_target')}"],
                ["persist_targets_visible", classification.get("all_persist_targets_visible"), f"mountinfo_matches={classification.get('mountinfo_match_count')}"],
                ["persist_auto_dir", classification.get("persist_auto_dir_error_count"), f"mkdir_failed={classification.get('persist_mkdir_failed_count')}"],
                ["server_check", classification.get("server_check_payload"), f"after_wlan_pd_ms={classification.get('server_after_wlan_pd_ms')}"],
                ["cascade", "", f"wlan_pd={cascade.get('wlan_pd_up')} icnss_qmi={cascade.get('icnss_qmi_connected')} fw_ready={cascade.get('fw_ready')} wlan0={cascade.get('wlan0')}"],
            ],
        ),
        "",
        "## Process-Root Paths",
        "",
        markdown_table(
            ["path", "exists", "dir", "mode", "uid", "gid", "errno"],
            [
                [name, item.get("exists"), item.get("is_dir"), item.get("mode"), item.get("uid"), item.get("gid"), item.get("errno")]
                for name, item in paths.items()
                if isinstance(item, dict)
            ],
        ),
        "",
        "## Interpretation",
        "",
        "- V2103 exposed a concrete AP-infra miss: the leaf persist-RFS dirs were visible, but `/mnt`, `/mnt/vendor`, and `/mnt/vendor/persist` were `0750 root:root`, so stock `tftp_server` as `vendor_rfs` could not traverse to them.",
        "- V2107 changes only those private-root parent dirs to `root:system 0750`; the stock process has supplemental group `system`, so this is the minimal parent traversal parity fix.",
        "- If EACCES clears without early `ota_firewall/wlanmdsp`, the remaining gate is modem-internal before the WLAN-PD firmware fetch branch.",
        "",
        "## Steps",
        "",
        *step_lines,
        *([] if step_lines else ["- `none`"]),
        "",
        "## Safety",
        "",
        "- No Wi-Fi HAL, wificond, supplicant, hostapd, scan/connect, credentials, DHCP/routes, or external ping was used.",
        "- No macloader retry, DIAG, rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR readback, QMI payload send, or `tftp_server` ptrace was run.",
        "- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.",
        "- Mutation scope: `/cache` one-shot clean-DSP flag, V2106 test-boot flash-handoff, namespace-local RFS bridges/tmpfs mirrors, namespace-local `/mnt*` parent chmod/chown in the private rootfs, read-only tftp process-root audit, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.",
        "",
    ])


def configure_prev2081() -> None:
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.CYCLE = CYCLE
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.OUT_DIR = OUT_DIR
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.HANDOFF_DIR = HANDOFF_DIR
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.HANDOFF_REPORT = HANDOFF_REPORT
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.REPORT_PATH = REPORT_PATH
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.V2080_OUT = V2106_OUT
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.V2080_INIT = V2106_INIT
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.V2080_BOOT = V2106_BOOT
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.REMOTE_PROPERTY_ROOT = REMOTE_PROPERTY_ROOT
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.TEST_EXPECT_VERSION = TEST_EXPECT_VERSION
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.TEST_LOG_PATH = TEST_LOG_PATH
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.TEST_SUMMARY_PATH = TEST_SUMMARY_PATH
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.TEST_HELPER_RESULT_PATH = TEST_HELPER_RESULT_PATH
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.EXPECTED_HELPER_VERSION = EXPECTED_HELPER_VERSION
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.artifact_hook_check = artifact_hook_check
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.collect_details = collect_details
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.classify = classify
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.render_report = render_report
    prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.configure_prev2059()


def main(argv: list[str] | None = None) -> int:
    configure_prev2081()
    return prev2103.prev2101.prev2098.prev2096.prev2083.prev2081.prev2059.main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
