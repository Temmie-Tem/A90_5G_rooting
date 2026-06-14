# Native Init v115 Remote Shell Hardening

Date: `2026-05-04`
Build: `A90 Linux init 0.9.15 (v115)`
Marker: `0.9.15 v115 RSHELL HARDENING`
Baseline: `A90 Linux init 0.9.14 (v114)`

## Summary

v115 hardens the optional custom TCP remote shell path over USB NCM.
It keeps the service disabled by default and USB-only, while adding device-side audit output and host-side negative authentication validation.

No Wi-Fi remote shell, internet-facing service, automatic token export, or destructive runtime change was added.

## Source Changes

- Added `stage3/linux_init/init_v115.c` and `stage3/linux_init/v115/*.inc.c` from v114.
- Updated `stage3/linux_init/a90_config.h` to `0.9.15` / `v115`.
- Extended `rshell status` with token file mode and strict-permission reporting.
- Added `rshell audit` for helper, BusyBox, token, flag, log, NCM, and tcpctl state.
- Extended `scripts/revalidation/rshell_host.py` with:
  - `invalid-token`
  - `harden`
- Added v115 ABOUT/changelog/menu entries.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v115` | `4054706e0c8d004b826aef882b46cd065a3b734fb12a3c68d7380d7e60e9435e` |
| `stage3/ramdisk_v115.cpio` | `bdfc75560ea4f76c60527a0973d741366b4372bb1e1460e97539ba435e61857a` |
| `stage3/boot_linux_v115.img` | `549d4838416bad7400cb36951f112e99cf03cb046387784c3eade4ff7bbdf042` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.15 (v115)`
  - `A90v115`
  - `0.9.15 v115 RSHELL HARDENING`
  - `rshell-audit`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, and `rshell_host.py` — PASS.
- v115 include tree stale marker check for v114 current markers — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v115.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.15 (v115)" \
  --verify-protocol auto
```

Result:

- Native bridge v114 to TWRP recovery path succeeded.
- Boot partition prefix SHA matched `stage3/boot_linux_v115.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.15 (v115)` — PASS.
- Boot selftest reported `pass=11 warn=0 fail=0` — PASS.

Remote shell hardening checks:

| Command | Result |
|---|---|
| `rshell audit` | PASS, helper and BusyBox present, token mode `0600`, strict `yes`, warnings `0` |
| `rshell status` | PASS, token mode/strict visible without printing token value |
| host NCM ping | PASS, `192.168.7.2` 3/3 replies after host `192.168.7.1/24` setup |
| `rshell_host.py harden` | PASS, invalid token rejected with `ERR auth`, smoke commands returned `A90RSH1 END rc=0`, service stopped |
| rollback to ACM-only | PASS, ACM bridge responded after USB re-enumeration |
| final `netservice status` | PASS, `ncm0=absent tcpctl=stopped` |
| final `rshell status` | PASS, `running=no`, `ncm=absent`, `tcpctl=stopped` |

## Soak Regression

Command:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 2 \
  --expect-version "A90 Linux init 0.9.15 (v115)" \
  --out tmp/soak/v115-rshell-hardening.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- `rshell start` can still interrupt framed command output when it must start NCM first; host tooling treats it as raw-control-like and verifies status after reconnect.
- `a90_usbnet off` only restores USB composition and can leave tcpctl running; `netservice stop` remains the canonical service rollback command.
- v116 should extend diagnostics to include runtime/helper/service/net/rshell evidence from this cycle.
