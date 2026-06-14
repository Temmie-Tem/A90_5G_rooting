# NATIVE_INIT V2394 — Audio ACDB/HAL boundary and Magisk measurement branch

## Scope

Host-only analysis after V2393. No flash, Android boot, ADSP write, `/dev/snd` open, mixer write,
PCM playback, HAL launch, or Magisk module install ran in this unit.

The question for this unit was whether the V2393 `pcm_prepare()` failure can still be solved by
more native `tinymix`/tinyalsa route tuning, or whether the frontier has moved to the Qualcomm
ACDB/App Type/HAL calibration path. The user also asked to keep the Magisk-module direction in mind,
as the Wi-Fi work previously used Android/Magisk-style handoffs as a measurement/staging tool.

## Inputs inspected

- V2393 live result: `docs/reports/NATIVE_INIT_V2393_AUD4_PREPARE_DSP_CAL_FAILURE_2026-06-15.md`
- Android route delta: `docs/reports/NATIVE_INIT_V2377_ANDROID_ROUTE_DELTA_MODERN_APK_LIVE_2026-06-15.md`
- Audio inventory: `docs/reports/NATIVE_INIT_V2324_AUDIO_AUD0_HOST_INVENTORY_2026-06-14.md`
- Vendor dump: `workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump/`
- Kernel source drop: `workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel/`

## V2393 root cause recap

V2393 moved the blocker from userspace transport to the kernel/DSP calibration path. The bounded
post-failure dmesg tail showed:

- AFE port `0x4000` starts.
- `afe_get_cal_topology_id` reports cal types `8` and `9` are not initialized for port `16384`.
- `send_afe_cal_type cal_block not found!!` appears.
- `q6asm_send_cal: cal_block is NULL` appears.
- `msm_pcm_routing_get_app_type_idx` falls back because the App Type is not available.
- `adm_open` reaches ADSP and returns `ADSP_EFAILED`.
- ALSA prepare fails as `msm_pcm_playback_prepare: stream reg failed ret:-22`.

That means the native route recipe successfully reached the Q6 audio stack, but the DSP-side ADM/AFE
open path did not have the calibration/topology/App Type state that Android normally programs before
speaker playback.

## Host findings

### `libacdbloader.so` is the calibration writer

The 32-bit vendor `libacdbloader.so` exports the relevant Qualcomm calibration entry points,
including:

- `acdb_loader_init_ACDB`
- `acdb_loader_init_v2`
- `acdb_loader_init_v3`
- `acdb_loader_init_v4`
- `acdb_loader_send_audio_cal`
- `acdb_loader_send_audio_cal_v2` / `_v3` / `_v4` / `_v5`
- `acdb_loader_send_common_custom_topology`
- `acdb_loader_set_audio_cal_v2`
- `acdb_loader_get_calibration`
- `acdb_loader_get_default_app_type`
- `acdb_loader_send_gain_dep_cal`
- `send_afe_topology`, `send_adm_topology`, `send_asm_topology`, and codec/meta-info helpers

Its dynamic dependencies include `libaudcal.so`, `libtinyalsa.so`, `libacdbrtac.so`, `libadiertac.so`,
`libacdb-fts.so`, and `libion.so`. Its strings show it opens `/dev/msm_audio_cal`, reads from
`/vendor/etc/acdbdata`, uses `/vendor/etc/audconf/OPEN`, and sends AFE/ADM/ASM topology and audio
calibration commands such as `AUDIO_SET_AFE_CAL`, `AUDIO_SET_AUDPROC_CAL`, and custom topology
commands.

This matches the V2393 dmesg failure: the kernel/DSP path is missing calibration blocks that the
ACDB loader normally submits.

### `audio.primary.msmnile.so` owns the higher-level policy

The primary HAL contains the platform and extension logic that decides which ACDB ID, App Type,
sample rate, bit width, and speaker-protection path to use. Relevant strings/symbol references
include:

