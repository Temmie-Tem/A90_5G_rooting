# S22+ M34 S10A Module-Load Beacon Live Result (2026-07-09)

## Verdict

S10A was executed once under the bounded `AGENTS.md` boot-only exception and is
now consumed. The one-bit module-load predicate remained false with the same
89-module S9 recipe.

Result:

```text
download-beacon-miss-parked-manual-download-required
```

Machine-readable evidence:

```text
workspace/private/runs/s22plus_m34_s10a_module_load_beacon_live_gate_live_20260709T095435Z/result.json
workspace/private/runs/s22plus_m34_s10a_module_load_beacon_live_gate_live_20260709T095435Z/timeline.json
```

The selected device serial is intentionally not recorded in this report.

## Correction

The previous S9.2 steer said S9 missed because S9 loaded devlink providers but
not their `modules.dep` symbol dependencies. The built artifacts disprove that
premise: both the S9 v0.10 artifact and the regenerated v0.11 S9 artifact
already include the alleged missing symbol-deps.

Confirmed present in S9:

```text
cmd-db.ko
smem.ko
qcom-scm.ko
qcom_ipc_logging.ko
minidump.ko
sec_debug.ko
qnoc-qos.ko
qcom_iommu_util.ko
secure_buffer.ko
```

S9 and S10A use the same module-list SHA256:

```text
c07425f4c738b53822e9f6783a142a2b5eafd72a15bd34c06fb3b49357c8fe26
```

So "add symbol-deps" is a no-op against the real S9 artifact. S10A instead
tested the earlier layer directly: did those core modules appear in
`/proc/modules` after native-init attempted the load?

## Candidate

S10A starts from the S9 89-module runtime recipe and changes only the one-bit
beacon. It does not proceed to downstream configfs, UDC bind, TypeC role writes,
soft_connect, FunctionFS, stock composite, display, Android handoff, Magisk
handoff, persistent mounts, or block writes.

Pinned artifact hashes:

```text
AP.tar.md5 SHA256: 064cc0431e649eb78bc8c8d1d89fcd16d09426f898120edb3c31c375275e3182
Padded boot.img SHA256: a1ca7a4bf64ec8ecfc56d28d3f5e8511e6045bb1b2513fbafdb4249f75e15217
/init SHA256: f8ad5df4ef3ff5db7229b3c7f55f2453bc8fe5a72260ca539534e9cddbbdc4e8
Module-list SHA256: c07425f4c738b53822e9f6783a142a2b5eafd72a15bd34c06fb3b49357c8fe26
Template source SHA256: f5e116e65f7e0075a304c8ef36610fc1604055310ca28d7fad97eb1b5457b772
Known booting Magisk base boot SHA256: 2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

S10A predicate:

```text
module_load_probe=proc_modules_core_loaded
core_module_count=8
modules=cmd_db,qcom_rpmh,gcc_waipio,pinctrl_waipio,qcom_pdc,i2c_msm_geni,mfd_max77705,pdic_max77705
true_action=reboot_download
false_action=park
```

The host-visible HIT is a new Odin Download endpoint after the original Odin
endpoint disconnects. The observed result was MISS, so the candidate parked and
required manual Download rollback.

## Live Result

The helper passed default dry-run first, then flashed only the pinned S10A boot
AP. The original Odin endpoint disconnected after candidate transfer. No new
Odin Download endpoint appeared during the 90 second observation window.

The operator reported no normal bootloop during the observation window, then
reported RDX and manual Download entry for rollback. The helper detected the
manual Download endpoint, flashed the pinned Magisk boot-only rollback AP, and
Android returned to the Magisk baseline. Post-rollback boot hash verification
passed.

Result JSON summary:

```text
schema: s22plus_m34_s10a_result_v1
stage: S10A
result: download-beacon-miss-parked-manual-download-required
rc: 0
rollback_target: magisk
base_boot_sha256: 2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

Timeline events:

```text
live_session_start: 2026-07-09T09:54:38.482128Z
candidate_flash_start: 2026-07-09T09:54:49.258674Z
candidate_flash_done: 2026-07-09T09:54:50.742170Z
candidate_boot_ready: 2026-07-09T09:54:52.010807Z
rollback_flash_start: 2026-07-09T10:00:01.311565Z
rollback_flash_done: 2026-07-09T10:00:02.636900Z
rollback_boot_ready: 2026-07-09T10:01:09.225255Z
live_session_end: 2026-07-09T10:01:10.280729Z
```

## Interpretation

S10A does not prove which individual module failed, because the channel is still
one bit. It does prove that the S9/S10A runtime did not reach the all-core-loaded
state in `/proc/modules`.

Do not advance to B2/B3/B4, descriptor/composition, FunctionFS, stock composite,
display/distro, or S9 repeat from this evidence. The next useful unit is
host-only design for a finer module-load bisection ladder or a retained
log/bitmask channel. The goal is to identify the first missing module or first
`finit_module` failure before another boot-only live candidate.

Candidate ladder if no richer retained channel is available:

```text
P0: cmd_db
P1: qcom_rpmh
P2: gcc_waipio
P3: pinctrl_waipio + qcom_pdc
P4: i2c_msm_geni
P5: mfd_max77705
P6: pdic_max77705
```

## Validation

Commands already run for this unit:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests/test_s22plus_m34_runtime_gadget_split_build.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/build_s22plus_m34_runtime_gadget_split.py \
  --force

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m34_s10a_module_load_beacon_live_gate.py
```

Result:

```text
M34 runtime-gadget split tests: Ran 5, OK
S10A full host build: OK
S10A default dry-run: OK
S10A live gate: rc=0, MISS, Magisk rollback clean
```
