# S22+ Stock Boot Recovery Loop Diagnosis - 2026-07-06

## Scope

Read-only diagnosis after the S22+ failed to stay in stock Android and kept
returning to TWRP recovery.

No device partition was written in this diagnostic unit. A host-side stock
vbmeta-only Odin package was prepared for a possible next test, but it was not
flashed.

## Current Device State

ADB is available in TWRP recovery:

```text
state=recovery
ro.twrp.version=3.7.0_12-1_afaneh92
ro.product.device=g0q
ro.boot.boot_recovery=1
ro.boot.bootloader=S906NKSS7FYG8
ro.boot.em.model=SM-S906N
ro.boot.sales_code=SKC
ro.boot.verifiedbootstate=orange
```

The TWRP ramdisk reports `SM-S906E`, but bootloader/device identity reports
`SM-S906N` and the bootloader build is `S906NKSS7FYG8`, matching the local SKC
firmware baseline.

## Partition Readback

Local stock images:

```text
stock_boot_sha=4150b962314e6136acba61b20f471d6ee1c418b83cf8c3ee4d9cf7c91a3640ae
stock_recovery_sha=93fac06ca79bf4b365b25a8d49902bc41aba112ea253c30880c90e314d7895d4
stock_vbmeta_sha=1031323af6c69c6894bb00ca5895463ea3f00066ec4d5eacc2bb58b0b2c6047b
stock_vendor_boot_sha=096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7
```

Device readback:

```text
boot_sha=4150b962314e6136acba61b20f471d6ee1c418b83cf8c3ee4d9cf7c91a3640ae
vendor_boot_sha=096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7
```

So the currently installed `boot` and `vendor_boot` partitions match stock
exactly.

The installed recovery and vbmeta are intentionally not stock:

```text
twrp_recovery_prefix_sha=e4e1861760298da756d1d649029c33b4c953f12272ebda1705214da56245e036
disabled_vbmeta_prefix_sha=d6b5803d2751aa6d675df90b2b6dd3c772f47acfe3e56ba19fc3e39da082f1a7
```

## Normal Reboot Probe

Host `adb reboot` was sent from TWRP recovery. The device returned to TWRP
recovery after 38 seconds:

```text
adb_seen_after_sec=38
adb_state=recovery
ro.twrp=1
ro_boot_recovery=1
ro_build_fingerprint=samsung/twrp_g0q/g0q:12/SP2A.220405.004/eng.afaneh.20221211.215927:eng/test-keys
```

Current `/proc/last_kmsg` proves the bootloader did attempt normal boot first:

```text
Booting Into Mission Mode
Requested Partition: boot
Requested Partition: dtbo
Requested Partition: vendor_boot
(Booting) AUTHENTICATE Succeed Kernel binary: boot
(Booting) AUTHENTICATE Succeed Dtbo binary: dtbo
(Booting) AUTHENTICATE Succeed Vendor_boot binary: vendor_boot
```

The next boot then entered recovery:

```text
Booting Into Recovery Mode
Requested Partition: recovery
bootloader_mode = 2
reboot_reason = 0x11
```

This rules out a simple "stock boot image was not restored" explanation. The
stock boot image is present and is authenticated; the failure is in the current
boot stack combination or early boot policy.

## Strongest Root-Cause Candidate

The installed disabled vbmeta is not derived from the current S22+ FYG8 stock
vbmeta. It is an older generic/Samsung payload:

```text
disabled_vbmeta_strings:
com.android.build.boot.security_patch=2020-10-01
com.android.build.system.security_patch=2020-10-01
com.android.build.vendor.security_patch=2020-10-01
G981BXXU5ZTJA
SM-G981B_EUR_XX_EKEY0
```

The stock FYG8 vbmeta matches the current device build:

```text
stock_vbmeta_strings:
com.android.build.boot.security_patch=2025-08-01
com.android.build.system.security_patch=2025-08-01
com.android.build.vendor.security_patch=2025-08-01
S906NKSS7FYG8
SM-S906N_KOR_KX_QKEY4
```

The live ABL log is consistent with that mismatch: with the current disabled
vbmeta, ABL reports old AVB OS/patch metadata rather than the FYG8 Android 15
metadata.

## Interpretation

The issue can be described as an image problem, but the evidence points away
from `boot.img`:

- `boot` matches stock byte-for-byte.
- `vendor_boot` matches stock byte-for-byte.
- The device does attempt normal boot.
- The installed disabled `vbmeta` is for a different/older Samsung build family.

The most likely fault is the current `stock boot + stock vendor_boot + TWRP
recovery + old generic disabled vbmeta` combination.

## Prepared Next Artifact

A host-only stock vbmeta rollback AP was prepared:

```text
path=workspace/private/outputs/s22plus_stock_vbmeta_rollback/AP.tar.md5
sha256=fdf42fb913ac82bba7414d41a2995300c9bc56d31e7cddf907b487e7b2ae707b
contents=vbmeta.img.lz4
payload_sha256=e470f3ed7fecf028e0e8782c1c08ad6a9096f8940db618be59a50001f7047e76
```

This artifact was not flashed.

## Recommended Next Test

If the goal is to recover stock Android boot while keeping the write minimal:

1. Flash stock `vbmeta` only.
2. Reboot normally.
3. Poll whether Android userspace appears or whether the device still returns to
   recovery.

If the goal is full stock state, then stock recovery should also be restored.
That removes the TWRP recovery shell and should be treated as a separate
operator-approved rollback step.

