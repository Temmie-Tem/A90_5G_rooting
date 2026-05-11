# A90 v188 Broker Audit Reporting Report

Date: `2026-05-11`
Baseline device build: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v188` host broker audit/reporting
Device flash: none
Base commit: `8ce8d39`

## Summary

v188 turns the `A90B1` broker audit JSONL into a validated evidence artifact.
The broker now redacts sensitive command arguments in audit records and provides
`a90_broker.py report` to generate integrity summaries, redacted record exports,
and Markdown reports with private/no-follow output handling.

## Changes

- `scripts/revalidation/a90_broker.py`
  - redacts sensitive argv values before audit write
  - records command name and argc in `accept`/`dispatch` audit events
  - adds `report` subcommand
  - validates malformed JSONL, missing dispatch, missing result, duplicate result,
    and orphan result conditions
  - writes `broker-audit-summary.json`, `broker-audit-records-redacted.json`, and
    `broker-audit-report.md`
- `scripts/revalidation/README.md`
  - documents `a90_broker.py report`
- task docs
  - records v188 as broker audit/reporting work

## Validation

Static and selftest:

```bash
python3 -m py_compile scripts/revalidation/a90_broker.py
python3 scripts/revalidation/a90_broker.py selftest
git diff --check
```

Result: PASS.

Fake backend report:

```bash
python3 scripts/revalidation/a90_broker.py serve --backend fake --runtime-dir <run>/broker
python3 scripts/revalidation/a90_broker.py call --runtime-dir <run>/broker --json version
python3 scripts/revalidation/a90_broker.py call --runtime-dir <run>/broker --json status
python3 scripts/revalidation/a90_broker.py call --runtime-dir <run>/broker --json --allow-error reboot
python3 scripts/revalidation/a90_broker.py report --runtime-dir <run>/broker --out-dir <run>/report --json
```

Result:

- audit integrity PASS
- results `3`
- non-ok results `1` for blocked `reboot`

Live ACM broker report:

```bash
python3 scripts/revalidation/a90_broker.py serve \
  --backend acm-cmdv1 \
  --runtime-dir tmp/a90-v188-broker-20260511-202018/broker

python3 scripts/revalidation/a90_broker.py call --runtime-dir ... --json version
python3 scripts/revalidation/a90_broker.py call --runtime-dir ... --json status
python3 scripts/revalidation/a90_broker.py call --runtime-dir ... --json selftest verbose
python3 scripts/revalidation/a90_broker.py call --runtime-dir ... --json --allow-error reboot
python3 scripts/revalidation/a90_broker.py report --runtime-dir ... --out-dir tmp/a90-v188-broker-20260511-202018/broker-report --json
```

Result:

- audit integrity PASS
- accepted `4`
- dispatched `4`
- results `4`
- non-ok results `1` for blocked `reboot`

Broker-backed supervisor smoke plus report:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  --device-backend broker \
  --broker-runtime-dir tmp/a90-v188-broker-20260511-202018/broker \
  smoke \
  --run-dir tmp/a90-v188-broker-20260511-202018/supervisor-smoke

python3 scripts/revalidation/a90_broker.py report \
  --runtime-dir tmp/a90-v188-broker-20260511-202018/broker \
  --out-dir tmp/a90-v188-broker-20260511-202018/broker-report-after-smoke \
  --json
```

Result:

- supervisor smoke PASS
- manifest `device_client.backend=broker`
- audit integrity PASS
- accepted `6`
- dispatched `6`
- results `6`
- non-ok results `1`

## Evidence

- `tmp/a90-v188-broker-20260511-202018/`

## Remaining Work

- v189 should decide between:
  - NCM/tcpctl broker backend integration
  - broker concurrent smoke script and audit bundle retention policy
- Keep direct ACM bridge as rescue/default until broker mixed-soak gate passes.

## Conclusion

Recommendation: PASS.

Broker audit output is now structured enough to use as evidence for later
broker mixed-soak and network exposure decisions.
