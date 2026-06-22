# Native Init V3088 DOOMGENERIC UDP Input Live Validation

## Summary

- Cycle: `V3088`
- Resident tested: `A90 Linux init 0.10.100 (v3086-doomgeneric-pageflip-cadence)`
- Decision: `v3088-doomgeneric-udp-input-live-pass-after-host-ncm-setup`
- Result: PASS
- New flash: no
- Rollback: not needed

## Context

V3087 proved the DOOM presenter can reach 60Hz pageflip cadence after disabling the extra pageflip submit guard. V3088 checked the next practical issue: whether host keyboard-style UDP/NCM input reaches the running DOOM helper continuously without blocking serial control-plane commands.

## Initial Finding

The first scripted UDP input packets did not create or update the DOOM input-state file.

Host-side network inspection showed the cause was not the DOOM helper:

- Device NCM was active.
- The host USB NCM interface was up but lacked the expected local IPv4 address.
- Host route selection for the device NCM address was going through a non-USB gateway.
- Device ping over NCM failed before host setup.

The host NCM link was repaired with the checked repository helper:

`workspace/public/src/scripts/revalidation/ncm_host_setup.py --interface <host-usb-ncm-iface> --manual-host-config setup`

After setup:

- Host USB NCM interface had the expected local IPv4 address.
- Device ping over NCM succeeded.

No device boot image or partition write was performed in this unit.

## Continuous Loop

Command:

`video demo doom loop-start 0 --wad runtime-private --sha256 <expected-runtime-wad-sha256>`

Result:

- Background continuous loop started.
- V3086 engine/helper markers were present.
- Shared-frame IPC remained active.
- Pageflip min submit interval was `0`.
- Background serial-preserve marker was present.
- Audio co-run start returned rc `0`.

## UDP Input Checks

Packet format:

- little-endian `{magic, version, seq, mask, active}`
- transport: UDP over USB NCM
- target: DOOM helper input UDP listener

Single-state checks:

- Sent `seq=400`, mask `forward+run`.
- Sent `seq=401`, mask `forward+run+fire`.
- Sent `seq=402`, mask `release`.
- Device input-state file reported `seq=402` and all roles released.

Held-state check:

- Sent `seq=500`, mask `forward+run+fire`.
- Device input-state file reported:
  - `seq=500`
  - `forward=1`
  - `fire=1`
  - `run=1`
  - `active=1`
- Sent `seq=501`, mask `release`.
- Device input-state file reported `seq=501` and `active=0`.

30-second burst check:

- Sent 600 timed input packets plus final release.
- Final release packet used `seq=1199`.
- Device input-state file reported `seq=1199` and `active=0`.
- Continuous DOOM loop remained active after the burst.

## Serial Control-Plane During Input

During the 30-second UDP burst, serial/cmdv1 commands were issued concurrently:

- `version`: completed successfully three times.
- `video demo doom loop-status`: completed successfully three times.
- No A90P1 framing loss was observed.
- No END marker timeout was observed.
- No serial command error was observed.

This confirms that the V3084 serial-preserve fix and the V3059 UDP input transport work together on V3086 once host NCM is configured correctly.

## Cleanup / Health

- `video demo doom loop-stop` completed with rc `0`.
- Audio stop/reset path completed with rc `0`.
- Final `selftest` completed with fail count `0`.

## Conclusion

The remaining input issue in this run was host-side NCM configuration, not the device helper or DOOM input parser. With the host USB NCM interface configured, UDP input state updates are observed on-device while DOOM runs continuously, and serial control-plane commands remain reliable during sustained input traffic.

## Remaining Issues / Next Suspects

1. Human hands-on evdev validation is still needed for true feel: `host_doompad_keyboard_v3033.py --input-backend evdev --input-transport udp ...`.
2. The host tool has no noninteractive scripted mode, so repeatable input soak currently uses ad hoc UDP packet sends.
3. First post-boot DOOM commands can still need explicit menu hide if autohud owns the display.
4. Real DOOM SFX is still not implemented; current audio remains the bounded co-run tone path.

## Recommended Next Unit

- Run ID: `V3089`
- Purpose: make host input validation repeatable.
- Scope:
  - add a scripted UDP input validator or a `--scripted-demo` mode to `host_doompad_keyboard_v3033.py`,
  - include host NCM preflight with a clear diagnostic when the USB NCM interface lacks the required address,
  - optionally auto-run `ncm_host_setup.py` when explicitly requested,
  - keep interactive evdev mode as the hands-on path.
