# Native Init V1354 — Execns Helper v281 Deploy

- Date: 2026-06-01
- Cycle: `V1354`
- Type: deploy-only helper update
- Result: PASS

## Summary

V1354 deployed helper `a90_android_execns_probe v281` to
`/cache/bin/a90_android_execns_probe` so the pcie1 RC power observer could run
with the new `mdm2ap_timing.*` pcie1/GPIO fields.

## Evidence

| Field | Value |
| --- | --- |
| Deploy wrapper | `scripts/revalidation/wifi_execns_helper_v281_deploy_preflight_v1354.py` |
| Local helper | `stage3/linux_init/helpers/a90_android_execns_probe_v281` |
| Remote helper | `/cache/bin/a90_android_execns_probe` |
| Helper SHA256 | `a68b2fb226d02d949890781ff72af8853958fcfb073a8d055068a48ba50d8c6f` |
| Transfer method | `serial appendfile + uudecode` |
| Serial chunks | `1061` |
| Max cmdv1 line bytes | `3786` of safe limit `3968` |
| Deploy manifest | `tmp/wifi/v1354-execns-helper-v281-deploy/manifest.json` |
| Decision | `execns-helper-v281-deploy-pass` |

## Notes

- NCM was not active, so the deploy used the serial fallback.
- A first attempt with `--serial-chunk-size 3000` failed before any write because
  the generated cmdv1 line would exceed the native console line limit.
- The successful deploy used `--serial-chunk-size 1800`, verified the target
  SHA256, and did not start daemons or Wi-Fi bring-up.

## Guardrails

No daemon start, Wi-Fi HAL start, scan/connect, credential handling,
DHCP/routes, external ping, boot image write, or partition write was part of the
deploy.
