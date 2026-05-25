# V944 V943 Queue-Timing Classifier Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only classifier | `tmp/wifi/v944-v943-queue-timing-classifier/manifest.json` | `v944-pm-provider-lifetime-gap-selected` |

V944 classifies the V943 fresh queue failure as a PeripheralManager
provider/lifetime gap, not as missing `/dev/esoc-0` reachability.

## Implementation

- Added classifier:
  `scripts/revalidation/native_wifi_v943_queue_timing_classifier_v944.py`
- Inputs:
  - `tmp/wifi/v943-mdm-helper-queue-timing-capture-live/manifest.json`
  - `docs/reports/NATIVE_INIT_V867_PM_INIT_CONTRACT_START_ONLY_2026-05-25.md`
- Evidence:
  `tmp/wifi/v944-v943-queue-timing-classifier/summary.md`

## Findings

| Marker | Value |
| --- | --- |
| `per_mgr` alive across lower window | `true` |
| `per_mgr` has `/dev/subsys_modem` fd | `false` |
| `per_mgr` has `/dev/subsys_esoc0` fd | `false` |
| `pm-proxy` lifecycle present | `false` |
| `pm_proxy_helper` lifecycle present | `false` |
| `mdm_helper` reaches `/dev/esoc-0` | `true` |
| `ks` / MHI pipe | `false` |
| spawn to `/dev/esoc-0` fd | `14ms` |
| queue window duration | `12044ms` |
| prior `pm_proxy_helper` D-state risk | `true` |

Fresh queue failure:

```text
[10282.918067]  [3:     mdm_helper: 1231] unable to queue event for SDX50M
```

## Interpretation

The fresh failure occurs after `mdm_helper` reaches `/dev/esoc-0`, while
`pm-service` is alive but lacks the Android-equivalent subsystem fd/provider
state. Starting `pm_proxy_helper` blindly is not selected because V867 already
showed a D-state cleanup risk.

The next unit should therefore improve observability around provider readiness
or refresh Android PM timing read-only. It should not start `pm_proxy_helper`,
open `/dev/subsys_esoc0`, send eSoC notifications, or start Wi-Fi HAL.

## Guardrails

- Host-only classifier only.
- No device command.
- No actor start.
- No service-manager/CNSS/Wi-Fi HAL start.
- No `/dev/subsys_esoc0` open.
- No eSoC ioctl.
- No scan/connect/link-up.
- No credential use.
- No DHCP/route mutation.
- No external ping.
- No boot image or partition write.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v943_queue_timing_classifier_v944.py
python3 scripts/revalidation/native_wifi_v943_queue_timing_classifier_v944.py
```

## Next

V945 should be source/build-only helper work for provider readiness diagnostics
inside the existing bounded runtime-contract path, or a read-only Android PM
timing recapture if we need positive timing first. The safer default is helper
diagnostics first: no new actor lifecycle and no live trigger expansion.
