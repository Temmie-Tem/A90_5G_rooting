# NATIVE INIT V2325 — Audio AUD-1 ADSP Path Plan

Date: 2026-06-14

## Header

- Run ID: V2325
- Native init: unchanged from current validated test artifact `A90 Linux init 0.9.287 (v2323-usb-multi-lun-identity)`
- Build tag: unchanged
- Boot image: unchanged
- Device flash: no
- Device action: none
- Host commit at start: `281fc8e9`
- Scope: AUD-1 host-only ADSP/PIL path analysis and AUD-2 plan

## Decision

AUD-1 identifies a concrete, reviewable ADSP liveness path, but **does not authorize running it**.

The likely downstream trigger is:

```text
write "1" > /sys/kernel/boot_adsp/boot
```

That write is the first ADSP activation boundary. It must remain hard operator-gated as AUD-2.

## Sources Consulted

Local evidence:

- Stock kallsyms/System.map: `workspace/private/runs/kernel/v2197-stock-kallsyms/System.map`
- Stock kernel image string scan: `workspace/private/builds/native-init/v2321-usb-clean-identity-rodata/kernel_v2321_usb_clean_identity_rodata`
- Kernel source drop DTS: `workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel/arch/arm64/boot/dts/qcom/`
- Prior native firmware-mount reports: V1058/V1059
- Prior DSP liveness report: V2291
- AUD-0 inventory report: `docs/reports/NATIVE_INIT_V2324_AUDIO_AUD0_HOST_INVENTORY_2026-06-14.md`

External reference used for driver-shape comparison:

- Android GoogleSource `drivers/soc/qcom/qdsp6v2/adsp-loader.c`: https://android.googlesource.com/kernel/msm/+/android-7.1.0_r0.2/drivers/soc/qcom/qdsp6v2/adsp-loader.c

The external reference is not treated as this device's source of truth. It is used only because this device's public source drop strips the downstream ADSP loader driver while the stock kernel kallsyms still exposes matching symbol names.

## Local Stock-Kernel Evidence

The exact stock kernel image/kallsyms contains these relevant symbols:

```text
ffffff800968d1d0 t adsp_loader_probe
ffffff800968d298 t adsp_loader_remove
ffffff800968d2c0 t adsp_load_fw
ffffff800968d730 t adsp_boot_store
ffffff800968d838 t adsp_ssr_store
ffffff800968fb78 T apr_load_adsp_image
ffffff80086d12c0 T __subsystem_get
ffffff80086d1320 T subsystem_get
ffffff80086d13f8 T subsystem_get_with_fwname
```

The stock kernel image also contains the string tokens:

```text
qcom,adsp-loader
qcom,msm-adsp-loader
boot_adsp
adsp_boot_store
Q6 image loading failed
apr_adsp_up
adsp not up
ADSP slimbus not up yet
sound card is not enumerated
```

This is stronger than source-drop inference: the booted stock kernel carries the downstream ADSP loader and APR/Q6 paths even though the driver source is not present in the open-source package.

## Driver Shape

The GoogleSource Qualcomm downstream `adsp-loader.c` creates a `boot_adsp` kobject under `kernel_kobj`, exposes a write-only `boot` attribute, parses integer writes, and on `1` calls the ADSP loader path, which uses `subsystem_get("adsp")`. On `0`, it unloads through `subsystem_put()`.

This matches the local stock-kernel evidence:

- local symbols include `adsp_boot_store`, `adsp_load_fw`, and `subsystem_get`;
- local strings include `boot_adsp` and `qcom,adsp-loader`;
- prior Android trace evidence already saw `__subsystem_get(): __subsystem_get: adsp count:0` during Android lower bring-up.

Therefore the most likely AUD-2 activation write is the Android-style boot attribute, not a generic remoteproc write.

## Remoteproc vs Qualcomm Subsys Model

The generic Linux remoteproc view is not the primary control model for this stock downstream kernel under native init:

- V2291 read-only native liveness showed no `/sys/class/remoteproc/remoteproc*` entries printed.
- V2291 did show `/sys/bus/rpmsg/devices`, but only modem-side GLINK/RPMSG channels were live.
- The stock kernel contains Qualcomm `subsystem_restart` strings, `subsys_%s` char-device creation strings, and `subsystem_get*` symbols.
- The ADSP loader path specifically maps to `/sys/kernel/boot_adsp/boot` in the comparable downstream driver.

AUD-2 should still enumerate `/sys/class/remoteproc/*` as read-only metadata, but it must not assume remoteproc is the control path.

## Firmware Search Path

Prior native evidence from V1058 established:

```text
/sys/module/firmware_class/parameters/path = /vendor/firmware_mnt/image
```

V1058 also showed that when `/vendor/firmware_mnt` is absent, PIL firmware such as `modem.mdt` is invisible. V1059 then proved a read-only mount refresh can mount firmware partitions into `/vendor/firmware_mnt` without moving lower readiness markers.

AUD-0 confirmed the ADSP firmware is present in the NON-HLOS/APNHLOS image:

```text
/IMAGE/ADSP.MDT
/IMAGE/ADSP.B00 .. ADSP.B16
/IMAGE/ADSPR.JSN
/IMAGE/ADSPUA.JSN
```

