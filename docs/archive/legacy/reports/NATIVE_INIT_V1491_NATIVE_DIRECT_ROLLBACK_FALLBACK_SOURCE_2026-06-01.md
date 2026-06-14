# Native Init V1491 Native Direct Rollback Fallback Source Update

## Summary

- Cycle: `V1491`
- Type: source-only handoff runner safety update
- Decision: `v1491-native-direct-rollback-fallback-source-pass`
- Result: PASS
- Reason: added an explicit native direct rollback fallback for future test-boot handoffs when recovery ADB is unavailable

## Change

- Updated `scripts/revalidation/native_wifi_test_boot_handoff_v1395.py`.
- Added `--native-direct-rollback-fallback`.
- Added rollback controls for:
  - pre-staged remote image path: `/cache/boot_linux_v724.img`
  - boot block path: `/dev/block/sda24`
  - boot block major/minor: `259:8`
  - native direct rollback timeout
- Fallback sequence:
  - verify the pre-staged rollback image sha256 on-device
  - create the boot block node if missing
  - write the rollback image with `dd ... conv=fsync && sync`
  - read back the written boot prefix sha256
  - reboot
  - verify expected rollback version through the serial bridge

## Safety Scope

No device mutation, flash, reboot, partition write, Wi-Fi HAL, scan/connect,
credential handling, DHCP/routes, external ping, PMIC/GPIO/GDSC write, blind
eSoC notify/`BOOT_DONE` spoof, global PCI rescan, or platform bind/unbind was
performed by this source-only update. Live validation was limited to read-only
status/selftest checks.

## Rationale

V1490 proved that the generic TWRP rollback path can fail when recovery ADB does
not appear after a native `recovery` request, while native serial/NCM access can
still recover the device. Future handoff runners need this fallback before more
rollbackable Wi-Fi test boot flashes.

## Verification

- Python syntax check passed for the updated base runner.
- Diff whitespace check passed.
- Secret literal scan over changed tracked files passed.
- Device stayed on `A90 Linux init 0.9.68 (v724)` with selftest `fail=0`.

## Next

V1492 should use the new fallback flag in a bounded live handoff only after the
rollback image is pre-staged at `/cache/boot_linux_v724.img` with the expected
v724 sha256.
