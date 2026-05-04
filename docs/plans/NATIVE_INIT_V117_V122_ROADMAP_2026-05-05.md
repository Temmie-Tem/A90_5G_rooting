# A90 Native Init v117-v122 Roadmap

Date: 2026-05-05
Baseline: `A90 Linux init 0.9.16 (v116)`
Cycle target: keep v116 stability while reducing PID 1 control debt before returning to risky hardware bring-up work.

## Decision

The next cycle should start with PID 1 slimming and control-path cleanup, not Wi-Fi bring-up.

Reasons:

- v104 Wi-Fi feasibility already marked active bring-up as `no-go/baseline-required`; the next Wi-Fi step must remain read-only inventory refresh until the native environment is cleaner.
- v116 is operationally stable enough for refactoring, but large dispatch/controller/menu paths still live inside the PID 1 include tree.
- Wi-Fi driver/firmware work can introduce USB/network/display regressions that are harder to debug if shell/menu/process boundaries remain tangled.

## Guardrails

- No partition write/format work in this cycle.
- No Wi-Fi enablement, rfkill write, module load/unload, firmware mutation, or automatic remote download.
- USB ACM serial remains the rescue/control channel.
- NCM/rshell remain opt-in service paths; do not make them the only recovery path.
- Every boot image version must be flash-verified before README/latest-verified promotion.

## Version Plan

### v117 — PID1 Slim Roadmap Baseline

Build: `A90 Linux init 0.9.17 (v117)`
Marker: `0.9.17 v117 PID1 SLIM ROADMAP`

Scope:

- Add this roadmap and preserve v116 runtime behavior.
- Establish the order for shell/menu/controller/guard/Wi-Fi refresh work.
- Validate that a no-behavior-change version bump still boots cleanly.

Acceptance:

- `version`, `status`, `bootstatus`, `selftest verbose` pass.
- Quick soak passes.
- Docs point the next execution item to v118.

### v118 — Shell Metadata Cleanup

Build: `A90 Linux init 0.9.18 (v118)`
Marker: `0.9.18 v118 SHELL META API`

Scope:

- Move command inventory/count/flag summary helpers into `a90_shell.c/h`.
- Keep handler bodies and command table in the include tree.
- Add a small read-only command/report path for command table health if useful.

Acceptance:

- `help`, `last`, `cmdv1 version/status`, unknown command, and busy framed result behavior unchanged.
- No direct behavior change for destructive raw-control commands.

### v119 — Menu Routing Cleanup

Build: `A90 Linux init 0.9.19 (v119)`
Marker: `0.9.19 v119 MENU ROUTE API`

Scope:

- Reduce repeated menu app/changelog dispatch logic through `a90_menu` helper APIs.
- Keep actual app renderers in their existing modules.
- Preserve nonblocking `screenmenu` and blocking rescue `blindmenu` behavior.

Acceptance:

- `screenmenu` returns immediately.
- `hide`, menu navigation, changelog/about apps, and power-page busy gate remain unchanged.

### v120 — Command Group Split

Build: `A90 Linux init 0.9.20 (v120)`
Marker: `0.9.20 v120 COMMAND GROUP API`

Scope:

- Split low-risk command group helpers out of the monolithic shell dispatch path.
- Prefer wrappers around existing module APIs rather than moving risky command handler bodies wholesale.
- Keep `cmdv1/cmdv1x`, command table, and shell loop stable.

Acceptance:

- Storage/runtime/helper/userland/network observer commands pass.
- `run`, `runandroid`, `cpustress`, and service commands keep current cancel/result semantics.

### v121 — PID1 Guard

Build: `A90 Linux init 0.9.21 (v121)`
Marker: `0.9.21 v121 PID1 GUARD`

Scope:

- Add read-only PID 1 guard checks for process role, service registry, log/selftest readiness, runtime root, and command table sanity.
- Expose `pid1guard` or fold the summary into existing status/diag output.
- Warn-only; never block shell/HUD entry.

Acceptance:

- Known-good system reports guard PASS or WARN=0/FAIL=0.
- Guard failures are logged and visible without rebooting or mutating state.

### v122 — Wi-Fi Inventory Refresh

Build: `A90 Linux init 0.9.22 (v122)`
Marker: `0.9.22 v122 WIFI REFRESH`

Scope:

- Refresh Wi-Fi read-only evidence after PID1 cleanup.
- Compare native visible paths with prior v103/v104 baseline.
- Do not attempt bring-up; this version decides whether a later Wi-Fi cycle has enough evidence to proceed.

Acceptance:

- `wifiinv`, `wififeas`, and host inventory collector still work.
- Report explicitly states whether active Wi-Fi work remains blocked.

## Completion Audit

After v122, write a v117-v122 completion audit covering:

- report/commit/artifact presence for every version,
- real-device flash evidence,
- latest docs consistency,
- unresolved carry-forward items,
- whether Wi-Fi should remain read-only or graduate to a controlled bring-up plan.
