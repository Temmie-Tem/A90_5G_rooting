# V1026 Helper v174 Deploy

- date: `2026-05-26`
- scope: deploy-only
- helper: `a90_android_execns_probe v174`
- decision: `execns-helper-v174-deploy-pass`
- pass: `True`
- evidence: `tmp/wifi/v1026-execns-helper-v174-deploy-retry/manifest.json`
- failed safety-check attempt: `tmp/wifi/v1026-execns-helper-v174-deploy/manifest.json`

## Summary

Helper `v174` was deployed to `/cache/bin/a90_android_execns_probe` and verified
by remote sha and usage/contract parity.

The first run used `--serial-chunk-size 3000`; the deploy precheck rejected it
before writing any chunks because it exceeded the native console safe line
limit. The retry used the default safe chunk size and completed.

## Result

| Item | Value |
| --- | --- |
| decision | `execns-helper-v174-deploy-pass` |
| remote sha | `07b9efdebddd955e388026afa2afed86cd52d762dcc4ac36638318f4661fe78f` |
| chunks written | `886` |
| daemon start | `False` |
| Wi-Fi bring-up | `False` |
| device mutation | `/cache/bin/a90_android_execns_probe` replacement only |

Postflight checks passed:

- native health: `BOOT OK`, selftest `fail=0`
- service-manager experiment process count: `0`
- Wi-Fi link surface count: `0`
- remote helper sha: matched
- remote helper contract: `v174`, service-manager matrix mode, PM full-contract order

## Guardrails

- no service-manager/CNSS/Wi-Fi HAL live start
- no Wi-Fi scan/connect/link-up
- no credentials
- no DHCP/route/external ping
- no eSoC ioctl/subsystem open
- no GPIO/sysfs/debugfs write
- no boot image or partition write

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_helper_v174_deploy_v1026.py
python3 scripts/revalidation/native_wifi_helper_v174_deploy_v1026.py plan
python3 scripts/revalidation/native_wifi_helper_v174_deploy_v1026.py preflight
python3 scripts/revalidation/native_wifi_helper_v174_deploy_v1026.py \
  --apply \
  --assume-yes \
  --approval-phrase "approve v1026 deploy execns helper v174 only; no daemon start and no Wi-Fi bring-up" \
  run
git diff --check
```

## Next

Proceed to V1027: run the bounded PM full-contract live classifier using helper
`v174`. The next gate should prove whether `pm_proxy_helper` and `pm-service`
both hold `/dev/subsys_modem` before a post-provider subsystem retry can arm.
