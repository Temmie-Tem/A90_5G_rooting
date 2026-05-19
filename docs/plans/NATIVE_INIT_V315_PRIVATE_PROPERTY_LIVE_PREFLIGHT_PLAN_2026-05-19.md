# v315 Plan: Private Property Live Preflight

- date: `2026-05-19`
- scope: read-only live preflight before private property namespace materialization
- boot image change: none
- restored device build: `A90 Linux init 0.9.60 (v261)`
- status: planned

## Summary

v314 produced a fail-closed executor scaffold but did not touch the device. v315
checks the actual native-init device state with read-only shell commands before
any future materialization implementation is allowed.

The goal is to prove that the current device is in the expected safe baseline:
native v261 is running, SD workspace is mounted read-write, selftest has no
failures, netservice is disabled, and logs are on the SD workspace.

## Key Changes

- Add `scripts/revalidation/wifi_private_property_live_preflight.py`.
- Consume `tmp/wifi/v314-private-property-materialization-executor/manifest.json`.
- Capture read-only commands only:
  - `version`
  - `status`
  - `selftest`
  - `storage`
  - `mountsd status`
  - `logpath`
- Record `device_mutations: false`.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_private_property_live_preflight.py
python3 scripts/revalidation/wifi_private_property_live_preflight.py \
  --out-dir tmp/wifi/v315-private-property-live-preflight \
  run
git diff --check
```

Expected decision:

```text
private-property-live-preflight-ready
```

## Acceptance

- Native version is `A90 Linux init 0.9.60 (v261)`.
- `status` confirms SD writable runtime, disabled netservice, and selftest
  summary.
- `selftest` reports `fail=0`.
- `storage` confirms `backend=sd` and `rw=yes`.
- `mountsd status` confirms expected mounted SD workspace.
- `logpath` points to `/mnt/sdext/a90/logs/native-init.log`.
- No `run`, write, mount, push, reboot, or Wi-Fi bring-up action is executed.

## Next Boundary

v316 may implement a minimal approved private namespace copy/materialization
proof, but it still must not start service-manager, HAL, or any Wi-Fi daemon.
