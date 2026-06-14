# V1037 PM Runtime-Domain Guard Live v176 Report

- date: `2026-05-26`
- scope: bounded live PM runtime-domain proof
- helper: `a90_android_execns_probe v176`
- decision: `v1037-pm-full-contract-missing-no-open`
- pass: `True`
- evidence: `tmp/wifi/v1037-pm-runtime-domain-guard-live-v176/manifest.json`

## Summary

V1037 advanced beyond the V1032 blocker. With helper `v176` and current-boot
policy load, the PM runtime-domain guard no longer blocked PM actor execution:
all four guarded PM actor domains matched.

The next blocker is lower and more specific: the PM full fd contract did not
form. `pm_proxy_helper` and `pm-service` did not hold `/dev/subsys_modem`, so
service-manager/CNSS start and `/dev/subsys_esoc0` open remained blocked.

## Result

| Item | Value |
| --- | --- |
| decision | `v1037-pm-full-contract-missing-no-open` |
| runtime-domain guard blocked | `False` |
| runtime-domain guard matched | `4` |
| `pm_proxy_helper` started | `True` |
| `pm-service` started | `True` |
| `pm-proxy` started | `True` |
| `mdm_helper` started | `True` |
| PM full fd contract | `False` |
| `mdm_helper` `/dev/esoc-0` fd seen | `True` |
| service-manager start | `False` |
| CNSS daemon start | `False` |
| `/dev/subsys_esoc0` open attempted | `False` |
| live eSoC ioctl | `False` |
| Wi-Fi HAL start | `False` |
| scan/connect | `False` |
| credential use | `False` |
| DHCP/route | `False` |
| external ping | `False` |
| cleanup reboot | `True` |

## Findings

- Runtime-domain guard was active and matched all four guarded PM actor
  contexts.
- `pm_proxy_helper` and `pm-service` repeatedly reported zero
  `/dev/subsys_modem` fd matches.
- `mdm_helper` did acquire `/dev/esoc-0`.
- PM full-contract polling ran but never saw the required lower fd predicate.
- Because the actor/trigger stop state was not proven safe, cleanup reboot ran.
- Post-reboot device health stayed clean:
  `boot: BOOT OK shell`, `selftest: pass=11 warn=1 fail=0`.

## Interpretation

The current blocker is no longer PM SELinux domain entry. It is the missing PM
fd contract under otherwise-correct PM runtime domains.

Repeating V1037 unchanged is not useful. The next unit should classify the
Android/native delta for `pm_proxy_helper` and `pm-service` acquiring
`/dev/subsys_modem`, using V1024 Android PM fd evidence, V1028/V1029 PM
classifiers, V1036 domain proof, and V1037 live evidence.

## Guardrails

- no Wi-Fi HAL start
- no `wificond`
- no `IWifi.start` or `qcwlanstate` write
- no scan/connect/link-up
- no credentials
- no DHCP, route, or external ping
- no live eSoC ioctl, notify, or BOOT_DONE
- no `/dev/subsys_esoc0` open
- no boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs write

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_runtime_domain_guard_live_v1037.py
python3 scripts/revalidation/native_wifi_pm_runtime_domain_guard_live_v1037.py plan
python3 scripts/revalidation/native_wifi_pm_runtime_domain_guard_live_v1037.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-cnss-service-manager-matrix \
  --allow-cleanup-reboot \
  --assume-yes \
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

V1038 should be a host-only PM fd contract delta classifier. It should not run a
new live actor path until it can explain why the Android PM stack gets
`/dev/subsys_modem` fds and the V1037 native path does not.
