# Native Init V3148 DOOMGENERIC SFX Stream Refresh Live

## Summary

- Cycle: `V3148`
- Build: `v3148-doomgeneric-sfx-stream-refresh`
- Init version: `0.10.130`
- Result: PASS
- Device command: yes, boot partition only through `native_init_flash.py`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3148_doomgeneric_sfx_stream_refresh.img`
- Boot SHA256: `0f9b2d74e93e539bf73bffc102ef581335263b34ed3f286e0a0ed19401396605`
- Init SHA256: `5afc6e04ca7ef1f90b15ec8fa5bd277b62e96206d7d2f209052701fc6dae17e0`
- Ramdisk SHA256: `401dc47e7c6958fd2f1710b3576b22bed5350b464c62a27fcb1f1f0c6011873e`
- Helper SHA256: `062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910`

## Change

- DOOM SFX was confirmed audible when a bounded PCM stream worker was manually restarted.
- Root cause: the previous SFX worker was a 10-second bounded `audio play --pcm-stream` co-run, so continuous DOOM playback became silent after the worker completed.
- V3148 keeps the 10-second audio safety cap and adds quiet automatic refresh every `13000ms` during continuous background DOOM loop playback.
- The quiet refresh path uses `a90_audio_start_pcm_stream_worker_quiet()` to avoid periodic serial-console log spam from `audio play` preflight output.

## Preflight

- Rollback image `boot_linux_v2321_usb_clean_identity_rodata.img` SHA256 matched `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Fallback image `boot_linux_v2237_supplicant_terminate_poll.img` SHA256 matched `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- Final fallback `boot_linux_v48.img` was present.
- Current resident before flash was `A90 Linux init 0.10.129 (v3147-doomgeneric-sfx-stream-sigpipe-safe)`.
- Pre-flash `status` reported `selftest: pass=12 warn=1 fail=0`.
- Pre-flash `selftest verbose` reported `fail=0`.

## Flash

- Helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`
- Command shape: `native_init_flash.py --from-native --expect-version v3148-doomgeneric-sfx-stream-refresh --expect-sha256 <V3148_BOOT_SHA> <V3148_BOOT_IMAGE>`
- Recovery/TWRP path was exercised by the helper.
- Remote pushed image SHA256 matched the local V3148 SHA256.
- Boot partition readback SHA256 matched `0f9b2d74e93e539bf73bffc102ef581335263b34ed3f286e0a0ed19401396605`.
- Helper post-reboot verification passed `version/status`.

## Health

- Post-flash version: `A90 Linux init 0.10.130 (v3148-doomgeneric-sfx-stream-refresh)`.
- Post-flash `status`: `BOOT OK`, `selftest: pass=12 warn=1 fail=0`.
- Post-flash `selftest verbose`: `pass=12 warn=1 fail=0`.
- Runtime storage: SD backend mounted read-write.
- DOOM status: runtime WAD present, expected SHA256 matched, helper present and executable.

## Functional Validation

- Started continuous DOOM loop with runtime-private WAD and expected SHA256.
- Loop start prepared FIFO `/cache/a90-runtime/a90-doomgeneric-v3148-sfx.pcmstream`.
- Loop start created initial audio worker `pid=652`.
- After the first refresh window, `audio play-status` showed a new active SFX worker `pid=661`.
- After the next refresh window, `audio play-status` showed a new active SFX worker `pid=663`.
- `doompad tap fire` succeeded while refreshed worker `pid=663` was active.
- `video demo doom loop-status` remained `active=1`, `continuous=1`.

## Host Validation

- `py_compile`: V3033/V3148 builders and V3148 focused test.
- `unittest`: `tests.test_native_doomgeneric_sfx_stream_refresh_source_v3148` passed.
- Source build: AArch64 helper/native-init compile, ramdisk pack, boot image pack, SHA256 capture.
- `git diff --check`: PASS.

## Safety

- No forbidden partition writes were performed.
- No Wi-Fi connect, DHCP, ping, PMIC, regulator, GDSC, GPIO, modem, vbmeta, bootloader, keymaster, RPMB, `/efs`, or `/sec_efs` work was performed.
- WAD/IWAD bytes stayed runtime-private on SD and were not copied into public source or this report.
- Device identifiers, serials, MACs, BSSIDs, IPs, and PARTUUIDs are intentionally omitted.