- `platform_send_audio_calibration`
- `platform_send_audio_cal`
- `platform_get_default_app_type`
- `platform_get_default_app_type_v2`
- `platform_add_app_type`
- `audio_extn_utils_send_audio_calibration`
- `audio_extn_utils_send_app_type_cfg`
- `audio_extn_utils_update_stream_app_type_cfg_for_usecase`
- `set_stream_app_type_mixer_ctrl`
- `platform_get_snd_device_acdb_id`
- `platform_get_spkr_prot_acdb_id`
- `external_speaker_feature_init`
- `spkr_prot_feature_init`
- `audio_extn_qdsp_init`
- `audio_extn_hidl_init`

The HAL depends on the Android vendor userspace stack (`libhidlbase`, QTI audio extension libraries,
Samsung speaker extension libraries, processgroup/power libraries, and the ACDB loader). This strongly
suggests that the missing V2393 state is not just one mixer switch; it is the HAL/ACDB calibration
sequence around App Type + ACDB ID + topology programming.

### The open-source kernel drop cannot answer the driver internals

A search for `msm_audio_cal`, `send_afe_cal`, `afe_get_cal_topology_id`, `q6asm_send_cal`,
`adm_open`, and `msm_pcm_playback_prepare` in the Samsung open-source kernel drop returned no hits.
The relevant downstream audio driver source is not present in the public drop. For this device, the
kernel-side behavior has to be inferred from the stock image strings, dmesg, vendor libraries, and
Android-side observations.

## Decision

Do not continue blind AUD-4 retries that only vary route controls, PCM period size, card/device,
sample rate, bit width, or amplitude. V2393 already proved the next blocker is missing ACDB/App Type
calibration before `SNDRV_PCM_IOCTL_PREPARE` can succeed.

Tinyalsa-direct native speaker playback is **not closed as impossible**, but the current minimal
route recipe is now blocked until one of these is designed:

1. a bounded native ACDB bootstrap that invokes the vendor ACDB path without launching the full audio
   HAL service graph; or
2. a decision that the minimal bootstrap still collapses into the full Android audio HAL/HwBinder
   stack, in which case direct native speaker playback should be classified as likely non-viable for
   this project scope.

## Magisk-module direction

Magisk is useful here in the same role it had during the Wi-Fi work: **measurement and staging inside
normal Android**, not as the final native-init runtime dependency.

Good uses:

- Package an Android-side helper or boot hook to run after the real vendor audio HAL and ACDB loader
  are alive.
- Capture vendor logs around `acdb_loader_init*`, `platform_send_audio_calibration`, App Type setup,
  and `/dev/msm_audio_cal` activity during a controlled low-amplitude framework playback.
- Stage small probes without modifying the boot image for every iteration.
- Compare Android's calibrated state before/during/after playback against the native-init state.
- Extract a minimal, reproducible sequence candidate for a later native ACDB bootstrap.

Bad uses:

- Treating Magisk as part of the final native-init boot path.
- Letting a Magisk module hide that native init still lacks ACDB/App Type initialization.
- Shipping a path that only works after Android's framework/HAL has already initialized audio.

The practical split is:

- **Android/Magisk side:** observe, trigger normal vendor HAL behavior, and collect the exact ACDB/App
  Type sequence.
- **Native-init side:** reproduce only the minimum safe subset, or explicitly stop if the minimum
  subset requires the full Android service graph.

## Recommended next unit

V2395 should be host-only design before any further live playback:

1. Disassemble or symbol-map the `audio.primary.msmnile.so` path around
   `platform_send_audio_calibration`, `audio_extn_utils_send_app_type_cfg`, and
   `platform_get_default_app_type_v2`.
2. Inspect `libacdbloader.so` call signatures and likely initialization sequence around
   `acdb_loader_init_v4` and `acdb_loader_send_audio_cal_v4`.
3. Define a bounded Android/Magisk measurement plan for ACDB/App Type logs if static analysis is not
   enough.
4. Only after that, decide whether to build a private native ACDB bootstrap probe or to park native
   speaker playback as HAL-dependent.

## Validation

- Host-only file/string/readelf/source analysis only.
- No code changed in this unit.
- No device action ran.
- `git diff --check` is required before commit.
