# v373 Report: Service-Manager Start-Only Smoke Runner Scaffold

- date: `2026-05-20`
- scope: fail-closed runner scaffold for service-manager start-only smoke
- boot image change: none
- native baseline: `A90 Linux init 0.9.61 (v319)`
- plan: `docs/plans/NATIVE_INIT_V373_SERVICE_MANAGER_START_ONLY_SMOKE_PLAN_2026-05-20.md`
- result: `PASS / blocked before mutation`

## Summary

V373 adds `wifi_service_manager_start_only_smoke.py`. The runner scaffold keeps
live execution fail-closed: no-approval `run` returns approval-required with no
bridge commands, and `preflight` performs read-only checks only. Current preflight
correctly blocks on `helper-service-manager-mode` because the deployed
`a90_android_execns_probe` helper does not yet advertise a bounded service-manager
start-only mode.

## Evidence

| item | path | decision |
| --- | --- | --- |
| plan | `tmp/wifi/v373-service-manager-start-only-smoke-plan-20260520-013827/` | `service-manager-start-only-smoke-plan-ready` |
| preflight | `tmp/wifi/v373-service-manager-start-only-smoke-preflight-20260520-013827/` | `service-manager-start-only-smoke-blocked` |
| no-approval run | `tmp/wifi/v373-service-manager-start-only-smoke-refusal-20260520-013827/` | `service-manager-start-only-smoke-approval-required` |

Preflight summary:

```text
decision: service-manager-start-only-smoke-blocked
pass: True
reason: blocked before mutation by helper-service-manager-mode
live_execution_approved: False
daemon_start_executed: False
device_mutations: False
```

Preflight checks:

```text
v372-approval-packet: pass
native-version: pass
status-selftest-clean: pass
service-manager-binaries: pass (servicemanager/hwservicemanager visible; vndservicemanager absent)
service-manager-processes-clean: pass
wifi-link-surface-clean: pass
temporary-binder-nodes-clean: pass
approval-gate: needs-operator
helper-service-manager-mode: blocked
```

No-approval run summary:

```text
decision: service-manager-start-only-smoke-approval-required
pass: True
steps: 0
live_execution_approved: False
daemon_start_executed: False
device_mutations: False
```

## Guardrails Kept

- No service-manager daemon was started.
- No Wi-Fi HAL, `wificond`, supplicant, hostapd, CNSS, or diagnostic daemon was
  started.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing was executed.
- No temporary `/dev` node was created by V373.
- No rfkill, ICNSS, module, firmware, or Android partition mutation occurred.

## Next Step

V374 should update or wrap `a90_android_execns_probe` with a bounded
service-manager start-only mode. That mode must support plan/preflight/refusal
first, and approved live execution must still require the V373 exact phrase.
