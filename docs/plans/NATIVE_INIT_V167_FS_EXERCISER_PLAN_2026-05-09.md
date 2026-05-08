# Native Init v167 Filesystem Exerciser Mini Plan (2026-05-09)

## Summary

- target label: `v167 Filesystem Exerciser Mini`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- 목적은 SD workspace 안의 test-owned directory에서 create/write/read/truncate/rename/unlink/fsync sequence를 deterministic하게 실행해 filesystem operation stability를 확인하는 것이다.

## Scope

- `scripts/revalidation/fs_exerciser_mini.py` 추가.
- test root는 기본 `/mnt/sdext/a90/test-fsx/<run-id>`이다.
- operation set:
  - create
  - write
  - truncate
  - rename
  - unlink
  - fsync/sync
  - verify size/hash
- payload는 bounded zero pattern이며 SHA-256으로 검증한다.
- seed 기반 operation log를 JSON으로 남긴다.

## Recommended Run

```bash
RUN_ID=v167-fsx-$(date +%Y%m%d-%H%M%S)
umask 077

python3 scripts/revalidation/fs_exerciser_mini.py \
  --run-id "$RUN_ID" \
  --ops 64 \
  --seed v167-fsx-seed \
  --bridge-timeout 45
```

Output:

```text
tmp/soak/fs-exerciser/<run-id>/fs-exerciser-report.md
tmp/soak/fs-exerciser/<run-id>/fs-exerciser-report.json
```

## Guardrails

- device path must stay under `/mnt/sdext/a90/test-fsx`.
- no raw block access.
- no Android/EFS/modem/bootloader/key/security path writes.
- cleanup removes only the run-owned directory.
- host evidence files use private directory/file permissions and reject symlink destinations.

## Validation

- `python3 -m py_compile scripts/revalidation/fs_exerciser_mini.py`
- `git diff --check`
- smoke run:
  - `--ops 10`
  - `--seed v167-smoke`
- full run:
  - `--ops 64`
  - `--seed v167-fsx-seed`

## Acceptance

- every operation record is OK.
- final verification for remaining files passes.
- cleanup removes the run directory.
- report includes seed, operation counts, operation log, remaining file state, and failure list.

## Next

- If v167 passes, proceed to v168 Kernel Selftest Feasibility.
- If v167 fails, classify the failure as path guard, create/write, hash verify, truncate, rename, unlink, fsync/sync, or cleanup before continuing.
