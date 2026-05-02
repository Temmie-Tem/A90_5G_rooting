# Native Init v95 Netservice / USB Gadget API Report (2026-05-03)

## Summary

- Version: `A90 Linux init 0.8.26 (v95)`
- Goal: move USB configfs/UDC primitives and NCM/tcpctl netservice policy behind compiled `.c/.h` APIs.
- Result: PASS. v95 flashed, booted, selftest passed, USB ACM reset recovered, NCM ping and TCP control smoke passed, opt-in boot auto-start worked, and netservice rollback restored ACM-only state.

## Changes

- Added `a90_usb_gadget.c/h` for ACM setup, UDC bind/unbind/reset, and read-only USB gadget status snapshots.
- Added `a90_netservice.c/h` for opt-in flag state, NCM start/stop, `a90_tcpctl` process lifecycle, and netservice status snapshots.
- Updated boot path, `status`, network menu, selftest, `usbacmreset`, and `netservice` command wrappers to call the new APIs.
- Preserved raw-control behavior for USB re-enumerating commands; `netservice start/stop` may lose framed END while still completing and recovering by status check.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v95` | `13390d59c7a1d4dd460d2e88b6424ddc1759bb79d80aadbd2fd48382faa34390` |
| `stage3/ramdisk_v95.cpio` | `3d6080c15201766f725cc3adf4c434278f528ea4ab5776e6d759f56ea95c81e5` |
| `stage3/boot_linux_v95.img` | `cab9b2466e3162ec429e2634728e793990fe8cafc217e3be6b2c9a2f684b5824` |

## Validation

- Static ARM64 build with `-Wall -Wextra` — PASS
- `readelf -d stage3/linux_init/init_v95` showed no dynamic section — PASS
- Boot image marker strings `A90 Linux init 0.8.26 (v95)`, `A90v95`, `0.8.26 v95 NETSERVICE USB API` — PASS
- Device flash: `native_init_flash.py stage3/boot_linux_v95.img --from-native --expect-version "A90 Linux init 0.8.26 (v95)" --verify-protocol auto` — PASS
- Boot partition prefix SHA256 matched `stage3/boot_linux_v95.img` — PASS
- Post-boot `cmdv1 version/status` — PASS
- Boot selftest: `pass=8 warn=0 fail=0 duration=39ms` — PASS
- Base regression: `bootstatus`, `selftest verbose`, `storage`, `mountsd status`, `statushud`, `autohud 2`, `screenmenu`, `hide` — PASS
- USB regression: `usbacmreset` after `hide`, bridge reconnect, `version` — PASS
- NCM/TCP regression: host ping `192.168.7.2` 3/3, `tcpctl_host.py ping/status/run` — PASS
- Opt-in boot regression: `netservice enable` → reboot → `enabled=yes`, `ncm0=present`, `tcpctl=running` — PASS
- Rollback: `netservice disable`, `ncm0=absent`, `tcpctl=stopped`, bridge `version` — PASS

## Notes

- Host NCM interface during validation was `enxbe1310bdf7f6`; the user set `192.168.7.1/24` manually because sudo authentication is interactive.
- `netservice start/stop` can disconnect/rebind USB and may not return an `A90P1 END` marker; status polling is the authoritative post-operation check.
