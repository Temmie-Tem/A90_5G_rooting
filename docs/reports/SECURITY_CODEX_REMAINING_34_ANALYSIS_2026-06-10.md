# Codex Security Remaining 34 Analysis

Date: 2026-06-10

## Inputs

- Latest CSV: `workspace/private/raw-logs/security/codex/2026-06-10/codex-security-findings-2026-06-10T13-27-23.601Z.csv`
- Prior plan: `workspace/private/outputs/security/codex/2026-06-10/codex_security_disposition_plan.json`

## Executive Summary

- This CSV (`...T13-27-23`) is a snapshot at the **V2189 promotion** (latest finding commit `eeb11b10`,
  15:57). It does **not** yet reflect `f16efca0 "Harden active security triage surfaces"` (committed 17:15,
  already in HEAD) or `e6f58aed`. So several listed findings are already fixed in source and will clear on
  the next Codex rescan.
- **Reconciliation against current tree (verified in code): 7/34 are now FIXED in HEAD/working tree.**
  See "Post-rescan reconciliation" below. The 2 high (#1, #2) split: #1 fixed, #2 is a dormant SDX50M mode.
- The remaining **~27 are non-active backlog**, not active-runtime blockers:
  - **~21 are `a90_android_execns_probe.c` helper modes that are NOT compiled into the promoted baseline.**
    The shipped V2189 helper runs only `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`;
    the flagged modes sit behind `#if A90_WIFI_TEST_BOOT_*` (229 such gates) and `local_security_rescan` S010
    confirms active builders do not define `-DA90_WIFI_TEST_BOOT` (source debt, not current binary behavior).
  - **~6 are host validation-runner evidence/reliability bugs** (redaction leak, out-of-repo path crash,
    wrong cleanup dir, approval-gate bypass, broken archive runner) — private-output / availability scope.
- Local targeted rescan on the current tree: **PASS=10, WARN=1, FAIL=0** (WARN = intentional trusted-lab
  USB-local/localhost root-control channels). No active-path P0/P1 reopened.

## Counts

- Severity: `{'high': 2, 'medium': 9, 'low': 11, 'informational': 12}`
- Family: `{'manual_validation_runner_backlog': 6, 'current_helper_trust_boundary': 1, 'manual_lab_boundary': 1, 'native_helper_legacy_mode_backlog': 23, 'active_host_infra_backlog': 2, 'new_tooling_bug': 1}`
- Prior priority/reachability: `{('P2', 'active_manual_validation_runner'): 6, ('P2', 'current_helper_packaged_trust_boundary'): 1, ('P2', 'manual_lab_tool'): 1, ('P2', 'current_helper_packaged_unproven_mode'): 22, ('P2', 'current_helper_mode_gated_unproven'): 1, ('P2', 'active_host_infra'): 2, ('NEW', 'NEW'): 1}`

## Post-rescan reconciliation (f16efca0 / current tree)

Verified in code. These clear on the next Codex rescan:

| # | sev | finding | fix in current tree | evidence |
|---:|---|---|---|---|
| 1 | high | Autostarted serial bridge remains exposed | bridge wrapper + `serial_tcp_bridge.py` default to `127.0.0.1`, pin Samsung ACM identity; tcpctl behind token auth | `a90_bridge.py:29` `DEFAULT_HOST="127.0.0.1"`; rescan S002/S003 PASS |
| 3 | med | Unauthenticated Wi-Fi upload receiver (LAN DoS) | token auth (`X-A90-Wifi-Lab-Token`), per-upload size cap, concurrent-client cap, idle timeout, peer allowlist | `a90_termux_wifi_lab.sh` (`...auth-limits-v3`) |
| 4 | med | Wildcard NCM transfer listeners (`::`) | scoped `fe80:` link-local bind with `if_nametoindex(ifname)` scope_id; host repair now opt-in (`A90_NCM_REPAIR_HOST_NET`) | `a90_ncm_transport.py:174-179,253,318` |
| 5 | med | V2167 supplicant without UID drop | `apply_wificond_identity_contract()` called before supplicant exec (drops gid/uid to AID_WIFI, restricts caps) | `helpers/a90_android_execns_probe.c` `start_supplicant_quiet` |
| 12 | low | Wi-Fi validation passes despite credential leak flags | `classify()` now fails when any `secret_values_logged`/`credentials_logged` flag is nonzero | `native_wifi_v2178_autoconnect_phase_validation.py:103-117` |
| 13 | low | Default searches hide live legacy imports | archive no longer on import path by default; opt-in via `A90_INCLUDE_ARCHIVE_REVALIDATION` | `_workspace_bootstrap.py:22-41` |
| 23 | info | Absolute `--out` crashes local rescan | `display_path()` returns absolute string when path is outside repo instead of raising `ValueError` | `local_security_rescan.py` (working tree, **uncommitted** — needs commit) |

Regression coverage added by `f16efca0`: `security_unit_a_regression.py`, `security_unit_b_regression.py`,
`security_tier2_regression.py`.

## Recommended Disposition

- **#23**: commit the working-tree `display_path()` fix in `local_security_rescan.py` (currently `M`, uncommitted).
- **#1/#3/#4/#5/#12/#13**: source-fixed; trigger a fresh Codex rescan to auto-close in the console. Do not bulk-close manually before the rescan confirms.
- **~21 execns helper modes (#2, #6–#11, #14–#20, #25, #27, #28, #30, #32, #33)**: single highest-leverage cleanup is to **trim / compile-gate the dead test-boot helper modes out of the shipped binary** rather than fix each dormant-mode bug. Rescan S010 already proves they are not compiled into the active baseline; document them as accepted source debt (`won't fix — not in promoted-baseline binary`) and track helper de-bloat as architecture work. `#2` is the abandoned SDX50M cnss-daemon mode and is moot per project scope (wlan0 works via the internal-modem path).
- **Host runner backlog (#22, #31, #34, #21, #24)**: P3 evidence-integrity/reliability. Fix opportunistically when the runner is next touched; #22 (manifest redaction leak) is the most worthwhile because it writes unredacted dmesg/debug into `manifest.json`.
- Keep all of the above as an explicit backlog; none is an active-runtime emergency.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/local_security_rescan.py`
- `python3 workspace/public/src/scripts/revalidation/local_security_rescan.py --out /tmp/a90-local-security-rescan-absolute-test.md` (abs path no longer crashes — #23)
- `python3 workspace/public/src/scripts/revalidation/local_security_rescan.py --out workspace/private/scratch/local_security_rescan_relative_test.md`
- Full-tree local rescan (2026-06-10, current HEAD): PASS=10, WARN=1, FAIL=0.

## Remaining Findings

> Raw inventory of the 34 CSV rows (state at the V2189-promotion snapshot). Rows **#1, #3, #4, #5, #12, #13, #23
> are now FIXED in the current tree** (see Post-rescan reconciliation) and will clear on the next Codex rescan;
> they are listed here only for traceability. The other rows are the non-active backlog.

| # | Severity | Family | Prior | Reachability | Title | Current Path Evidence |
|---:|---|---|---|---|---|---|
| 1 | high | manual_validation_runner_backlog | P2 | active_manual_validation_runner | Autostarted serial bridge remains exposed after runner exits | `workspace/public/src/scripts/revalidation/serial_tcp_bridge.py (mapped)` |
| 2 | high | current_helper_trust_boundary | P2 | current_helper_packaged_trust_boundary | Private cnss-daemon is executed without live SHA verification | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 3 | medium | manual_lab_boundary | P2 | manual_lab_tool | Unauthenticated Wi-Fi upload receiver allows LAN DoS | `docs/operations/A90_PHONE_WIFI_TRANSFER_SERVER.md`<br>`workspace/public/src/scripts/phone/a90_termux_wifi_lab.sh` |
| 4 | medium | manual_validation_runner_backlog | P2 | active_manual_validation_runner | Wildcard NCM transfer listeners expose host services | `workspace/public/src/scripts/revalidation/a90_ncm_transport.py (mapped)` |
| 5 | medium | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | V2167 starts wpa_supplicant without enforced UID drop | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 6 | medium | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | MAC bridge exposes EFS/persist to sibling root daemons | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 7 | medium | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Compact TFTP trace trusts non-QRTR RRQ/WRQ records | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 8 | medium | native_helper_legacy_mode_backlog | P2 | current_helper_mode_gated_unproven | recvmsg trace can leak stale pd-mapper memory | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 9 | medium | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | mdm_helper can execute as unconstrained root | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 10 | medium | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | SELinux compile proof exposes live policy load interface | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 11 | medium | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Linker probe output can spoof safety-gate success | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 12 | low | manual_validation_runner_backlog | P2 | active_manual_validation_runner | Wi-Fi validation passes despite credential leak flags | `workspace/public/src/scripts/revalidation/native_wifi_v2178_autoconnect_phase_validation.py` |
| 13 | low | manual_validation_runner_backlog | P2 | active_manual_validation_runner | Default searches now hide live legacy Python imports | `workspace/public/src/scripts/revalidation/_workspace_bootstrap.py`<br>`workspace/public/src/scripts/revalidation/a90_v725_fasttransport_baseline_validation.py` |
| 14 | low | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Firmware fallback feeder can over-read heap | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 15 | low | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | PM children relabel SELinux context despite opt-out | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 16 | low | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Unbounded blocking modem open fallback can hang helper | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 17 | low | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Out-of-bounds cleanup count in execns helper | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 18 | low | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Unchecked hwbinder reply pointers can crash helper | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 19 | low | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Unbounded netlink IFNAME parsing can leak helper memory | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 20 | low | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | lshal query timeout can be bypassed by inherited pipes | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 21 | low | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | V407 runner allows unapproved legacy Wi-Fi HAL target | `docs/plans/NATIVE_INIT_V407_COMPOSITE_HAL_RETRY_PLAN_2026-05-20.md`<br>`workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 22 | low | active_host_infra_backlog | P2 | active_host_infra | Unredacted native captures are embedded in v217 manifests | `workspace/public/src/scripts/revalidation/a90_kernel_tools.py (mapped)` |
| 23 | informational | new_tooling_bug | NEW | NEW | Absolute --out path crashes local rescan | `workspace/public/src/scripts/revalidation/local_security_rescan.py` |
| 24 | informational | manual_validation_runner_backlog | P2 | active_manual_validation_runner | Archived V2167 runner fails due to missing bootstrap import | `workspace/public/archive/scripts/revalidation/native_wifi_connect_dhcp_google_ping_handoff_v2167.py`<br>`workspace/public/src/scripts/revalidation/README.md`<br>`docs/reports/REVALIDATION_SCRIPT_INVENTORY_2026-06-08.md` |
| 25 | informational | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | PerMgr summary uses non-exact rc=0x0 matching | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 26 | informational | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Order timestamp build fails without MCFG readback | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 27 | informational | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Prefix-matched uprobe names skew indication results | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 28 | informational | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Prefix collision corrupts PM-service uprobe hit counts | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 29 | informational | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | v219 preflight cannot recognize installed helper | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 30 | informational | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | CNSS gate can run without second provider confirmation | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 31 | informational | manual_validation_runner_backlog | P2 | active_manual_validation_runner | Out-of-repo output path crashes V1005 classifier | `workspace/public/src/scripts/revalidation/a90_kernel_tools.py (mapped)` |
| 32 | informational | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | Global cmdline scan can falsely pass ks preflight | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 33 | informational | native_helper_legacy_mode_backlog | P2 | current_helper_packaged_unproven_mode | V665 proof passes without checking repaired snapshot paths | `workspace/public/src/native-init/helpers/a90_android_execns_probe.c (mapped)` |
| 34 | informational | active_host_infra_backlog | P2 | active_host_infra | V594 cleanup targets the wrong proof directory | `workspace/public/src/scripts/revalidation/a90_kernel_tools.py (mapped)` |
