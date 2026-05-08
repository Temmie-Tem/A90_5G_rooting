# Native Init v161 Storage I/O Integrity Plan (2026-05-09)

## Summary

- target label: `v161 Storage I/O Integrity`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- 목적은 SD runtime root `/mnt/sdext/a90`가 bounded write/read/hash/rename/unlink/sync 반복을 견디는지 검증하는 것이다.
- v161은 host-side validation helper를 먼저 추가한다. device boot image bump는 device-side `iotest` command가 필요해질 때만 별도 판단한다.

## Scope

- `scripts/revalidation/storage_iotest.py` 추가.
- test root는 기본 `/mnt/sdext/a90/test-io/<run-id>`이며, 스크립트는 `/mnt/sdext/a90/test-*` 밖으로 쓰기를 거부한다.
- host가 deterministic pseudo-random payload를 만들고 USB NCM netcat 경로로 device test root에 전송한다.
- device는 toybox `sha256sum`으로 read/verify를 수행한다.
- 각 파일별로 다음을 검증한다.
  - transfer write
  - device read hash
  - rename there/back
  - native `sync` 후 rehash
  - unlink probe file 삭제 확인

## Recommended Run

```bash
RUN_ID=v161-storage-$(date +%Y%m%d-%H%M%S)
mkdir -p tmp/soak/$RUN_ID
umask 077

python3 scripts/revalidation/storage_iotest.py \
  --run-id "$RUN_ID" \
  run \
  --sizes 4K,64K,1M,16M \
  --out-md tmp/soak/$RUN_ID/storage-iotest-report.md \
  --out-json tmp/soak/$RUN_ID/storage-iotest-report.json
```

Cleanup after evidence is captured:

```bash
python3 scripts/revalidation/storage_iotest.py --run-id "$RUN_ID" clean
```

## Guardrails

- write target must start with `/mnt/sdext/a90/test-`.
- no raw block device access.
- no `/efs`, modem, bootloader, Android partition, key/security path writes.
- host output files use private directory/file permissions and reject symlink destinations.
- test sizes are bounded and explicit.

## Validation

- `python3 -m py_compile scripts/revalidation/storage_iotest.py`
- `git diff --check`
- quick run with `--sizes 4K,64K`.
- full run with `--sizes 4K,64K,1M,16M` when time allows.
- post-test:
  - `python3 scripts/revalidation/a90ctl.py storage`
  - `python3 scripts/revalidation/a90ctl.py 'mountsd status'`
  - `python3 scripts/revalidation/a90ctl.py selftest verbose`
  - `python3 scripts/revalidation/a90ctl.py longsoak status verbose`

## Acceptance

- every test file has `transfer_ok=true`, `sha_ok=true`, `rename_ok=true`, `fsync_ok=true`, `unlink_ok=true`.
- no writes outside the test root.
- cleanup removes the run directory.
- post-test storage remains mounted `rw` with expected UUID.
- longsoak/control channel remains healthy.

## Next

- If v161 passes, proceed to v162 Process/Concurrency Stability.
- If v161 fails, classify the failure as transfer/NCM, SD write, SD read/hash, rename, sync, unlink, or cleanup before continuing.
