# Runtime Kernel REPL VFS-Read SoC Fingerprint Bundle

Date: 2026-07-02 KST / 2026-07-01 UTC

## Scope

Add and live-prove a named `soc-fingerprint` observation bundle on top of the
existing VFS-read primitive. This follows the KEYSTONE-FIRST / RETIRE-SUBSUMED
policy: use `/sys/devices/soc0/*` file nodes instead of adding individual
`socinfo_get_*` state getter call-proofs.

No new boot artifact was built. The resident-session harness was extended to
accept `vfs-bundle:<name>` batch items, so observation bundles can run under the
same flash-once, warm-reboot-per-batch, per-target-flush, rollback-once model as
call-proof targets.

## Public Changes

- `a90_repl.py`: added `VFS_READ_BUNDLES["soc-fingerprint"]`.
- `a90_repl_resident_session.py`: batch items now dispatch either plain
  call-proof targets or `vfs-bundle:<name>` observation bundles.
- Tests: added SoC bundle redaction coverage and resident-session VFS-bundle
  dispatch/flush coverage.

## Bundle Contract

The bundle reads these read-only sysfs nodes with `read_len=128`:

- `/sys/devices/soc0/soc_id`
- `/sys/devices/soc0/family`
- `/sys/devices/soc0/machine`
- `/sys/devices/soc0/revision`
- `/sys/devices/soc0/vendor`
- `/sys/devices/soc0/raw_id`
- `/sys/devices/soc0/raw_version`
- `/sys/devices/soc0/build_id`
- `/sys/devices/soc0/hw_platform`
- `/sys/devices/soc0/platform_subtype`
- `/sys/devices/soc0/platform_subtype_id`
- `/sys/devices/soc0/serial_number`

Raw file bytes, runtime pointers, KASLR slide, and serial/fingerprint values
remain private-only. Public evidence records only path names, lengths, broad
classification, and pass/fail checks.

## Host Validation

Passed:

- `py_compile` for touched Python files.
- Focused VFS and resident-session tests:
  - `test_vfs_read_soc_fingerprint_bundle_uses_named_contract`
  - existing hardening/kernel-vitals VFS tests
  - resident-session parse/dispatch tests
- `tests.test_a90_repl_resident_session` full module.
- resident-session dry-run with `--batch vfs-bundle:soc-fingerprint`.

## Live Validation

Run directory:

`workspace/private/runs/kernel/repl-resident-session-soc-fingerprint-20260701T152851Z/`

Preflight:

- Candidate v1-repl image SHA256:
  `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Rollback v2321 image SHA256:
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Deep fallback v2237 image SHA256:
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
- Baseline v2321 serial health passed with `selftest fail=0`.

Resident-session flow:

- Flashed v1-repl once.
- Ran mandatory warm reboot before the batch.
- REPL selftest passed.
- `vfs-bundle:soc-fingerprint` passed and flushed per-target evidence to disk.
- Post-batch health passed.
- Rollback to v2321 completed through the recovery-direct fallback after
  `from-native` rollback failed.
- Final manual rollback health passed: resident is
  `v2321-usb-clean-identity-rodata`, `selftest pass=11 warn=1 fail=0`.

Bundle result:

- 12/12 sysfs paths opened, read, closed, and cleaned up successfully.
- All returned printable text.
- Decimal-looking nodes: `soc_id`, `raw_id`, `raw_version`,
  `platform_subtype_id`, and `serial_number`.
- Raw values are not included in this report.

Timing events are in canonical `events:[{name,timestamp_utc}]` shape. The eight
required phase events are present. Key durations:

- candidate flash: 64.140s
- candidate boot/health: 43.676s
- batch warm reboot: 33.238s
- batch live work: 282.750s
- rollback closure: 245.416s flash/fallback window, then manual boot health

Note: while investigating the long VFS live window, the harness process received
SIGINT after the bundle had completed. The parent process then had to be killed
after recovery-direct rollback finished because it held the serial transaction
lock during rollback-finally health. This did not affect the device end state:
rollback direct flash returned `0`, the bridge was restarted, and standalone
`version/status/selftest` confirmed v2321 with `fail=0`. The incident is a host
closure artifact, not a failed bundle proof.

## Timing Aggregate

After adding the canonical close event, the timing aggregator used 22/70
canonical timelines. Projection with `batch_size=10`, `resident_batches=10`,
`warm_reboot=15s`:

- flash count: `20 -> 2`
- resident session: `14.107s/target`
- speedup vs per-unit flash: `21.21x`
- speedup vs per-unit in-boot batch: `2.12x`

This run is heavier than a scalar call-proof because it reads 12 sysfs files and
its rollback closure included the manual/fallback window.

## Function-Map Outcome

`soc-fingerprint` is now the preferred observation surface for SoC identity and
board fingerprint values exposed under `/sys/devices/soc0`. Do not add
individual `socinfo_get_*` call-proofs for these equivalent file-node values
unless a future target requires a genuinely new ABI shape or a state value not
available through sysfs.
