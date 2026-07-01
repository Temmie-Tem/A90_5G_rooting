# Kernel Security Tier-2 Runtime Kernel REPL - VFS-read observation bundle

Date: 2026-07-01

- Decision: `a90-repl-vfs-read-bundle-pass`
- Scope: live composition of the previously proven VFS-read keystone,
  `filp_open` + `kernel_read` + `filp_close`, into a reusable read-only
  `/proc`/`/sys` observation primitive
- Device action: yes, boot partition only through `native_init_flash.py`;
  rollback to `v2321`
- Candidate image: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback image: `workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img`
- Rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Private evidence: `workspace/private/runs/kernel/vfs-read-observation-bundle-20260701T101310Z/proof/vfs-read/a90_repl_evidence.json`
- Private result: `workspace/private/runs/kernel/vfs-read-observation-bundle-20260701T101310Z/result.json`
- Private timeline: `workspace/private/runs/kernel/vfs-read-observation-bundle-20260701T101310Z/timeline.json`

## Selection

This implements the 2026-07-01 KEYSTONE-FIRST + RETIRE-SUBSUMED steer. The
individual `filp_open` and `kernel_read` function call-proofs were already
live-proven on 2026-06-29. This unit turns them into the higher-value
primitive: read any bounded kernel-visible file through owned kernel buffers,
without adding more lone state-getter proofs for values that already have
`/proc` or `/sys` file-node equivalents.

Trusted input contract:

- Absolute kernel-visible pathname, NUL-free, capped to 192 bytes.
- `filp_open(path, O_RDONLY, 0)` only.
- `kernel_read(file, owned_read_buffer, read_len, owned_loff_t_pos)` with
  `read_len <= 4096`.
- All pointer arguments are tool-owned or returned by the same-session
  `filp_open`.
- `filp_close(file, NULL)` and `kfree` cleanup must succeed for every path.

Retire-subsumed policy:

- Prefer this VFS-read primitive for `/proc` and `/sys` state nodes.
- Do not add new lone state-getter call-proofs when a file-node equivalent
  exists.
- Reserve future individual call-proofs for no file-node equivalent or a
  genuinely new ABI shape.

## Static Gate

The live command re-runs the C1/source/call-safety gate before touching the
device:

| Symbol | Resolution | Direct BL xrefs | Source contract | Safety |
| --- | --- | ---: | --- | --- |
| `filp_open` | `export-recovery`, map agrees | `48` | `extern struct file * filp_open(const char *, int, umode_t)` | `SAFE-WITH-VALID-PTR`, x0 pathname |
| `kernel_read` | `export-recovery`, map agrees | `17` | `extern ssize_t kernel_read(struct file *, void *, size_t, loff_t *)` | `SAFE-WITH-VALID-PTR`, x0/x1/x3 verified pointers |
| `filp_close` | `export-recovery`, map agrees | `67` | `extern int filp_close(struct file *, fl_owner_t id)` | `SAFE-WITH-VALID-PTR`, x0 verified file pointer |
| `__kmalloc` / `kfree` | `export-recovery`, map agrees | allocator baseline | owned-buffer setup/cleanup | existing REPL allocator contract |

`__kmalloc` passed the no-pre-call-x0-deref guard. `filp_close` is used only
as paired cleanup for the `struct file *` returned by this proof, not as a
general arbitrary file-close permission.

## Live Run

Attempt 1 at
`workspace/private/runs/kernel/vfs-read-observation-bundle-20260701T100931Z/`
flashed the candidate successfully, but the first candidate health phase hit
serial input fragmentation after a successful `version` response. No target
call ran. The script immediately rolled back to v2321; rollback flash matched
readback SHA. A manual bridge restart then confirmed final v2321
`version/status/selftest` with `selftest fail=0`. This was a transport abort,
not a promoted proof.

Attempt 2 added an explicit bridge restart after candidate flash. The accepted
live path:

- Baseline v2321 `version/status/selftest` passed.
- Candidate flash used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched the candidate SHA.
- Candidate health first attempt hit the same known serial fragmentation, but
  bridge restart + retry passed.
