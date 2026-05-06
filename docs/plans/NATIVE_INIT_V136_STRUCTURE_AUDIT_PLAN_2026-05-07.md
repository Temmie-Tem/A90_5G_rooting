# v136 Plan: Post-v135 Structure Audit

## Summary

v136 targets `A90 Linux init 0.9.36 (v136)` / `0.9.36 v136 STRUCTURE AUDIT 3`.

This version is the **C candidate** from the post-v135 choice: a structure audit
and low-risk cleanup checkpoint after the security hardening and policy-matrix
cycle. v137 is reserved for the **B candidate**: broader validation matrix / host
harness expansion.

The v136 goal is not to add user-visible features. The goal is to inspect the
current v95-v135 module stack for ownership drift, duplicate policy logic, stale
include-tree implementation, PID1 growth hotspots, and weak next cleanup
boundaries before adding more network-facing or Wi-Fi-adjacent work.

Current baseline:

- latest verified build is `A90 Linux init 0.9.35 (v135)`;
- v135 `policycheck run` passed `cases=91 pass=91 fail=0` on device;
- local targeted v135 rescan is `PASS=16`, `WARN=1`, `FAIL=0`;
- remaining warning is accepted USB-local/localhost root-control boundary;
- no new fresh-scan blocker is currently selected for implementation.

## Scope Decision

Choose `post-v135 structure audit` for v136.

Rationale:

- v95-v135 added many compiled modules and policy layers in a short span.
- Security batches closed the imported findings, but they also added guardrails,
  helper trust, diagnostics, exposure, and policy matrix logic that should be
  checked for duplicated ownership.
- Network/Wi-Fi expansion should not proceed until the current root-control and
  service boundaries are mechanically clear.
- v136 can produce a useful artifact even if it applies only documentation and
  low-risk source cleanup.

Do not implement Wi-Fi bring-up, new listeners, new authentication protocols,
new command surfaces, or a shell rewrite in v136.

## Key Changes

- Copy v135 into `init_v136.c` and `v136/*.inc.c`.
- Bump metadata in `a90_config.h` to `0.9.36` / `v136` and add changelog text
  `0.9.36 v136 STRUCTURE AUDIT 3`.
- Run targeted structure searches against active v136 include tree and shared
  modules.
- Apply only low-risk cleanup if a concrete issue is found:
  - remove stale forward declarations or dead local helpers;
  - replace direct state/path access with existing public APIs;
  - consolidate duplicated constants into `a90_config.h` only when behavior is
    unchanged;
  - document module ownership where ambiguity is real;
  - keep user-facing command output compatible unless the report calls out a
    deliberate wording-only clarification.
- Write `docs/reports/NATIVE_INIT_V136_STRUCTURE_AUDIT_2026-05-07.md` with
  audit evidence, findings, keep/split/merge candidates, and v137 input.
- Update README/task queue/next work only after real-device verification passes.

## Audit Targets

### 1. Module Ownership Drift

Check that compiled modules still own their intended responsibility:

- `a90_usb_gadget` owns configfs/UDC primitive operations;
- `a90_netservice` owns NCM/tcpctl policy;
- `a90_runtime` owns runtime path/package layout;
- `a90_helper` owns helper manifest/preference checks;
- `a90_exposure` owns exposure snapshot and read-only guard;
- `a90_controller` owns menu/power busy policy;
- `a90_shell` owns command metadata lookup/grouping;
- app modules own ABOUT/displaytest/input monitor rendering only.

Search examples:

```bash
rg -n "setup_acm_gadget|reap_tcpctl_child|/config/usb_gadget/g1/UDC|storage_state|boot_storage|tcpctl_pid|rshell_pid|console_fd|kms_state\." \
  stage3/linux_init/init_v136.c stage3/linux_init/v136 stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Expected:

- direct mutable state is private to the owning module;
- include-tree command handlers call public APIs;
- false positives are listed in the report, not blindly edited.

### 2. Duplicate Policy Logic

Check whether security policy exists in two places that can drift:

- menu-visible/power-page gate vs `policycheck` cases;
- exposure guard vs service/netservice/rshell status;
- helper trust vs runtime/userland command paths;
- mountsd/storage state vs log/runtime path selection.

Search examples:

```bash
rg -n "CMD_DANGEROUS|A90_CONTROLLER_BUSY|subcmd_|status_only|read[-_ ]only|trusted-lab|accepted|guard|token|required|manifest|sha256" \
  stage3/linux_init/v136 stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Expected:

- policy decisions have one owner and tests/harnesses read that owner;
- duplicated policy tables are either intentionally test matrices or flagged for
  v137 validation harness work.

### 3. Include-Tree Residue

Check whether old pre-module implementations remain in active include files:

```bash
rg -n "native_logf|timeline_record\(|cprintf\(|read_line\(|cmdv1x_decode|struct kms_display_state|cpustress_worker|auto_hud_loop|handle_.*status|fork\(|waitpid\(|kill\(" \
  stage3/linux_init/init_v136.c stage3/linux_init/v136
```

