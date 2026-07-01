# Kernel Security Tier-2 Runtime Kernel REPL - VFS-read boot-config bundle

- Decision: `a90-repl-vfs-read-boot-config-bundle-pass`
- Scope: add and live-prove a named VFS-read observation bundle for boot command-line and kernel config provenance.
- Date: 2026-07-02 KST / 2026-07-01 UTC
- Device state at end: rolled back to `v2321-usb-clean-identity-rodata`, standalone `selftest fail=0`
- Private run: `workspace/private/runs/kernel/repl-resident-session-boot-config-20260701T154854Z/`

## Change

Added `VFS_READ_BUNDLES["boot-config"]` to `a90_repl.py`.

The bundle reads:

| Path | Read len | Expected public classification |
| --- | ---: | --- |
| `/proc/cmdline` | 512 | printable proc-style text |
| `/proc/config.gz` | 512 | gzip-style binary prefix |

Raw file bytes, runtime pointers, KASLR slide, command-line contents, and kernel-config bytes remain private-only. Public evidence records only path names, observed byte counts, prefix class, cleanup checks, and pass/fail state.

## Static Validation

Host validation passed:

- `py_compile` for `a90_repl.py`, `a90_repl_resident_session.py`, and focused tests.
- Focused VFS bundle tests:
  - `test_vfs_read_boot_config_bundle_uses_named_contract`
  - existing hardening/kernel-vitals/soc-fingerprint bundle tests
- `tests.test_a90_repl_resident_session`
- resident-session dry-run with `--batch vfs-bundle:boot-config`

The static VFS gate remains unchanged: `filp_open`, `kernel_read`, `filp_close`, `__kmalloc`, and `kfree` resolve through the promoted C2B/export-recovery path with existing source/call-safety contracts. No DENY tier was relaxed.

## Live Validation

Resident-session command:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache \
python3 workspace/public/src/scripts/revalidation/a90_repl_resident_session.py \
  --batch vfs-bundle:boot-config \
  --max-batch-size 30 \
  --run-dir workspace/private/runs/kernel/repl-resident-session-boot-config-20260701T154854Z
```

Run result:

- Resident-session decision: `a90-repl-resident-session-pass`
- Candidate flash count: `1`
- Mandatory warm reboot before batch: yes
- Rollback flash count: `1`
- Timeline schema errors: `[]`
- Completed target count: `1/1`
- Target decision: `a90-repl-vfs-read-boot-config-bundle-pass`

Per-path public results:

| Path | Result | Observed len | Prefix class |
| --- | --- | ---: | --- |
| `/proc/cmdline` | PASS | 512 | text/proc-style |
| `/proc/config.gz` | PASS | 512 | binary, gzip prefix |

For both paths, the live checks passed: owned buffers allocated and initialized, `filp_open` returned a valid file pointer, `kernel_read` returned bytes and advanced `loff_t`, `filp_close` returned `0`, and all owned buffers were freed.

## Timing

Canonical `timeline.json` uses the single top-level `events` schema and includes all required phase events.

Measured phases:

| Phase | Seconds |
| --- | ---: |
| candidate flash | 64.221 |
| candidate boot/health | 43.061 |
| mandatory warm reboot | 33.222 |
| batch REPL selftest | 32.226 |
| live boot-config bundle | 175.970 |
| post-batch health | 1.290 |
| rollback flash | 64.290 |
| rollback boot/health | 48.023 |
| total candidate-start to rollback-ready | 462.352 |

The live bundle is slower than scalar call-proofs because `/proc/config.gz` is a compressed procfs stream and the proof reads it through serial REPL transactions. This does not regress safety, but it means `boot-config` should stay a named on-demand observation bundle rather than being folded into routine light health batches.

Run-timing aggregate after this run:

- canonical timelines used: `23/71`
- resident-session projection: `20 -> 2` flashes
- projected resident-session time: `14.710s/target`
- speedup vs unbatched per-unit flash: `20.83x`
- speedup vs per-unit in-boot batching: `2.08x`

## Final Health

After rollback, standalone checks passed:

- `a90ctl version`: `v2321-usb-clean-identity-rodata`
- `a90ctl status`: `selftest pass=11 warn=1 fail=0`
- `a90ctl selftest`: `pass=11 warn=1 fail=0`

## Map Outcome

`boot-config` is now the preferred observation surface for boot-parameter and kernel-config provenance exposed through procfs. Do not add individual getter proofs for equivalent state reachable through `/proc/cmdline` or `/proc/config.gz`; reserve individual call-proofs for functions with no file-node equivalent or a genuinely new ABI shape.
