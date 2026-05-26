# V1035 Helper v176 Deploy Plan

- date: `2026-05-26`
- type: deploy-only helper parity
- input: `docs/reports/NATIVE_INIT_V1034_PM_SELINUX_DOMAIN_ALLOWLIST_SUPPORT_2026-05-26.md`
- helper artifact: `tmp/wifi/v1034-execns-helper-v176-build/a90_android_execns_probe`
- expected sha256: `dff34476d956574be59628f1177179cb8ef87a04dda0c68e97cc5afcf5310f2d`

## Objective

Deploy helper `a90_android_execns_probe v176` to
`/cache/bin/a90_android_execns_probe` only.

This closes the V1034 source/build unit and prepares the device for a V1036 PM
SELinux domain proof rerun. It must not start Android actors, service-manager,
CNSS daemons, Wi-Fi HAL, scan/connect, DHCP, routes, or external ping.

## Guardrails

- deploy-only
- no actor start
- no daemon start
- no Wi-Fi HAL start
- no scan/connect/link-up
- no credentials
- no DHCP, route, or external ping
- no eSoC ioctl, notify, BOOT_DONE, or subsystem open
- no boot image write
- no partition write
- no firmware mutation
- no GPIO/sysfs/debugfs write

## Commands

```bash
python3 -m py_compile scripts/revalidation/native_wifi_helper_v176_deploy_v1035.py
python3 scripts/revalidation/native_wifi_helper_v176_deploy_v1035.py plan
python3 scripts/revalidation/native_wifi_helper_v176_deploy_v1035.py \
  --apply \
  --assume-yes \
  --approval-phrase "approve v1035 deploy execns helper v176 only; no daemon start and no Wi-Fi bring-up" \
  run
```

## Success Criteria

- Local helper artifact exists and matches the expected sha256.
- Remote helper reports marker `a90_android_execns_probe v176`.
- Remote helper sha256 matches the V1034 artifact.
- No daemon, actor, Wi-Fi, eSoC, boot, partition, firmware, GPIO, sysfs, or
  debugfs action occurs.

## Next

V1036 should rerun the PM SELinux domain proof with helper `v176` and the
current-boot V490 policy-load precondition.
