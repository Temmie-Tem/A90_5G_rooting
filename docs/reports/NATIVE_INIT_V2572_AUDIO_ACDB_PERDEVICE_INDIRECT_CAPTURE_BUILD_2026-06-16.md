# NATIVE_INIT V2572 — ACDB per-device generic-indirect capture build

Date: 2026-06-16

## Scope

Host-only build unit following V2571. No live Android handoff, no native replay, no speaker write,
and no raw ACDB payload bytes are committed.

## Purpose

V2570 proved that the V2568 public-send path should not be rerun unchanged: the hook reached
`before_send_audio_cal_v5` but produced no useful per-device ACDB payloads before timeout. V2572
builds a narrower capture route:

- keep `acdb_ioctl` silent until the interposed pre-init hook manually arms capture;
- skip the real public `acdb_loader_send_common_custom_topology()` call by default because V2547
  already pinned the topology payload;
- patch the known initialized flag, arm capture, then call
  `acdb_loader_send_audio_cal_v5(15, 0, 0x11135, 48000, 48000, 0, 1)`;
- capture both direct `out_buf` records and bounded generic indirect output records described by
  `in_buf={len, ptr}` when `ret==0`.

## Public Source Changes

- `workspace/public/src/android/acdb_payload_capture/libacdbtap_v2572.c`
  - adds generic indirect-output capture for armed `acdb_ioctl` calls;
  - distinguishes raw files/events as `direct` vs `indirect`;
  - keeps the non-zero success discriminator and adds a conservative user-pointer range filter
    before dereferencing an indirect pointer.
- `workspace/public/src/android/acdb_payload_capture/libacdb_preinit_perdevice_v2572.c`
  - exports the same common-topology symbol as the V2568 hook;
  - skips the real common-topology public call by default;
  - patches the initialized flag, manually arms capture, calls `send_audio_cal_v5`, and exits before
    the known init-tail crash path.
- `workspace/public/src/android/acdb_payload_capture/a90_acdb_init_drive_exec_linked_v2572.c`
  - starts `acdb_loader_init_v3()` only; it does not open `/dev/msm_audio_cal` or issue ioctls.
- `workspace/public/src/scripts/revalidation/build_android_acdb_perdevice_indirect_capture_v2572.py`
  - builds private ARM32 artifacts and validates source, vendor-symbol, and ELF export contracts.

## Private Build Artifacts

Private artifacts were built under
`workspace/private/builds/audio/v2572-acdb-perdevice-indirect-capture-host-only/` and are not
committed.

- Helper: `workspace/private/builds/audio/v2572-acdb-perdevice-indirect-capture-host-only/bin/a90_acdb_perdevice_indirect_exec_linked_v2572`
  - SHA-256: `5cc7b9c6f2bacdb7c4789bb9f9f62ec2f2ec7488e9124e97b0364b3644af023d`
  - size: `3368` bytes
- Preload: `workspace/private/builds/audio/v2572-acdb-perdevice-indirect-capture-host-only/bin/liba90_acdb_perdevice_indirect_capture_v2572.so`
  - SHA-256: `08046bcb104a9da948a8d05bba7d0126d07f35de30a9978231d445153189a7d4`
  - size: `14072` bytes

## Boundary

- No native replay.
- No native speaker/mixer/PCM write.
- No committed raw ACDB bytes or proprietary vendor libraries.
- `AUDIO_ALLOCATE_CALIBRATION`, `AUDIO_DEALLOCATE_CALIBRATION`, and `AUDIO_SET_CALIBRATION` remain
  fake-success in the ioctl preload when `A90_ACDB_FAKE_ALLOCATE=1`; no real SET reaches the kernel
  in this capture route.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/build_android_acdb_perdevice_indirect_capture_v2572.py`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/build_android_acdb_perdevice_indirect_capture_v2572.py --build`
- Build manifest result: `ok=true`, `source_required_ok=true`, `source_prohibited_ok=true`,
  `required_for_v2572_ok=true`, `build_ok=true`.
- `file` reports both artifacts as 32-bit ARM ELF objects.
- `readelf -Ws` confirms the preload exports `acdb_ioctl`, `ioctl`, `a90_arm_capture`, and
  `acdb_loader_send_common_custom_topology`.
- Compile stderr has no C warnings after the pointer-filter/warning-cleanup patch; linker stderr
  only contains the existing host `libxml2.so.2` version-information warning from the private
  toolchain compatibility shim.
- `git diff --check` passed before commit.

## Next Step

V2572 is build-only. A future live handoff may stage the private V2572 helper/preload through the
existing checked Android rollback envelope, but live execution is a separate iteration and must keep
V2321 rollback and raw-payload privacy rules intact.
