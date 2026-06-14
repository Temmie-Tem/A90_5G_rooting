# NATIVE INIT V2324 — Audio AUD-0 Host Inventory

Date: 2026-06-14

## Header

- Run ID: V2324
- Native init: unchanged from current validated test artifact `A90 Linux init 0.9.287 (v2323-usb-multi-lun-identity)`
- Build tag: unchanged
- Boot image: unchanged
- Device flash: no
- Device action: none
- Host commit at start: `9adbbe5c`
- Scope: AUD-0 host-only inventory and feasibility decision basis for internal speaker/headphone playback

## Inputs

Private/proprietary inputs stayed under `workspace/private/` or existing private scratch areas and were not staged for commit.

- Firmware package: `workspace/private/inputs/firmware/SAMFW.COM_SM-A908N_KTC_A908NKSU5EWA3_fac/`
- Vendor image already extracted for host inspection: `tmp/wifi/v1073-host-only/vendor-extract/vendor.raw.ext4`
- Kernel source drop: `workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel/`
- Stock/native kernel image string scan: `workspace/private/runs/audio/v2324-aud0-inventory/kernel_audio_strings.txt`
- Evidence scratch: `workspace/private/runs/audio/v2324-aud0-inventory/`

No device node was opened, no ADSP/remoteproc state was touched, and no partition/boot image was written.

## Inventory Summary

| Area | Result | Evidence |
| --- | --- | --- |
| Vendor kernel modules | No audio `.ko` modules found. The only vendor modules in the vendor image inventory were `rdbg.ko`, `rmnet_perf.ko`, and `rmnet_shs.ko`. | `audio_categories.txt` `.ko` section |
| Kernel/audio driver model | Audio support is not supplied as vendor modules. The stock boot kernel image contains downstream Q6/ASoC/codec strings for `qcom,msm-pcm-dsp`, `qcom,msm-pcm-routing`, `qcom,msm-dai-q6*`, `qcom,sm8150-asoc-snd-pahu`, `qcom,sm8150-asoc-snd-tavil`, `wcd934x`, `wsa881x`, `q6asm`, and APR failure paths. | `kernel_audio_strings.txt` |
| Source-drop gap | The open-source drop has the relevant SM8150 DTS audio/ADSP nodes, but driver source directories such as `sound/`, `techpack/audio/`, `drivers/remoteproc/`, `drivers/slimbus/`, and `drivers/soundwire/` are absent. `drivers/rpmsg/` remains present. | host source tree scan |
| ADSP firmware | `NON-HLOS.bin` contains `/IMAGE/ADSP.MDT`, `ADSP.B00`..`ADSP.B16` segments, `ADSPR.JSN`, and `ADSPUA.JSN`. String evidence includes `QC_IMAGE_VERSION_STRING=ADSP.HT.5.0.c1-00042-SM8150-1` and `IMAGE_VARIANT_STRING=855.adsp.prodQ`. | `non_hlos_image_dir.txt`, `bl_unpacked_string_hits.txt` |
| ADSP RFSA/shared libs | `dspso.bin` is an ext4 `dsp` image with `/adsp`, `/cdsp`, and `/sdsp`; `/adsp` contains codec/modules and `fastrpc_shell_0`/skeleton libraries. Vendor also contains `/lib/rfsa/adsp/*` and `/lib64/rfsa/adsp/*`. | private `dspso.bin` debugfs inventory, `vendor_keyword_hits.txt` |
| ACDB calibration | 33 `.acdb` files found. Carrier sets `SKC`, `OPEN`, `LUC`, and `KTC` each include Bluetooth/Codec/General/Global/Handset/Hdmi/Headset/Speaker calibration files. Also present: `/etc/acdbdata/adsp_avs_config.acdb`. | `audio_categories.txt` `.acdb` section |
| Mixer routes | `/etc/mixer_paths_pahu.xml` and `/etc/mixer_paths_tavil.xml` present. | `audio_categories.txt` |
| Audio platform metadata | `/etc/audio_platform_info.xml`, `/etc/audio_platform_info_diff.xml`, and `/etc/audio_platform_info_qrd.xml` present. | `audio_categories.txt` |
| Audio HAL and libs | Primary 32-bit HAL is `/lib/hw/audio.primary.msmnile.so`. It depends on `libtinyalsa.so`, `libtinycompress.so`, `libaudioroute.so`, `libaudioutils.so`, `libacdbloader.so`-adjacent calibration libraries, Samsung/QTI extensions, and HIDL/base/processgroup/power libs. The audio service binary is `/vendor/bin/hw/android.hardware.audio.service` and depends on Binder/HwBinder/HIDL/libhardware stack. | `readelf -d` on dumped HAL/service binaries |
| Audio services | Vendor init defines `vendor.audio-hal`, `vendor.adsprpcd`, `vendor.adsprpcd_audiopd`, and `vendor.dspservice`. | dumped vendor init rc files |

## ADSP / Device Tree Basis

