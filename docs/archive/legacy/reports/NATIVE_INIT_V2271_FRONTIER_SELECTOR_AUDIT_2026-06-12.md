# V2271 Frontier Selector Audit

Date: `2026-06-12`

## Decision

`v2271-frontier-selector-audit-host-only-pass`

## Scope

Host-only loop-selection tooling and audit. No boot image was built, no device was
flashed, and no Wi-Fi scan/connect/DHCP/ping action was run.

## Track Evaluation

The GOAL.md tier policy was applied in order.

### T1 Kernel Observation

- Status: deferred for this iteration.
- Drop trigger: V2253 closed the documented firmware_class boundary and the
  generic CPU-clock sampler loop. The current public state names no new
  independent kernel-observation oracle.
- Safety note: this is not a hardware-wall or T1-complete conclusion. It only
  prevents re-running the same closed boundary without a new oracle.

### T2 WLAN Native-Init

- Status: deferred for this iteration.
- Drop trigger: V2254/V2256 are the current promoted WLAN surface baseline, and
  the TODO limits longer Wi-Fi/data-path soak to cases where new promotion
  criteria require it.
- Safety note: no live validation criterion was selected, so no bridge/device
  command was needed.

### T3 Self-Directed Cleanup

- Selected work: add a host-only frontier selector/audit utility.
- Trigger: after V2270, inventory has no actionable direct command-client
  migration group, no delete-review rows, and no active live phase/residual
  metadata backlog. The useful next step is to make that selection state
  machine-readable so future loops do not keep reselecting closed work.

## Changes

- Added `workspace/public/src/scripts/revalidation/native_init_frontier_select.py`.
- Registered the selector in `inventory_revalidation_scripts.py` as an active
  host-only utility.
- Refreshed the public script inventory.
- Updated `GOAL.md` and the current TODO/risk register with the selector result
  and next-selection guard.

## Selector Output

Current selector summary:

```json
{
  "decision": "frontier-selector-no-automatic-safe-unit",
  "selected_track": null,
  "t1_marker": true,
  "t2_complete": true,
  "t3_status": "no-cleanup-backlog"
}
```

Full decision semantics:

- T1: `defer-until-new-independent-oracle`.
- T2: `defer-until-new-promotion-or-live-validation-criterion`.
- T3: `no-cleanup-backlog`.
- Next operator decision: define a new T1 oracle, set a concrete V2254
  live-validation/promotion criterion, or revive a historical runner before
  selecting the next bounded live/migration unit.

## Inventory Result

Refreshed inventory state:

```json
{
  "active": 108,
  "delete_review": 0,
  "frontier_selector_label": "active",
  "direct_actionable_now": 0
}
```

The selector itself is host-only and does not contain direct command-client
subprocess references.

## Validation

Commands run:

```sh
PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_init_frontier_select.py \
  workspace/public/src/scripts/revalidation/inventory_revalidation_scripts.py

PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/native_init_frontier_select.py --json

PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/inventory_revalidation_scripts.py --write
```

Assertions passed:

- selector decision is `frontier-selector-no-automatic-safe-unit`;
- selector reports no selected track;
- T1 closed-boundary marker is present;
- T2 baseline-complete and soak-deferred markers are present;
- T3 status is `no-cleanup-backlog`;
- `native_init_frontier_select.py` is classified as `active`;
- inventory `source_delete_review_count=0`;
- inventory `direct_a90ctl_actionable_now_count=0`.

## Next Step

Do not select another live or migration unit from inertia. The next bounded unit
needs one of these explicit inputs:

1. a new independent T1 observation oracle;
2. a concrete V2254 live-validation/promotion criterion;
3. a historical runner intentionally revived for a bounded validation.
