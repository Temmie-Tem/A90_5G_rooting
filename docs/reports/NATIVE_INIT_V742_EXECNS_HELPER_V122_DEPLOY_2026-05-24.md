# Native Init V742 Execns Helper v122 Deploy Report

- date: `2026-05-24 KST`
- wrapper: `scripts/revalidation/wifi_execns_helper_v122_deploy_preflight.py`
- helper artifact: `tmp/wifi/v741-execns-helper-v122-build/a90_android_execns_probe`
- helper sha256: `032fe43041b908577bb1a2e4b3ff7a7dfea24958169723907df5d403f811e989`
- evidence: `tmp/wifi/v742-execns-helper-v122-deploy-run-serial1850/`
- decision: `execns-helper-v122-deploy-pass`
- pass: `true`

## Summary

V742 deployed helper v122 to `/cache/bin/a90_android_execns_probe` using the
serial appendfile path. The first serial run with chunk size `3000` failed
safely before writing because the generated `cmdv1x` line exceeded the safe
line limit. The rerun with chunk size `1850` completed and verified the remote
helper hash and marker.

No daemon start, Wi-Fi HAL start, scan/connect, DHCP/routes, external ping, or
boot/partition write was executed by this deploy unit.

## Key Results

| check | result |
| --- | --- |
| deploy method | serial appendfile + uudecode |
| safe chunk size | `1850` |
| chunks written | `739/739` |
| max command line | `3888` bytes under safe limit `3968` |
| remote sha256 | `032fe43041b908577bb1a2e4b3ff7a7dfea24958169723907df5d403f811e989` |
| remote marker | `a90_android_execns_probe v122` |
| V741 plan rerun | pass |

## Evidence

```text
decision: execns-helper-v122-deploy-pass
pass: True
reason: helper v122 deployed or already current; V741 plan was rerun
device_mutations: True
daemon_start_executed: False
wifi_bringup_executed: False
```

## Next Gate

Run the V741 service-`74` gated `mdm_helper` proof on the current boot after
refreshing `selinuxfs` and SELinux policy-load state.
