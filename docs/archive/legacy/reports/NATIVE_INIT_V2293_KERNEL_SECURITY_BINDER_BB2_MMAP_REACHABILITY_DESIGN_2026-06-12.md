# V2293 Kernel Security Recon: Binder BB2 mmap reachability design

Date: 2026-06-12

Scope: design only. No live device action, no devnode creation, no ioctl, no
`mmap`, no Binder protocol command, no Binder transaction, no context-manager
registration, no payload, no crash trigger, and no exploit execution.

This report designs `BB2`, the Binder allocator reachability gate defined by
V2292. It does not authorize running BB2.

## Current state

- Resident rollback checkpoint remains `A90 Linux init 0.9.268`
  (`v2237-supplicant-terminate-poll`).
- FastRPC trigger work is shelved in the resident boot because V2291 classified
  the DSP/rpmsg channel as down.
- Binder is the next self-contained in-kernel candidate:
  - V2285: source/fix-marker absence for the CVE-2023-21255 full mitigation;
  - V2287: `/dev/binder`, `/dev/hwbinder`, `/dev/vndbinder` are materializable
    and openable;
  - V2292: Binder branch gate design exists.

## BB2 purpose

BB2 answers one narrow reachability question:

> Can native init set up Binder userspace buffer allocator state through
> `binder_mmap()` without entering Binder protocol or transaction paths?

This is the Binder equivalent of FastRPC Unit A. If `mmap` setup fails, BB3 is
unreachable in the resident native-init environment regardless of the source
fix-marker state. If it succeeds, Binder allocator setup is reachable, but BB3
still requires a separate target plan and explicit trigger approval.

## Source facts

Source root:

`tmp/wifi/v766-icnss-qcacld-patch-apply-build/source`

Relevant code:

- `drivers/android/binder.c`:
  - `binder_fops` exposes `.open`, `.unlocked_ioctl`, `.compat_ioctl`, and
    `.mmap`.
  - `binder_mmap()` rejects non-group-leader mapping with `-EINVAL`.
  - mappings larger than `SZ_4M` are capped to `4 MiB`.
  - `FORBIDDEN_MMAP_FLAGS` is `VM_WRITE`; a userspace mapping that requests
    writable VMA state is rejected with `-EPERM`.
  - successful setup installs `binder_vm_ops`, sets `vma->vm_private_data`, and
    calls `binder_alloc_mmap_handler(&proc->alloc, vma)`.
  - `binder_vma_close()` calls `binder_alloc_vma_close(&proc->alloc)`.
- `drivers/android/binder_alloc.c`:
  - `binder_alloc_mmap_handler()` returns:
    - `0` on success;
    - `-EBUSY` if the Binder proc already has an allocator buffer;
    - `-ENOMEM` for allocator metadata failures.
  - on success it sets `alloc->buffer`, allocates the page metadata array,
    creates one free `binder_buffer`, sets `alloc->buffer_size`, initializes
    `alloc->free_async_space`, and publishes `alloc->vma`.
  - `binder_alloc_deferred_release()` expects `alloc->vma` to be cleared before
    final proc release.
- `binder_vm_fault()` returns `VM_FAULT_SIGBUS`. Therefore BB2 must not read
  from or write to the mapped address. The mapping is a reachability probe, not
  a data buffer access test.

## Proposed BB2 live sequence

BB2 requires a separate explicit operator approval before running.

Allowed live sequence:

1. Confirm the serial bridge is up.
2. Confirm resident baseline is still v2237:
   - `a90ctl version`;
   - `a90ctl status`;
   - `a90ctl 'selftest verbose'` with `fail=0`.
3. Snapshot a bounded kernel log tail before touching Binder.
4. Materialize only a temporary `/dev/binder` node:
   - character device major `10`, minor `81`;
   - do not create `/dev/hwbinder` or `/dev/vndbinder` for BB2.
5. Run one small native helper that performs only:
   - `open("/dev/binder", O_RDWR | O_CLOEXEC)`;
   - `mmap(NULL, 1 MiB, PROT_READ, MAP_PRIVATE | MAP_NORESERVE, fd, 0)`;
   - record return pointer or errno;
   - do not dereference the mapping;
   - `munmap()` if mapping succeeded;
   - `close(fd)`;
   - exit.
