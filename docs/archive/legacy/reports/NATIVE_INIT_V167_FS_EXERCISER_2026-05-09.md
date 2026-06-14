# Native Init v167 Filesystem Exerciser Mini Report (2026-05-09)

## Result

- status: PASS
- label: `v167 Filesystem Exerciser Mini`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- device build was not bumped for this host-side validation step.
- objective: run deterministic bounded filesystem operation sequence under `/mnt/sdext/a90/test-fsx`.

## Implemented

- Added `scripts/revalidation/fs_exerciser_mini.py`.
- Added `docs/plans/NATIVE_INIT_V167_FS_EXERCISER_PLAN_2026-05-09.md`.
- The validator captures private host evidence under `tmp/soak/fs-exerciser/<run-id>`.
- The validator refuses roots outside `/mnt/sdext/a90/test-fsx`.

## Evidence Paths

```text
tmp/soak/fs-exerciser/v167-smoke-20260509-020156/fs-exerciser-report.md
tmp/soak/fs-exerciser/v167-smoke-20260509-020156/fs-exerciser-report.json
tmp/soak/fs-exerciser/v167-fsx-20260509-020232/fs-exerciser-report.md
tmp/soak/fs-exerciser/v167-fsx-20260509-020232/fs-exerciser-report.json
```

## Smoke Profile

```text
run_id: v167-smoke-20260509-020156
result: PASS
ops_requested: 10
duration: 9.821s
cleanup: PASS
```

## Full Profile

```text
run_id: v167-fsx-20260509-020232
result: PASS
duration: 39.945s
seed: v167-fsx-seed
ops_requested: 64
records: 69
cleanup_ok: True
remaining_files_before_cleanup: 2
failed_records: 0
```

## Operation Counts

| Operation | Count |
|---|---:|
| `create` | `12` |
| `write` | `11` |
| `truncate` | `7` |
| `rename` | `6` |
| `unlink` | `10` |
| `fsync` | `9` |
| `verify` | `9` |
| `final-verify` | `2` |
| `sync` | `1` |
| `cleanup` | `1` |
| `cleanup-verify` | `1` |

## Static Validation

```text
python3 -m py_compile scripts/revalidation/fs_exerciser_mini.py
git diff --check
```

Result: PASS.

## Notes

- All paths stayed under `/mnt/sdext/a90/test-fsx/<run-id>`.
- The sequence is replayable from the JSON report seed and operation log.
- This is a bounded smoke exerciser, not a replacement for full xfstests/fsx.

## Next

- v168: Kernel Selftest Feasibility.
