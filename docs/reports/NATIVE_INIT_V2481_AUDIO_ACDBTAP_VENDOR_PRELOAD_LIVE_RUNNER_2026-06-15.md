# V2481 — ACDB tap vendor-preload live runner

## Purpose

V2481 turns the V2480 vendor-path preload plan into a recoverable Android
handoff runner. The runner stages the temporary measurement-only Magisk capsule,
reboots Android so Magisk can mount the systemless vendor path, verifies which
candidate path exposes the V2475 `libacdbtap.so` SHA, then runs the V2477 ACDB
tap capture only if `android.hardware.audio.service` maps-confirmation proves
`libacdbtap` is actually loaded.

This is still an Android-good measurement route. It does not issue native
`/dev/msm_audio_cal` calibration ioctls and does not replay ACDB payloads.

## Flow

1. Flash checked Android boot via the existing handoff path.
2. Re-check ADB boot readiness and Magisk `su` root.
3. Materialize and stage `a90_acdbtap_vendor_preload_v2480`.
4. Install only the exact `/data/adb/modules/a90_acdbtap_vendor_preload_v2480`
   directory.
5. Reboot Android for Magisk mount activation.
6. Re-check ADB/root readiness.
7. Verify `/vendor/lib/libacdbtap.so` and `/system/vendor/lib/libacdbtap.so`;
   select only a path whose `sha256sum` matches the V2475 tap SHA.
8. Recreate `/data/local/tmp/a90-acdb-tap` and manually re-exec
   `android.hardware.audio.service` with `LD_PRELOAD=<verified vendor path>`.
9. Abort before playback unless `/proc/<pid>/maps` shows `libacdbtap` in the HAL.
10. Run the existing bounded AudioTrack stimulus and pull the complete
    `/data/local/tmp/a90-acdb-tap/` directory.
11. Clean up the manual HAL, capture tree, and exact Magisk module path before
    checked rollback to V2321.

## Safety boundary

Hard stops remain:

- no `setenforce 0`;
- no `magisk --install-module`;
- no `service.sh`, `post-fs-data.sh`, `system.prop`, or `sepolicy.rule` module
  hooks;
- no native calibration ioctl or native speaker playback;
- no `acdb_loader_init_v4` fallback guessing;
- no playback unless vendor-path preload is SHA-verified and maps-confirmed.

If the vendor path still does not load through the HAL namespace, the runner
preserves linker/SELinux evidence and stops before playback.

## Acceptance policy

The V2477 artifact summarizer is reused unchanged:

- `captured-acdbtap-full-outbuf-set-with-4916`: full success.
- `captured-acdbtap-full-outbuf-set-no-4916`: partial success; ordered non-4916
  per-device ACDB out-buffer payloads are preserved for operator mapping and do
  not count as a fails-twice dead run.
- metadata-only, malformed, or empty captures remain non-successful.

V2481 only changes how the interposer becomes namespace-visible; it does not
reinterpret command IDs or build a replay manifest.

## Validation

Commands run:

```bash
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 -m py_compile \
    workspace/public/src/scripts/revalidation/native_audio_acdbtap_vendor_preload_live_handoff_v2481.py \
    tests/test_native_audio_acdbtap_vendor_preload_live_handoff_v2481.py

PYTHONPATH=tests:workspace/public/src/scripts/revalidation \
  python3 -m unittest tests.test_native_audio_acdbtap_vendor_preload_live_handoff_v2481 -v

PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/native_audio_acdbtap_vendor_preload_live_handoff_v2481.py
```

Observed dry-run result:

```json
{
  "decision": "v2481-acdbtap-vendor-preload-live-dry-run",
  "future_live_ready": true,
  "future_live_blockers": [],
  "ok": true
}
```

## Next step

Run the V2481 live handoff in the recoverable envelope. Expected first useful
outcomes are:

- full or partial ACDB tap capture, followed by V2321 rollback;
- `vendor-preload-candidate-not-verified`, if the Magisk overlay does not expose
  the V2475 SHA under a vendor-visible path;
- `preload-not-confirmed`, if the vendor path exists but the HAL still does not
  map `libacdbtap`.
