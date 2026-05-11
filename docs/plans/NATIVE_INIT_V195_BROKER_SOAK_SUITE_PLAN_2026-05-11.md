# v195 Plan: Broker-backed Soak Suite

## Summary

v195 adds a host-side broker soak suite. It composes the broker concurrent smoke,
broker-backed mixed-soak gate, and broker recovery tests into one private
evidence bundle. It does not change the native-init boot image.

## Scope

- Add `scripts/revalidation/a90_broker_soak_suite.py`.
- Run three broker gates as one suite:
  - fake concurrent smoke with blocked command audit;
  - broker-backed mixed-soak gate;
  - broker recovery/failure tests.
- Support `--dry-run` for safe planning/CI mode.
- Support longer real-device runs via `--duration-sec` and optional
  `--include-live-recovery`.

## Non-Goals

- Do not configure NCM or start tcpctl automatically in this suite; v194 owns
  listener lifecycle automation.
- Do not alter native-init PID1, Wi-Fi, USB gadget policy, or bridge code.
- Do not replace the existing individual validators.

## Validation

```bash
python3 -m py_compile scripts/revalidation/a90_broker_soak_suite.py
python3 scripts/revalidation/a90_broker_soak_suite.py \
  --dry-run \
  --duration-sec 30 \
  --observer-interval 10 \
  --run-dir tmp/a90-v195-dry-suite
```

Optional live validation:

```bash
python3 scripts/revalidation/a90_broker_soak_suite.py \
  --duration-sec 3600 \
  --observer-interval 15 \
  --include-live-recovery \
  --run-dir tmp/a90-v195-live-suite
```

## Acceptance

- Dry-run suite produces one summary/report bundle with all three steps PASS.
- Live suite, when run, must keep broker audit integrity PASS and zero mixed-soak
  failures.
