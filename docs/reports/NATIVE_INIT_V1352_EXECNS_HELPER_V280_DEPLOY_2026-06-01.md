# Native Init V1352 — Execns Helper v280 Deploy

- Date: 2026-06-01
- Cycle: `V1352`
- Type: deploy-only helper update
- Result: PASS

## Summary

V1352 deployed helper `a90_android_execns_probe v280` to
`/cache/bin/a90_android_execns_probe` so V1351 could run with the new
`cnss_wlfw_pre.*` observer flag.

## Evidence

| Field | Value |
| --- | --- |
| Deploy wrapper | `scripts/revalidation/wifi_execns_helper_v280_deploy_preflight_v1352.py` |
| Local helper | `stage3/linux_init/helpers/a90_android_execns_probe_v280` |
| Remote helper | `/cache/bin/a90_android_execns_probe` |
| Helper SHA256 | `509f7bb1eb599883d337afb167b29e271c3fe238e1bb1205fb9a93229263c278` |
| Deploy manifest | `tmp/wifi/v1352-execns-helper-v280-deploy/manifest.json` |
| Decision | `execns-helper-v280-deploy-pass` |

## Notes

- The first V1351 live attempt failed because the remote helper was still
  `a90_android_execns_probe v279`.
- V1352 updated the remote helper and the second V1351 run passed.
- `scripts/revalidation/tcpctl_host.py` now has an optional
  `--install-control-channel tcpctl` install mode for future cases where NCM is
  alive but the ACM bridge is unavailable. The default install control channel
  remains unchanged.

## Guardrails

No daemon start, Wi-Fi HAL start, scan/connect, credentials, DHCP/routes,
external ping, boot image write, or partition write was part of V1352.
