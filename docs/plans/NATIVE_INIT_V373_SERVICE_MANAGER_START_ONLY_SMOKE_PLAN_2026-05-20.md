# v373 Plan: Service-Manager Start-Only Smoke Runner Scaffold

- date: `2026-05-20`
- scope: fail-closed runner scaffold for service-manager start-only smoke
- boot image change: none
- native baseline: `A90 Linux init 0.9.61 (v319)`
- prerequisite: V372 approval packet ready

## Summary

V373 adds the host-side runner scaffold for the future service-manager
start-only smoke. It does not start service-manager yet. The runner verifies the
V372 approval packet, refreshes read-only current native state, refuses live run
without the exact approval phrase, and blocks approved execution before mutation
when the deployed `a90_android_execns_probe` helper lacks a service-manager
start-only mode.

This avoids improvising daemon start through raw shell commands. The next real
work is V374: add a bounded service-manager start-only mode to the execns helper
or otherwise provide an equivalent fail-closed primitive.

## Implementation

Add:

```text
scripts/revalidation/wifi_service_manager_start_only_smoke.py
```

Modes:

```bash
python3 scripts/revalidation/wifi_service_manager_start_only_smoke.py \
  --out-dir tmp/wifi/v373-service-manager-start-only-smoke-plan-20260520-013827 \
  plan

python3 scripts/revalidation/wifi_service_manager_start_only_smoke.py \
  --out-dir tmp/wifi/v373-service-manager-start-only-smoke-preflight-20260520-013827 \
  preflight

python3 scripts/revalidation/wifi_service_manager_start_only_smoke.py \
  --out-dir tmp/wifi/v373-service-manager-start-only-smoke-refusal-20260520-013827 \
  run
```

## Expected Current Decisions

```text
plan: service-manager-start-only-smoke-plan-ready
preflight: service-manager-start-only-smoke-blocked
run without approval: service-manager-start-only-smoke-approval-required
```

The preflight blocker should be:

```text
helper-service-manager-mode
```

## Required Approval Phrase

```text
approve v373 service-manager start-only smoke only; no Wi-Fi HAL start and no Wi-Fi bring-up
```

## Acceptance

- No-approval run returns approval-required with `steps=0`.
- Preflight executes only read-only `cmdv1` captures.
- Preflight confirms V372 packet, status/selftest, service-manager binary
  visibility, clean process surface, clean Wi-Fi link surface, and cleaned
  temporary Binder nodes.
- Preflight blocks before mutation because helper service-manager mode is absent.
- `daemon_start_executed=false` and `device_mutations=false` in all V373 paths.
