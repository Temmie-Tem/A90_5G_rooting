# Native Init V3058 DOOMGENERIC Input Socket Live

## Summary

- Cycle: `V3058`
- Track: active Video playback / DOOM capstone input responsiveness.
- Result: PASS
- Device flash: `yes`
- Flashed artifact: `workspace/private/inputs/boot_images/boot_linux_v3057_doomgeneric_input_socket.img`
- Flashed SHA256: `27a6e03e8af7005078be184b2d722f25ebbebf990ea21ab73573cea73d64458a`
- Init: `A90 Linux init 0.10.86 (v3057-doomgeneric-input-socket)`

## Safety Gates

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img` SHA256 matched:
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img` SHA256 matched:
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- Final fallback `boot_linux_v48.img` was present with SHA256:
  `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
- TWRP recovery files were present under `workspace/private/inputs/firmware/twrp/`.
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py` only.
- Forbidden partitions were not touched.

## Flash Evidence

- Local image marker matched expected init version before flash.
- Local SHA256: `27a6e03e8af7005078be184b2d722f25ebbebf990ea21ab73573cea73d64458a`
- Remote pushed image SHA256 matched the local SHA256.
- Boot block readback prefix SHA256 matched the local SHA256.
- Post-flash native-init verification passed through cmdv1 `version` and `status`.
- Post-flash `selftest verbose`: `pass=12 warn=1 fail=0`.

## Functional Validation

- `video demo doom status` after `hide` reported:
  - `video.demo.engine.bridge=v3057-doomgeneric-input-socket`
  - `video.demo.engine.active=doomgeneric-private-link-v3057-input-socket`
  - `video.demo.input.active=serial-doompad-to-DG_GetKey-via-unix-dgram`
  - `video.demo.input.state_path=/tmp/a90-doomgeneric-v3057-input.state`
  - `video.demo.input.socket_path=/tmp/a90-doomgeneric-v3057-input.sock`
  - WAD present/regular/size_ok all `1`
- `video demo doom loop-start 0 --wad runtime-private --sha256 ...` returned `rc=0`.
- `video demo doom loop-status` returned:
  - `video.demo.doom.loop_status.active=1`
  - `video.demo.doom.loop_status.continuous=1`
  - `video.demo.doom.loop_status.frames=0`
- `doompad state 100 0x11` returned:
  - `doompad.input_state.updated=1`
  - `doompad.input_state.rc=0`
  - `doompad.input_socket.sent=1`
  - `doompad.input_socket.rc=0`
- `doompad state 101 0x00` returned:
  - `doompad.input_state.updated=1`
  - `doompad.input_state.rc=0`
  - `doompad.input_socket.sent=1`
  - `doompad.input_socket.rc=0`
- Final `selftest verbose`: `pass=12 warn=1 fail=0`.

## Result

V3057 is live on-device and the structural input change is proven at the device
boundary: native `doompad` state updates now reach the helper-owned Unix datagram
socket with `rc=0`, while the text state file remains available as dashboard and
fallback state.

The DOOM loop was left running in continuous mode for operator testing.

## Next Unit

- Run ID: `V3059`
- Scope: host-side retest with `host_doompad_keyboard_v3033.py --input-backend evdev`
  against the V3057 resident, then measure whether remaining latency is now serial
  transport/render cadence rather than device-internal IPC.
- Follow-on structural step: UDP/NCM input transport to remove serial console
  transaction and lock contention entirely.
