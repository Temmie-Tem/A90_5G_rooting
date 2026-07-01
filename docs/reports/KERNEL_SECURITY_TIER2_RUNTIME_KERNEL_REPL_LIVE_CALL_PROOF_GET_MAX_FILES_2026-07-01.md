# Kernel Security Tier-2 Runtime Kernel REPL - Live Call Proof: get_max_files

Date: 2026-07-01

- Decision: `a90-repl-live-call-proof-get_max_files-pass`
- Scope: one-target live-call proof; boot partition only; rollback to `v2321`
- Target: `get_max_files(void)`
- Public artifact: this report and `GOAL.md`
- Private evidence: `workspace/private/runs/kernel/live-call-proof-get-max-files-20260701T054248Z/proof/a90_repl_evidence.json`
- Private timeline: `workspace/private/runs/kernel/live-call-proof-get-max-files-20260701T054248Z/timeline.json`

## Target Selection

`get_max_files` was selected as a VFS state-observation target rather than
another generic helper. It extends the live-proven function map with a read-only
query for the kernel's open-file table limit.

The proof was one-target only. The nearby `get_nr_dirty_inodes` VFS state
candidate remains available for a later proof, but was not called in this unit.

## Static Gate

- Address: `get_max_files=0xffffff800829005c`.
- Resolution: `export-recovery`, map agreement, one export candidate.
- Direct BL xrefs: `1`.
- JOPP entry: yes.
- Source declaration: `extern unsigned long get_max_files(void)` at
  `include/linux/fs.h:71`.
- Source implementation: `fs/file_table.c`, with `get_max_files(void)` returning
  `files_stat.max_files`.
- ABI/source contract: no pointer arguments.
- C1 tier: `SAFE-SCALAR`.
- Required valid pointer args: none.
- Next-symbol boundary: `proc_nr_files` at `+0x18`.
- Static words: 6-word body pinned, including the final `0x00be7bad` boundary
  guard.

The classifier observed no argument pointer dereferences before return and no
context-call blockers. The static implementation check proves the intended
read-only source path is the one being called.

## Live Run

Flash gate:

- Rollback image `v2321`, deeper fallback `v2237`, final fallback `v48`, and TWRP
  recovery artifacts were present with expected SHA256 values.
- Baseline v2321 `version/status/selftest` passed before candidate flash.
- Candidate image
  `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
  matched SHA256
  `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
- Candidate flash used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched the candidate SHA.
- Candidate helper verification passed. The first explicit candidate health
  attempt hit serial `cmdv1AT` framing noise after `hide`; the sequential retry
  passed `hide/version/status/selftest`.

Initial proof attempt:

- The first `call-proof get_max_files` command failed before any target call
  because `--source-root` pointed at `workspace/private/inputs/kernel_source`
  instead of the concrete `.../Kernel` tree. The static implementation check
  could not read `fs/file_table.c`.
- No live target call occurred in that failed attempt and no evidence file was
  produced.
- The successful retry used
  `workspace/private/inputs/kernel_source/SM-A908N_KOR_12_Opensource/Kernel`.

Live proof:

- Called `get_max_files()` twice with no arguments.
- Both calls returned `0x71c6a`.
- Both values were positive, below the conservative sane upper bound, and stable
  across the short repeat.
- Raw runtime pointers and the KASLR slide are private-only and not committed.

Health and rollback:

- Post-proof `hide/status/selftest` passed with `selftest pass=11 warn=1 fail=0`
  and `pstore entries=0`.
- Rollback to `v2321` used `native_init_flash.py`; pushed-image SHA and boot
  readback SHA matched
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- Rollback helper verification passed. The first explicit final health attempt
  hit serial framing noise during `version` capture after the version body was
  visible; a later sequential `hide/version/status/selftest` retry passed and
  confirmed resident `v2321-usb-clean-identity-rodata`.

## Timing

Timing was recorded in:

- `workspace/private/runs/kernel/live-call-proof-get-max-files-20260701T054248Z/timeline.json`.

| Phase | Elapsed |
| --- | ---: |
| candidate flash helper total | `65.663s` |
| candidate flash start to boot ready | `66s` |
| candidate explicit health initial | `12.567s` |
| candidate explicit health retry | `6.691s` |
| live proof initial | `2.666s` |
| live proof retry | `5.410s` |
| post-proof candidate health | `1.231s` |
| rollback flash helper total | `64.683s` |
| rollback flash start to boot ready | `65s` |
| final health initial | `12.346s` |
| final health retry | `6.684s` |
| candidate start to final health done | approximately `274s` |

The helper total and start-to-boot-ready rows are retained for compatibility
with prior reports and are not additive. All serial bridge commands in this unit
were run sequentially; there was no overlapping health/proof command.

## Validation

Host validation:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map get_max_files --no-objdump`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_fs_state_batch_passes_with_no_arg_contracts`

Live validation:

- Candidate flash passed with matching candidate readback SHA.
- `get_max_files` live proof passed under the no-argument read-only VFS
  open-file-limit contract.
- Post-proof health passed.
- Rollback to v2321 passed with matching rollback readback SHA.
- Final v2321 health retry passed with `selftest fail=0`.

## Function Map Entry

`get_max_files` is live-proven only under this contract:

- input: no arguments; VFS `files_stat.max_files` is read-only and no returned
  pointer is dereferenced or freed.
- return: unsigned long open-file limit is positive, below the conservative sane
  count bound, and stable across short-repeat proof calls.
- observed: two calls returned `0x71c6a`.
- cleanup: none; no owned resource was created.
- policy: same-session proof target only; not a mass auto-call target.
