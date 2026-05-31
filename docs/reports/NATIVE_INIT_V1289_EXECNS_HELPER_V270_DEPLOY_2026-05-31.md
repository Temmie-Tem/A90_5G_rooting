# Native Init V1289 Execns Helper v270 Deploy

- generated: 2026-05-31
- cycle: V1289
- command: deploy-only
- decision: `execns-helper-v270-deploy-pass`
- pass: true
- helper: `a90_android_execns_probe v270`
- remote path: `/cache/bin/a90_android_execns_probe`
- sha256: `f1748fdc9c64a748c3270cd02a2b9bb796065b79632849e7384c2f37910f6e88`

## Result

| field | value |
| --- | --- |
| deploy method | serial fallback |
| chunks written | `1010` |
| line check | pass |
| remote SHA verification | pass |
| post-deploy selftest | `pass=11 warn=1 fail=0` |
| service-manager start | not executed |
| Wi-Fi bring-up | not executed |

Evidence:

- `tmp/wifi/v1289-execns-helper-v270-deploy/manifest.json`
- `tmp/wifi/v1289-execns-helper-v270-deploy/summary.md`
- `tmp/wifi/v1289-execns-helper-v270-deploy/host/serial-install-helper.txt`

## Safety

The deploy gate wrote only `/cache/bin/a90_android_execns_probe`. It did not
start service-manager, Wi-Fi HAL, CNSS, scan/connect, credential handling,
DHCP/routing, external ping, flash, boot image write, or partition write.

## Next

V1290 should rerun the bounded no-write TLMM/PCIe response sampler live with
helper v270.
