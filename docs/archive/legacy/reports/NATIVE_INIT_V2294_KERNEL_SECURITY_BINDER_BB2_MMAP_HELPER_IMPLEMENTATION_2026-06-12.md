# V2294 Kernel Security Recon: Binder BB2 mmap helper implementation

Date: 2026-06-12

Scope: source implementation and build-only validation. No live device action,
no devnode creation, no ioctl, no Binder protocol command, no Binder
transaction, no context-manager registration, no payload, no crash trigger, and
no exploit execution.

## Purpose

V2293 designed `BB2` as the Binder allocator reachability gate. This iteration
implements the minimal helper and runner needed to run that gate later, while
keeping default behavior build-only.

## Added files

| Path | Purpose |
| --- | --- |
| `workspace/public/src/native-init/helpers/a90_binder_mmap_bb2.c` | Static AArch64 helper source for one Binder `open` + read-only `mmap` + `munmap` + `close`. |
| `workspace/public/src/scripts/revalidation/native_kernel_binder_mmap_reachability_v2294.py` | Build-only by default runner; optional live runner gated by the exact V2293 BB2 approval phrase. |

## Helper behavior

The helper performs only:

1. `open(path, O_RDWR | O_CLOEXEC)`;
2. `mmap(NULL, length, PROT_READ, MAP_PRIVATE | MAP_NORESERVE, fd, 0)`;
3. no mapped-buffer read or write;
4. `munmap()` if mapping succeeded;
5. `close(fd)`;
6. key-value result printing.

The helper source has no `ioctl(...)` call and no Binder protocol constants.

Default parameters:

- path: `/dev/binder`;
- length: `1048576` bytes;
- maximum accepted length: `4194304` bytes;
- mapping protection: `PROT_READ`;
- mapping flags: `MAP_PRIVATE | MAP_NORESERVE`.

## Runner guardrails

The runner is build-only unless `--run-live` is supplied.

Live mode additionally requires this exact confirmation phrase:

`Stage B-Binder BB2 go: one-shot Binder mmap reachability on v2237, no ioctl, no transaction, no retry`

Live mode hard stops embedded in the runner:

- refuses live mode without exact confirmation;
- verifies resident version contains `0.9.268` and `v2237`;
- requires preflight `selftest verbose` to report `fail=0`;
- aborts if `/dev/binder` already exists, so it cannot delete a pre-existing
  legitimate node;
- materializes only `/dev/binder` major `10`, minor `81`;
- transfers only the BB2 helper to `/cache/bin/a90_binder_mmap_bb2`;
- runs the helper once under a bounded shell watchdog;
- removes helper, output file, and the temporary devnode;
- captures bounded `dmesg` tail before and after;
- reruns post `selftest verbose`;
- does not continue to BB3.

The runner never issues `BINDER_VERSION`, `BINDER_WRITE_READ`, `BC_*`, or
context-manager ioctls.

## Build-only validation

Command:

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/native_kernel_binder_mmap_reachability_v2294.py

python3 workspace/public/src/scripts/revalidation/native_kernel_binder_mmap_reachability_v2294.py \
  --out-dir workspace/private/runs/security/v2294-binder-bb2-build-only-validation
```

Result:

- decision: `v2294-binder-bb2-helper-built-not-run`;
- helper SHA256:
  `4d751a75b511ab75a0e4f149e7c18d5f13a19ccd41cfefe21940c824602bcec0`;
- private build output:
  `workspace/private/runs/security/v2294-binder-bb2-build-only-validation/a90_binder_mmap_bb2`;
- `file` output: AArch64, statically linked, stripped;
- helper forbidden-token check:
  `rg '\bioctl\s*\(|BINDER_WRITE_READ|BC_TRANSACTION|BC_REPLY|BC_FREE_BUFFER|PROT_WRITE|SET_CONTEXT_MGR' workspace/public/src/native-init/helpers/a90_binder_mmap_bb2.c`
  returned no matches;
- `git diff --check`: pass.

The compiled helper remains private and is not tracked.

## Decision

Classification:

> `binder-bb2-helper-implemented-build-only-not-run`

BB2 is now implementable with a minimal tracked helper and guarded runner. The
live BB2 run remains blocked until the exact BB2 approval phrase is provided.
BB3 remains separately blocked behind the V2292 transaction-path approval phrase.
