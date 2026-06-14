# Native Init V830 Service-notifier Listener Probe Report

## Result

- decision: `v830-service-notifier-listener-state-not-up`
- pass: `true`
- reason: listener registered but current state is `uninit`
- evidence: `tmp/wifi/v830-service-notifier-listener-run-20260525-115840/`
- runner: `scripts/revalidation/native_wifi_service_notifier_listener_probe_v830.py`
- helper: `a90_android_execns_probe v127`
- helper sha256: `e2ba21fc7f00afc433fa23358d05780dcc0e5288bfc7db7d015e87c61d3e36d7`

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_service_notifier_listener_probe_v830.py \
  scripts/revalidation/wifi_execns_helper_v127_deploy_preflight.py

strings tmp/wifi/v830-execns-helper-v127-build/a90_android_execns_probe \
  | rg 'a90_android_execns_probe v127|--allow-service-notifier-listener-probe|--qrtr-readback-matrix'

python3 scripts/revalidation/native_wifi_service_notifier_listener_probe_v830.py \
  --out-dir tmp/wifi/v830-service-notifier-listener-plan-check \
  plan

python3 scripts/revalidation/native_wifi_service_notifier_listener_probe_v830.py \
  --out-dir tmp/wifi/v830-service-notifier-listener-preflight \
  preflight

python3 scripts/revalidation/native_wifi_service_notifier_listener_probe_v830.py \
  --out-dir tmp/wifi/v830-service-notifier-listener-run-20260525-115840 \
  run
```

## Evidence Summary

- service-notifier endpoint: service `66`, encoded instance `46081`, node `0`,
  port `2`
- request bytes: `31`
- response: QMI result `0`, error `0`
- response current state: `0x7fffffff` / `uninit`
- state indication: not observed
- ACK: not sent because no indication arrived
- cleanup reboot: executed
- post-cleanup health: native build `0.9.68 (v724)`, status `ok`

## Guardrails

- service-manager: not executed
- Wi-Fi HAL: not executed
- scan/connect/link-up: not executed
- credential use: not executed
- DHCP/route/external ping: not executed
- `esoc0`, module load/unload, boot image write, partition write, custom-kernel
  flash: not executed

## Interpretation

V829 eliminated the `pd-mapper` empty-domain hypothesis. V830 proves the
service-notifier endpoint accepts the listener registration for
`msm/modem/wlan_pd`, but reports `SERVREG_SERVICE_STATE_UNINIT`. The current
blocker is therefore not domain-list discovery or listener registration. The
next useful gate is a narrower modem/WLAN-PD online trigger classifier that can
explain why the registered service remains uninitialized before any Wi-Fi HAL,
scan, connect, or external network attempt.
