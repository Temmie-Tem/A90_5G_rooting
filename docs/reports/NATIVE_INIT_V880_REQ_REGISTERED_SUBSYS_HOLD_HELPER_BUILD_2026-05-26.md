# V880 REQ-registered Subsystem Hold Helper Build Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper build | `tmp/wifi/v880-execns-helper-v138-build/manifest.json` | `v880-helper-v138-build-pass` |

V880 was source/build-only. It did not contact the device, did not deploy the
helper, did not execute live eSoC ioctls, did not open `/dev/subsys_esoc0`, and
did not bring up Wi-Fi.

## Changes

- Updated `stage3/linux_init/helpers/a90_android_execns_probe.c` to helper
  marker `a90_android_execns_probe v138`.
- Repaired stale successful-open `errno` reporting in the existing eSoC control
  and engine-register preflight paths.
- Added mode `wifi-companion-esoc-req-registered-subsys-hold-preflight`.
- Added allow flag
  `--allow-esoc-req-registered-subsys-hold-preflight`.
- Added fail-closed output markers for no-allow execution.
- Added live-capable markers for future `REG_REQ_ENG` fd hold, child
  `/dev/subsys_esoc0` open attempt, timeout, reaping, and reboot-required
  classification.

## Build

```text
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v880-execns-helper-v138-build/a90_android_execns_probe
```

Artifact:

- path: `tmp/wifi/v880-execns-helper-v138-build/a90_android_execns_probe`
- size: `1057232`
- sha256:
  `2ac8c6730768f86a221722a6ff259e3a4617134221498bd1956a63980a22a9b5`
- type: static AArch64 ELF
- dynamic section: absent

String checks passed for:

- `a90_android_execns_probe v138`
- `wifi-companion-esoc-req-registered-subsys-hold-preflight`
- `--allow-esoc-req-registered-subsys-hold-preflight`
- `esoc_req_registered_subsys_hold_preflight.begin=1`
- `esoc_req_registered_subsys_hold_preflight.allowed=0`
- `esoc_req_registered_subsys_hold_preflight.result=reboot-required`

## Interpretation

V879 closed direct userspace `CMD_EXE` because `REG_CMD_ENG` returned `EBUSY`.
The overview also shows that `/dev/subsys_esoc0` must not be retried without
first satisfying the `REQ_ENG` precondition. V880 implements that next
instrumentation path without running it live.

## Guardrails

- Direct userspace `CMD_EXE` and explicit userspace `PWR_ON` remain blocked.
- `WAIT_FOR_REQ` and `NOTIFY` remain blocked.
- Actor starts, service-manager starts, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, and external ping remain blocked.
- Future live use must be a separate bounded gate with explicit cleanup and
  reboot-required handling.

## Next

V881 should deploy helper `v138` only and prove checksum/version/mode parity.
It should still avoid live eSoC ioctls and `/dev/subsys_esoc0` open.
