# V2269 Wi-Fi Detail Runner Transport Migration

Date: 2026-06-12
Track: T2/T3 script consolidation after T1 downgrade
Type: host-only current-baseline runner transport cleanup
Decision: `v2269-wifi-detail-runner-transport-migration-pass`
Result: PASS

## Summary

V2269 acts on the V2268 top consolidation group. The current-baseline Wi-Fi
detail surface runner `native_wifi_detail_surface_handoff_v2255.py` now uses
`a90_transport.run_serial_step` for device cmdv1 commands instead of constructing
direct `a90ctl.py` subprocess command lists. No live flash or device command was
run for this migration.

## Track Selection

- T1 was not selected because the latest kernel-observation boundary remains
  closed by V2253 and no new independent oracle was introduced for this unit.
- T2 Wi-Fi lifecycle remains complete for the current V2254 baseline.
- T2/T3 consolidation was selected because V2268 identified
  `native_wifi_detail_surface_handoff_v2255.py` as the highest-impact direct
  `a90ctl.py` reference group and it is the current-baseline live-surface
  validator.

## Changes

- Removed direct `a90ctl.py` subprocess command construction from
  `native_wifi_detail_surface_handoff_v2255.py`.
- Replaced serial command execution with `a90_transport.run_serial_step`, keeping
  per-attempt step logging, `A90CTL_INPUT_MODE=slow`, and existing
  phase/residual metadata.
- Changed dry-run command display for device commands to `cmdv1 ...` markers
  instead of direct script paths.
- Added `serial_command_transport=a90_transport.run_serial_step` to the runner
  manifest.
- Changed dry-run artifact writing so host-only dry-run stores `report.md` under
  the private run directory and does not overwrite the historical public V2255
  report unless `--execute` or `--write-public-report` is used.
- Refreshed inventory Markdown/JSON and updated GOAL/TODO state.

## Inventory Delta

- `native_wifi_detail_surface_handoff_v2255.py` now reports `Transport=shared`
  and no `a90ctl-subprocess` marker.
- `direct_a90ctl_reference_count`: `15` -> `14`.
- New `direct_a90ctl_top_group`: `flash_capable_kernel_handoff_runners` with
  count `6`.
- Current-baseline Wi-Fi detail runner is no longer a direct-ref migration
  candidate.

## Validation

```bash
PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_wifi_detail_surface_handoff_v2255.py \
  workspace/public/src/scripts/revalidation/inventory_revalidation_scripts.py
PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/native_wifi_detail_surface_handoff_v2255.py --help >/tmp/v2269_v2255_help.txt
PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/native_wifi_detail_surface_handoff_v2255.py --label v2269-dry-run-check >/tmp/v2269_v2255_dryrun.json
git diff --name-only -- docs/reports/NATIVE_INIT_V2255_WIFI_DETAIL_SURFACE_LIVE_2026-06-12.md
PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/inventory_revalidation_scripts.py --write >/tmp/v2269_inventory_write.log
python3 - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('docs/reports/REVALIDATION_SCRIPT_INVENTORY_2026-06-10.json').read_text())
s = payload['consolidation_signals']
entry = next(e for e in payload['entries'] if e['name'] == 'native_wifi_detail_surface_handoff_v2255.py')
assert s['direct_a90ctl_reference_count'] == 14
assert s['direct_a90ctl_top_group']['group'] == 'flash_capable_kernel_handoff_runners'
assert not entry['mentions_a90ctl_subprocess']
assert entry['imports_a90_transport']
print(json.dumps({'top_group': s['direct_a90ctl_top_group'], 'v2255_entry': entry}, indent=2, sort_keys=True))
PY
git diff --check
```

Observed dry-run output:

```json
{
  "decision": "v2255-wifi-detail-surface-dry-run-ready",
  "pass": true,
  "execute": false
}
```

The public report diff check returned no path, confirming dry-run validation did
not alter the historical V2255 live-evidence report.

## Safety

This was host-only script work. No live runner was executed with `--execute`, no
flash or reboot occurred, no Wi-Fi scan/connect/DHCP/ping was run, no credentials
were used, no BPF/perf attach or tracefs write occurred, and no device or
partition write was performed.
