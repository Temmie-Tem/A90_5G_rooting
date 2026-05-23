# Native Init V695 Provider-confirmed CNSS Retry Plan

- date: `2026-05-24 KST`
- cycle: `v695`
- target helper: `a90_android_execns_probe v118`
- target mode: `wifi-companion-service74-gated-peripheral-manager-vndservice-query-cnss-retry-start-only`

## Goal

V694 proved that `pm-service` registers `vendor.qcom.PeripheralManager` through
the private `vndservicemanager` namespace. V695 closes the next ordering gap by
running the same bounded provider query and then starting one fresh
`cnss-daemon` retry tail in the same helper invocation.

This keeps the proof below Wi-Fi bring-up while distinguishing three states:

- provider registration is present but CNSS retry is withheld;
- provider registration is present and CNSS retry runs, but WLFW/BDF/`wlan0`
  remain absent;
- provider registration plus CNSS retry advances WLFW/BDF/`wlan0`.

## Gate

Expected order:

```text
qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon,
service74_gate,servicemanager,hwservicemanager,vndservicemanager,
vndservicemanager_ready,cnss_daemon_initial_cleanup,
per_mgr,vndservice_query,per_proxy,vndservice_query,cnss_daemon_retry
```

Success labels:

- `v695-provider-confirmed-cnss-retry-wifi-surface-advanced`: provider
  registration was confirmed, retry ran, and WLFW/BDF/`wlan0` advanced.
- `v695-provider-confirmed-cnss-retry-gap-persists`: provider registration was
  confirmed and retry ran, but WLFW/BDF/`wlan0` remained absent.
- `v695-provider-confirmed-cnss-retry-withheld`: provider registration was
  confirmed, but the retry tail did not start.

## Guardrails

V695 must not:

- start Wi-Fi HAL, `wificond`, supplicant, or hostapd;
- scan, connect, link up, use credentials, run DHCP, change routes, or external ping;
- write subsystem sysfs nodes or open/hold `esoc0`;
- write boot images or partitions.

## Implementation

- Add helper v118 mode that combines the V694 `vndservice` query with the V690
  CNSS retry tail.
- Keep both `vndservice` query phases bounded to 3000 ms.
- Deploy helper v118 with serial chunk size `1850` to avoid unsafe long command
  lines and NCM endpoint ambiguity.
- Add direct V695 runner, current-boot orchestrator, and helper deploy wrapper.

## Validation Plan

```bash
mkdir -p tmp/wifi/v695-execns-helper-v118-build
bash scripts/revalidation/build_android_execns_probe_helper.sh tmp/wifi/v695-execns-helper-v118-build/a90_android_execns_probe
python3 -m py_compile \
  scripts/revalidation/native_wifi_provider_confirmed_cnss_retry_v695.py \
  scripts/revalidation/native_wifi_provider_confirmed_cnss_retry_orchestrator_v695.py \
  scripts/revalidation/wifi_execns_helper_v118_deploy_preflight.py
python3 scripts/revalidation/wifi_execns_helper_v118_deploy_preflight.py --out-dir tmp/wifi/v695-execns-helper-v118-deploy-preflight-current-rerun preflight
python3 scripts/revalidation/wifi_execns_helper_v118_deploy_preflight.py --out-dir tmp/wifi/v695-execns-helper-v118-deploy-live-serial1850 --transfer-method serial --serial-chunk-size 1850 --approval-phrase "approve v695 deploy execns helper v118 only; no daemon start and no Wi-Fi bring-up" --apply --assume-yes run
python3 scripts/revalidation/native_wifi_provider_confirmed_cnss_retry_orchestrator_v695.py --out-dir tmp/wifi/v695-provider-confirmed-cnss-retry-orchestrated-live --apply --assume-yes run
```