- REPL selftest returned `a90-repl-v2a1-selftest-pass`.
- `vfs-read` read five paths in one REPL session.
- Post-proof candidate health passed.
- Rollback to v2321 used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched the v2321 SHA.
- Final rollback health first attempt hit the same serial fragmentation, but
  bridge restart + retry passed with `selftest pass=11 warn=1 fail=0`.
- Final bridge status was `connected-no-immediate-error`.

Public observations:

| Path | Result | Observed bytes | Public classification |
| --- | --- | ---: | --- |
| `/proc/cmdline` | PASS | `128` | text, proc-style; raw content redacted |
| `/proc/sys/fs/file-max` | PASS | `7` | text decimal |
| `/proc/sys/kernel/tainted` | PASS | `4` | text decimal |
| `/sys/kernel/uevent_seqnum` | PASS | `5` | text decimal |
| `/proc/config.gz` | PASS | `128` | binary gzip-style config stream |

Each path passed the same per-path checks: owned buffer allocation, pathname
poke/peek verification, `filp_open` returned a sane non-ERR `struct file *`,
`kernel_read` returned `1..read_len` bytes and advanced `pos` by the returned
byte count, `filp_close` returned `0`, and all owned buffers were freed.

Raw runtime pointers, KASLR slide, `/proc/cmdline`, and raw file bytes remain
private-only and are not committed.

## Timing

Timing was recorded in:

- `workspace/private/runs/kernel/vfs-read-observation-bundle-20260701T101310Z/timeline.json`.

Attempt 2 started at `2026-07-01T10:13:10Z`.

| Phase | Elapsed |
| --- | ---: |
| baseline bridge status | `0.327s` |
| baseline version/status/selftest | `1.449s` |
| candidate flash helper total | `66.065s` |
| candidate bridge restart after flash | `1.097s` |
| candidate health first attempt | serial fragmentation at `10.168s` |
| candidate bridge restart | `1.639s` |
| candidate health retry | `8.073s` |
| REPL selftest | `5.938s` |
| live VFS-read bundle | `129.323s` |
| post-proof candidate health | `1.445s` |
| rollback flash helper total | `64.357s` |
| rollback bridge restart after flash | `0.902s` |
| rollback health first attempt | serial fragmentation at `10.164s` |
| rollback bridge restart | `1.671s` |
| rollback health retry | `8.142s` |
| final bridge status | `0.336s` |

The helper total rows are host-observed phase durations and are not additive
with helper-internal timing. All serial bridge operations in the accepted live
path were run sequentially.

## Validation

Host validation:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py tests/test_a90_repl.py`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 tests/test_a90_repl.py SelftestIntegrationTests.test_call_proof_filp_open_passes_with_owned_pathname_contract SelftestIntegrationTests.test_call_proof_kernel_read_passes_with_owned_file_buffer_pos_contract SelftestIntegrationTests.test_vfs_read_files_reads_proc_nodes_with_redacted_summary`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py vfs-read --help`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img --no-objdump filp_open kernel_read filp_close`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 tests/test_a90_repl.py` (`203` tests, OK)
- `git diff --check`

Live validation:

- Candidate flash passed with matching candidate readback SHA.
- Candidate health retry and REPL selftest passed.
- `vfs-read` bundle passed for `/proc/cmdline`,
  `/proc/sys/fs/file-max`, `/proc/sys/kernel/tainted`,
  `/sys/kernel/uevent_seqnum`, and `/proc/config.gz`.
- Post-proof candidate health passed.
- Rollback to v2321 passed with matching rollback readback SHA.
- Final v2321 health retry and bridge status passed.

## Function Map / Bundle Outcome

This does not add a new lone state getter. It promotes the observation bundle:

- Primitive: `filp_open` + `kernel_read` + `filp_close`.
- Status: live-proven under the bounded owned-buffer file-read contract above.
- Scope: read-only observation of kernel-visible files.
- Cleanup: per-path `filp_close` and `kfree` succeeded.
- Subsumption rule: future `/proc`/`/sys`-equivalent state should be read by
  this primitive instead of enumerating more redundant getter call-proofs.
