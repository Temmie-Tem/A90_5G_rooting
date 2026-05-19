# Native Init v292 Binder Open-Only Smoke Plan

- date: `2026-05-19`
- scope: temporary Binder devnode create + open/close-only smoke
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- target artifact: `scripts/revalidation/wifi_binder_open_smoke.py`
- prerequisite: v291 decision `binder-devnode-create-cleanup-pass`

## Summary

v291 proved that native init can temporarily create and remove Binder devnodes.
v292 performs the next smallest runtime check: create the three Binder nodes,
open and close each device without reading data or issuing Binder ioctls, then
remove the nodes.

The open-only check uses the already-present `/cache/bin/toybox`:

```text
toybox dd if=/dev/<binder-node> of=/dev/null bs=1 count=0
```

`count=0` is intentionally used so the command opens the input device and then
exits without copying data. This avoids adding a new helper binary and keeps the
test narrower than a Binder protocol smoke.

## Scope

Allowed:

- temporary `mknodc` for `/dev/binder`, `/dev/hwbinder`, `/dev/vndbinder`
- `stat` verification
- `toybox dd ... count=0` open/close-only check
- cleanup with `toybox rm -f`

Blocked:

- Binder ioctl
- binderfs mount
- service-manager execution
- HAL, `wificond`, supplicant, hostapd execution
- Wi-Fi scan/connect/link-up/credential/DHCP/routing
- rfkill/ICNSS writes
- Android partition writes

## Procedure

1. Load v291 manifest and require decision `binder-devnode-create-cleanup-pass`.
2. Create Binder devnodes using v290 major/minor values.
3. Verify created nodes with `stat`.
4. For each node, run:
   - `run /cache/bin/toybox dd if=/dev/binder of=/dev/null bs=1 count=0`
   - `run /cache/bin/toybox dd if=/dev/hwbinder of=/dev/null bs=1 count=0`
   - `run /cache/bin/toybox dd if=/dev/vndbinder of=/dev/null bs=1 count=0`
5. Cleanup all temporary nodes.
6. Verify all nodes are absent after cleanup.

## Expected Decisions

PASS decisions:

- `binder-open-smoke-plan-ready`
- `binder-open-only-smoke-pass`

Failure decisions:

- `binder-open-smoke-input-missing`
- `binder-open-smoke-create-failed`
- `binder-open-smoke-open-failed`
- `binder-open-smoke-cleanup-failed`

## Validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_binder_open_smoke.py \
  scripts/revalidation/wifi_binder_devnode_smoke.py \
  scripts/revalidation/a90ctl.py
git diff --check
```

Live dry-run:

```bash
python3 scripts/revalidation/wifi_binder_open_smoke.py \
  --out-dir tmp/wifi/v292-binder-open-smoke-plan \
  plan
```

Live apply:

```bash
python3 scripts/revalidation/wifi_binder_open_smoke.py \
  --out-dir tmp/wifi/v292-binder-open-smoke-live-$(date +%Y%m%d-%H%M%S) \
  run --apply
```

## Acceptance

- All three temporary Binder nodes are created and visible.
- All three `dd count=0` open-only checks return success.
- All temporary nodes are removed after the test.
- No Binder ioctl, service-manager process, HAL, or Wi-Fi daemon is executed.
- Next work can evaluate service-manager prerequisites, but must not jump
  directly to HAL/`wificond` execution.
