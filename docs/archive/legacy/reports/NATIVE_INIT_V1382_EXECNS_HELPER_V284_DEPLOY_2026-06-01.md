# Native Init V1382 Execns Helper v284 Deploy Preflight

## Summary

- Cycle: `V1382`
- Type: deploy-only helper preflight
- Script: `scripts/revalidation/wifi_execns_helper_v284_deploy_preflight_v1382.py`
- Remote helper: `/cache/bin/a90_android_execns_probe`
- Helper: `a90_android_execns_probe v284`
- SHA256: `da1f8b65cbc3872f7ec31a368bd382720a399d3a785e50ae383c800632047b9f`
- Decision: `execns-helper-v284-deploy-pass`
- Result: PASS
- Device mutation: replacing `/cache/bin/a90_android_execns_probe` only
- No daemon start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, flash, boot image write, or partition write occurred.

## Result Matrix

| field | value |
| --- | --- |
| decision | `execns-helper-v284-deploy-pass` |
| pass | `true` |
| remote sha verified | `true` |
| helper usage marker checked | `true` |
| helper immediate flag checked | `true` |
| helper output markers source/build verified | `true` |
| post selftest | `pass` |
| deploy method | `serial` |
| serial chunks | `1061` |
| serial chunk size | `1800` |
| max cmdv1 line bytes | `3788` |
| device mutations | `true` |
| daemon start executed | `false` |
| wifi bringup executed | `false` |
| V373 post-deploy preflight | `service-manager-start-only-smoke-approval-required` |

## Transfer Notes

- NCM was not reachable during preflight, so `auto` transfer selected serial fallback.
- V1382 used the V1375/V1378-proven safe `--serial-chunk-size 1800`.
- The serial transfer wrote `1061` chunks, used cmdv1x appendfile + uudecode, and kept max encoded line size `3788` below the safe limit `3968`.

## Post-Deploy Native Steps

| step | result | rc | status | file |
| --- | --- | --- | --- | --- |
| version | PASS | 0 | ok | `native/version.txt` |
| status | PASS | 0 | ok | `native/status.txt` |
| selftest | PASS | 0 | ok | `native/selftest.txt` |
| netservice-status | PASS | 0 | ok | `native/netservice-status.txt` |
| stat-helper | PASS | 0 | ok | `native/stat-helper.txt` |
| sha-helper | PASS | 0 | ok | `native/sha-helper.txt` |
| helper-usage | FAIL | 2 | error | `native/helper-usage.txt` |
| ps | PASS | 0 | ok | `native/ps.txt` |
| proc-net-dev | PASS | 0 | ok | `native/proc-net-dev.txt` |

Note: `helper-usage` exits non-zero when invoked without a full mode, but it printed the v284 marker and immediate corrected RC1 flag required for deploy verification. V1381 already verified the internal output markers in the source/build artifact.

## Evidence

- `tmp/wifi/v1382-execns-helper-v284-deploy/manifest.json`
- `tmp/wifi/v1382-execns-helper-v284-deploy/post-deploy-steps.json`
- `tmp/wifi/v1382-execns-helper-v284-deploy/host/serial-install-helper.txt`
- `tmp/wifi/v1382-execns-helper-v284-deploy/native/sha-helper.txt`
- `tmp/wifi/v1382-execns-helper-v284-deploy/native/helper-usage.txt`
- `tmp/wifi/v1382-execns-helper-v284-deploy/v373-preflight/manifest.json`

## Next Gate

V1383 may run the bounded Android participant parity + immediate corrected RC1 live gate using helper v284. It must measure `__subsystem_get(esoc0)` to corrected-RC1 timing, record GPIO142/PCI/MHI/WLFW/`wlan0`, and stay below Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, PMIC/GPIO/GDSC direct writes, eSoC notify/`BOOT_DONE`, flash, boot image write, and partition write.
