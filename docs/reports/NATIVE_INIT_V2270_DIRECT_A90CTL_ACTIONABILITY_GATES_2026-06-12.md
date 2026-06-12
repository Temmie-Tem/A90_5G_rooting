# V2270 Direct a90ctl Actionability Gates

Date: `2026-06-12`

## Decision

`v2270-direct-a90ctl-actionability-gates-host-only-pass`

## Scope

Host-only inventory consolidation. No boot image was built, no device was flashed,
and no Wi-Fi scan/connect/DHCP/ping action was run.

## Why This Unit

After V2269, the current-baseline Wi-Fi detail runner no longer used direct
`a90ctl.py` subprocess command lists. The remaining direct references were all
historical or review-only runner families, but the inventory still ranked the
largest group as the top candidate. That created a loop risk: future iterations
could keep selecting historical direct-reference migration even when no runner
was being revived for a bounded validation.

V2270 changes the inventory signal from "what exists" to "what is actionable
now".

## Changes

- Added `actionable_now` and `migration_gate` metadata to direct `a90ctl.py`
  candidate groups in `inventory_revalidation_scripts.py`.
- Added aggregate `consolidation_signals` fields:
  - `direct_a90ctl_actionable_now_count`;
  - `direct_a90ctl_actionable_now_names`;
  - `direct_a90ctl_review_only_count`;
  - `direct_a90ctl_review_only_names`;
  - `direct_a90ctl_next_actionable_group`.
- Refreshed the public inventory Markdown and JSON reports.
- Updated `GOAL.md` and the current TODO/risk register so future loops do not
  treat historical references as actionable migration work by default.

## Result

Current inventory signals:

```json
{
  "direct_a90ctl_reference_count": 14,
  "direct_a90ctl_actionable_now_count": 0,
  "direct_a90ctl_review_only_count": 14,
  "direct_a90ctl_next_actionable_group": {}
}
```

Candidate groups are still preserved for review:

| Group | Count | Actionability | Gate |
| --- | ---: | --- | --- |
| `flash_capable_kernel_handoff_runners` | 6 | review-only | `revive-for-bounded-live-run` |
| `live_readonly_kernel_catalog_runners` | 4 | review-only | `revive-or-modify-observer` |
| `legacy_bpf_anchor_runners` | 4 | review-only | `reactivate-legacy-anchor` |

## Validation

Commands run:

```sh
PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 -m py_compile workspace/public/src/scripts/revalidation/inventory_revalidation_scripts.py
PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/inventory_revalidation_scripts.py --write
python3 - <<'PY'
import json
from pathlib import Path
signals = json.loads(Path('docs/reports/REVALIDATION_SCRIPT_INVENTORY_2026-06-10.json').read_text())['consolidation_signals']
assert signals['direct_a90ctl_reference_count'] == 14
assert signals['direct_a90ctl_actionable_now_count'] == 0
assert signals['direct_a90ctl_review_only_count'] == 14
assert signals['direct_a90ctl_next_actionable_group'] == {}
assert signals['direct_a90ctl_top_group']['group'] == 'flash_capable_kernel_handoff_runners'
PY
```

Observed summary:

```json
{
  "actionable_now_count": 0,
  "direct_count": 14,
  "next_actionable_group": {},
  "review_only_count": 14,
  "top_group": "flash_capable_kernel_handoff_runners"
}
```

## Next Step

Do not migrate more direct `a90ctl.py` references just because they remain in
historical scripts. Pick the next work item from the normal tier policy. If a
historical flash-capable or read-only kernel observer is revived, migrate that
specific runner to shared transport as part of the bounded revival unit.
