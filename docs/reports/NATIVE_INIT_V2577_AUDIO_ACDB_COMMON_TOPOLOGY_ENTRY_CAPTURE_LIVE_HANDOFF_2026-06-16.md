# NATIVE_INIT V2577 — ACDB common-topology entry-arm topology capture

Date: 2026-06-16

## Scope

Android own-process ACDB capture handoff using the V2490 checked Android boot/stage/pull/rollback engine and the V2577 common-topology entry-arm helper/preload artifacts.

## Result

- decision: `v2577-common-topology-entry-armed-no-acdbtap-events-rollback-pass`
- ok: `False`
- out_dir: `workspace/private/runs/audio/v2577-acdb-common-topology-entry-capture-20260616-133126`
- v2490_engine_decision: `v2490-helper-timeout-ownprocess-context-only-no-events-before-rollback-rollback-pass`
- classification: `v2577-common-topology-entry-armed-no-acdbtap-events`
- init_v3_ok: `False`
- common_hook_armed_before_real_common_topology: `True`
- common_hook_event_count: `2`
- common_hook_stages: `['enter_common_topology', 'armed_before_real_common_topology']`
- acdb_log_has_common_topology: `False`
- acdb_log_has_topology_get: `False`
- helper_sigsegv: `False`
- topology_success_count: `0`
- successful_nonzero_count: `0`
- size_query_count: `0`
- real_audio_set_pass_through_count: `0`

## Captured Records

- size_query_records: `0`
- topology_4916_records: `0`

Raw ACDB buffers remain private under the run directory and are not committed.

## Artifacts

- helper_sha256: `5cc7b9c6f2bacdb7c4789bb9f9f62ec2f2ec7488e9124e97b0364b3644af023d`
- preload_sha256: `5fef19840f60a4ae4af15fb6ee5d294db43064ccb60573825c855494e3b8629c`

## Boundary

- The preload is armed only at `acdb_loader_send_common_custom_topology()` entry: earlier `acdb_ioctl` calls pass through without dump/hash/file I/O, then every `out_len>0` ACDB call is dumped.
- `A90_ACDB_FAKE_ALLOCATE=1` is forced; any real `AUDIO_SET_CALIBRATION` pass-through is classified as a boundary violation.
- Success requires `ret==0`, non-all-zero raw bytes, and `out_len==4916`; requested length alone is not success.

## Interpretation

- The V2577 hook entered `acdb_loader_send_common_custom_topology()` and armed capture before the real function, but the `acdb_ioctl` wrapper recorded zero `out_len>0` rows.
- The underlying V2490 engine decision was `v2490-helper-timeout-ownprocess-context-only-no-events-before-rollback-rollback-pass`, so the real common-topology call did not complete inside the bounded helper window.
- This narrows the remaining blocker away from the pre-arm timing race: either the common-topology path does not traverse the imported `acdb_ioctl` symbol in this own-process namespace, or the relevant bytes are carried through a different call/indirect buffer than the current wrapper observes.

- This run is useful negative evidence if the common-topology hook arms but no target rows appear: the arm point is at the correct function boundary, so the next discriminator is whether `out_buf` or the indirect request buffer carries the topology bytes on this build.
