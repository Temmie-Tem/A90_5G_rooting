# Native Init V3030 DOOMGENERIC SD WAD Command Live Validation

## Summary

- Cycle: `V3030`
- Track: active Video playback / DOOM capstone.
- Decision: `v3030-doomgeneric-sd-wad-command-live-pass-before-rollback`
- Result before rollback: `1`
- Candidate: `A90 Linux init 0.10.74 (v3029-doomgeneric-sd-wad-command)`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_v3029_doomgeneric_sd_wad_command.img`
- Candidate SHA256: `9b45abb847ac64c9032f0e873038a3abf577e27f2dabc2ceccad8cd8e95cf804`
- Candidate helper SHA256: `435dc0bda50dff6c27410ed727d4d513c02bfba89e876ff654a045cf00d26b44`
- Runtime WAD path: `/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`
- Runtime WAD SHA256: `1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`
- Rollback attempted: `1`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Preflight

- Rollback v2321 SHA256 ok: `1`
- Fallback v2237 SHA256 ok: `1`
- Fallback v48 present/hash recorded: `1`
- Candidate SHA256 ok: `1`
- Candidate Android boot magic ok: `1`
- Bridge doctor ok: `1`
- Current resident before candidate flash: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
- Current resident selftest fail=0 before candidate flash: `1`
- TWRP recovery image present on host: `1`
- TWRP recovery confirmed before candidate boot write: `1`
- Flash helper: `workspace/public/src/scripts/revalidation/native_init_flash.py`

## Flash Evidence

- Candidate flashed through checked helper: `1`
- Candidate remote SHA256 matched local: `1`
- Candidate boot readback SHA256 matched expected: `1`
- Candidate post-flash version rc/status: `0` / `ok`
- Candidate post-flash status rc/status: `0` / `ok`
- Candidate post-flash selftest fail=0: `1`

## SD-WAD Command Evidence

- `video demo doom status` rc/status: `0` / `ok`
- `video.demo.engine.bridge=v3029-doomgeneric-sd-wad-command`: `1`
- `video.demo.engine.active=doomgeneric-private-link-v3029-sd-wad-smoke`: `1`
- `video.demo.engine.helper.present=1`: `1`
- `video.demo.engine.helper.executable=1`: `1`
- `video.demo.asset.wad.runtime_path=/mnt/sdext/a90/runtime/doom/v3028/DOOM1.WAD`: `1`
- `video.demo.asset.wad.expected_sha256=1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`: `1`
- `video.demo.asset.wad.present=1`: `1`
- `video.demo.asset.wad.bytes=4196020`: `1`
- `video.demo.asset.wad.size_ok=1`: `1`
- `video.demo.asset.wad.embedded_in_boot=0`: `1`
- `video.demo.input.otg_required=0`: `1`

## Verify Evidence

- `video demo doom verify --wad runtime-private --sha256 EXPECTED` rc/status: `0` / `ok`
- `video.demo.doom.verify=doomgeneric-sd-wad`: `1`
- `video.demo.doom.verify.actual_sha256=1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771`: `1`
- `video.demo.doom.verify.sha256_checked=1`: `1`
- `video.demo.doom.verify.sha256_match=1`: `1`
- `video.demo.doom.verify.magic=IWAD`: `1`
- `video.demo.doom.verify.magic_ok=1`: `1`
- `video.demo.doom.verify.bytes=4196020`: `1`
- `video.demo.doom.verify.ok=1`: `1`
- `video.demo.doom.verify.rc=0`: `1`

## Play Smoke Evidence

- `video demo doom play 4 --wad runtime-private --sha256 EXPECTED` rc/status: `0` / `ok`
- `video.demo.doom.play=doomgeneric-sd-wad-smoke`: `1`
- `video.demo.doom.play.frames=4`: `1`
- `video.demo.doom.play.verify.sha256_checked=1`: `1`
- `video.demo.doom.play.verify.sha256_match=1`: `1`
- `video.demo.doom.play.verify.magic_ok=1`: `1`
- `video.demo.doom.play.verify.ok=1`: `1`
- `video.demo.doom.play.rc=0`: `1`
- `video.demo.doom.play.duration_ms=100`: `1`
- `video.demo.doom.play.timed_out=0`: `1`

## Rollback Evidence

- Rollback target: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Rollback flashed through checked helper: `1`
- Rollback remote SHA256 matched local: `1`
- Rollback boot readback SHA256 matched expected: `1`
- Rollback post-flash version rc/status: `0` / `ok`
- Rollback selftest fail=0 after helper verify: `1`
- Final rollback version re-check: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`
- Final rollback selftest fail=0 re-check: `1`

## Notes

- One grouped post-flash command attempt hit serial input corruption and failed before `A90P1 END`; the candidate stayed reachable, and individual normal/slow command retries passed. This is transport noise, not a V3029 health regression.
- `video demo doom play 4` is a bounded WAD-backed helper smoke, not the final visible/playable DOOM UI. It proves the SD WAD path/hash gate and helper engine initialization/run path on-device.

## Safety

- Only the boot partition was flashed, through `native_init_flash.py`.
- The exact V3029 and V2321 SHA256 values were checked before flash and confirmed by boot readback.
- Rollback target remained `v2321`; deeper fallbacks `v2237` and `v48` plus TWRP were preflighted.
- WAD/IWAD bytes stayed on the SD runtime path only; no WAD data was copied into public paths, ramdisk, or boot image.
- No Wi-Fi connect/DHCP/ping, forbidden partition, evdev injection, uinput, sysfs write, Venus, GPU, raw DSI, panel init, backlight, PMIC, PWM, regulator, GPIO, or GDSC path was used.
- Raw command transcripts and bridge logs remain private/untracked; this report includes metadata only and omits raw serial, MAC/BSSID/IP, and SD UUID values.

## Next Unit

- Run ID: `V3031`
- Type: host-only WAD-backed visible DOOM frame/menu integration.
- Scope: decide and implement the bounded source path that carries doomgeneric frames from the WAD-backed helper/engine into the native KMS/menu presentation flow, without embedding WAD bytes or widening the flash surface. Live validation remains gated behind a later source-build report and rollback checks.
