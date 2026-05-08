# A90 v180 CPU/Memory Workload Profiles Plan

Date: `2026-05-09`
Device build baseline: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v180` host harness, not a native-init boot image
Roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

v180 adds a CPU/memory workload module that can run under the v179 mixed-soak
scheduler. It introduces low/medium/spike/cooldown profiles while keeping all
memory writes bounded and temporary. This is a host-harness change only; no
native-init boot image is built or flashed.

## Scope

- Add `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py`.
- Register `cpu-memory-profiles` in `native_test_supervisor.py`.
- Make the mixed-soak default CPU workload use `cpu-memory-profiles`.
- Use `DeviceClient` for all device commands so observer and workloads share the
  same serial single-writer lock.
- Verify per-profile CPU stress, bounded `/tmp` memory write, SHA-256 check, and
  cleanup.

## Profiles

- `smoke`: `low`, `cooldown`
- `quick`: `low`, `medium`, `spike`, `cooldown`

Memory sizes are intentionally small (`4M`, `8M`, `16M`) to avoid OOM testing in
this phase. Full memory pressure and OOM behavior remain out of scope.

## Acceptance

- `cpu-memory-profiles` appears in supervisor `list` and `plan` output.
- `run cpu-memory-profiles --profile quick` PASS on real device.
- `mixed-soak` default schedule includes `cpu-memory-profiles`.
- `mixed-soak` 30s smoke PASS with observer failures `0`.
- Memory verify mismatch is `0`.
- Observer remains active without bridge connection reset.
- Next executable item becomes v181 NCM/TCP + Storage Workload Integration.
