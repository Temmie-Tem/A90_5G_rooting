# A90 Native Init v121 PID1 Guard

Date: 2026-05-05
Build: `A90 Linux init 0.9.21 (v121)`
Marker: `0.9.21 v121 PID1 GUARD`

## Summary

v121 adds a read-only PID1 guard layer. The guard checks boot/control invariants after ACM setup and exposes the same result through `pid1guard`, `status`, and `bootstatus`. It is intentionally warn-only for boot flow: failures are logged and surfaced, but shell/HUD entry is not blocked.

## Changes

- Added `a90_pid1_guard.c/h`.
- Added `pid1guard [status|run|verbose]`.
- Added boot-time guard execution after `selftest`.
- Added guard summary to `status` and `bootstatus`.
- Added About/changelog entry `0.9.21 v121 PID1 GUARD`.

## Guard Checks

- `pid1`: current process is PID 1.
- `config`: version/build strings are present.
- `log`: native log is ready.
- `timeline`: boot timeline contains entries.
- `selftest`: boot selftest ran and has no failures.
- `storage`: boot storage status is available and not in fallback.
- `runtime`: runtime root is initialized and writable.
- `services`: service registry count matches expected service IDs.
- `usb`: ACM configfs gadget is present and bound.
- `netservice`: helper status can be read without starting/stopping NCM.
- `shell`: command table and command group coverage are available.

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v121` | `6a22eb714e21ec3cc2c5a3cdeae6d67b5c6b74a09d7935346a23cf2410d411f0` |
| `stage3/ramdisk_v121.cpio` | `8ea7de80913c42070e0e6365d2866bb31329fa7c1e7bec8972454c862b4d1cca` |
| `stage3/boot_linux_v121.img` | `34760cd69b4adca766c5bf7f498269be267e626cf72cdc870a12efd40c694e91` |
| `tmp/soak/v121-quick-soak.txt` | `57d37127293fc5befe0ca305f3cd9ccecb3ceb4a4ae829cccf37be35a3211c24` |
| `tmp/v121-guard-validation.txt` | `2586116edfed52526554fdfc670a8b7dc7a32513014140a6c1a8cc60e9ae449b` |
| `tmp/v121-guard-validation-argv-fix.txt` | `2b52a24e20c157b09d6311d9f5321f398b6b8c32e5c2617ee64b68fd403a51a9` |

## Validation

### Static

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` — PASS
- `strings` marker check for `A90 Linux init 0.9.21 (v121)`, `A90v121`, `0.9.21 v121 PID1 GUARD`, `pid1guard` — PASS
- `git diff --check` — PASS
- host Python `py_compile` for flash/control scripts — PASS
- stale `v120` marker check in v121 source tree — PASS

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v121.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.21 (v121)" \
  --verify-protocol auto
```

Result: PASS

Evidence:

- local image marker and SHA256 verified
- TWRP push and remote SHA256 verified
- boot partition prefix SHA256 matched image SHA256
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`

### Runtime Regression

- `pid1guard` — PASS (`pass=11 warn=0 fail=0`)
- `pid1guard verbose` — PASS, all 11 entries PASS
- `status` — PASS, includes `pid1guard: pass=11 warn=0 fail=0`
- `bootstatus` — PASS, includes guard summary
- `selftest verbose` — PASS (`pass=11 warn=0 fail=0`)
- `cmdgroups` — PASS (`total=82 core=16 filesystem=13 storage=8 display=15 input=7 menu=6 process=2 service=4 network=4 android=4 power=3`)
- `storage`, `mountsd status`, `service list` — PASS
- display/menu: `statushud`, `screenmenu`, `hide` — PASS
- `native_soak_validate.py --cycles 3 --sleep 2` — PASS (`cycles=3 commands=14`)

## Next

Proceed to v122 `Wi-Fi inventory refresh`:

- keep the track read-only,
- refresh WLAN/rfkill/firmware/sysfs evidence against the current v121 runtime,
- do not start Wi-Fi, load modules, alter partitions, or rebind USB as part of the inventory refresh.
