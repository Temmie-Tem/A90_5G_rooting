# v195 Broker-backed Soak Suite

## Summary

v195 adds a host-side broker soak suite that composes existing v189/v190/v192
validators into a single evidence bundle. The latest verified native-init device
build remains `A90 Linux init 0.9.59 (v159)`.

## Changes

- Added `scripts/revalidation/a90_broker_soak_suite.py`.
- Suite steps:
  - fake concurrent smoke;
  - broker-backed mixed-soak gate;
  - broker recovery/failure tests.
- Supports `--dry-run` for device-safe execution and longer real-device runs via
  `--duration-sec`.

## Validation

```bash
python3 -m py_compile scripts/revalidation/a90_broker_soak_suite.py
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_soak_suite.py \
  --dry-run \
  --duration-sec 30 \
  --observer-interval 10 \
  --run-dir tmp/a90-v195-dry-suite
```

Result: PASS.

Evidence:

- `tmp/a90-v195-dry-suite/broker-soak-suite-summary.json`
- `tmp/a90-v195-dry-suite/broker-soak-suite-report.md`
- `tmp/a90-v195-dry-suite/fake-concurrent-smoke/`
- `tmp/a90-v195-dry-suite/mixed-soak/`
- `tmp/a90-v195-dry-suite/recovery-tests/`

## Acceptance

- The suite gives one command for broker smoke/mixed/recovery validation.
- Dry-run mode is safe for local iteration and still verifies wiring across the
  component validators.

## Next

v196 should add a fresh security scan follow-up workflow so broker/security
changes can be triaged consistently after local hardening.
