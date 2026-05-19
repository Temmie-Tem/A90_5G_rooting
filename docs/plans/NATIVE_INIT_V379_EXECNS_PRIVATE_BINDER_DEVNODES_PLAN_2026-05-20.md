# V379 Execns Private Binder Devnodes Plan

## Summary

- V379 keeps the device build at `A90 Linux init 0.9.61 (v319)` and updates only the host-built Android exec namespace helper.
- Target helper version: `a90_android_execns_probe v13`.
- Goal: address the V378 `service-manager-runtime-gap-binder-devnode-required` classification by materializing private Binder device nodes inside the helper namespace before `service-manager-start-only` execution.
- Scope is helper source/build only. V379 does not deploy the helper, start Android service managers, start Wi-Fi HAL, or bring up Wi-Fi.

## Design

- Add private namespace paths for:
  - `/dev/binder` -> `c 10 81`
  - `/dev/hwbinder` -> `c 10 80`
  - `/dev/vndbinder` -> `c 10 79`
- Provision these nodes only when both conditions are true:
  - `--mode service-manager-start-only`
  - `--allow-service-manager-start-only`
- Keep node creation inside the helper temporary root so cleanup removes the nodes with the namespace tree.
- Use `0666` mode because the helper drops the child to Android `system` uid/gid before exec; `0600 root:root` would convert the previous `ENOENT` blocker into an `EACCES` blocker.
- Expose `context.dev_binder`, `context.dev_hwbinder`, and `context.dev_vndbinder` in preexec context output for evidence.

## Guardrails

- No global native `/dev/binder` creation.
- No persistent device mutation in V379.
- No service-manager live start in V379.
- No Wi-Fi HAL start, scan, connect, DHCP, routing, credential, rfkill, or firmware mutation.

## Validation

- Build static ARM64 helper:
  - `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -o tmp/wifi/v379-a90_android_execns_probe-v13/a90_android_execns_probe stage3/linux_init/helpers/a90_android_execns_probe.c`
- Check marker and mode strings:
  - `a90_android_execns_probe v13`
  - `service-manager-start-only`
  - `--allow-service-manager-start-only`
  - `dev_binder`, `dev_hwbinder`, `dev_vndbinder`
- Check artifact is static with no dynamic section.
- Run `git diff --check` and host Python py_compile for affected harness scripts.

## Next Step

- V380 should deploy `/cache/bin/a90_android_execns_probe` v13 and run preflight only.
- Bounded service-manager start-only with v13 remains a separate live step after deployment verification.