6. Remove the temporary devnode.
7. Snapshot bounded kernel log tail after cleanup.
8. Re-run `a90ctl 'selftest verbose'`.
9. Stop and report. Do not proceed to BB3 in the same run.

The helper must be single-shot. It must not loop over sizes, flags, devices, or
retry after a failure. If a helper is implemented, its source can live in
tracked workspace code if it contains only the BB2 sequence above; compiled
binary and raw logs remain private.

## BB2 hard stops

BB2 must not perform any of these actions:

- no `BINDER_WRITE_READ`;
- no `BC_*` command buffer;
- no `BINDER_SET_CONTEXT_MGR` or `BINDER_SET_CONTEXT_MGR_EXT`;
- no `BINDER_VERSION` unless a separate BB1 smoke test is explicitly chosen;
- no Binder transaction;
- no `BC_FREE_BUFFER`;
- no `mmap` with `PROT_WRITE`;
- no read/write/dereference of the mapped Binder buffer;
- no `/dev/hwbinder` or `/dev/vndbinder`;
- no heap spray, reclaim, or grooming;
- no privilege escalation;
- no retry loop;
- no continuation to BB3 without the BB3-specific approval phrase from V2292.

## Expected outcomes

| Outcome | Classification | Meaning |
| --- | --- | --- |
| `bb2-mmap-ok` | Pass | Binder allocator setup is reachable in native init. BB3 target design can be discussed separately. |
| `bb2-mmap-eperm-vmwrite` | Helper bug | Mapping requested writable VMA state despite the BB2 design; fix helper before any rerun. |
| `bb2-mmap-einval-not-group-leader` | Helper/process-shape issue | `binder_mmap()` likely rejected because the mapping thread was not the group leader. Do not retry blindly; redesign helper. |
| `bb2-mmap-ebusy` | State hygiene issue | The same Binder proc already has allocator state. Cleanup or helper shape is wrong. |
| `bb2-mmap-enomem` | Environment/resource failure | Allocator metadata setup failed; BB3 is not reachable in this boot without solving resource/state. |
| `bb2-sigbus` | Helper bug | The helper touched the mapping. BB2 result invalid. |
| `bb2-hang-or-timeout` | Stop | Recover console if needed, snapshot logs, and do not retry blindly. |
| `bb2-preflight-fail` | No Binder result | Bridge/version/status/selftest was not clean before the probe. |
| `bb2-post-selftest-fail` | Stop | Binder state or helper caused a regression; do not continue to BB3. |

## Interpretation

`bb2-mmap-ok` is necessary but not sufficient for BB3. It proves only:

- the Binder device can be opened;
- the Binder allocator VMA can be installed;
- allocator metadata can be initialized and cleaned up in native init.

It does not prove:

- a valid transaction target exists;
- a context manager can be safely registered;
- a transaction can be completed;
- the CVE-adjacent failed-buffer-release path is triggerable;
- a no-crash result would be meaningful.

The next design after `bb2-mmap-ok` would be target reachability, not a direct
UAF trigger. In a clean native-init Binder context there is no Android
`servicemanager`, so any later target plan must explicitly account for a fresh
context-manager setup. That belongs to a later BB3 design and remains blocked.

## Approval boundary

Running BB2 needs explicit approval because it mutates live Binder allocator
state, even though it does not enter protocol or transaction paths.

Acceptable BB2 approval phrase:

`Stage B-Binder BB2 go: one-shot Binder mmap reachability on v2237, no ioctl, no transaction, no retry`

This phrase approves BB2 only. It does not approve BB3.

BB3 remains gated by the separate V2292 phrase:

`Stage B-Binder go: one-shot crash-only Binder transaction-path trigger on v2237, no heap spray, no privilege escalation, no retry`

## Decision

Classification:

> `binder-bb2-mmap-reachability-designed-not-run`

BB2 is the next substantive Binder checkpoint. BB1 can be skipped unless a
version-only helper/ABI smoke test is desired. BB2 should be implemented and
run only after explicit BB2 approval, with the hard stops above enforced.
