# v194 NCM/tcpctl Broker Lifecycle Automation

## Summary

v194 adds a host-side lifecycle validator for the `A90B1` `ncm-tcpctl` backend.
This is a host tooling change only; the latest verified native-init device build
remains `A90 Linux init 0.9.59 (v159)`.

## Changes

- Added `scripts/revalidation/a90_broker_ncm_lifecycle_check.py`.
- The wrapper composes existing tools:
  - `tcpctl_host.py start` to start authenticated `/cache/bin/a90_tcpctl`;
  - `a90_broker_concurrent_smoke.py --backend ncm-tcpctl` for broker NCM run
    requests;
  - `tcpctl_host.py stop` for cleanup.
- Evidence is written through private/no-follow output helpers.
- `--dry-run` records the planned command sequence without touching device state.

## Validation

```bash
python3 -m py_compile scripts/revalidation/a90_broker_ncm_lifecycle_check.py
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_ncm_lifecycle_check.py \
  --dry-run \
  --run-dir tmp/a90-v194-dry-run
```

Result: PASS.

Evidence:

- `tmp/a90-v194-dry-run/planned-commands.json`
- `tmp/a90-v194-dry-run/broker-ncm-lifecycle-summary.json`
- `tmp/a90-v194-dry-run/broker-ncm-lifecycle-report.md`

## Acceptance

- The lifecycle wrapper exists and validates its command plan offline.
- Live NCM execution is intentionally optional because it requires the attached
  device NCM interface to be configured and a bridge to be active.

## Next

v195 should use the broker and lifecycle pieces for a longer broker-backed soak
so audit integrity and device observation remain connected over time.
