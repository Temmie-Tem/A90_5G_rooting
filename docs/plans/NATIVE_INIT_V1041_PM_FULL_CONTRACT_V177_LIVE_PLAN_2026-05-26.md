# V1041 PM Full-Contract v177 Live Plan

- date: `2026-05-26`
- type: bounded live PM full-contract proof
- selected after: V1040 helper `v177` deploy
- helper: `/cache/bin/a90_android_execns_probe`
- helper version: `a90_android_execns_probe v177`
- helper sha256: `d71c7c87a7759eb8e2eb0058c2057e0e9348a4c6f572f48d6d9b2962053a4795`

## Objective

Rerun the bounded PM full-contract proof using helper `v177`, after the
`pm-proxy` SELinux context parity fix from V1039 and deploy from V1040.

The immediate question is whether the Android-positive PM fd contract now forms:

```text
pm_proxy_helper -> /dev/subsys_modem
pm-service      -> /dev/subsys_modem
pm-proxy        -> u:r:vendor_per_proxy:s0
mdm_helper      -> /dev/esoc-0
```

## Gate

Allowed live order:

```text
property shim
  -> pm_proxy_helper
  -> pm-service
  -> pm-proxy
  -> mdm_helper
  -> PM fd predicate
  -> service-manager/CNSS only if lower guards pass
```

The runtime-domain guard remains active with
`--require-android-selinux-exec-match`. If any guarded PM actor does not match
its requested Android SELinux exec context, helper startup must fail closed
before target `execv`.

## Hard Guardrails

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

## Success Criteria

- Remote helper sha/marker match helper `v177`.
- Runtime-domain guard is enabled and does not block correctly matched PM
  actors.
- The PM fd predicate either forms or the new V1039 fd/wchan gap snapshots are
  captured.
- Forbidden Wi-Fi actions remain false.
- Cleanup reboot runs if actor stop state is not proven safe, and post-reboot
  health remains clean.

## Next

If the PM fd contract forms, the next unit can proceed to the gated
service-manager/CNSS continuation. If it does not form, V1042 should classify
V1041's focused fd/wchan evidence rather than retrying the same PM order.
