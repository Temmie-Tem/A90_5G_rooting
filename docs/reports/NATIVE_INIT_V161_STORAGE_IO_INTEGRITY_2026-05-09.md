# Native Init v161 Storage I/O Integrity Report (2026-05-09)

## Result

- status: PASS
- label: `v161 Storage I/O Integrity`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- device build was not bumped for this host-side validation step.
- objective: verify SD runtime root write/read/hash/rename/sync/unlink behavior under `/mnt/sdext/a90/test-*`.

## Implemented

- Added `scripts/revalidation/storage_iotest.py`.
- Added `docs/plans/NATIVE_INIT_V161_STORAGE_IO_INTEGRITY_PLAN_2026-05-09.md`.
- The script refuses device test roots outside `/mnt/sdext/a90/test-*`.
- Host output uses private file handling and symlink refusal.

## Evidence Paths

```text
tmp/soak/v161-smoke-20260509-012114/storage-iotest-report.md
tmp/soak/v161-smoke-20260509-012114/storage-iotest-report.json
tmp/soak/v161-storage-20260509-012156/storage-iotest-report.md
tmp/soak/v161-storage-20260509-012156/storage-iotest-report.json
```

## Smoke Profile

```text
run_id: v161-smoke-20260509-012114
sizes: 4K,64K
result: PASS
files: 2
duration: 19.896s
cleanup: PASS
```

## Full Profile

```text
run_id: v161-storage-20260509-012156
sizes: 4K,64K,1M,16M
result: PASS
files: 4
duration: 40.766s
```

| File | Size | Transfer | Read Hash | Rename | Sync/Rehash | Unlink |
|---|---:|---|---|---|---|---|
| `file-01-4096.bin` | `4096` | `True` | `True` | `True` | `True` | `True` |
| `file-02-65536.bin` | `65536` | `True` | `True` | `True` | `True` | `True` |
| `file-03-1048576.bin` | `1048576` | `True` | `True` | `True` | `True` | `True` |
| `file-04-16777216.bin` | `16777216` | `True` | `True` | `True` | `True` | `True` |

Cleanup:

```text
cleaned /mnt/sdext/a90/test-io/v161-storage-20260509-012156
stat: /mnt/sdext/a90/test-io/v161-storage-20260509-012156: No such file or directory
```

## Post-Test Control Checks

```text
storage: PASS backend=sd root=/mnt/sdext/a90 fallback=no rw=yes
mountsd status: PASS mounted mode=rw uuid match=yes avail=56842MB
selftest verbose: PASS pass=11 warn=1 fail=0
longsoak status verbose: PASS running=yes samples=462 health=ok
```

## Static Validation

```text
python3 -m py_compile scripts/revalidation/storage_iotest.py
git diff --check
```

Result: PASS.

## Notes

- Test writes were constrained to `/mnt/sdext/a90/test-io/<run-id>`.
- The script uses NCM for payload transfer and serial/cmdv1 for setup, hash, rename, sync, unlink, and cleanup commands.
- This validates SD runtime root behavior only; it does not touch Android, EFS, modem, bootloader, or raw block device paths.

## Next

- v162: Process/Concurrency Stability.