The source drop still exposes the hardware graph even though many downstream driver sources are stripped:

- `sm8150.dtsi` has `pil_adsp_region`, `qcom,firmware-name = "adsp"`, `memory-region = <&pil_adsp_mem>`, ADSP SMP2P/GLINK/QRTR nodes, `q6prm`, and `qcom,msm-adsprpc-mem`.
- `sm8150.dtsi` has `slim_aud: slim@171c0000` and `slim_qca: slim@17240000`, both `qcom,slim-ngd`.
- `msm-audio-lpass.dtsi` has downstream Q6 PCM/routing/DAI compatibles such as `qcom,msm-pcm-dsp`, `qcom,msm-pcm-routing`, `qcom,msm-dai-q6`, and `qcom,msm-dai-q6-dev`.
- `sm8150-wcd.dtsi` configures WCD pinctrl paths for speaker/headphone controls under `&slim_aud`.
- The stock kernel image string scan independently confirms these downstream driver families are compiled into the booted kernel image even though they are absent from the public source drop.

## Bring-Up Chain Inferred from Host Evidence

The realistic stock-vendor chain is:

1. Boot stock kernel with built-in downstream ADSP/PIL, GLINK/RPMSG/QRTR, APR/Q6, ASoC machine, WCD/Tavil/Pahu codec, and WSA smart-amp support.
2. Load ADSP firmware from the NON-HLOS image (`ADSP.MDT` + segments) through the stock ADSP PIL/remoteproc path.
3. Serve ADSP RFSA/DSP shared objects from vendor/RFSA paths and `dspso.bin`-style contents as needed by ADSP services.
4. Start or replicate the minimal userspace pieces that normally accompany Android audio: `adsprpcd`, `adsprpcd audiopd`, `dspservice`, ACDB loader path, and/or audio HAL.
5. Only after ADSP and ASoC registration should an ALSA card and `/dev/snd/*` nodes be expected.
6. Playback then needs mixer route programming from `mixer_paths_pahu.xml`/`mixer_paths_tavil.xml`, ACDB calibration, and PCM/compress playback through Q6.

## Tinyalsa-Direct vs Full HAL Decision

AUD-0 does **not** prove that full Android audio HAL is strictly mandatory for a minimal playback experiment. It does prove that the production Android path is heavy and HAL-centered.

Evidence pushing toward full HAL:

- The primary HAL is the real device-specific `audio.primary.msmnile.so`, not a tiny standalone binary.
- The HAL depends on Binder/HwBinder/HIDL, `libaudioroute`, `libtinyalsa`, `libtinycompress`, Samsung/QTI audio extension libraries, and power/processgroup services.
- ACDB calibration files and `libacdbloader`/`libaudcal` are present; speaker/headphone routes likely depend on calibrated ADSP state, not only ALSA mixer writes.
- Android vendor init explicitly starts `vendor.audio-hal`, `vendor.adsprpcd`, `vendor.adsprpcd_audiopd`, and `vendor.dspservice`.

Evidence keeping tinyalsa-direct plausible enough for one more host-only design unit:

- The stock kernel image appears to already contain the downstream Q6/ASoC/codec drivers; no vendor audio modules need to be inserted.
- The primary HAL itself uses `libtinyalsa`/`libtinycompress`, so ALSA/PCM/compress is still the kernel-facing substrate.
- Mixer route XML and platform XML exist and can be parsed host-side to identify the likely speaker/headphone route names before any device write.
- The unknown first wall is earlier than HAL choice: whether native init can safely bring ADSP up and produce an ALSA card at all.

Conclusion: **do not close the audio epic as non-viable from AUD-0 alone.** The correct next step is AUD-1, still host-only: map the ADSP/remoteproc/PIL sysfs path, firmware search/serving requirement, and a reviewable AUD-2 liveness plan. If AUD-1 shows ADSP activation requires unsafe or non-recoverable behavior, close there. If AUD-1 produces a bounded recoverable liveness plan, stop for explicit operator approval before any AUD-2 device action.

## Risk Boundary

- No speaker/headphone playback should be attempted until ADSP liveness and ALSA card materialization are proven.
- No `tinymix` or `tinyplay` route should be run from the autonomous loop without a fresh explicit operator gate.
- Modem/call audio and `q6voice` remain out of scope.
- Proprietary firmware, vendor binaries, ACDB files, and DSP images remain private and uncommitted.

## Validation

- Host-only evidence generation only.
- No touched Python or C source.
- No build artifact or device step.
- `git diff --check`: PASS.

## Next Unit

AUD-1 — host-only ADSP/remoteproc path analysis:

1. Identify the exact sysfs/driver path that should expose ADSP remoteproc/PIL state under the stock kernel.
2. Identify the firmware lookup path and whether native init must materialize NON-HLOS-derived `adsp` firmware files into a specific rootfs location.
3. Define the minimum read-only preflight for AUD-2 and the exact write that would trigger ADSP load, without running it.
4. Define abort/rollback criteria for operator-gated AUD-2.
