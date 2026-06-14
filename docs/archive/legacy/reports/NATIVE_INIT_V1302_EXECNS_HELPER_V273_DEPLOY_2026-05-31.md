# Native Init V1302 Execns Helper v273 Deploy

## Summary

- Cycle: `V1302`
- Type: deploy-only
- Decision: `execns-helper-v273-deploy-pass`
- Result: PASS
- Remote helper: `/cache/bin/a90_android_execns_probe`
- Expected SHA256: `dd1d15a5ef01189526720814c50b007f6dc9a0f25e9239caf0e9da34c65b6b46`
- Evidence:
  - `tmp/wifi/v1302-execns-helper-v273-deploy/manifest.json`
  - `tmp/wifi/v1302-execns-helper-v273-deploy/summary.md`
  - `tmp/wifi/v1302-execns-helper-v273-deploy/host/serial-install-helper.txt`
  - `tmp/wifi/v1302-execns-helper-v273-deploy/post-deploy-steps.json`

V1302 deployed the V1301-built `a90_android_execns_probe v273` helper to `/cache/bin/a90_android_execns_probe`. NCM was not active, so the wrapper used serial fallback.

## Deploy Result

| field | value |
| --- | --- |
| method | `serial` |
| chunk_size | `1800` |
| chunks | `1010` |
| chunks_written | `1010` |
| encoded_bytes | `1817918` |
| line_check_ok | `true` |
| max_cmdv1_line_bytes | `3788` |
| safe_line_limit | `3968` |
| uses_cmdv1x | `true` |

The remote post-deploy sha check returned:

```text
dd1d15a5ef01189526720814c50b007f6dc9a0f25e9239caf0e9da34c65b6b46  /cache/bin/a90_android_execns_probe
```

## Postflight

- Native version remained `A90 Linux init 0.9.68 (v724)`.
- Native selftest remained `pass=11 warn=1 fail=0`.
- Service-manager post-deploy preflight returned `service-manager-start-only-smoke-approval-required`, which is expected because V1302 is deploy-only.
- `daemon_start_executed=false`.
- `wifi_bringup_executed=false`.

## Safety

- Device mutation was limited to replacing `/cache/bin/a90_android_execns_probe`.
- No PM/CNSS actor start, Wi-Fi HAL, scan/connect, credential use, DHCP/routes, external ping, PMIC write, GPIO request/hold, direct eSoC ioctl, flash, boot image write, or partition write occurred.

## Next

V1303 should run the bounded compact dense live sampler with helper `v273` and require the new `powerup_marker` keys. The expected useful output is whether `powerup_thread_count` becomes positive during the response window while GPIO142/PCIe/MHI/WLFW/`wlan0` remain absent.
