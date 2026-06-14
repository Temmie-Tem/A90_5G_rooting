# Native Init v76 AT Fragment Filter Report (2026-04-27)

## Summary

- Version: `A90 Linux init 0.8.7 (v76)`
- Source: `stage3/linux_init/init_v76.c`
- Boot image: `stage3/boot_linux_v76.img`
- Goal: ignore short host serial probe fragments before they become shell `unknown command` noise.

## Change

- Added `is_unsolicited_at_fragment_noise()`.
- Ignores short `A`/`T` only fragments up to 8 bytes, including:
  - `A`
  - `T`
  - `AT`
  - `ATA`
  - `ATAT`
- Keeps the existing full `AT...` probe filter for lines such as `AT+GCAP`.
- Keeps normal lowercase shell commands, `cmdv1`, and `cmdv1x` behavior unchanged.
- Added on-device changelog entry: `0.8.7 v76 AT FRAGMENT FILTER`.

## Artifacts

- `stage3/linux_init/init_v76`
  - SHA256 `053986f290d7e87a080515253ad7e1dfbabc73baa462a1e978fe58acb4b1f467`
- `stage3/ramdisk_v76.cpio`
  - SHA256 `06e1d300cd20deea918a86a3eb7413756ddc09ee0ed198f031bb3ceda1d3a0c5`
- `stage3/boot_linux_v76.img`
  - SHA256 `016b2d0c38f3acd1e0868fd5fa86805e52ef88c2e22fdb240dc071b1b39f4b68`

## Validation

- Static ARM64 build — PASS
- v76 ramdisk and boot image generation — PASS
- boot image marker strings:
  - `A90 Linux init 0.8.7 (v76)`
  - `A90v76`
  - `0.8.7 v76 AT FRAGMENT FILTER`
- native init v75 → TWRP recovery → boot partition flash → v76 boot — PASS
- `native_init_flash.py ... --verify-protocol auto` verified `cmdv1 version/status` with `rc=0`, `status=ok`.
- Raw bridge injection:
  - input: `A`, `T`, `AT`, `ATA`, `ATAT`, `AT+GCAP`, `version`
  - result: no `unknown command`
  - result: `version` returned `A90 Linux init 0.8.7 (v76)`
- `/cache/native-init.log` recorded:
  - `serial: ignored AT fragment line=A`
  - `serial: ignored AT fragment line=T`
  - `serial: ignored AT fragment line=AT`
  - `serial: ignored AT fragment line=ATA`
  - `serial: ignored AT fragment line=ATAT`
  - `serial: ignored AT probe line=AT+GCAP`
- `a90ctl.py --json echo "hello v76 noise filter"` used `cmdv1x` and returned `rc=0`, `status=ok`.

## Current Baseline

`0.8.7 (v76)` is now the latest verified native init baseline.

The v48 fallback image remains the known-good rescue path, and v49 remains an isolated failed experiment.
