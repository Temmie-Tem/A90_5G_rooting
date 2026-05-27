# Native Init V1131 Execns Helper v213 Deploy Plan

Date: `2026-05-27`

## Objective

Deploy the V1130-built `a90_android_execns_probe v213` helper to
`/cache/bin/a90_android_execns_probe` and verify that the remote helper exposes
the PM observer modem pre-holder contract needed for the next bounded live gate.

## Preconditions

- Local helper artifact:
  `tmp/wifi/v1130-execns-helper-v213-build/a90_android_execns_probe`
- Expected helper marker: `a90_android_execns_probe v213`
- Expected helper sha256:
  `d1c354b2b089ede50cc53d452666d119e9151b1e97b7bb1344dbd0431bd69356`
- Native baseline: `A90 Linux init 0.9.68 (v724)`
- Device health: `selftest` has `fail=0`

## Scope

The deploy step may write only the helper under `/cache/bin/`.

It must not start PM actors, service-manager actors, CNSS, Wi-Fi HAL, scanning,
association, DHCP, route changes, external ping, partition writes, boot image
writes, or flashing.

## Validation

Run:

```bash
python3 -m py_compile scripts/revalidation/wifi_execns_helper_v213_deploy_preflight.py
python3 scripts/revalidation/wifi_execns_helper_v213_deploy_preflight.py plan
python3 scripts/revalidation/wifi_execns_helper_v213_deploy_preflight.py preflight
python3 scripts/revalidation/wifi_execns_helper_v213_deploy_preflight.py \
  --approval-phrase "approve v1131 deploy execns helper v213 only; no Wi-Fi HAL start and no Wi-Fi bring-up" \
  --apply \
  --assume-yes \
  run
```

## Success Criteria

- Local helper sha and marker match V1130.
- Native version and selftest pass.
- Remote helper is deployed or already current.
- Remote usage exposes `wifi-companion-pm-service-trigger-observer`.
- V373 post-deploy preflight advances past the helper-mode blocker.
- The manifest records `daemon_start_executed=false` and
  `wifi_bringup_executed=false`.

## Next

V1131 live should combine the current-boot V401/V490 preconditions, global
firmware mounts, the PM observer order, and the new modem pre-holder flags to
classify whether `/dev/subsys_modem` first-opener state advances
`mss`/`mdm3`/WLFW/`wlan0`.
