# Native Init V488 SELinux Policy Inventory

- Date: 2026-05-21 KST
- Scope: bounded native-init Android SELinux policy assembly inventory
- Result: `v488-selinux-policy-compile-candidate`
- Pass meaning: policy-load direction was narrowed; native-init Wi-Fi connect and external ping are still not achieved

## What Changed

- Added `a90_android_execns_probe v46`.
- Added helper mode `sepolicy-inventory`.
- The helper mounts system/vendor in its private namespace and inspects Android SELinux policy inputs without starting daemons.
- Added `native_selinux_policy_inventory_v488.py` to run the inventory and classify the next policy-load path.
- Added `wifi_execns_helper_v46_deploy_preflight.py` for bounded helper deployment.

## Evidence

- Build artifact: `tmp/wifi/v488-a90_android_execns_probe-v46/a90_android_execns_probe`
- Build SHA-256: `81a205579fada4d286eb4cac751a378c09a46757eb39aed593176cbead12ef24`
- Deploy preflight: `tmp/wifi/v488-helper-preflight-20260521-054706/manifest.json`
- Deploy evidence: `tmp/wifi/v488-helper-deploy-20260521-054722/manifest.json`
- Live evidence: `tmp/wifi/v488-selinux-policy-inventory-20260521-055348/manifest.json`
- Live transcript: `tmp/wifi/v488-selinux-policy-inventory-20260521-055348/commands/sepolicy-inventory.txt`
- Live summary: `tmp/wifi/v488-selinux-policy-inventory-20260521-055348/summary.md`

## Inventory Result

| item | value |
|---|---:|
| split policy device | `1` |
| vendor precompiled policy present | `1` |
| precompiled usable | `0` |
| precompiled hash matches | `0/2` |
| secilc present | `1` |
| vendor policy CIL present | `1` |
| vendor platform public versioned CIL present | `1` |
| compile inputs present | `1` |
| decision | `v488-selinux-policy-compile-candidate` |

Key files:

```text
/system/etc/selinux/plat_sepolicy.cil: present size=1807055
/system/system_ext/etc/selinux/system_ext_sepolicy.cil: present size=367615
/system/bin/secilc: present executable size=323624
/vendor/etc/selinux/precompiled_sepolicy: present size=1329357
/vendor/etc/selinux/vendor_sepolicy.cil: present size=1869858
/vendor/etc/selinux/plat_pub_versioned.cil: present size=964985
/vendor/etc/selinux/plat_sepolicy_vers.txt: present value=30.0
```

Hash compatibility facts:

```text
sepolicy.hash.plat.match=0
sepolicy.hash.plat.actual=504517f99d49800884e1b44956c0cc553f7f24bbb294be35298ef13b70435c31
sepolicy.hash.plat.precompiled=ce604792a5d11583da397cdeed1a82a7ca4871b12b626997ca4d7032b0e74078
sepolicy.hash.system_ext.match=0
sepolicy.hash.system_ext.actual=d2d2591213ac17a60da870de6c882700b469930075f0c88c925e0306926f2fd9
sepolicy.hash.system_ext.precompiled=a5b7fd9545be0930eed3de9fe0a810e85ce6f7fe02b06449e908296c8ee92c9e
sepolicy.hash.product.actual_present=0
sepolicy.hash.product.precompiled_present=1
```

## AOSP Reference

AOSP states that Android 8.0+ devices use split SELinux policy from `system`, `system_ext`, `product`, `vendor`, and `odm` components. Precompiled policy can be loaded only when the platform, system_ext, and product policy hashes match the corresponding precompiled hashes. If they differ, init falls back to on-device compilation with `secilc`.

References:

- AOSP SELinux build documentation: `https://source.android.com/docs/security/features/selinux/build`
- AOSP init split-policy implementation: `https://android.googlesource.com/platform/system/core/+/master/init/selinux.cpp`

## Interpretation

- V487 proved native processes remain in `kernel`, including an attempted `u:r:init:s0` handoff.
- V488 shows the mounted system/vendor pair is a split-policy device.
- Vendor precompiled policy exists, but its recorded hashes do not match the currently mounted system/system_ext policy hashes.
- Therefore, direct precompiled policy load is not the correct first candidate.
- The required compile path is plausible because `secilc`, `plat_sepolicy.cil`, `system_ext_sepolicy.cil`, `vendor_sepolicy.cil`, `plat_pub_versioned.cil`, and vendor platform version `30.0` are present.
- The next step should prove a bounded compile path first, not start the Wi-Fi HAL again.

## Safety

- No service-manager, hwservicemanager, Wi-Fi HAL, CNSS, wpa_supplicant, wificond, scan, connect, DHCP, route change, credential read, or external ping was executed.
- Helper deployment only replaced `/cache/bin/a90_android_execns_probe`.
- The inventory helper used private namespace read-only system/vendor mounts.
- Final post-run status remained healthy: `selftest: pass=11 warn=1 fail=0`.

## Next Work

1. Plan V489 as a bounded `secilc` compile proof:
   - build the exact file list using vendor `plat_sepolicy_vers.txt=30.0`
   - compile to a private temp output under `/tmp` or `/dev`
   - do not write `/sys/fs/selinux/load`
   - do not reexec PID1
2. If V489 compile succeeds, plan V490 policy-load proof as a separate high-risk gated step.
3. Only after a child can enter `u:r:init:s0` or `u:r:hal_wifi_default:s0`, retry Samsung HAL registration.
4. Continue final Wi-Fi path: HAL registration, readiness calls, scan/connect/link-up, DHCP/routing, external ping.
