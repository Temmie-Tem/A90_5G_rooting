# Native Init V3064 DOOMGENERIC Frame MS28 Live

## Summary

- Cycle: `V3064`
- Track: active Video playback / DOOM capstone frame pacing.
- Decision: `v3064-doomgeneric-frame-ms28-live-pass`
- Result: PASS
- Flashed artifact: `workspace/private/inputs/boot_images/boot_linux_v3063_doomgeneric_frame_ms28.img`
- Boot SHA256: `18a8594d1122da86fe3262548715adb801dc34a7414d314ba08f3a205de0c174`
- Init after flash: `A90 Linux init 0.10.89 (v3063-doomgeneric-frame-ms28)`

## Flash Gate

- Built artifact was checksummed before flash.
- Rollback images were present and matched the required SHA256 values for `v2321` and `v2237`; `v48` fallback was present.
- Recovery/TWRP files were present under the private firmware input path.
- Flash path: `native_init_flash.py` only.
- Flash helper verified local marker, remote pushed-image SHA256, boot readback prefix SHA256, reboot to native init, and post-boot `version`/`status`.

## Health

- Pre-flash resident: `0.10.88 (v3061-doomgeneric-presenter-pacing)`.
- Pre-flash health: `selftest pass=12 warn=1 fail=0`.
- Post-flash health: `selftest pass=12 warn=1 fail=0`.
- Post-flash storage/runtime: SD-backed runtime mounted and writable.
- Post-flash transport: serial ready, NCM/tcpctl ready on the device side.

## DOOM Status Markers

- `video.demo.engine.bridge=v3063-doomgeneric-frame-ms28`
- `video.demo.engine.active=doomgeneric-private-link-v3063-frame-ms28`
- `video.demo.engine.helper=/bin/a90_doomgeneric_private_engine_v3063`
- `video.demo.doom.loop.frame_ms=28`
- `video.demo.doom.presenter.pacing=helper-frame-mtime`
- `video.demo.doom.presenter.poll_ms=4`
- `video.demo.input.active=udp-ncm-to-DG_GetKey-with-serial-doompad-fallback`
- `video.demo.input.udp_port=30570`
- `video.demo.doom.dashboard.large_frame=1`

## Live Functional Check

- Started continuous loop with `video demo doom loop-start 0 --wad runtime-private --sha256 EXPECTED`.
- Loop status after start: `active=1`, `continuous=1`.
- Frame artifact existed at the V3063 frame path with expected byte size `1024000`.
- Sent compact UDP input packets after restoring the host NCM route.
- Device input-state file advanced to `seq=303` and returned to all-up state.
- Loop status after UDP input remained `active=1`, `continuous=1`.

## Additional Finding

The V3062 host-side NCM route issue reproduced after the recovery/system reboot. The A90 NCM function re-enumerated as a new host interface identity; the previous NetworkManager profile no longer applied, so `<device-ncm-ip>` traffic again routed through the normal LAN gateway.

Remediation used the checked `ncm_host_setup.py setup --interface <host-ncm-iface>` helper:

- Re-detected the current verified A90 NCM host interface from device-reported NCM metadata.
- Assigned `<host-ncm-ip>/24` to that current host interface via NetworkManager.
- Re-applied the device-side NCM address.
- Verified `<device-ncm-ip>` ping success over USB NCM.
- After that, UDP input packets updated `/tmp/a90-doomgeneric-v3063-input.state`.

This is now a repeated host-side operational issue: any reboot/re-enumeration can invalidate the host NCM profile binding. UDP input should be preflighted with `ncm_host_setup.py status|setup` before judging gameplay input responsiveness.

## Pacing Result

V3063 proves the `frame_ms=28` experiment is bootable and playable with the same V3061 single-pacing presenter and UDP input path. It does not yet prove the visual result is better by measurement; the operator-visible comparison is the deciding factor for this experiment.

If stutter remains visible, the next priority from the attached suspicion list is to isolate large-dashboard CPU scaling by disabling or optimizing the 640x400 to 960x600 software scale path while keeping V3061/V3063 input and presenter pacing unchanged.

## Safety

- No forbidden partition was touched.
- No raw host-side partition command was used outside `native_init_flash.py`.
- No Wi-Fi credential action was attempted.
- Public report redacts host/device IP, MAC, interface, and serial identifiers.
- DOOM loop was left active for operator visual inspection.
