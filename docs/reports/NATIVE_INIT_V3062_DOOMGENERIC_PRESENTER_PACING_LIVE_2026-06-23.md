# Native Init V3062 DOOMGENERIC Presenter Pacing Live

## Summary

- Cycle: `V3062`
- Track: active Video playback / DOOM capstone frame pacing.
- Decision: `v3062-doomgeneric-presenter-pacing-live-pass`
- Result: PASS
- Flashed artifact: `workspace/private/inputs/boot_images/boot_linux_v3061_doomgeneric_presenter_pacing.img`
- Boot SHA256: `c0b7d48542dbe0217029caa615029a608adb8dd838b05733fb067e36ae2f13eb`
- Init after flash: `A90 Linux init 0.10.88 (v3061-doomgeneric-presenter-pacing)`

## Flash Gate

- Built artifact was checksummed before flash.
- Rollback images were present and matched the required SHA256 values for `v2321` and `v2237`; `v48` fallback was present.
- Recovery/TWRP files were present under the private firmware input path.
- Flash path: `native_init_flash.py` only.
- Flash helper verified local marker, remote pushed-image SHA256, boot readback prefix SHA256, reboot to native init, and post-boot `version`/`status`.

## Health

- Pre-flash resident: `0.10.87 (v3059-doomgeneric-udp-input)`.
- Pre-flash health: `selftest pass=12 warn=1 fail=0`.
- Post-flash health: `selftest pass=12 warn=1 fail=0`.
- Post-flash storage/runtime: SD-backed runtime mounted and writable.
- Post-flash transport: serial ready, NCM/tcpctl ready on the device side.

## DOOM Status Markers

- `video.demo.engine.bridge=v3061-doomgeneric-presenter-pacing`
- `video.demo.engine.active=doomgeneric-private-link-v3061-presenter-pacing`
- `video.demo.engine.helper=/bin/a90_doomgeneric_private_engine_v3061`
- `video.demo.doom.loop.frame_ms=33`
- `video.demo.doom.presenter.pacing=helper-frame-mtime`
- `video.demo.doom.presenter.poll_ms=4`
- `video.demo.input.active=udp-ncm-to-DG_GetKey-with-serial-doompad-fallback`
- `video.demo.input.udp_port=30570`
- `video.demo.doom.dashboard.large_frame=1`

## Live Functional Check

- Started continuous loop with `video demo doom loop-start 0 --wad runtime-private --sha256 EXPECTED`.
- Loop status after start: `active=1`, `continuous=1`.
- Frame artifact existed at the V3061 frame path with expected byte size `1024000`.
- Sent compact UDP input packets after restoring the host NCM route.
- Device input-state file advanced to `seq=203` and returned to all-up state.
- Loop status after UDP input remained `active=1`, `continuous=1`.

## Additional Finding

The pacing change was not the only issue. Initial UDP input packets did not reach the device because the host route to `<device-ncm-ip>` was going through the normal LAN gateway instead of the A90 USB NCM interface. The current host NCM interface had no `<host-ncm-ip>/24` address.

Remediation used the checked `ncm_host_setup.py setup --interface <host-ncm-iface>` helper:

- Assigned `<host-ncm-ip>/24` to the verified A90 NCM host interface via NetworkManager.
- Re-applied the device-side NCM address.
- Verified `<device-ncm-ip>` ping success over USB NCM.
- After that, UDP input packets updated `/tmp/a90-doomgeneric-v3061-input.state`.

This means a future "keyboard does not react" report can be caused by host NCM route loss even when the device-side DOOM loop and UDP listener are healthy.

## Serial Note

While the DOOM loop was active, two `a90ctl --input-mode slow` read-only commands saw serial command text corruption before normal framing recovered. Re-running with normal mode succeeded. This did not affect the UDP input path, but it is a separate host/serial command-path stability item to track if status polling is used during gameplay.

## Safety

- No forbidden partition was touched.
- No raw host-side partition command was used outside `native_init_flash.py`.
- No Wi-Fi credential action was attempted.
- Public report redacts host/device IP, MAC, interface, and serial identifiers.
- DOOM loop was left active for operator visual inspection.

## Next

- If stutter is still visible with V3061 active, the next highest-probability causes are frame-file IPC cost and large-dashboard 640x400 to 960x600 CPU scaling.
- The lowest-risk next experiment is a build toggle for a lighter presenter path: keep UDP input and single pacing, but disable/skip large dashboard scaling or cache/reuse the frame buffer read path.
