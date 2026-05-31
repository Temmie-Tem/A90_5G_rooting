# Native Init V1344 — Current Route Lower Response Reconciliation Plan

- Date: 2026-06-01
- Cycle: `V1344` (project axis; no boot image or partition write implied)
- Native build: `A90 Linux init 0.9.68 (v724)` (unchanged)
- Type: host-only evidence reconciliation plan
- Status: PLAN

## Goal

V1343 proved that the current provider-ready route can still reproduce the
V1221 lower-path trigger:

```text
private cnss-daemon.sdx50m
  -> CNSS registers SDX50M
  -> pm-service reaches /dev/subsys_esoc0
  -> no WLFW/BDF/wlan0
```

V1344 should reconcile that current result with the older lower-response
classifiers before starting another live gate. The intended output is a compact
host-only classifier that answers one question:

```text
Does V1343 match the established post-AP2MDM MDM2AP/PCIe response gap,
or did the current route regress or expose a different blocker?
```

## Inputs

| Evidence | Required fact |
| --- | --- |
| `tmp/wifi/v1343-provider-ready-sdx50m-route-live/manifest.json` | current route registers `SDX50M`, reaches `per_mgr_esoc0_any`, and has no WLFW/`wlan0` |
| `docs/reports/NATIVE_INIT_V1343_PROVIDER_READY_SDX50M_ROUTE_LIVE_2026-06-01.md` | human-readable V1343 decision |
| `docs/reports/NATIVE_INIT_V1222_POST_ESOC_POWER_BOUNDARY_2026-05-31.md` | earlier post-eSoC boundary reached but WLFW/BDF/`wlan0` absent |
| `docs/reports/NATIVE_INIT_V1318_CRITICAL_LOWER_TRACE_COLLECTOR_2026-05-31.md` | native AP-side activity: GPIO1270/GPIO135 present, GPIO142 absent |
| `docs/reports/NATIVE_INIT_V1324_PROVIDER_RESPONSE_DELTA_CLASSIFIER_2026-05-31.md` | native-vs-Android delta: Android gets GPIO142/PCIe/MHI/WLFW/`wlan0`, native does not |

## Classifier Shape

Add `scripts/revalidation/native_wifi_current_route_lower_response_reconcile_v1344.py`.

The runner should be host-only and read the existing manifests/reports. It must
not talk to the device. It should emit:

- `tmp/wifi/v1344-current-route-lower-response-reconcile/manifest.json`
- `tmp/wifi/v1344-current-route-lower-response-reconcile/summary.md`
- `docs/reports/NATIVE_INIT_V1344_CURRENT_ROUTE_LOWER_RESPONSE_RECONCILIATION_2026-06-01.md`

Minimum extracted fields:

| Field | Source |
| --- | --- |
| `v1343_sdx50m_registered` | V1343 manifest route analysis |
| `v1343_per_mgr_esoc0_any` | V1343 manifest route analysis |
| `v1343_wlfw_or_wlan_dmesg_seen` | V1343 manifest route analysis |
| `v1343_wlan0_up` | V1343 manifest route analysis |
| `v1222_esoc_boundary_reached` | V1222 report text or manifest, if present |
| `v1318_gpio135_high_count` | V1318 report table |
| `v1318_gpio142_line_count` | V1318 report table |
| `v1324_delta_label` | V1324 report decision text |
| `forbidden_action_seen` | union of Wi-Fi HAL/scan/connect/credential/DHCP/external ping/flash markers |

## Decision Labels

| Decision | Meaning | Next |
| --- | --- | --- |
| `v1344-current-route-matches-post-ap2mdm-response-gap` | V1343 reaches eSoC and still matches V1324: AP-side trigger without MDM2AP/PCIe response | plan V1345 bounded lower-response sampler using current V1343 route |
| `v1344-route-regressed-before-esoc` | current route no longer reaches SDX50M or eSoC | repair provider/CNSS route before lower work |
| `v1344-unexpected-wlfw-or-wlan0` | V1343 already saw WLFW/BDF/`wlan0` | stop lower-gap work and classify readiness before HAL/scan |
| `v1344-forbidden-action-detected` | any evidence says HAL/scan/connect/credentials/DHCP/external ping/flash happened | stop and audit the evidence chain |
| `v1344-insufficient-evidence` | required evidence is missing or unparsable | regenerate only the missing host report or bounded live evidence |

## Expected Outcome

Given the current evidence, the expected decision is:

```text
v1344-current-route-matches-post-ap2mdm-response-gap
```

That would make V1345 a bounded live observer, not a Wi-Fi connection attempt.
V1345 should focus on the current V1343 route and capture the first downstream
response after AP-side eSoC power-up:

- GPIO142 / MDM2AP interrupt count deltas.
- PCIe RC1/LTSSM dmesg deltas.
- MHI pipe and `ks` process appearance.
- WLFW/BDF/FW-ready/`wlan0` markers.
- `mdm3` state changes.

## Safety Contract

V1344 is host-only.

Blocked:

- device commands;
- PM/CNSS actor start;
- Wi-Fi HAL, `wificond`, scan/connect/link-up;
- credential use;
- DHCP/routes;
- external ping;
- manual `/dev/subsys_esoc0` open;
- eSoC ioctl/notify/BOOT_DONE spoof;
- PMIC/GPIO/GDSC writes;
- boot image write, flash, or partition write.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_current_route_lower_response_reconcile_v1344.py
python3 scripts/revalidation/native_wifi_current_route_lower_response_reconcile_v1344.py
jq '{decision,pass,reason,next_step}' tmp/wifi/v1344-current-route-lower-response-reconcile/manifest.json
git diff --check
run the focused secret-scan pattern only on new V1344 files
```

V1344 must not move to Wi-Fi HAL/scan/connect/DHCP/external ping. The final
Wi-Fi objective remains blocked until WLFW/BDF/`wlan0` lower readiness is proven
or the lower-response gap is intentionally changed by a separately approved gate.
