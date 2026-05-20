# Native Init V489 SELinux Compile Proof

- Date: 2026-05-21 KST
- Scope: bounded native-init Android SELinux split-policy compile proof
- Result: `v489-selinux-compile-proof-pass`
- Pass meaning: Android split-policy can be compiled in the native-init private namespace; native-init Wi-Fi connect and external ping are still not achieved

## What Changed

- Added `a90_android_execns_probe v47`.
- Added helper mode `sepolicy-compile-proof`.
- The helper mounts system/vendor/SELinuxfs in its private namespace and runs `/system/bin/secilc` only.
- The compiled policy output is written to the helper temp root and removed before namespace cleanup.
- Added `native_selinux_compile_proof_v489.py` to gate and classify the compile proof.
- Added `wifi_execns_helper_v47_deploy_preflight.py` for bounded helper deployment.

## Evidence

- Build artifact: `tmp/wifi/v489-a90_android_execns_probe-v47/a90_android_execns_probe`
- Build SHA-256: `ee49f2b762081c3d617cf84f957080846c8c003ef1ea08836772ae21d7149efb`
- Deploy preflight: `tmp/wifi/v489-deploy-20260521-060711/manifest.json`
- Deploy evidence: `tmp/wifi/v489-deploy-run-20260521-060724/manifest.json`
- Live preflight: `tmp/wifi/v489-compile-preflight-20260521-061348/manifest.json`
- Live evidence: `tmp/wifi/v489-compile-run-20260521-061359/manifest.json`
- Live transcript: `tmp/wifi/v489-compile-run-20260521-061359/commands/sepolicy-compile-proof.txt`
- Live summary: `tmp/wifi/v489-compile-run-20260521-061359/summary.md`
- Post-run status: `tmp/wifi/v489-post-status.json`

## Compile Result

| item | value |
|---|---:|
| decision | `v489-selinux-compile-proof-pass` |
| result | `compile-pass` |
| reason | `policy-version-31-pass` |
| attempts | `1` |
| pass policy version | `31` |
| kernel policy version | `31` |
| vendor mapping version | `30.0` |
| output hash | `0x588d1b76d1f86909` |

Key command shape:

```text
/system/bin/secilc
/system/etc/selinux/plat_sepolicy.cil
-m -M true -G -N
-c 31
/system/etc/selinux/mapping/30.0.cil
-o /sepolicy-v489-31.compiled
-f /sys/fs/selinux/null
/system/etc/selinux/mapping/30.0.compat.cil
/system/system_ext/etc/selinux/system_ext_sepolicy.cil
/system/system_ext/etc/selinux/mapping/30.0.cil
/system/system_ext/etc/selinux/mapping/30.0.compat.cil
/vendor/etc/selinux/plat_pub_versioned.cil
/vendor/etc/selinux/vendor_sepolicy.cil
```

Safety facts from the live transcript:

```text
sepolicy_compile.policy_load_executed=0
sepolicy_compile.init_reexec_executed=0
sepolicy_compile.daemon_start_executed=0
sepolicy_compile.wifi_hal_start_executed=0
sepolicy_compile.wifi_bringup_executed=0
sepolicy_compile.attempt_31.exit_code=0
sepolicy_compile.attempt_31.result=compile-pass
```

## AOSP Reference

AOSP `init` uses split SELinux policy on modern Treble devices. If the precompiled vendor policy hashes do not match platform policy hashes, `init` falls back to compiling policy with `/system/bin/secilc`, mapping CIL for the vendor platform version, `-f /sys/fs/selinux/null`, and a temp compiled-policy output. V489 follows that compile shape but deliberately stops before any policy load.

References:

- AOSP init split-policy implementation: `https://android.googlesource.com/platform/system/core/+/master/init/selinux.cpp`
- AOSP SELinux build documentation: `https://source.android.com/docs/security/features/selinux/build`

## Interpretation

- V488 showed vendor precompiled policy is not directly usable with the currently mounted system/system_ext policy hashes.
- V489 proves the fallback compile path itself is viable in native init.
- The compile succeeds with policy version `31` while using vendor mapping version `30.0`.
- This removes the previous uncertainty around whether native init can assemble a loadable Android policy blob.
- This does not prove policy load safety, PID1 reexec safety, SELinux domain transition, HAL registration, Wi-Fi scan/connect, DHCP, route setup, or external internet reachability.

## Safety

- No write to `/sys/fs/selinux/load`.
- No PID1 reexec.
- No service-manager, hwservicemanager, Wi-Fi HAL, CNSS, wpa_supplicant, wificond, scan, connect, DHCP, route change, credential read, or external ping was executed.
- Helper deployment only replaced `/cache/bin/a90_android_execns_probe`.
- Final post-run status remained healthy: `selftest: pass=11 warn=1 fail=0`.

## Next Work

1. Plan V490 as a separate explicit policy-load proof:
   - use the same compiled-policy argument set
   - write to `/sys/fs/selinux/load` only under a new approval gate
   - capture pre/post enforcing state, current context, and rollback requirements
   - do not start HAL in the same step
2. If policy load succeeds, retry a minimal domain-transition proof before daemon start.
3. If a child can enter `u:r:init:s0` or the needed HAL domain, retry service-manager/HAL registration.
4. Continue final Wi-Fi path: HAL registration, readiness calls, scan/connect/link-up, DHCP/routing, external ping.
