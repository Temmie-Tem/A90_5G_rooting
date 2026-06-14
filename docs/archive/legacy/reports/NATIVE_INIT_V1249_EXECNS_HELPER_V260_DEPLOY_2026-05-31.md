# V1249 Execns Helper v260 Deploy

- report: `docs/reports/NATIVE_INIT_V1249_EXECNS_HELPER_V260_DEPLOY_2026-05-31.md`
- deploy wrapper: `scripts/revalidation/wifi_execns_helper_v260_deploy_preflight_v1249.py`
- helper binary: `stage3/linux_init/helpers/a90_android_execns_probe_v260`
- remote path: `/cache/bin/a90_android_execns_probe`
- evidence: `tmp/wifi/v1249-execns-helper-v260-deploy/manifest.json`
- result: `execns-helper-v260-deploy-pass`
- pass: `true`
- helper sha256: `0313d613d95c56af5681871062b7fceb47ede3c3ef8fcff534d0eea3338eaa2f`

## Scope

V1249 deployed helper v260 only. It did not start Android service-manager, PM,
CNSS, Wi-Fi HAL, wificond, supplicant, scan/connect, credentials, DHCP/routes,
or external ping.

## Deployment

NCM was not active, so deployment used serial fallback. A first attempt with
`--serial-chunk-size 3000` was rejected by the deploy guard because the encoded
cmdv1x line would exceed the native console safe line limit. The successful run
used `--serial-chunk-size 1800`.

| Field | Value |
| --- | --- |
| Method | `serial appendfile + uudecode` |
| Chunk size | `1800` |
| Chunks written | `1010` |
| Line check | `pass` |
| Remote SHA | `0313d613d95c56af5681871062b7fceb47ede3c3ef8fcff534d0eea3338eaa2f` |

## Safety

- deploy-only; no PMIC/GPIO/debugfs/regulator write
- no eSoC ioctl, PM actor, CNSS actor, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, reboot, flash, boot image write, or partition write

## Next

V1250 should run only the read-only PMIC soft-reset preflight mode from helper
v260.
