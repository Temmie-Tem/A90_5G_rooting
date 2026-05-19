# Native Init v292 Binder Open-Only Smoke

- date: `2026-05-19`
- scope: temporary Binder devnode create + open/close-only smoke
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- plan: `docs/plans/NATIVE_INIT_V292_BINDER_OPEN_SMOKE_PLAN_2026-05-19.md`
- tool: `scripts/revalidation/wifi_binder_open_smoke.py`
- evidence:
  - plan mode: `tmp/wifi/v292-binder-open-smoke-plan/`
  - live mode: `tmp/wifi/v292-binder-open-smoke-live-20260519-141358/`

## Result

- decision: `binder-open-only-smoke-pass`
- pass: `True`
- reason: temporary Binder devnodes were created, opened with `dd count=0`,
  and removed.

## Validation

Static validation passed:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_binder_open_smoke.py \
  scripts/revalidation/wifi_binder_devnode_smoke.py \
  scripts/revalidation/a90ctl.py
git diff --check
```

Plan mode passed:

```bash
python3 scripts/revalidation/wifi_binder_open_smoke.py \
  --out-dir tmp/wifi/v292-binder-open-smoke-plan \
  plan
```

Live apply passed:

```bash
python3 scripts/revalidation/wifi_binder_open_smoke.py \
  --out-dir tmp/wifi/v292-binder-open-smoke-live-20260519-141358 \
  run --apply
```

## Live Steps

| Step | Result |
| --- | --- |
| pre `stat /dev/binder` | absent |
| pre `stat /dev/hwbinder` | absent |
| pre `stat /dev/vndbinder` | absent |
| `mknodc /dev/binder 10 81` | PASS |
| `mknodc /dev/hwbinder 10 80` | PASS |
| `mknodc /dev/vndbinder 10 79` | PASS |
| created `stat` for all three nodes | PASS |
| `toybox dd if=/dev/binder of=/dev/null bs=1 count=0` | PASS |
| `toybox dd if=/dev/hwbinder of=/dev/null bs=1 count=0` | PASS |
| `toybox dd if=/dev/vndbinder of=/dev/null bs=1 count=0` | PASS |
| cleanup `run /cache/bin/toybox rm -f ...` | PASS |
| post `stat` for all three nodes | absent |

`dd` reported `0+0 records in`, `0+0 records out`, and `0 bytes copied` for
all three Binder domains.

## Interpretation

The kernel accepts open/close of all three Binder device nodes when the native
init environment creates the matching misc character devices. This removes the
lowest-level Binder device blocker found in v288/v289.

This is still not a Binder protocol or Android service-manager pass. v292 did
not issue Binder ioctls, register services, start service managers, start Wi-Fi
HALs, run `wificond`, or touch Wi-Fi link state.

## Guardrails Kept

- no Binder ioctl
- no binderfs mount
- no service-manager execution
- no Wi-Fi daemon execution
- no QMI/QRTR packet
- no Wi-Fi scan/connect/link-up/credential/DHCP/routing
- no rfkill/ICNSS writes
- no Android partition write
- cleanup completed in the same tool run

## Next

- v293 should model service-manager prerequisites before any service-manager
  execution.
- The next blocker set is no longer Binder device open. It is:
  - service-manager process model
  - Android property runtime
  - SELinux/domain expectations
  - linker namespace and mounted Android runtime completeness
- Do not jump directly from v292 to HAL/`wificond` execution.
