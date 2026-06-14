# Native Init v73 cmdv1 Protocol Report (2026-04-27)

## Summary

- Version: `A90 Linux init 0.8.4 (v73)`
- Source: `stage3/linux_init/init_v73.c`
- Goal: make serial bridge automation less brittle by adding a framed one-shot shell protocol.
- Status: built, flashed, and verified through the serial bridge.

## What Changed

- Added `cmdv1 <command> [args...]` shell wrapper.
- Added `A90P1 BEGIN` and `A90P1 END` protocol records around one command.
- Included `seq`, `cmd`, `argc`, `flags`, `rc`, `errno`, `duration_ms`, and `status` fields in the END record.
- Framed normal success, unknown command, and menu-busy outcomes for automation.
- Added `scripts/revalidation/a90ctl.py` host wrapper with text/JSON output.
- Added `--hide-on-busy` retry path in `a90ctl.py` for visible auto-menu situations.
- Added on-device changelog entry for `0.8.4 v73`.

## Build Artifacts

- `stage3/linux_init/init_v73`
  - SHA256 `7ce8063b6e343dd49ec8e1f2a0856936794bee761242ae6bd333ae1a96b51083`
- `stage3/ramdisk_v73.cpio`
  - SHA256 `dfb14b9a9ab5c48cd95175a0301c4ba8f737638639f2d77dc87af5613524c5df`
- `stage3/boot_linux_v73.img`
  - SHA256 `241e44ef70eb3dc187c8dd44c62c26943c42bd952c7d122374295463d67f159a`

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v73.img \
  --from-native \
  --expect-version "A90 Linux init 0.8.4 (v73)" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

Result:

- local marker check: PASS
- local image SHA256: `241e44ef70eb3dc187c8dd44c62c26943c42bd952c7d122374295463d67f159a`
- TWRP ADB push: PASS
- remote `/tmp/native_init_boot.img` SHA256: PASS
- boot partition prefix SHA256: PASS
- reboot to native init: PASS
- bridge `version`: `A90 Linux init 0.8.4 (v73)` PASS

## Runtime Validation

Raw bridge check:

```bash
printf 'cmdv1 status\ncmdv1 nope\ncmdv1 waitkey 1\n' | nc -w 12 127.0.0.1 54321
```

Observed:

- `cmdv1 status` → `A90P1 END ... rc=0 ... status=ok`
- `cmdv1 nope` → `A90P1 END ... rc=-2 ... status=unknown`
- `cmdv1 waitkey 1` while auto menu visible → `A90P1 END ... rc=-16 ... status=busy`

Host wrapper checks:

```bash
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py --json --allow-error nope
python3 scripts/revalidation/a90ctl.py --hide-on-busy status
```

Observed:

- `a90ctl.py status` parsed END marker and exited `0`.
- `a90ctl.py --json --allow-error nope` emitted parsed JSON with `rc=-2` and `status=unknown`.
- `a90ctl.py --hide-on-busy status` completed successfully after the retry path was available.

## Notes

- `cmdv1` is intended for one-shot automation and scripts, not for replacing the interactive serial shell.
- Commands with whitespace-containing arguments are intentionally rejected by `a90ctl.py` until native argument quoting is implemented.
- Destructive commands such as `recovery`, `reboot`, and `poweroff` can terminate before an END marker is observed, so wrappers should continue to treat them as special operations.
