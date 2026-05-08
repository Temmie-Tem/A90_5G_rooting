# Native Init v176 Long-Run Supervisor Plan (2026-05-09)

## Summary

- label: `v176 Long-Run Supervisor`
- baseline: `A90 Linux init 0.9.59 (v159)`
- objective: make the observer usable for bounded and unlimited long-run monitoring.

v176 is host tooling only. It does not change or flash the boot image.

## Scope

- Extend observer duration to accept `unlimited`.
- Add `--max-cycles` for bounded smoke validation of unlimited mode.
- Add heartbeat evidence after each observer cycle.
- Add stop reason and interrupted state to observer summary.
- Preserve partial evidence on KeyboardInterrupt.

## Guardrails

- Observer commands remain read-only.
- No module side effects are introduced.
- Unlimited mode must still write valid bundle files when stopped or cycle-limited.

## Acceptance

- Static validation passes:

```bash
python3 -m py_compile scripts/revalidation/native_test_supervisor.py scripts/revalidation/a90harness/*.py scripts/revalidation/a90harness/modules/*.py
git diff --check
```

- Bounded unlimited-mode smoke:

```bash
python3 scripts/revalidation/native_test_supervisor.py observe \
  --duration-sec unlimited \
  --max-cycles 2 \
  --interval 2 \
  --run-dir tmp/soak/harness/v176-long-run-<stamp>
```

Expected output directory contains:

- `manifest.json`
- `summary.md`
- `README.md`
- `bundle-index.json`
- `observer.jsonl`
- `observer-summary.json`
- `heartbeat.json`

## Next

- v177 Safety Gate / Dry-Run Policy.
