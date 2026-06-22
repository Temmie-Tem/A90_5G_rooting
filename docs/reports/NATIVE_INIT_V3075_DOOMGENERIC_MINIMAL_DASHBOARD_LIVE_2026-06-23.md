# Native Init V3075 DOOMGENERIC Minimal Dashboard Live

## Summary

- Cycle: `V3075`
- Track: active Video playback / DOOM capstone frame pacing.
- Decision: `v3075-doomgeneric-minimal-dashboard-live-pass`
- Result: PASS
- Flashed artifact: `workspace/private/inputs/boot_images/boot_linux_v3074_doomgeneric_minimal_dashboard.img`
- Boot SHA256: `c96455943889bae54f8e625618a9fe01675dd110f9eda0e0c720ca8dd5eb3c50`
- Init after flash: `A90 Linux init 0.10.94 (v3074-doomgeneric-minimal-dashboard)`

## Flash Gate

- Built artifact was checksummed before flash.
- Rollback images were present and matched the required SHA256 values for `v2321` and `v2237`; `v48` fallback was present.
- Recovery/TWRP files were present under the private firmware input path.
- Flash path: `native_init_flash.py` only.
- Flash helper verified local marker, remote pushed-image SHA256, boot readback prefix SHA256, reboot to native init, and post-boot `version`/`status`.

## Health

- Pre-flash resident: `0.10.93 (v3071-doomgeneric-frame-timing)`.
- Pre-flash DOOM loop was stopped before flashing.
- Post-flash health: `selftest pass=12 warn=1 fail=0`.
- Post-flash storage/runtime: SD-backed runtime mounted and writable.
- Post-flash transport: serial ready, NCM/tcpctl ready on the device side.

## DOOM Status Markers

- `video.demo.engine.bridge=v3074-doomgeneric-minimal-dashboard`
- `video.demo.engine.active=doomgeneric-private-link-v3074-minimal-dashboard`
- `video.demo.engine.helper=/bin/a90_doomgeneric_private_engine_v3074`
- `video.demo.doom.loop.frame_ms=28`
- `video.demo.doom.presenter.pacing=helper-frame-mtime`
- `video.demo.doom.presenter.poll_ms=4`
- `video.demo.doom.loop.timing_probe=1`
- `video.demo.doom.loop.timing=frame-ipc-kms-stage-us`
- `video.demo.doom.presenter.reader=reused-loop-buffer`
- `video.demo.doom.presenter.buffer_reuse=1`
- `video.demo.doom.dashboard.native=1`
- `video.demo.doom.dashboard.profile=minimal-fastdraw`
- `video.demo.doom.dashboard.layout=top-frame-minimal-input`
- `video.demo.doom.dashboard.redraw=doom-frame-plus-compact-status`
- `video.demo.doom.dashboard.metrics_interval_frames=0`
- `video.demo.doom.dashboard.metrics_pacing=disabled-minimal`
- `video.demo.doom.dashboard.large_frame=0`
- `video.demo.doom.dashboard.frame_mode=minimal-dashboard`
- `video.demo.doom.dashboard.frame_scale=1:1`
- `video.demo.input.active=udp-ncm-to-DG_GetKey-with-serial-doompad-fallback`
- `video.demo.input.udp_port=30570`
- `video.demo.doom.audio_corun.mode=native-audio-corun-tone-v3053`

## Foreground Timing Probe

Foreground `video demo doom loop 180 --wad runtime-private --sha256 EXPECTED` passed with:

- `frames_presented=180`
- `poll_count=708`
- `helper_done=0`
- `display.rc=0`
- `loop.rc=0`
- `presenter.buffer_allocations=1`

`helper_done=0` is expected for this bounded comparison: the presenter reached the requested 180 displayed frames first, then stopped the still-running helper. In the V3073 full-dashboard audit, the helper finished first while the presenter showed only 121 frames.

Stage timing, in microseconds:

| Stage | Average | Max |
| --- | ---: | ---: |
| alloc | 1 | 22 |
| frame-file read | 481 | 995 |
| KMS begin | 4500 | 4606 |
| dashboard/draw | 792 | 1303 |
| KMS present | 7447 | 12948 |
| total | 13221 | 18639 |

## Comparison To V3073

| Metric | V3073 full dashboard | V3075 minimal dashboard |
| --- | ---: | ---: |
| frames presented in 180-frame run | 121 | 180 |
| frame-file read max | 957 us | 995 us |
| dashboard/draw average | 26336 us | 792 us |
| dashboard/draw max | 454916 us | 1303 us |
| KMS present average | 12834 us | 7447 us |
| total average | 42680 us | 13221 us |
| total max | 462781 us | 18639 us |

## Interpretation

The top suspect is confirmed. The prior stutter was not caused by the 1MB frame-file read path or DOOM engine CPU load. Replacing full dashboard repaint with the minimal dashboard path reduced draw max from about `455ms` to about `1.3ms`, reduced total max from about `463ms` to about `18.6ms`, and allowed the presenter to show all requested frames.

The remaining steady cost is now KMS begin/present, still using the existing `SETCRTC` path. That is the next rendering suspect after the dashboard repaint issue.

## Continuous Functional Check

- Started continuous DOOM loop with the V3074 minimal-dashboard image.
- Loop status after start: `active=1`, `continuous=1`.
- Host NCM route was missing after reboot/re-enumeration; repaired with the checked `ncm_host_setup.py setup` helper.
- UDP input over NCM advanced the device input-state to a newer sequence and returned to all-up state.
- Loop status after UDP input remained `active=1`, `continuous=1`.
- CPU sample during continuous playback showed CPU mostly idle; presenter and engine were each low single-digit CPU usage.

## Operational Notes

- A stale long-lived serial bridge produced transient missing-character command input after flash. Restarting the managed `a90_bridge.py` wrapper restored normal cmdv1 framing.
- Two long shell commands later hit the same serial input fragility when sent back-to-back; rerunning the short command separately succeeded.
- Continue to keep live validation commands sequential, avoid immediate chained cmdv1 calls after large output, and restart the managed bridge if command text is visibly corrupted.
- An earlier V3074 image was flashed successfully before a marker-only status correction changed the final boot SHA256. The final validated artifact is the SHA256 recorded in this report.

## Safety

- No forbidden partition was touched.
- No raw host-side partition command was used outside `native_init_flash.py`.
- No Wi-Fi credential action was attempted.
- Public report redacts host/device IP, MAC, interface, UUID, and serial identifiers.
- DOOM loop was left active for operator visual inspection.
