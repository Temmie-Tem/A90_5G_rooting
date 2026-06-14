# V873 Helper v136 Deploy-only Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| plan | `tmp/wifi/v873-execns-helper-v136-plan/manifest.json` | `execns-helper-v136-deploy-plan-ready` |
| preflight | `tmp/wifi/v873-execns-helper-v136-preflight/manifest.json` | `execns-helper-v136-deploy-preflight-ready` |
| deploy | `tmp/wifi/v873-execns-helper-v136-deploy/manifest.json` | `execns-helper-v136-deploy-pass` |

V873 deployed helper `v136` to `/cache/bin/a90_android_execns_probe`. It did
not start Android actors and did not bring up Wi-Fi.

## Deploy Details

| Item | Value |
| --- | --- |
| method | serial appendfile + uudecode |
| chunk size | `1850` |
| chunks written | `788` |
| encoded bytes | `1456699` |
| max cmdv1 line bytes | `3890` |
| safe line limit | `3968` |
| uses cmdv1x | `true` |

Remote helper:

```text
76dce733b8444073fc615a44df240aa7f8256dfb7f6c123c3f5e388907356980  /cache/bin/a90_android_execns_probe
```

Usage output includes:

- `a90_android_execns_probe v136`
- `wifi-companion-esoc-control-preflight`

## Guardrails

- No actor start, no `mdm_helper`, no `ks`, no `pm_proxy_helper`, no CNSS, no
  service-manager trio, and no Wi-Fi HAL.
- No scan/connect, credentials, DHCP/routes, or external ping.
- No live eSoC preflight or mutating eSoC ioctl in V873.

## Next

Run V874 bounded live eSoC control preflight.
