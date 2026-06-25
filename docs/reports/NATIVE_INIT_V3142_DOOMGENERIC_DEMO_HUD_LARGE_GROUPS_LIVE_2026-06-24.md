# Native Init V3142 DOOMGENERIC Large Groups Demo HUD Live Validation

## Summary

- Cycle: `V3142`
- Track: DOOM native demo presentation live validation of the V3141 large grouped HUD build.
- Result: PASS
- Flashed image: `workspace/private/inputs/boot_images/boot_linux_v3141_doomgeneric_demo_hud_large_groups.img`
- Boot SHA256: `968a203b06b536527b11b8b2939cda81b4ed16ee12cf3f8a2e777f521ceff25f`
- Init: `A90 Linux init 0.10.124 (v3141-doomgeneric-demo-hud-large-groups)`

## Flash Gate

- Rollback precondition: v2321, v2237, and v48 rollback images existed and matched the expected SHA256 values.
- Recovery precondition: checked recovery image was present under the private firmware inputs.
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py --from-native`.
- Remote write/readback: boot partition prefix SHA256 matched the local V3141 image SHA256.
- Forbidden partitions: no forbidden partition write path was used.

## Health

- Native flash helper verification: `version` and `status` returned V3141 with status OK.
- Direct post-flash `selftest`: PASS after one serial framing retry.
- Final selftest: `pass=12 warn=1 fail=0`.
- Note: first direct selftest attempt after flash lost the protocol END marker and echoed a malformed command; a following `version` command resynchronized the console, and the repeated `selftest` passed.

## DOOM HUD Contract

- `video.demo.engine.bridge=v3141-doomgeneric-demo-hud-large-groups`
- `video.demo.engine.active=doomgeneric-private-link-v3141-demo-hud-large-groups`
- `video.demo.doom.dashboard.layout=top-frame-large-grouped-hw-doom-input-footer`
- `video.demo.doom.dashboard.large_groups=1`
- `video.demo.doom.dashboard.text_scale=group4-main4-sub3-small2`
- Runtime WAD: present, regular, size OK.
- WAD verify: SHA256 match, `IWAD`, `ok=1`.

## Frame Loop Validation

- First 240-frame loop: `frames_presented=240`, `display.rc=0`, `loop.rc=0`.
- First loop timing: draw avg/max `4514/58910 us`, total avg/max `7756/61391 us`.
- Warm 240-frame loop: `frames_presented=240`, `display.rc=0`, `loop.rc=0`.
- Warm loop timing: draw avg/max `4293/4743 us`, total avg/max `7529/17437 us`.
- Warm loop shared-frame telemetry: `shared_missed_frames=0`, max sequence gap `1`.
- Presenter path: pageflip, shared-mmap direct blit, cached metrics/status pacing.

## Input Validation

- USB-NCM route was rebound through NetworkManager to the post-reboot USB ethernet interface.
- USB-NCM ping: 2/2 received, 0 percent loss, avg about `2.2 ms`.
- Continuous loop start: `active=1`, `continuous=1`, PID reported.
- UDP input right-down smoke: sent seq `314101`, mask `0x08`; state file showed `right=1`, `active=1`.
- UDP input all-up smoke: sent seq `314102`, mask `0x00`; state file showed all buttons `0`, `active=0`.
- Current final loop status: `active=1`, `continuous=1`, frames `0`.

## Safety Notes

- No Wi-Fi connect, DHCP, or Wi-Fi ping was run.
- Network validation was limited to the USB-NCM local input path required by this DOOM sub-goal.
- No GPU/GL stack, panel re-init, PMIC, regulator, GDSC, GPIO, or external subsystem work was performed.

