# Native Init Roadmap: v109-v116

Date: `2026-05-04`
Baseline: `A90 Linux init 0.9.8 (v108)` / `0.9.8 v108 APP INPUTMON API`
Goal: turn the v108 UI/App split baseline into a cleaner, longer-running, server-like native runtime without weakening recovery safety.

## Summary

v106-v108 removed the lowest-risk UI app ownership from `40_menu_apps.inc.c`:

- v106: `a90_app_about.c/h`
- v107: `a90_app_displaytest.c/h`
- v108: `a90_app_inputmon.c/h`

The next cycle should not jump directly to risky Wi-Fi or partition work. It should first reduce remaining controller/service debt and then validate long-running operation.

## Guardrails

- Keep USB ACM serial bridge as the rescue/control channel.
- Keep Wi-Fi bring-up blocked until Android/TWRP/native baseline comparison changes the v104 gate result.
- Keep `/efs`, modem, key/security, bootloader, and partition format/write experiments out of this cycle.
- Prefer read-only diagnostics, bounded service tests, and opt-in NCM/rshell paths.
- Every boot image version must have: static build, marker string check, `git diff --check`, host Python `py_compile`, real-device flash, command regression, report, and commit.

## Version Plan

### v109. Post-v108 Structure Audit

Target: `A90 Linux init 0.9.9 (v109)` / `0.9.9 v109 STRUCTURE AUDIT 2`

Goal:

- Audit remaining include-tree and module boundary debt after the first UI/App split.
- Avoid feature changes; apply only low-risk cleanup if it directly removes stale markers or dead code.

Scope:

- Inspect remaining `v108/40_menu_apps.inc.c`, `v108/70_storage_android_net.inc.c`, and `v108/80_shell_dispatch.inc.c` ownership.
- Check for stale version markers, duplicate app routing, direct module state access, and old renderer helpers.
- Produce `docs/reports/NATIVE_INIT_V109_STRUCTURE_AUDIT_2026-05-04.md`.
- If code changes are needed, keep them behavior-preserving.

Validation:

- `version`, `status`, `bootstatus`, `selftest verbose`, `inputlayout`, `displaytest safe`, `screenmenu`, `hide`.
- 3-cycle quick soak.

### v110. Menu/App Controller Cleanup

Target: `A90 Linux init 0.9.10 (v110)` / `0.9.10 v110 APP CONTROLLER CLEANUP`

Goal:

- Reduce `40_menu_apps.inc.c` app controller coupling without moving high-risk command handlers.
- Keep `screenmenu` nonblocking and `blindmenu` foreground rescue behavior unchanged.

Scope:

- Extract small app-controller state helpers if the v109 audit identifies clear boundaries.
- Keep shell dispatch and app command implementations in the include tree unless visibility risk is low.
- Preserve menu busy gate and power-page dangerous command policy.

Validation:

- `screenmenu` immediate return.
- Menu visible state still allows observation commands.
- `hide`, `statushud`, `autohud 2`, input layout/displaytest regressions.

### v111. Extended Soak RC

Target: `A90 Linux init 0.9.11 (v111)` / `0.9.11 v111 EXTENDED SOAK RC`

Goal:

- Build confidence in the v108-v110 baseline before service/runtime expansion.

Scope:

- Add or document a bounded host runner profile for longer idle/menu/service checks.
- Run at least one practical host-driven soak in this repo session.
- Mark cable unplug/replug or 30-60 minute soak as optional/manual if physical interaction is required.

Validation:

- `native_soak_validate.py` with an extended profile or explicit cycle count.
- Final `status`, `service list`, `bootstatus`, `selftest verbose`.

### v112. USB/NCM Service Soak

Target: `A90 Linux init 0.9.12 (v112)` / `0.9.12 v112 USB SERVICE SOAK`

Goal:

- Validate opt-in NCM/tcpctl/rshell service behavior over repeated start/stop and host traffic.

Scope:

- Prefer host tooling/report updates unless code defects are found.
- Exercise `netservice start`, host NCM ping, `tcpctl_host.py`, optional `rshell_host.py`, and rollback to ACM-only.
- Keep netservice disabled by default.

Validation:

- ACM bridge survives rollback.
- NCM ping/TCP smoke passes when enabled.
- `netservice stop` returns to `ncm0=absent`, `tcpctl=stopped`.

### v113. Runtime Package Layout

Target: `A90 Linux init 0.9.13 (v113)` / `0.9.13 v113 RUNTIME PACKAGE LAYOUT`

Goal:

- Make SD runtime root more package-friendly without introducing a full package manager.

Scope:

- Clarify runtime directories and state files under `/mnt/sdext/a90`.
- Add read-only/reporting improvements if needed: runtime root, bin inventory, package dir, helper manifest path.
- Avoid destructive SD format/migration.

Validation:

- `runtime`, `helpers verbose`, `userland`, `storage`, `mountsd status`, `selftest verbose`.

### v114. Helper Deployment 2

Target: `A90 Linux init 0.9.14 (v114)` / `0.9.14 v114 HELPER DEPLOY 2`

Goal:

- Improve helper manifest/hash/update visibility so runtime helpers can be managed safely.

Scope:

- Extend helper inventory or docs around ramdisk fallback vs SD/cache preferred helper.
- Record helper hashes in report.
- Do not add automatic remote downloads.

Validation:

- `helpers verbose`, `runtime`, `userland`, `diag`, helper paths and hashes.

### v115. Remote Shell Hardening

Target: `A90 Linux init 0.9.15 (v115)` / `0.9.15 v115 RSHELL HARDENING`

Goal:

- Harden custom token TCP remote shell over USB NCM.

Scope:

- Review token file policy, idle timeout, logging, command execution path, and stop/reap behavior.
- Keep service opt-in and USB-only by default.
- No internet-facing/Wi-Fi remote shell.

Validation:

- `service start rshell`, `rshell_host.py smoke`, invalid token check if supported, idle/stop rollback, ACM bridge recovery.

### v116. Diagnostics Bundle 2

Target: `A90 Linux init 0.9.16 (v116)` / `0.9.16 v116 DIAG BUNDLE 2`

Goal:

- Improve post-failure evidence capture after v109-v115 changes.

Scope:

- Extend `diag`/host collection only if gaps are found: service state, runtime package info, helper hashes, netservice/rshell state, recent log tail.
- Keep diagnostics read-only.
- Produce a final v116 report tying the v109-v116 cycle together.

Validation:

- `diag`, `diag_collect.py`, `status`, `bootstatus`, `selftest verbose`, quick soak final state.

## Recommended Execution Order

1. v109 audit/report first, because it determines whether v110 should be code extraction or only cleanup.
2. v110 cleanup only if v109 identifies low-risk boundaries.
3. v111 soak before service/runtime expansion.
4. v112-v115 service/runtime/helper/rshell hardening.
5. v116 diagnostics bundle after the cycle so failure evidence covers all new areas.

## Completion Criteria for This Cycle

- Latest verified build reaches `A90 Linux init 0.9.16 (v116)`.
- README, project status, versioning, task queue, and next-work docs point to v116.
- Every version v109-v116 has a report and commit.
- Real-device flash validation is recorded for every boot image version unless a version is explicitly documentation-only and does not claim a new build tag.
- Any physical/manual-only validation gap is explicitly recorded, not implied as complete.

## Current Completion Status

As of `2026-05-04`, v116 is verified as `A90 Linux init 0.9.16 (v116)`. The v109-v116 implementation cycle is complete and the next immediate work item is a completion audit across reports, docs, commits, artifacts, and validation evidence.
