# A90 Native Init v125 Security Batch 4

Date: 2026-05-06
Build: `A90 Linux init 0.9.25 (v125)`
Marker: `0.9.25 v125 SECURITY BATCH4`

## Summary

v125 implements Security Batch 4 log, diagnostics, and on-screen disclosure
hardening. Runtime log/state directories are private, logs and diagnostics are
created with owner-only modes, host diagnostics are written into a private host
directory, the fallback log moved from world-accessible `/tmp/native-init.log`
to `/tmp/a90-native/native-init.log`, and passive HUD log tail rendering is now
opt-in through `hudlog on`.

## Changes

- Changed native fallback log path to `/tmp/a90-native/native-init.log` and ensured the private fallback directory is `0700`.
- Kept native log files and diagnostic bundles at `0600` with no-follow opens.
- Changed runtime `logs`, `tmp`, `state`, `run`, and `state/services` directories to `0700`.
- Changed `diag full` and `diag bundle` to redact log-tail file paths and omit log tail contents by default.
- Changed `diag_collect.py` host output to create parent directory `0700` and output file `0600`.
- Added `hudlog [status|on|off]` to make passive background HUD log tail opt-in; default is off.

## Finding Coverage

| finding | v125 result |
|---|---|
| F009 | Mitigated: device bundles and host diagnostics are owner-only; log tails are redacted from default diagnostic captures. |
| F024 | Mitigated: passive HUD log tail is disabled by default and requires explicit `hudlog on`. |
| F025 | Mitigated: fallback log is no longer `/tmp/native-init.log`; it is under a private `/tmp/a90-native` directory and opened `0600`. |

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v125` | `24f0056707d89182b7ad6aa49f13c599247bbe13885f2277720b2d9492ced128` |
| `stage3/ramdisk_v125.cpio` | `653f1b66f201e5f72534aa3ade1d475a89b696486436b4c6e820a37c6ef25ad9` |
| `stage3/boot_linux_v125.img` | `69e60ee06bbb0c7591b01495f17743fab88873677c13427ee731a58dbd06031d` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.25 (v125)`, `A90v125`, `0.9.25 v125 SECURITY BATCH4`, `hudlog`, and `/tmp/a90-native` — PASS.
- host Python `py_compile` for control/diagnostic scripts — PASS.
- shell syntax checks for BusyBox build and baseline capture scripts — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v125.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.25 (v125)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified
- TWRP push and remote SHA256 verified
- boot partition prefix SHA256 matched image SHA256
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`

### Runtime Checks

- `hudlog status` — PASS, default `off`.
- `hudlog on/status/off/status` — PASS, opt-in state toggles and returns to off.
- `diag full` — PASS, log tail path/content lines report `path=<redacted>` and `tail=redacted`.
- `diag bundle` — PASS, wrote `/mnt/sdext/a90/logs/a90-diag-51708.txt`.
- Device mode check — PASS: runtime `logs`, `tmp`, `state`, `run` directories are `700`; native log and diag bundle are `600`.
- Host `diag_collect.py --skip-device-evidence` — PASS: host output directory is `700`, output file is `600`.
- `statushud`, `autohud 2`, `screenmenu`, `hide` — PASS.

## Notes

- `diag full` still reports selected operational state to the authenticated serial console, but default stored diagnostics no longer expose native log tails through world-readable host/device files.
- Passive background HUD log tail is off by default. Use `hudlog on` only in trusted lab conditions when on-screen log visibility is desired.