Expected:

- old API names are absent;
- large orchestrators such as `auto_hud_loop` and shell handlers may remain, but
  the report should classify them as keep/split candidates rather than mixing
  them into v136 cleanup.

### 4. PID1 Growth Hotspots

Measure active include/module size and identify the largest remaining files:

```bash
wc -l stage3/linux_init/init_v136.c stage3/linux_init/v136/*.inc.c stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h | sort -n | tail -30
```

Expected:

- report lists top hotspots by line count;
- v136 does not attempt a large file migration;
- v137 remains validation-focused unless a severe structural risk appears.

### 5. Host Tooling Alignment

Check whether host revalidation scripts track latest version and safety gates:

```bash
rg -n "0\.9\.35|v135|0\.9\.36|v136|expect-version|policycheck|exposure|selftest|soak|guard" scripts/revalidation docs/security README.md docs/plans
```

Expected:

- latest-oriented scripts are updated only where appropriate;
- historical report references remain untouched;
- v137 candidates include any missing host harness coverage.

## Deferred Work

v136 must not include these:

- v137 integrated validation matrix/harness implementation;
- Wi-Fi active bring-up;
- dropbear/SSH exposure;
- new root-control listener;
- PID1 service split into multiple boot-time processes;
- command handler full migration out of include tree;
- broad UI/menu redesign.

## Test Plan

### Local Build

Build v136 with the same module set as v135:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -o stage3/linux_init/init_v136 \
  stage3/linux_init/init_v136.c \
  stage3/linux_init/a90_util.c \
  stage3/linux_init/a90_log.c \
  stage3/linux_init/a90_timeline.c \
  stage3/linux_init/a90_console.c \
  stage3/linux_init/a90_cmdproto.c \
  stage3/linux_init/a90_run.c \
  stage3/linux_init/a90_service.c \
  stage3/linux_init/a90_kms.c \
  stage3/linux_init/a90_draw.c \
  stage3/linux_init/a90_input.c \
  stage3/linux_init/a90_hud.c \
  stage3/linux_init/a90_menu.c \
  stage3/linux_init/a90_metrics.c \
  stage3/linux_init/a90_shell.c \
  stage3/linux_init/a90_controller.c \
  stage3/linux_init/a90_storage.c \
  stage3/linux_init/a90_selftest.c \
  stage3/linux_init/a90_usb_gadget.c \
  stage3/linux_init/a90_netservice.c \
  stage3/linux_init/a90_runtime.c \
  stage3/linux_init/a90_helper.c \
  stage3/linux_init/a90_userland.c \
  stage3/linux_init/a90_diag.c \
  stage3/linux_init/a90_exposure.c \
  stage3/linux_init/a90_wifiinv.c \
  stage3/linux_init/a90_wififeas.c \
  stage3/linux_init/a90_changelog.c \
  stage3/linux_init/a90_app_about.c \
  stage3/linux_init/a90_app_displaytest.c \
  stage3/linux_init/a90_app_inputmon.c \
  stage3/linux_init/a90_pid1_guard.c
```

Confirm markers:

```bash
strings stage3/linux_init/init_v136 | rg "A90 Linux init 0\.9\.36 \(v136\)|A90v136|0\.9\.36 v136 STRUCTURE AUDIT 3"
```

### Static Checks

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/local_security_rescan.py \
  scripts/revalidation/native_soak_validate.py
rg -n "A90v135|0\.9\.35|init_v135|v135/" stage3/linux_init/init_v136.c stage3/linux_init/v136 stage3/linux_init/a90_config.h || true
```

### Device Validation

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v136.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.36 (v136)" \
  --verify-protocol auto
```

Regression commands:

```bash
python3 scripts/revalidation/a90ctl.py version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py selftest verbose
python3 scripts/revalidation/a90ctl.py exposure guard
python3 scripts/revalidation/a90ctl.py policycheck run
python3 scripts/revalidation/a90ctl.py screenmenu
python3 scripts/revalidation/a90ctl.py hide
python3 scripts/revalidation/native_soak_validate.py --cycles 3 --sleep 1 --expect-version "A90 Linux init 0.9.36 (v136)"
```

## Acceptance

- v136 boots and verifies as `A90 Linux init 0.9.36 (v136)`.
- v136 report lists concrete module ownership, duplicate policy, include residue,
  and PID1 growth findings.
- No user-facing runtime behavior changes unless explicitly documented as
  wording-only or dead-code cleanup.
- `selftest`, `exposure guard`, `policycheck run`, `screenmenu`/`hide`, and
  quick soak pass.
- Task queue names v137 as integrated validation matrix / host harness expansion
  candidate.

## Assumptions

- v135 is the latest verified baseline.
- v136 is a checkpoint/audit version and may contain minimal cleanup only.
- v137 should take the B candidate: strengthen validation coverage across
  `exposure`, `selftest`, `service`, `netservice`, `rshell`, and policy checks.
- Network-facing feature expansion remains blocked until v136 and v137 pass.
