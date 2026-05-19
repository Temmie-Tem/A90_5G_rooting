# V379 Execns Private Binder Devnodes Report

## Result

- decision: `execns-helper-v13-private-binder-devnodes-local-pass`
- pass: `true`
- device build: `A90 Linux init 0.9.61 (v319)`
- helper version: `a90_android_execns_probe v13`
- scope: local helper source/build only
- device deploy: `false`
- daemon start: `false`
- Wi-Fi bring-up: `false`

## Artifact

| item | value |
| --- | --- |
| local artifact | `tmp/wifi/v379-a90_android_execns_probe-v13/a90_android_execns_probe` |
| sha256 | `9866c8f1e7c346906f4a400ee431ea35ed3880c157e5ee4e8b1757377dcfffa8` |
| file | `ELF 64-bit LSB executable, ARM aarch64, statically linked` |
| dynamic section | none |

## Changes

- Bumped `EXECNS_VERSION` to `a90_android_execns_probe v13`.
- Added private temp-root paths for `/dev/binder`, `/dev/hwbinder`, and `/dev/vndbinder`.
- Added service-manager-only Binder node materialization:
  - `/dev/binder` as `c 10 81`
  - `/dev/hwbinder` as `c 10 80`
  - `/dev/vndbinder` as `c 10 79`
- Gated node creation on `service-manager-start-only` plus `--allow-service-manager-start-only`.
- Printed Binder node context paths in preexec evidence.
- Used `0666` mode so Android `system` uid service-manager children can open the private nodes after identity drop.

## Validation

- static ARM64 build: PASS
- required strings: PASS
- no dynamic section: PASS
- `git diff --check`: PASS
- host Python py_compile: PASS

## Interpretation

V379 fixes the first V376/V378 runtime blocker at the helper namespace boundary: the service-manager child should now see Binder device nodes after `chroot()`. This does not prove service-manager can remain alive; the next possible blockers are Binder driver policy, property runtime, SELinux/runtime files, or additional Android framework expectations.

## Next

- V380: deploy v13 to `/cache/bin/a90_android_execns_probe` and verify remote SHA/usage/preflight.
- After V380: rerun bounded service-manager start-only with exact live approval, still without Wi-Fi HAL or Wi-Fi bring-up.
