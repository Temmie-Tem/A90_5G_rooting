# V1041 PM Full-Contract v177 Live

- date: `2026-05-26`
- scope: bounded live PM full-contract proof
- helper: `a90_android_execns_probe v177`
- decision: `v1041-pm-runtime-domain-guard-blocked-clean`
- pass: `True`
- evidence: `tmp/wifi/v1041-pm-full-contract-v177-live/manifest.json`

## Summary

V1041 verified that helper `v177` is deployed and callable, but the live PM
full-contract path did not advance to the fd predicate. The runtime-domain guard
blocked all four PM actors because `/proc/self/attr/exec` remained `kernel`
instead of the requested Android service domains.

This is a clean fail-closed result. Target `execv` was blocked before the PM
actors could run in the wrong domain. Service-manager, CNSS, Wi-Fi HAL,
`wificond`, scan/connect, DHCP, external ping, and `/dev/subsys_esoc0` open did
not execute.

## Result

| Item | Value |
| --- | --- |
| remote helper sha/marker | pass |
| runtime-domain guard blocked | `True` |
| blocked children | `pm_proxy_helper`, `per_mgr_light`, `pm_proxy`, `mdm_helper` |
| matched guarded children | `0` |
| `pm-proxy` expected domain | `u:r:vendor_per_proxy:s0` |
| observed exec attr | `kernel` |
| PM fd contract | not reached |
| service-manager start | `False` |
| CNSS daemon start | `False` |
| `/dev/subsys_esoc0` open attempted | `False` |
| Wi-Fi HAL / scan / connect | `False` |
| external ping | `False` |
| cleanup reboot | not needed |

## Interpretation

V1039 fixed the helper source mapping for `pm-proxy`, and V1040 deployed that
helper. V1041 shows the next prerequisite was missing in the current boot:
current-boot SELinux policy/domain refresh was not in the same proven state as
V1036/V1037.

The corrected expected context is visible: `pm-proxy` now expects
`u:r:vendor_per_proxy:s0`. The blocker is not the `pm-proxy` mapping anymore;
it is that the live exec attr still reads `kernel` for every guarded PM actor.

## Guardrails

- No Wi-Fi HAL start.
- No `wificond`.
- No `IWifi.start` or `qcwlanstate` write.
- No scan/connect/link-up.
- No credentials.
- No DHCP, route, or external ping.
- No live eSoC ioctl, notify, or BOOT_DONE.
- No `/dev/subsys_esoc0` open.
- No boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs write.

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_full_contract_v177_live_v1041.py
python3 scripts/revalidation/native_wifi_pm_full_contract_v177_live_v1041.py plan
python3 scripts/revalidation/native_wifi_pm_full_contract_v177_live_v1041.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-cnss-service-manager-matrix \
  --allow-cleanup-reboot \
  --assume-yes \
  run
```

Live result:

```text
decision: v1041-pm-runtime-domain-guard-blocked-clean
pass: True
subsys_esoc0_open_attempted: False
wifi_bringup_executed: False
external_ping_executed: False
```

## Next

V1042 should refresh/prove the current-boot SELinux policy and PM domain proof
with helper `v177`, analogous to the V1036 precondition, before rerunning the PM
full-contract live gate. Do not retry V1041 unchanged.
