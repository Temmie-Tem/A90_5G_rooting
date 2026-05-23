# Native Init V692 Peripheral Registry Snapshot Live Report

## Result

- decision: `v692-provider-registration-snapshot-captured`
- pass: `true`
- helper: `a90_android_execns_probe v116`
- helper sha256: `cce86ee252a045c7b8127b5e566abcb3ef24cdd89ac16d4592636838b9eb3e2b`
- deploy evidence: `tmp/wifi/v692-execns-helper-v116-deploy-live/`
- live evidence: `tmp/wifi/v692-peripheral-manager-registry-snapshot-orchestrated-live/`
- device mutations: `true`
- Wi-Fi HAL start: `false`
- scan/connect/link-up: `false`
- DHCP/external ping: `false`

## Scope

V692 extends the V690/V691 provider path with registry snapshots around
`pm-service` and `pm-proxy` start. It preserves the exact private property ack
contract and does not attempt Wi-Fi bring-up.

The live arm executed successfully. The first orchestrator process failed only
while assembling the host-side top-level manifest because of a missing local
`registry_surface` variable. The runner was fixed and the existing arm evidence
was reprocessed into the top-level V692 manifest without rerunning the device
arm.

## Registry Snapshot

All expected registry snapshot phases completed:

| phase | begin | end | child_count | dirs_captured | files_captured | child_proc_captured |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `before_initial_cnss_cleanup` | `1` | `1` | `9` | `2` | `0` | `0` |
| `after_initial_cnss_cleanup` | `1` | `1` | `9` | `2` | `0` | `0` |
| `after_per_mgr_probe` | `1` | `1` | `10` | `2` | `0` | `0` |
| `after_per_proxy_probe` | `1` | `1` | `11` | `2` | `0` | `0` |
| `window` | `1` | `1` | `12` | `2` | `0` | `0` |

Captured directory state used the private namespace paths:

- `/tmp/a90-v231-619/root/dev/__properties__`
- `/tmp/a90-v231-619/root/dev/socket`

Binder debug files were not exposed in this native surface, so
`files_captured=0` and `child_proc_captured=0` are expected for this run. The
useful signal is the complete phase coverage and `/dev/socket` registry state.

## Provider Surface

The provider pair became observable but still did not persist:

| child | start_order | observable | exit_code | signal | postflight_safe | context result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `per_mgr` | `10` | `1` | `0` | `0` | `1` | `no-default-context-for-target` |
| `per_proxy` | `11` | `1` | `1` | `0` | `1` | `no-default-context-for-target` |
| `cnss_daemon_retry` | `12` | `1` | `-1` | `9` | `1` | `u:r:vendor_wcnss_service:s0` |

The helper saw both provider readiness probes as ready, but the final result was
`start-only-runtime-gap` with reason `child-exited-before-observe-window`.
Therefore V692 captured the registration window but did not prove a persistent
PeripheralManager provider.

## Wi-Fi Markers

The lower path remained unchanged:

| marker | count |
| --- | ---: |
| QRTR RX/TX | `1` / `1` |
| `sysmon-qmi` | `4` |
| service-notifier `180` | `1` |
| service-notifier `74` | `1` |
| `cnss-daemon` netlink | `10` |
| `cnss-daemon` `cld80211` | `4` |
| Binder transaction failed | `1` |
| QMI server connected | `0` |
| WLFW start/request | `0` |
| BDF `regdb`/`bdwlan` | `0` |
| WLAN firmware ready | `0` |
| `wlan0` | `0` |

## Guardrails

- no Wi-Fi HAL or `wificond` start;
- no supplicant or hostapd start;
- no scan/connect/link-up;
- no credential use;
- no DHCP, route change, or external ping;
- no sysfs subsystem state write;
- no `esoc0` open or hold;
- no boot image or partition write.

## Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_peripheral_manager_registry_snapshot_v692.py \
  scripts/revalidation/native_wifi_peripheral_manager_registry_snapshot_orchestrator_v692.py \
  scripts/revalidation/wifi_execns_helper_v116_deploy_preflight.py

scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v692-execns-helper-v116-build/a90_android_execns_probe

python3 scripts/revalidation/wifi_execns_helper_v116_deploy_preflight.py \
  --out-dir tmp/wifi/v692-execns-helper-v116-deploy-live \
  --apply --assume-yes \
  --approval-phrase "approve v692 deploy execns helper v116 only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/native_wifi_peripheral_manager_registry_snapshot_orchestrator_v692.py \
  --out-dir tmp/wifi/v692-peripheral-manager-registry-snapshot-orchestrated-live \
  --apply --assume-yes \
  run

git diff --check
```

The changed-file secret scan was restricted to the V692 plan, scripts, helper
source, and docs index. It found only guardrail text such as `credential use`
and no configured SSID/passphrase.

## Next Gate

V693 should parse the captured `/dev/socket` registry snapshots and provider
stdout/stderr to determine whether `pm-service` registers anything before
`pm-proxy` exits. If no registration appears, the next repair should target the
provider runtime/context/default-service mapping rather than starting Wi-Fi HAL
or attempting scan/connect.
