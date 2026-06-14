# Native Init v176 Long-Run Supervisor Report (2026-05-09)

## Summary

- label: `v176 Long-Run Supervisor`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- scope: host-side observer long-run support only; no boot image change
- result: `PASS`

v176 extends the supervisor observer for long-running operation:

- `--duration-sec unlimited`
- `--max-cycles` bounded validation gate
- `heartbeat.json` after each observer cycle
- observer summary `stop_reason`
- observer summary `interrupted`

## Implemented

- `scripts/revalidation/a90harness/observer.py`
  - `run_observer(duration_sec=None, max_cycles=N)`
  - heartbeat evidence
  - interrupt-aware summary
- `scripts/revalidation/native_test_supervisor.py`
  - `observe --duration-sec unlimited`
  - `observe --max-cycles N`
  - bundle finalization still runs after long-run observer completion

## Validation

Static validation:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

Bounded unlimited-mode smoke:

```bash
python3 scripts/revalidation/native_test_supervisor.py observe \
  --duration-sec unlimited \
  --max-cycles 2 \
  --interval 2 \
  --run-dir tmp/soak/harness/v176-long-run-20260508T180122Z
```

Result:

```text
PASS run_dir=/home/temmie/dev/A90_5G_rooting/tmp/soak/harness/v176-long-run-20260508T180122Z samples=14 failures=0
```

Evidence:

- run directory: `tmp/soak/harness/v176-long-run-20260508T180122Z/`
- `manifest.json`: pass `True`, schema `a90-harness-v175`
- `observer-summary.json`: cycles `2`, samples `14`, failures `0`, stop_reason `max-cycles`, interrupted `False`
- `heartbeat.json`: cycle `2`, samples `14`, failures `0`
- `bundle-index.json`: indexed files `6`

## Acceptance

| Requirement | Evidence | Result |
| --- | --- | --- |
| `unlimited` duration accepted | command above | PASS |
| Bounded smoke exits by max cycles | `observer-summary.json stop_reason=max-cycles` | PASS |
| Observer samples are recorded | `observer.jsonl`, samples=14 | PASS |
| Heartbeat is written | `heartbeat.json` | PASS |
| Bundle finalization still runs | `manifest.json`, `summary.md`, `README.md`, `bundle-index.json` | PASS |
| Static validation passes | `py_compile` and `git diff --check` | PASS |

## Next

- v177 Safety Gate / Dry-Run Policy.