Expected runtime lookup after a read-only APNHLOS firmware mount:

```text
/vendor/firmware_mnt/image/adsp.mdt
/vendor/firmware_mnt/image/adsp.b00
...
/vendor/firmware_mnt/image/adsp.b16
```

Because the mounted image is FAT, case-insensitive lookup should make the uppercase directory entries usable through lowercase firmware_class requests. AUD-2 must verify file visibility before writing the boot attribute.

## Minimal Driver Load / Userspace Order

Host-only plan for the future AUD-2 boot artifact or command path:

1. Keep the existing native-init baseline and USB control channel.
2. Add a read-only `audio adsp-status` command first. It must only read:
   - `/sys/module/firmware_class/parameters/path`;
   - `/vendor/firmware_mnt/image/adsp.mdt` and ADSP segment visibility;
   - `/sys/kernel/boot_adsp/boot` existence/mode;
   - `/sys/class/remoteproc/*/{name,state}` if present;
   - `/sys/bus/rpmsg/devices`, `/sys/class/rpmsg`, `/sys/class/fastrpc`;
   - `/sys/class/sound`, `/proc/asound`, and `/dev/snd`;
   - filtered kmsg markers: `adsp-loader`, `Q6/ADSP`, `apr_adsp_up`, `apr_tal`, `opened rpmsg channel`, `snd_card_register`, `sound card is not enumerated`, `ADSP slimbus not up yet`.
3. Add a separate operator-gated `audio adsp-boot-once` path. It must refuse to run unless:
   - rollback images and recovery preconditions pass before any flash;
   - post-flash `version/status/selftest fail=0` is clean;
   - `/sys/kernel/boot_adsp/boot` exists;
   - `firmware_class.path` is `/vendor/firmware_mnt/image` or explicitly reported;
   - ADSP firmware files are visible under `/vendor/firmware_mnt/image`;
   - ADSP is not already clearly up;
   - no audio playback/mixer command is bundled.
4. The only activation write in AUD-2 is exactly one write of `1\n` to `/sys/kernel/boot_adsp/boot`.
5. After the write, wait bounded time for metadata only:
   - ADSP loader success marker (`Q6/ADSP image is loaded` or equivalent);
   - APR/Q6 marker (`apr_adsp_up`, `Q6 Is Up`, or equivalent);
   - RPMSG/ADSPRPC channel (`opened rpmsg channel for ...`);
   - ALSA card materialization (`/sys/class/sound/card*`, `/dev/snd/controlC*`, `/proc/asound/cards`).
6. Do not write `0` to the boot attribute during AUD-2. Leave cleanup to reboot/rollback if needed; unnecessary unload/SSR increases risk without proving liveness.

## AUD-2 Classification

The future AUD-2 report should classify exactly one of:

- `adsp-preflight-missing-firmware` — boot attribute may exist, but firmware files are not visible; no write attempted.
- `adsp-preflight-no-boot-attr` — firmware exists, but `/sys/kernel/boot_adsp/boot` is absent; no write attempted.
- `adsp-boot-write-accepted-no-card` — write returned success and ADSP markers moved, but no ALSA card appeared within the bounded window.
- `adsp-boot-card-materialized` — write returned success, ADSP markers moved, and ALSA card or `/dev/snd` appeared.
- `adsp-boot-failed` — write returned error or kmsg shows ADSP/PIL failure.
- `adsp-boot-hung-or-control-lost` — USB/serial control did not return; auto-rollback/incident path applies.

Only `adsp-boot-card-materialized` should unlock a separately gated AUD-3 playback plan.

## Abort Rules for AUD-2

Stop before the activation write if any preflight is missing or ambiguous:

- rollback image/recovery precondition not confirmed;
- post-flash health check not clean;
- control channel unstable;
- ADSP firmware files not visible;
- boot attribute absent;
- native selftest fails;
- unexpected live ADSP/rpmsg state suggests the system is not in the planned baseline.

Stop after the write and do not retry if:

- write returns an error;
- bounded wait expires;
- ADSP crashes/SSR loops;
- control channel drops;
- selftest regresses.

On failure after a flashed AUD-2 artifact, follow the AGENTS.md auto-rollback gate to V2321. Do not loop or try alternate ADSP writes in the same run.

## Explicit Non-Goals

AUD-2 must not include:

- `tinymix`, `tinyplay`, PCM writes, speaker route changes, volume changes, or any playback;
- full Android audio HAL bring-up;
- Binder/HwBinder service stack bring-up;
- `adsprpc` invoke/ioctl experiments;
- `/dev/subsys_adsp` open as a first trigger;
- ADSP unload (`echo 0`) unless a separate future design explicitly justifies it;
- modem/call audio or `q6voice`.

## Validation

- Host-only analysis only.
- No device action, no flash, no boot artifact.
- No touched Python or C source.
- `git diff --check`: PASS.

## Next Step

AUD-1 is complete as a design unit. The loop must now stop before AUD-2 until the operator explicitly authorizes the new ADSP device-risk domain.

Recommended operator phrase if proceeding later:

```text
Stage AUD-2 go: one-shot ADSP liveness probe on v2321/v2323 lineage, firmware preflight required, write /sys/kernel/boot_adsp/boot once, no audio playback, no mixer, no HAL, no retry
```
