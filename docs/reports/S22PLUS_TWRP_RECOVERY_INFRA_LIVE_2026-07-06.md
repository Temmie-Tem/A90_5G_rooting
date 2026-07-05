# S22+ TWRP Recovery Infrastructure Live - 2026-07-06

## Scope

Live installation of the pinned unofficial `g0q` TWRP recovery and pinned
disabled vbmeta on the Samsung S22+ `SM-S906N` / `g0q` test device.

This unit did not flash Magisk, did not run `multidisabler`, did not format
data, and did not write any partition outside the narrow
`AGENTS.md` S22+ recovery-infra exception.

## Authorization / Gate

The narrow S22+ recovery/vbmeta Odin4 exception was committed first:

- Commit: `078f4a65 Authorize S22+ recovery infra flash gate`

The earlier artifact gate and rollback plan is recorded in:

- `docs/reports/S22PLUS_TWRP_RECOVERY_INFRA_PLAN_2026-07-06.md`

## Preflight

ADB state immediately before download-mode reboot:

- Model: `SM-S906N`
- Device: `g0q`
- Product: `g0qksx`
- Bootloader/PDA: `S906NKSS7FYG8`
- Bootloader lock: `0`
- Verified boot state: `orange`
- Warranty bit: `1`

Pinned artifacts confirmed:

- TWRP tar:
  `0914c68a5353c367216805a3a2fdeb4982c6629368dc021c7fefc10d3d3bd034`
- `vbmeta_disabled.tar`:
  `0b347193ab3f822b423b2641001781e35fba0c932fcfb85d090b282d0fc6471b`
- Stock recovery-only rollback AP:
  `8d3647313d2e100134f77984d13c7e5dc9946510ab57d8e34dd0cd192ca8586d`
- Stock boot-only rollback AP:
  `1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e`
- Full stock firmware:
  `f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8`

Odin4 detected the device in download mode:

```text
/dev/bus/usb/<redacted>
```

## Flash Command

No `--reboot` option was used.

```text
odin4 \
  -a workspace/private/inputs/s22plus_twrp/g0q/twrp-3.7.0_12-1_afaneh92-g0q.tar \
  -u workspace/private/inputs/s22plus_twrp/g0q/vbmeta_disabled.tar \
  -d /dev/bus/usb/<redacted>
```

Odin4 transcript:

```text
Check file : workspace/private/inputs/s22plus_twrp/g0q/twrp-3.7.0_12-1_afaneh92-g0q.tar
Check file : workspace/private/inputs/s22plus_twrp/g0q/vbmeta_disabled.tar
/dev/bus/usb/<redacted>
Setup Connection
initializeConnection
Receive PIT Info
success getpit
Upload Binaries
recovery.img
(56%)
(99%)
vbmeta.img
(100%)
Close Connection
odin_exit=0
```

## Recovery Boot / ADB

After the Odin transfer, the operator manually booted directly into recovery.
Recovery ADB came up as TWRP:

```text
recovery usb:... product:twrp_g0q model:SM_S906E device:g0q
```

Read-only recovery status:

```text
ro.twrp.version=3.7.0_12-1_afaneh92
ro.product.model=SM-S906E
ro.product.device=g0q
ro.product.name=twrp_g0q
ro.boot.verifiedbootstate=orange
Linux localhost 5.10.81-afaneh92-g0418bf01a3e2 #1 SMP PREEMPT Tue Jun 14 02:16:15 EEST 2022 aarch64
```

The TWRP ramdisk reports model `SM-S906E`, but the preflight Android device was
`SM-S906N` and the recovery device codename is `g0q`. The upstream g0q guide
groups `S906E`, `S906N`, and `S9060` under the same Snapdragon S22+ build.

Read-only by-name checks:

```text
/dev/block/by-name/boot -> /dev/block/sda25
/dev/block/by-name/recovery -> /dev/block/sda26
/dev/block/by-name/vbmeta -> /dev/block/sde20
recovery size=104857600
vbmeta size=131072
boot size=100663296
```

## Readback Proof

The installed recovery prefix matches the extracted TWRP `recovery.img` exactly:

```text
recovery_size=55435280
local_recovery_sha=e4e1861760298da756d1d649029c33b4c953f12272ebda1705214da56245e036
device_recovery_prefix_sha=e4e1861760298da756d1d649029c33b4c953f12272ebda1705214da56245e036
```

The installed vbmeta prefix matches the extracted disabled `vbmeta.img` exactly:

```text
vbmeta_size=9936
local_vbmeta_sha=d6b5803d2751aa6d675df90b2b6dd3c772f47acfe3e56ba19fc3e39da082f1a7
device_vbmeta_prefix_sha=d6b5803d2751aa6d675df90b2b6dd3c772f47acfe3e56ba19fc3e39da082f1a7
```

## Result

PASS:

- Odin4 wrote `recovery.img` and `vbmeta.img` with exit `0`.
- TWRP recovery ADB came up.
- Operator visually confirmed the TWRP/recovery screen on the device panel.
- TWRP version is `3.7.0_12-1_afaneh92`.
- Recovery and vbmeta readback prefixes match the pinned local payloads exactly.
- No Magisk, `multidisabler`, format-data, boot image write, or extra partition
  write was performed in this unit.

Current state at report time: the S22+ is in TWRP recovery with recovery ADB
available.

## Next

Do not boot Android yet if the next target is making recovery persistent through
the afaneh92 documented flow. The next bounded unit should decide whether to run
`multidisabler` / format-data, or whether this recovery-only shell is sufficient
for the native-init experiment environment.
