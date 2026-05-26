# V1026 Helper v174 Deploy Plan

- date: `2026-05-26`
- type: deploy-only
- helper: `a90_android_execns_probe v174`
- local artifact: `tmp/wifi/v1025-execns-helper-v174-build/a90_android_execns_probe`
- expected sha256: `07b9efdebddd955e388026afa2afed86cd52d762dcc4ac36638318f4661fe78f`

## Objective

Deploy helper `v174` to `/cache/bin/a90_android_execns_probe` so the next live
gate can test the Android PM full-contract order added in V1025.

## Scope

Allowed:

- serial helper file replacement under `/cache/bin`
- remote sha256 verification
- helper usage/contract parity verification
- native `bootstatus`, `selftest`, process, and link-surface checks

Forbidden:

- service-manager, CNSS, Wi-Fi HAL, `wificond`, supplicant, or hostapd live start
- Wi-Fi scan/connect/link-up
- credentials
- DHCP, routing, or external ping
- eSoC ioctl, subsystem open, GPIO/sysfs/debugfs write
- boot image or partition write

## Gate

The deploy passes only if:

1. local helper sha matches the V1025 build
2. native boot/selftest are healthy before deploy
3. no service-manager experiment is already running
4. no Wi-Fi link surface is active
5. remote helper sha matches after deploy
6. remote helper usage contains `v174` and the PM full-contract order

## Commands

```bash
python3 scripts/revalidation/native_wifi_helper_v174_deploy_v1026.py plan
python3 scripts/revalidation/native_wifi_helper_v174_deploy_v1026.py preflight
python3 scripts/revalidation/native_wifi_helper_v174_deploy_v1026.py \
  --apply \
  --assume-yes \
  --approval-phrase "approve v1026 deploy execns helper v174 only; no daemon start and no Wi-Fi bring-up" \
  run
```

## Next

If V1026 passes, proceed to V1027: bounded PM full-contract live classifier.
V1027 may start PM/CNSS actors but still must not scan/connect or use
credentials.
