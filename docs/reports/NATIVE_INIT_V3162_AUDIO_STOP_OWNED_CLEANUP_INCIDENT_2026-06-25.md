# Native Init V3162 Audio Stop-Owned Cleanup Incident

## Summary

- Cycle: `V3162`
- Candidate: `v3162-audio-stop-owned-cleanup`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3162_audio_stop_owned_cleanup.img`
- Boot SHA256: `eaf08364d2b2b75c2c5176c9e7842eb1694878e538f342992ffc6584e40900e1`
- Incident: post-flash native-init verification failed; rollback attempt could not reach recovery ADB because the device was not visible on USB.
- Status: STOP. Do not flash anything else until the device is visible again in recovery/TWRP or native-init.

## Pre-Flash State

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img` existed and matched SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Deeper fallback `boot_linux_v2237_supplicant_terminate_poll.img` existed and matched SHA256 `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` existed.
- TWRP artifacts existed under `workspace/private/inputs/firmware/twrp/`.
- Pre-flash `selftest verbose` on the previous resident image returned `pass=12 warn=1 fail=0`.

## Flash Result

- `native_init_flash.py` was used.
- Local image SHA matched the pinned V3162 SHA.
- Recovery ADB became available for the flash step.
- Boot partition write completed.
- Boot readback prefix SHA matched `eaf08364d2b2b75c2c5176c9e7842eb1694878e538f342992ffc6584e40900e1`.
- Reboot to system was requested through TWRP.

## Failure

- Post-flash cmdv1 verification did not complete.
- The helper reported `A90P1 END marker not found before timeout (180.0s)`.
- Raw fallback verification also failed.
- Total verify elapsed time was about 360 seconds.
- The helper reported a bridge command timeout for `version`.

## Rollback Attempt

- Rollback target: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback target SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Rollback was attempted only through `native_init_flash.py`.
- Recovery ADB did not appear within the helper timeout.
- `adb devices -l` showed no attached device.
- `lsusb` showed no A90/Samsung device entry.
- Rollback did not run because the checked helper could not reach recovery.

## Current Rule

- No further flash attempts are allowed while the device remains USB-invisible.
- Next safe action is physical recovery: make the device visible in TWRP/recovery or native-init, then re-run the v2321 rollback through `native_init_flash.py`.
