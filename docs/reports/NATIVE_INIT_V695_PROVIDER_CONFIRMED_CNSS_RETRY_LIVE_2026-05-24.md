# Native Init V695 Provider-confirmed CNSS Retry Live Report

- date: `2026-05-24 KST`
- status: `live-pass`; Wi-Fi external ping is **not** complete
- helper: `a90_android_execns_probe v118`
- helper build: `tmp/wifi/v695-execns-helper-v118-build/a90_android_execns_probe`
- deploy evidence: `tmp/wifi/v695-execns-helper-v118-deploy-live-serial1850/`
- live evidence: `tmp/wifi/v695-provider-confirmed-cnss-retry-orchestrated-live/`
- decision: `v695-provider-confirmed-cnss-retry-gap-persists`

## Scope

V695 ran a single bounded private-namespace companion sequence that confirmed
`vendor.qcom.PeripheralManager` through `/vendor/bin/vndservice list` and then
started a fresh `cnss-daemon` retry tail.

The proof remained below Wi-Fi bring-up. It did not start Wi-Fi HAL,
`wificond`, supplicant, or hostapd; did not scan/connect/link-up; did not use
credentials, DHCP, routes, or external ping; did not write subsystem sysfs
nodes; and did not write boot partitions.

## Result

| key | value |
| --- | --- |
| decision | `v695-provider-confirmed-cnss-retry-gap-persists` |
| pass | `True` |
| helper marker | `a90_android_execns_probe v118` |
| helper sha256 | `7f91a939df2333dde0d92548d236a321d4b0adcce3d02e4d462e9178ac447e36` |
| current boot prep | pass |
| service `180/74` | pass |
| `vndservice` query ran | pass |
| exact provider match | pass |
| CNSS retry start order | `12` |
| CNSS retry observable | `1` |
| CNSS retry postflight safe | `1` |
| Wi-Fi HAL start | `False` |
| scan/connect | `False` |
| external ping | `False` |

## Query Evidence

| phase | exit | timeout | exact match | stdout bytes | stderr bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| `after_per_mgr_probe` | `0` | `0` | `1` | `2416` | `1457` |
| `after_per_proxy_probe` | `0` | `0` | `1` | `2422` | `1457` |

Both phases reported `vendor_qcom_peripheral_manager_seen=1`.

## Runtime Markers

| marker | count |
| --- | ---: |
| QRTR RX | `1` |
| QRTR TX | `1` |
| `sysmon-qmi` | `4` |
| service-notifier aggregate | `2` |
| service `180` | `1` |
| service `74` | `1` |
| CNSS netlink | `10` |
| CNSS `cld80211` | `4` |
| CNSS Binder transaction failed | `1` |
| kernel warning | `1` |
| QMI server connected | `0` |
| WLFW start | `0` |
| WLFW service request | `0` |
| WLAN-PD | `0` |
| BDF `regdb` | `0` |
| BDF `bdwlan` | `0` |
| firmware ready | `0` |
| `wlan0` | `0` |

## Interpretation

V695 removes two earlier blockers from the primary path:

- `vendor.qcom.PeripheralManager` registration is present in the private
  `vndservicemanager` namespace.
- A fresh `cnss-daemon` retry tail starts after that confirmed registration.

The remaining gap is below the userspace provider ordering repair. The retry
reaches CNSS netlink/`cld80211`, but WLFW service `69`, BDF transfer, firmware
ready, and `wlan0` creation still do not appear. The live dmesg delta also
captures a `pm_qos_add_request() called for already added request` warning in
the service `74` window and one CNSS Binder `-22` transaction failure.

## Validation

Executed:

```bash
mkdir -p tmp/wifi/v695-execns-helper-v118-build
bash scripts/revalidation/build_android_execns_probe_helper.sh tmp/wifi/v695-execns-helper-v118-build/a90_android_execns_probe
python3 -m py_compile scripts/revalidation/native_wifi_provider_confirmed_cnss_retry_v695.py scripts/revalidation/native_wifi_provider_confirmed_cnss_retry_orchestrator_v695.py scripts/revalidation/wifi_execns_helper_v118_deploy_preflight.py
python3 scripts/revalidation/wifi_execns_helper_v118_deploy_preflight.py --out-dir tmp/wifi/v695-execns-helper-v118-deploy-live-serial1850 --transfer-method serial --serial-chunk-size 1850 --approval-phrase "approve v695 deploy execns helper v118 only; no daemon start and no Wi-Fi bring-up" --apply --assume-yes run
python3 scripts/revalidation/native_wifi_provider_confirmed_cnss_retry_orchestrator_v695.py --out-dir tmp/wifi/v695-provider-confirmed-cnss-retry-orchestrated-live --apply --assume-yes run
printf '\nselftest\n' | nc -w 10 127.0.0.1 54321
```

Post-run `selftest` returned `pass=11 warn=1 fail=0`.

## Next Gate

Plan V696 as a post-provider retry blocker classifier:

- keep Wi-Fi HAL, scan/connect, DHCP, credentials, routes, and external ping
  blocked;
- compare the V695 dmesg service `74` to CNSS retry window against Android
  reference evidence;
- classify whether the primary next blocker is the CNSS Binder `-22`, the
  duplicate `pm_qos` request warning, or another missing kernel-side trigger
  before WLFW service `69`.
