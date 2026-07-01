# Runtime Kernel REPL - `is_boot_recovery` Resident-Session Proof (2026-07-01)

## Result

PASS. `is_boot_recovery()` is live-proven under a no-argument read-only
boot-recovery flag contract.

- Target: `is_boot_recovery`
- Source: `drivers/battery_v2/include/sec_battery.h:763`
- Signature: `extern unsigned int is_boot_recovery(void)`
- Static identity: `exact-leaf-map+xref+word-boundary`
- Link address: `0xffffff80086ec6bc`
- Next symbol boundary: `sec_bootstat_add_initcall` at `+0x10`
- Direct BL xrefs: `3`
- Body words: `90014e08 b949d900 d65f03c0 00be7bad`
- Return: `uint32_t` boot-recovery flag, no returned pointer

Live run:
`workspace/private/runs/kernel/repl-resident-session-is-boot-recovery-20260701T131159Z/`

- Decision: `a90-repl-live-call-proof-is_boot_recovery-pass`
- Observed return: `0x0`
- Repeat count: `2`
- Contract: both returns were stable, in `0..0xffffffff`, and bool-like
- Runtime address and KASLR slide stayed private-only

The generic 64-byte classifier scan still sees the following function's
`__pi_strcmp` call and therefore reports `signals.leaf=false`; that is not the
identity gate. This proof relies on the exact next-symbol boundary and accepted
`exact_leaf_map_ground_truth` evidence for the `0x10`-byte body.

## Safety

The proof used resident-session mode:

1. Flash v1-repl once.
2. Warm reboot resident v1-repl before the bounded batch.
3. Run one target batch and flush the target result to disk.
4. Roll back to v2321 once at the end.

Rollback/fallback artifacts were confirmed before live work:

- v2321 rollback SHA256: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- v2237 fallback SHA256: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- v48 fallback present
- v1-repl SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`

The resident-session summary reports:

- `decision`: `a90-repl-resident-session-pass`
- `flash_count`: `2`
- `candidate_flashed_once`: `true`
- `rollback_flashed_once`: `true`
- `warm_reboot_between_batches`: `true`
- `timeline_errors`: `[]`

Final health after a serial bridge restart:

- `version`: `v2321-usb-clean-identity-rodata`
- `selftest`: `pass=11 warn=1 fail=0`

## Timing

Canonical timeline:
`workspace/private/runs/kernel/repl-resident-session-is-boot-recovery-20260701T131159Z/timeline.json`

- Candidate flash: `64.310290s`
- Candidate boot/health: `43.935544s`
- Live session: `70.201288s`
- Warm reboot: `33.243462s`
- One-target live batch: `3.066112s`
- Rollback flash: `63.840645s`
- Rollback boot/health: `0.835342s`
- Candidate start to rollback boot ready: `243.139239s`

`analyze_repl_run_timing.py --json` now uses `15` canonical timelines and
projects resident mode as:

- Flashes: `20 -> 2`
- Resident per target: `13.550s`
- Speedup vs unbatched unit: `20.28x`
- Speedup vs per-unit in-boot batch: `2.03x`

## Validation

Host/static:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/revalidation/a90_repl.py tests/test_a90_repl.py`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache PYTHONPATH=tests python3 -m unittest tests.test_a90_repl.CallSafetyClassificationTests.test_safe_with_valid_pointer_seed_records_required_args tests.test_a90_repl.CallSafetyClassificationTests.test_seed_inventory_summary_counts_tiers tests.test_a90_repl.CallSafetyClassificationTests.test_source_signature_oracle_distinguishes_scalar_and_pointer_args tests.test_a90_repl.SelftestIntegrationTests.test_call_proof_is_boot_recovery_passes_with_boot_flag_contract`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl.py call-safety-classify --map workspace/private/runs/kernel/v2c-c2b-kallsyms-padding-fix/System.map --image workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img is_boot_recovery`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl_resident_session.py --batch is_boot_recovery --run-dir /tmp/a90-resident-dryrun-is-boot-recovery --dry-run`

Live:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_repl_resident_session.py --batch is_boot_recovery --run-dir workspace/private/runs/kernel/repl-resident-session-is-boot-recovery-20260701T131159Z`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90_bridge.py restart --discovered --allow-device-change --wait-timeout 12`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90ctl.py version`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest`
- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/analysis/analyze_repl_run_timing.py --json`
