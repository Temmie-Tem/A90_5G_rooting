# Native Init V1378 Execns Helper v283 Deploy Preflight

## Summary

- Cycle: `V1378`
- Type: deploy-only helper preflight
- Script: `scripts/revalidation/wifi_execns_helper_v283_deploy_preflight_v1378.py`
- Remote helper: `/cache/bin/a90_android_execns_probe`
- Helper: `a90_android_execns_probe v283`
- SHA256: `985eba4834b3b0324d886df39cecff9811ae183ea800119fdaea2d6ef8431a18`
- Decision: `execns-helper-v283-deploy-pass`
- Result: PASS
- Device mutation: replacing `/cache/bin/a90_android_execns_probe` only
- No daemon start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, flash, boot image write, or partition write occurred.

## Result Matrix

| field | value |
| --- | --- |
| decision | `execns-helper-v283-deploy-pass` |
| pass | `true` |
| remote sha verified | `true` |
| helper usage marker checked | `true` |
| post selftest | `pass` |
| deploy method | `serial` |
| serial chunks | `1061` |
| serial chunk size | `1800` |
| max cmdv1 line bytes | `3786` |
| device mutations | `true` |
| daemon start executed | `false` |
| wifi bringup executed | `false` |

## Transfer Notes

- NCM was inactive, so `auto` transfer selected serial fallback.
- V1378 used the V1375-proven safe `--serial-chunk-size 1800`.
- The serial transfer wrote `1061` chunks, used cmdv1x appendfile + uudecode, and kept max encoded line size `3786` below the safe limit `3968`.

## Post-Deploy Evidence

- `tmp/wifi/v1378-execns-helper-v283-deploy/manifest.json`
- `tmp/wifi/v1378-execns-helper-v283-deploy/post-deploy-steps.json`
- `tmp/wifi/v1378-execns-helper-v283-deploy/host/serial-install-helper.txt`
- `tmp/wifi/v1378-execns-helper-v283-deploy/native/sha-helper.txt`
- `tmp/wifi/v1378-execns-helper-v283-deploy/native/helper-usage.txt`

## Next Gate

V1379 may run the bounded Android participant parity + corrected RC1 enumerate gate using helper v283. The live gate must require `gate_pm_service_powerup_thread_count > 0`, remain below Wi-Fi HAL/scan/connect/network, and treat transport loss as reboot/recovery evidence rather than success.
