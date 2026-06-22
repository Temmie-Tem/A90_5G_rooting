# Native Init V3080 DOOMGENERIC Pace Socket Live Validation

## Summary

- Cycle: `V3080`
- Candidate flashed: `V3079 v3079-doomgeneric-pace-socket`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3079_doomgeneric_pace_socket.img`
- Boot SHA256: `beb44467df47e5ac69506920d8bbcfeeb0e88f2f80311eb029a27c622b90f102`
- Init after flash: `A90 Linux init 0.10.96 (v3079-doomgeneric-pace-socket)`
- Result: PASS

## Safety Gates

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img` exists and matched SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img` exists and matched SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` exists.
- TWRP recovery artifacts are present under `workspace/private/inputs/firmware/twrp/`.
- Flash path was only `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Forbidden partitions were not touched.

## Flash And Health

- Flash command used the expected V3079 boot SHA and expected V3079 version marker.
- Recovery push, boot partition write, and boot partition readback SHA all matched `beb44467df47e5ac69506920d8bbcfeeb0e88f2f80311eb029a27c622b90f102`.
- Native-init verification after reboot passed.
- Post-flash selftest: `pass=12 warn=1 fail=0`.

## DOOM Status Markers

- Engine bridge: `v3079-doomgeneric-pace-socket`.
- Active engine: `doomgeneric-private-link-v3079-pace-socket`.
- WAD: runtime-private SD path present, regular, size OK, SHA matched, not embedded in boot.
- Input: `udp-ncm-to-DG_GetKey-with-serial-doompad-fallback`.
- Presenter pacing: `presenter-pageflip-pace-socket`.
- Presenter: `pageflip`, `kms-dumb-buffer-pageflip`, timeout `1000 ms`.
- Pageflip submit guard: `18 ms`.
- Dashboard: `minimal-fastdraw`, `top-frame-minimal-input`, `frame_scale=1:1`.

## Foreground Timing

300-frame foreground loop completed with `rc=0`.

- Frames presented: `300`
- Poll count: `327`
- Helper done: `1`
- Buffer allocations: `1`
- Pace socket active: `1`
- Pace tokens sent: `300`
- Pace socket failures: `0`
- Pace socket wait timeouts: `0`

Timing probe:

- alloc avg/max: `1 / 15 us`
- read avg/max: `473 / 929 us`
- begin avg/max: `3111 / 3423 us`
- draw avg/max: `747 / 1292 us`
- present avg/max: `23148 / 23656 us`
- total avg/max: `27479 / 27910 us`

Pageflip delta:

- events: `300`
- delta count: `299`
- min/avg/max: `33212 / 33235 / 33253 us`

Compared with V3078 pageflip presenter live telemetry, the visible jitter spike was removed:

- V3078 delta min/avg/max: `16615 / 33456 / 49865 us`
- V3080 delta min/avg/max: `33212 / 33235 / 33253 us`

## Continuous Loop And Input

- `video demo doom loop-start 0 ...` succeeded.
- Continuous loop status: active `1`, continuous `1`, frames `0`.
- Host NCM setup completed and host-to-device ping passed with `0%` loss.
- UDP input packet mirror was verified through the helper state file:
  - `seq=9102`
  - all buttons up after cleanup
  - earlier nonzero packet produced `forward=1 fire=1 active=1`
- Serial `doompad status` intentionally does not show helper-owned UDP state; helper state file is the correct V3059+ validation point.

## Audio Check

- DOOM audio co-run started the native bounded tone worker.
- Worker status reached `done=1 rc=0`.
- PCM write completed:
  - sample rate `48000`
  - channels `2`
  - frames done `480000`
  - bytes done `1920000`

This proves the native audio path executed successfully, but it does not prove perceived loudness to the operator.

## Remaining Issues

- Serial ACM control-plane character loss still recurs under/after DOOM validation. It affected `a90ctl` commands, not UDP gameplay input. Restarting the bridge and using the NCM tcpctl path recovered validation.
- A 120-frame foreground sample showed one initial `16635 us` pageflip delta, while the later 300-frame captured sample was stable at about `33.2 ms`. Treat the 300-frame capture as the acceptance sample and keep the 120-frame anomaly noted for future startup-transient checks.
- The presenter still uses raw frame-file IPC. V3079 fixed cadence ownership, not the long-term direct KMS buffer architecture.

## Decision

V3079 is accepted as the current DOOM pacing baseline. The dominant remaining stutter cause from dual sleep ownership is resolved in the measured 300-frame sample. Next optimization should target serial control-plane robustness and then raw frame-file IPC, not another pageflip pacing tweak.
