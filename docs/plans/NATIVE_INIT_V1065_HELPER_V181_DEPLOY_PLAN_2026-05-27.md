# Native Init V1065 Helper v181 Deploy Plan

Date: `2026-05-27`

## Goal

Deploy the V1064 `a90_android_execns_probe v181` helper to `/cache/bin/a90_android_execns_probe` and verify remote parity without starting Android daemons or Wi-Fi bring-up.

## Gate

- Cycle label: `v1065-execns-helper-v181-deploy`.
- Local artifact: `tmp/wifi/v1064-pm-service-trigger-observer-helper/a90_android_execns_probe`.
- Expected sha256: `74eaa88bf8221715ed2afae654e53eb7571037655dd6b8e0df0966ab454ef9ce`.
- Remote path: `/cache/bin/a90_android_execns_probe`.
- Transfer path: authenticated NCM/TCP `a90_tcpctl` install flow.

## Guardrails

- Only `/cache/bin/a90_android_execns_probe` may be replaced.
- No service-manager, CNSS daemon, Wi-Fi HAL, `wificond`, scan/connect, DHCP, external ping, eSoC ioctl, subsystem open, GPIO/sysfs/debugfs write, boot image write, partition write, or firmware mutation.
- Verify native health and `netservice` status after deployment.

## Success Criteria

- Remote sha256 equals the local helper sha256.
- Remote helper usage contains `a90_android_execns_probe v181`, `wifi-companion-pm-service-trigger-observer`, and `--allow-pm-service-trigger-observer`.
- Post-deploy native selftest remains `fail=0`.
- NCM/TCP remains running with authenticated `tcpctl`.
