# V1035 Helper v176 Deploy Report

- date: `2026-05-26`
- scope: deploy-only helper parity
- decision: `execns-helper-v176-deploy-pass`
- pass: `True`
- evidence: `tmp/wifi/v1035-execns-helper-v176-deploy/manifest.json`
- helper: `/cache/bin/a90_android_execns_probe`
- helper marker: `a90_android_execns_probe v176`
- helper sha256: `dff34476d956574be59628f1177179cb8ef87a04dda0c68e97cc5afcf5310f2d`

## Summary

V1035 deployed helper `v176` only. The deployment used the existing serial
appendfile/uudecode path and did not run Android actors, service-manager, CNSS,
Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, or any eSoC
control path.

## Result

| Item | Value |
| --- | --- |
| decision | `execns-helper-v176-deploy-pass` |
| transfer method | `serial` |
| command | `serial appendfile + uudecode` |
| serial chunk size | `1850` |
| chunks written | `886` |
| encoded bytes | `1637328` |
| device mutation | `True` |
| Wi-Fi bring-up | `False` |

## Findings

- Helper `v176` is installed or already current at
  `/cache/bin/a90_android_execns_probe`.
- Remote deploy checks passed with the expected helper sha256.
- The only device mutation was helper replacement/parity verification.

## Guardrails

- no actor start
- no daemon start
- no Wi-Fi HAL start
- no scan/connect/link-up
- no credentials
- no DHCP, route, or external ping
- no eSoC ioctl, notify, BOOT_DONE, or subsystem open
- no boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs write

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_helper_v176_deploy_v1035.py
python3 scripts/revalidation/native_wifi_helper_v176_deploy_v1035.py plan
python3 scripts/revalidation/native_wifi_helper_v176_deploy_v1035.py \
  --apply \
  --assume-yes \
  --approval-phrase "approve v1035 deploy execns helper v176 only; no daemon start and no Wi-Fi bring-up" \
  run
python3 scripts/revalidation/a90ctl.py --timeout 5 bootstatus
python3 scripts/revalidation/a90ctl.py --timeout 5 selftest
```

Postflight:

```text
boot: BOOT OK shell
selftest: pass=11 warn=1 fail=0
```

## Next

Run V1036 PM SELinux domain proof with helper `v176`.
