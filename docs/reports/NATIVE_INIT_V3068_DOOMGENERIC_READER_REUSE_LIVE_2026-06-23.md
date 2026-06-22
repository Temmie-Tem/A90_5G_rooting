# Native Init V3068 DOOMGENERIC Reader Reuse Live

## Summary

- Cycle: `V3068`
- Track: active Video playback / DOOM capstone frame pacing.
- Decision: `v3068-doomgeneric-reader-reuse-live-pass`
- Result: PASS
- Flashed artifact: `workspace/private/inputs/boot_images/boot_linux_v3067_doomgeneric_reader_reuse.img`
- Boot SHA256: `3463ce2415217eeeba689bda796113a1343a8062229727dea0b2958b87790618`
- Init after flash: `A90 Linux init 0.10.91 (v3067-doomgeneric-reader-reuse)`

## Flash Gate

- Built artifact was checksummed before flash.
- Rollback images were present and matched the required SHA256 values for `v2321` and `v2237`; `v48` fallback was present.
- Recovery/TWRP files were present under the private firmware input path.
- Flash path: `native_init_flash.py` only.
- Flash helper verified local marker, remote pushed-image SHA256, boot readback prefix SHA256, reboot to native init, and post-boot `version`/`status`.

## Health

- Pre-flash resident: `0.10.90 (v3065-doomgeneric-large-scale-off)`.
- Pre-flash DOOM loop was stopped before flashing.
- Post-flash health: `selftest pass=12 warn=1 fail=0`.
- Post-flash storage/runtime: SD-backed runtime mounted and writable.
- Post-flash transport: serial ready, NCM/tcpctl ready on the device side.

## DOOM Status Markers

- `video.demo.engine.bridge=v3067-doomgeneric-reader-reuse`
- `video.demo.engine.active=doomgeneric-private-link-v3067-reader-reuse`
- `video.demo.engine.helper=/bin/a90_doomgeneric_private_engine_v3067`
- `video.demo.doom.loop.frame_ms=28`
- `video.demo.doom.presenter.pacing=helper-frame-mtime`
- `video.demo.doom.presenter.poll_ms=4`
- `video.demo.doom.presenter.reader=reused-loop-buffer`
- `video.demo.doom.presenter.buffer_reuse=1`
- `video.demo.doom.dashboard.native=1`
- `video.demo.doom.dashboard.large_frame=0`
- `video.demo.doom.dashboard.frame_scale=1:1`
- `video.demo.input.active=udp-ncm-to-DG_GetKey-with-serial-doompad-fallback`
- `video.demo.input.udp_port=30570`

## Live Functional Check

- Bounded foreground loop with `3` requested frames returned `rc=0`.
- Foreground loop proved the new reader path with `video.demo.doom.loop.presenter.buffer_allocations=1`.
- Started continuous loop with `video demo doom loop-start 0 --wad runtime-private --sha256 EXPECTED`.
- Loop status after start: `active=1`, `continuous=1`.
- Frame artifact existed at the V3067 frame path with expected byte size `1024000`.
- Repaired host NCM route with the checked `ncm_host_setup.py setup --interface <host-ncm-iface>` helper after reboot re-enumerated the host interface.
- Sent compact UDP input packets over USB NCM.
- Device input-state file advanced to `seq=503` and returned to all-up state.
- Loop status after UDP input remained `active=1`, `continuous=1`.

## Pacing Probe

- Short in-device mtime sampling still showed frame-file updates mostly in `30ms` and `40ms` steps.
- `top` during the continuous loop showed the presenter around `4.9%` CPU and the DOOM engine around `0.8%` CPU, with the system mostly idle.
- CPU saturation and thermal throttling are still unlikely as the primary stutter cause.

## New Finding

The presenter process was sampled in `D (disk sleep)`. Kernel stack access showed it blocked under:

- `wsa881x_get_temp`
- `thermal_zone_get_temp`
- `temp_show`
- `sysfs_kf_seq_show`
- `vfs_read`

That points at native dashboard metric collection, not DOOM rendering, as another concrete stutter source. The dashboard is reading thermal/sysfs data while presenting frames, and at least one speaker/codec thermal path can block through SoundWire register access. This explains visible cadence stalls even after presenter sleep sync, mtime gating, frame_ms=28, large scaling off, and reader-buffer reuse.

## Result

V3067 proves the per-frame presenter malloc/free cost can be removed without breaking boot, health, WAD playback, native dashboard visibility, audio corun startup, or UDP input. It does not materially change the observed frame-file mtime cadence. The next highest-value candidate is to cache/throttle native dashboard metric reads so per-frame presentation does not synchronously read slow thermal/sysfs paths.

## Operational Notes

- The repeated host-side NCM route issue reproduced again after reboot/re-enumeration. Any UDP input test should preflight `ncm_host_setup.py status|setup`.
- A concurrent serial validation attempt caused lock-busy/parse-noise; the bridge recovered immediately, and subsequent sequential `version`, `selftest`, and DOOM commands passed. Future validation commands that use cmdv1 should remain sequential.

## Safety

- No forbidden partition was touched.
- No raw host-side partition command was used outside `native_init_flash.py`.
- No Wi-Fi credential action was attempted.
- Public report redacts host/device IP, MAC, interface, and serial identifiers.
- DOOM loop was left active for operator visual inspection.
