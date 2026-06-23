# Native Init V3117 DOOMGENERIC Pre-Scaled Producer Live Validation

## Summary

- Decision: `v3117-doomgeneric-prescaled-producer-two-vblank-before-rollback`
- Result before rollback: `1`
- Loop classification: `prescaled-producer-two-vblank`
- Track: DOOM large-frame scale-path optimization.
- Candidate: `A90 Linux init 0.10.113 (v3116-doomgeneric-prescaled-producer)`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v3116_doomgeneric_prescaled_producer.img`
- Candidate SHA256: `4c7ca0757aad988dc8a500d3c06b3fe140dc4005f97e46beaf558591444462d3`
- Private run dir: `workspace/private/runs/video/v3117-doomgeneric-prescaled-producer-live-20260623-120341`
- Live execution: `1`

## Preflight

- Preflight ok: `1`
- Candidate SHA256 ok: `1`
- Rollback v2321 SHA256 ok: `1`
- Fallback v2237 SHA256 ok: `1`
- Fallback v48 exists: `1`
- Flash helper exists: `1`
- Recovery gate: `native_init_flash.py wait_recovery_adb during candidate flash; rollback_v2321 on failure`
- Operator prerequisite: `runtime-private WAD must already be staged on SD; host input is not required for this bounded loop`
- Expected pre-scaled scale path: `producer-pre-scaled-raw-rowcopy`
- Expected frame scale: `1:1-pre-scaled`

## Live Evidence

- Pre-flash current version: `0.9.285 (v2321-usb-clean-identity-rodata)`
- Pre-flash selftest fail=0: `1`
- Candidate version ok: `1`
- Candidate selftest fail=0: `1`
- Candidate hide-before-loop ok: `1`
- DOOM loop rc: `0` transport_rc=`0` protocol_end=`1`
- Frames requested/presented: `180` / `180`
- Pre-scaled marker count: `180` markers_ok=`1`
- Frame mode/scale/path: `minimal-large-pre-scaled-producer` / `1:1-pre-scaled` / `producer-pre-scaled-raw-rowcopy`
- Timing alloc/read/begin avg us: `1` / `484` / `4574`
- Timing draw avg/max us: `1166` / `1924`
- Timing present avg us: `16023`
- Timing total avg/max us: `22249` / `22655`
- Flip events: `180` delta avg/max us: `32802` / `33342` 60hz_stable=`0` 30hz_stable=`1`
- Shared seq missed/max-gap: `0` / `1` clean=`1`
- Duplicate frame polls: `174`
- Candidate post-loop selftest fail=0: `1`

## Loop Markers

- `video.demo.doom.dashboard.frame_mode=minimal-large-pre-scaled-producer`: `1`
- `video.demo.doom.dashboard.frame_scale=1:1-pre-scaled`: `1`
- `video.demo.doom.dashboard.pre_scaled_large_frame=1`: `1`
- `video.demo.doom.dashboard.scale_path=producer-pre-scaled-raw-rowcopy`: `1`
- `video.demo.doom.loop.flip_telemetry=pageflip-event-delta-us`: `1`
- `video.demo.doom.loop.seq_telemetry=1`: `1`
- `video.demo.doom.loop.timing_probe=1`: `1`
- `video.demo.doom.loop.verify.ok=1`: `1`
- `video.demo.doom.loop=doomgeneric-sd-wad-visible-playable-loop`: `1`

## Rollback Evidence

- Rollback attempted: `1`
- Rollback step ok: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Interpretation

- `prescaled-producer-clean` means large-frame presenter scaling is removed, shared-frame sequencing is clean, and pageflip cadence is stable; any residual stepped motion is the known DOOM 35 Hz game-tic cadence on a 60 Hz panel.
- `prescaled-producer-two-vblank` means the pre-scaled path is active and cadence is stable, but the loop presents one new frame about every two vblanks rather than every vblank.
- `prescaled-producer-timing-review` means V3116 is active but the next suspect is producer-side 960x600 pixel work, shared-frame double-copy, or dashboard/KMS clear cost.
- `prescaled-marker-missing` means the image did not exercise the intended pre-scaled producer path.
- This candidate still uses a bounded tone corun, not real DOOM music/SFX.

## Safety

- Live mode flashes only the boot partition through `native_init_flash.py`; rollback target remains `v2321`.
- The validation path hides the auto menu and then runs one bounded foreground `video demo doom loop` over the serial command bridge.
- No Wi-Fi connect/dhcp/ping, PMIC, backlight, GPIO, regulator, GDSC, panel re-init, GPU/GL stack, or forbidden partition path is touched.
- Raw command output stays private under `workspace/private/runs/`; this report includes metadata only.

## Host Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doomgeneric_prescaled_producer_live_validation_v3117.py tests/test_native_doomgeneric_prescaled_producer_live_v3117.py`: PASS
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doomgeneric_prescaled_producer_live_v3117`: PASS
- dry-run preflight/report: PASS when preflight assets are present.
- `git diff --check`: PASS
