# V1037 PM Runtime-Domain Guard Live v176 Plan

- date: `2026-05-26`
- type: bounded live PM runtime-domain proof
- input: `docs/reports/NATIVE_INIT_V1036_PM_SELINUX_DOMAIN_PROOF_V176_2026-05-26.md`
- helper: `/cache/bin/a90_android_execns_probe`
- helper version: `a90_android_execns_probe v176`
- helper sha256: `dff34476d956574be59628f1177179cb8ef87a04dda0c68e97cc5afcf5310f2d`

## Objective

Rerun the V1032 PM full-contract order with helper `v176` and
`--require-android-selinux-exec-match`.

V1036 proved the required PM domains can be entered after policy load. V1037
therefore tests the real actor path and stops at the existing lower PM fd
predicate before any subsystem open or Wi-Fi bring-up.

## Gate

The only allowed live order is:

```text
property shim
  -> pm_proxy_helper
  -> pm-service
  -> pm-proxy
  -> mdm_helper
  -> PM fd predicate
  -> service-manager/CNSS matrix only if lower guards pass
```

The runtime-domain guard remains active. If PM actor domains do not match the
requested Android SELinux contexts, target `execv` must be blocked.

## Guardrails

- no Wi-Fi HAL start
- no `wificond`
- no `IWifi.start`
- no `qcwlanstate` write
- no scan/connect/link-up
- no credentials
- no DHCP, route, or external ping
- no live eSoC ioctl, notify, or BOOT_DONE
- no `/dev/subsys_esoc0` open unless all lower gates pass
- no boot image write
- no partition write
- no firmware mutation
- no GPIO/sysfs/debugfs write

## Commands

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
```

## Success Criteria

- Runtime-domain guard is enabled.
- Required PM actor domains match and are not blocked before `execv`.
- If PM fd contract is missing, service-manager/CNSS and subsystem open remain
  blocked.
- If cleanup cannot prove every actor stopped, cleanup reboot executes.
- Post-reboot `bootstatus` and `selftest` remain healthy.

## Next

If PM domains match but the PM fd contract is missing, do not retry unchanged.
Classify why `pm_proxy_helper` and `pm-service` do not hold `/dev/subsys_modem`
under the now-correct PM runtime domains.
