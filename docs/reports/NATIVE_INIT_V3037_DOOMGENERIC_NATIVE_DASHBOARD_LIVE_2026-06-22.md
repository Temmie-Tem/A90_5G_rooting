# Native Init V3037 DOOMGENERIC Native Dashboard Live Validation

## Summary

- Cycle: `V3037`
- Track: active Video playback / DOOM capstone.
- Decision: `v3036-doomgeneric-native-dashboard-live-pass`
- Result: PASS
- Device flash: yes, boot partition only.
- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v3036_doomgeneric_native_dashboard.img`
- Candidate SHA256: `b7d64242c65a77b6555b7be9891b9b3b3b79e6b2f3d68a4b9448f4e1313706d6`
- Flashed init: `A90 Linux init 0.10.77 (v3036-doomgeneric-native-dashboard)`
- Final state: candidate left installed for operator demo; DOOM loop stopped and doompad reset.

## Safety Gates

- Forbidden partitions: not touched.
- Write target: boot partition only through the checked flash helper.
- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img`: present and SHA256 matched.
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img`: present and SHA256 matched.
- Final fallback `boot_linux_v48.img`: present and SHA256 matched.
- Recovery availability: TWRP `3.7.0_12-0` reached before flash.
- Wi-Fi actions: none.
- OTG, evdev injection, uinput, GPIO, PMIC, regulator, modem, vbmeta, bootloader, `/efs`, `/sec_efs`, keymaster, RPMB: not touched.

## Preflash Health

- Bridge wrapper: running and probe connected.
- Baseline before flash: `A90 Linux init 0.10.76 (v3033-doomgeneric-visible-loop)`.
- Preflash status: `BOOT OK`.
- Preflash selftest: `pass=12 warn=1 fail=0`.
- Prior DOOM loop state was stopped and doompad state was reset before rebooting to recovery.

## Flash Result

- Local Android boot magic check: PASS.
- Local marker check for `A90 Linux init 0.10.77 (v3036-doomgeneric-native-dashboard)`: PASS.
- Local candidate SHA256: matched.
- Remote pushed candidate SHA256 in recovery: matched.
- Boot write via checked helper: PASS.
- Boot readback prefix verification: PASS.
- Reboot to native init: PASS.
- Flash helper native verification: `version/status rc=0 status=ok`.
- Total helper elapsed time: `36.083s`.
- Rollback performed: no, because candidate booted and passed health checks.

## Postflash Health

- `version`: `A90 Linux init 0.10.77 (v3036-doomgeneric-native-dashboard)`.
- `status`: `BOOT OK`.
- `selftest`: `pass=12 warn=1 fail=0`.
- Storage backend: SD runtime workspace mounted read-write.
- Display: native KMS display ready.
- Thermal/power sample from status: CPU `45.9C`, GPU `43.7C`, power `0.5W`.

## DOOM Status

- Runtime WAD path: `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- Runtime WAD SHA256 contract: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Runtime WAD present: `1`
- Runtime WAD regular file: `1`
- Runtime WAD bytes: `4196020`
- Runtime WAD size_ok: `1`
- WAD embedded in boot: `0`
- Helper path: `/bin/a90_doomgeneric_private_engine_v3036`
- Helper present: `1`
- Helper executable: `1`
- Frame path: `/tmp/a90-doomgeneric-v3036-dashboard-frame.xbgr8888`
- Input state path: `/tmp/a90-doomgeneric-v3036-input.state`
- Loop visible: `1`
- Loop frame ms: `50`
- Native dashboard marker: `video.demo.doom.dashboard.native=1`
- Native dashboard layout: `video.demo.doom.dashboard.layout=top-frame-metrics-logs-input`
- Native dashboard display: `video.demo.doom.dashboard.display=demo-visible-native-kms`
- Host dashboard marker: `video.demo.input.host_dashboard=host_doompad_dashboard_v3035.py`
- Host keyboard bridge marker: `video.demo.input.host_keyboard_bridge=host_doompad_keyboard_v3033.py`
- OTG required marker: `video.demo.input.otg_required=0`

## Loop And Input Validation

- `doompad reset`: PASS, state path updated.
- `video demo doom loop-start 300 --wad runtime-private --sha256 EXPECTED`: PASS.
- Background loop pid reported: present.
- `video demo doom loop-status`: active `1`.
- KMS dashboard presenter log: `doomdash: presented framebuffer 1080x2400 on crtc=133`.
- `doompad key forward 1`: PASS, state changed to `forward=1 active=1`.
- `doompad status`: PASS, state retained `forward=1 active=1`.
- `doompad key fire 1`: PASS, state changed to `forward=1 fire=1 active=1`.
- `doompad key fire 0`: PASS, state changed to `forward=1 fire=0 active=1`.
- `doompad key forward 0`: PASS, state changed to all roles released and `active=0`.
- Second loop-status while inputs had been exercised: active `1`.
- `video demo doom loop-stop`: PASS.
- Final `doompad reset`: PASS, final state all roles released and `active=0`.

## Host Dashboard Check

- Command: `host_doompad_dashboard_v3035.py --once --no-loop-start --no-loop-stop --loop-frames 8`
- Result: PASS.
- Snapshot version: `A90 Linux init 0.10.77 (v3036-doomgeneric-native-dashboard)`.
- Snapshot selftest: `pass=12 warn=1 fail=0`.
- Snapshot loop status after cleanup: inactive.
- Snapshot included CPU/GPU thermal, power, memory, doompad state, and host input markers.

## Host Keyboard Check

- The live keyboard bridge remains the existing host terminal path:
  `host_doompad_keyboard_v3033.py` -> `a90ctl.py doompad key <role> <0|1>` -> serial doompad state file -> `DG_GetKey`.
- Physical host-key press validation was not performed by Codex because it requires interactive operator input.
- A non-interactive pseudo-TTY attempt was inconclusive and is not counted as validation evidence.
- Scripted serial doompad transitions above validate the device-side input consumer and native dashboard input-state visibility.

## Operator Demo State

- Device is left on V3036 because flash, boot, status, selftest, WAD checks, native dashboard markers, loop start/stop, and scripted input transitions all passed.
- DOOM loop is stopped.
- Doompad state is reset.
- To start the demo manually:

```sh
python3 workspace/public/src/scripts/revalidation/host_doompad_dashboard_v3035.py
```

- To use the simpler keyboard bridge manually:

```sh
python3 workspace/public/src/scripts/revalidation/host_doompad_keyboard_v3033.py
```

## Next

- Operator should run the interactive host dashboard and press `WASD`, arrow keys, space, enter, `m`, and `r` while watching both the phone display and dashboard input log.
- If physical host keyboard input is unreliable, add an explicit non-interactive validation mode to the host dashboard/keyboard script so CI can inject timed key tokens through the same command sender without depending on a terminal TTY.
