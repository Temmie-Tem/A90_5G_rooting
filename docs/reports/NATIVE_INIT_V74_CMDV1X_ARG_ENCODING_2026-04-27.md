# Native Init v74 cmdv1x Argument Encoding Report (2026-04-27)

## Summary

- Version: `A90 Linux init 0.8.5 (v74)`
- Source: `stage3/linux_init/init_v74.c`
- Purpose: keep v73 `cmdv1` compatibility while adding a safe encoded argv path for whitespace/special-character arguments.
- Verified status: host/static build complete, device flash/runtime validation PASS.

## Native Changes

- Added `cmdv1x <len:hex-utf8-arg>...`.
- Each argv token is encoded as decimal byte length, colon, and hex UTF-8 bytes.
- Example:
  - host argv: `["echo", "hello world"]`
  - wire line: `cmdv1x 4:6563686f 11:68656c6c6f20776f726c64`
- The old `cmdv1 <command> [args...]` token path remains intact for simple whitespace-free commands.
- Malformed `cmdv1x` input returns framed `A90P1 END ... status=error`.
- On-device ABOUT/CHANGELOG now lists `0.8.5 v74 CMDV1 ARG ENCODING`.

## Host Changes

- `scripts/revalidation/a90ctl.py`
  - Adds `encode_cmdv1_line()`.
  - Uses legacy `cmdv1` for simple argv.
  - Uses `cmdv1x` automatically when an argument is empty, starts with `#`, or contains whitespace.
  - Adds `shell_command_to_argv()` for shared host script parsing.
- `scripts/revalidation/ncm_host_setup.py`
- `scripts/revalidation/netservice_reconnect_soak.py`
- `scripts/revalidation/tcpctl_host.py`
  - Reuse `shell_command_to_argv()` and rely on `a90ctl.py` for wire-format selection.

## Artifacts

- `stage3/linux_init/init_v74`
  - SHA256 `7868795581cf7974b6c2f24af7dfea75399a429d163f6dc7700007b069bdd872`
- `stage3/ramdisk_v74.cpio`
  - SHA256 `90060ba7c2cd57ad3bb1c271ccafc9bc109fa57767d80747e03db02b8b08f92a`
- `stage3/boot_linux_v74.img`
  - SHA256 `e12839be90ad59e13c8289e2eab8d9441f8bfd2b907bd0f7f819ff65f581f1b4`

## Validation

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -o stage3/linux_init/init_v74 stage3/linux_init/init_v74.c` — PASS
- `aarch64-linux-gnu-strip stage3/linux_init/init_v74` — PASS
- `strings stage3/boot_linux_v74.img | rg 'A90 Linux init .*\\(v74\\)|A90v74|cmdv1x'` — PASS
- Host encoder smoke:
  - `["status"]` → `cmdv1 status`
  - `["echo", "hello world"]` → `cmdv1x 4:6563686f 11:68656c6c6f20776f726c64`
- `python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/ncm_host_setup.py scripts/revalidation/netservice_reconnect_soak.py scripts/revalidation/tcpctl_host.py scripts/revalidation/native_init_flash.py` — PASS
- `a90ctl.py` monkeypatch mock verified legacy `cmdv1` and encoded `cmdv1x` selection — PASS
- `git diff --check` and untracked whitespace check — PASS
- `native_init_flash.py stage3/boot_linux_v74.img --from-native --expect-version "A90 Linux init 0.8.5 (v74)" --verify-protocol auto` — PASS
- `a90ctl.py --json status` → `rc=0`, `status=ok` — PASS
- `a90ctl.py --json echo "hello world"` → wire path `cmdv1x`, `rc=0`, `status=ok` — PASS
- direct malformed `cmdv1x 4:6563686f 2:xx` → `rc=-22`, `status=error` — PASS

## Device Runtime Checks

1. Boot/flash:
   - `python3 scripts/revalidation/native_init_flash.py stage3/boot_linux_v74.img --expect-version "A90 Linux init 0.8.5 (v74)" --verify-protocol auto`
2. Legacy path:
   - `python3 scripts/revalidation/a90ctl.py status`
3. Encoded path:
   - `python3 scripts/revalidation/a90ctl.py echo "hello world"`
   - result: wire path `cmdv1x`, framed result `rc=0`, `status=ok`.
4. Follow-up host scripts:
   - `python3 scripts/revalidation/ncm_host_setup.py status`
   - `python3 scripts/revalidation/tcpctl_host.py smoke`

## Notes

- `stage3/boot_linux_v74.img` is a local ignored artifact, matching the existing image policy.
- `0.8.5 (v74)` is now the latest verified native init baseline.
