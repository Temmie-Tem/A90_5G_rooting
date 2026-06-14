# Native Init v160-v169 Stability Cycle Completion Audit (2026-05-09)

## Objective

Complete `docs/plans/NATIVE_INIT_V160_V169_STABILITY_ROADMAP_2026-05-09.md`
using the normal development loop: plan each step, run bounded real-device or
host-side validation, document results, commit each step, and move the next queue
item forward.

## Verdict

- status: PASS
- latest boot image remains: `A90 Linux init 0.9.59 (v159)`
- v160-v169 were stability/feasibility validations against the v159 runtime, not boot-image feature bumps.
- v166 is intentionally `DEFERRED` because host NCM IP assignment requires local sudo/operator setup.
- next execution item: v170+ Wi-Fi Baseline Refresh

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Roadmap exists | `docs/plans/NATIVE_INIT_V160_V169_STABILITY_ROADMAP_2026-05-09.md` | PASS |
| v160 plan/report | `docs/plans/NATIVE_INIT_V160_NCM_TCP_STABILITY_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V160_NCM_TCP_STABILITY_2026-05-09.md` | PASS |
| v161 plan/report | `docs/plans/NATIVE_INIT_V161_STORAGE_IO_INTEGRITY_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V161_STORAGE_IO_INTEGRITY_2026-05-09.md` | PASS |
| v162 plan/report | `docs/plans/NATIVE_INIT_V162_PROCESS_CONCURRENCY_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V162_PROCESS_CONCURRENCY_2026-05-09.md` | PASS |
| v163 plan/report | `docs/plans/NATIVE_INIT_V163_CPU_MEM_THERMAL_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V163_CPU_MEM_THERMAL_2026-05-09.md` | PASS |
| v164 plan/report | `docs/plans/NATIVE_INIT_V164_SCHED_LATENCY_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V164_SCHED_LATENCY_2026-05-09.md` | PASS |
| v165 plan/report | `docs/plans/NATIVE_INIT_V165_USB_RECOVERY_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V165_USB_RECOVERY_2026-05-09.md` | PASS |
| v166 plan/deferred report | `docs/plans/NATIVE_INIT_V166_NETWORK_THROUGHPUT_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md` | PASS |
| v167 plan/report | `docs/plans/NATIVE_INIT_V167_FS_EXERCISER_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V167_FS_EXERCISER_2026-05-09.md` | PASS |
| v168 plan/report | `docs/plans/NATIVE_INIT_V168_KSELFTEST_FEASIBILITY_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V168_KSELFTEST_FEASIBILITY_2026-05-09.md` | PASS |
| v169 plan/report | `docs/plans/NATIVE_INIT_V169_FAULT_DEBUG_FEASIBILITY_PLAN_2026-05-09.md`, `docs/reports/NATIVE_INIT_V169_FAULT_DEBUG_FEASIBILITY_2026-05-09.md` | PASS |
| Queue updated | `docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md` lists v160-v169 done/deferred and next v170 | PASS |
| Next work updated | `docs/plans/NATIVE_INIT_NEXT_WORK_2026-04-25.md` points to v170+ Wi-Fi baseline refresh | PASS |
| README updated | `README.md` includes v160-v169 stability evidence summary | PASS |

## Real Evidence

| Version | Evidence | Result |
|---|---|---|
| v160 NCM/TCP | `tmp/soak/v159-ncm-tcp-20260509-001148/ncm-tcp-stability-report.json` | PASS, 3602.5s, 360 cycles, failures 0 |
| v161 Storage I/O | `tmp/soak/v161-storage-20260509-012156/storage-iotest-report.json` | PASS, 4K/64K/1M/16M hash/rename/sync/unlink |
| v162 Process/Concurrency | `tmp/soak/process-concurrency/v162-process-20260509-013720/process-concurrency-report.json` | PASS, helper churn 32/32, tcpctl parallel 18/18, zombies 0 |
| v163 CPU/Mem/Thermal | `tmp/soak/cpu-mem-thermal/v163-cpu-mem-thermal-20260509-014606/cpu-mem-thermal-report.json` | PASS, 5 cycles, tmpfs 32MiB verify, max CPU 43.1C |
| v164 Scheduler/Latency | `tmp/soak/scheduler-latency/v164-sched-latency-20260509-015147/scheduler-latency-report.json` | PASS, p99 101-102ms, missed deadlines 0 |
| v165 USB Recovery | `tmp/soak/usb-recovery/v165-usb-recovery-20260509-015633/usb-recovery-report.json` | PASS, recovered 5/5, final ACM-only |
| v165 Sensor Supplement | `tmp/soak/usb-recovery/v165-usb-recovery-sensor-20260509-021853/longsoak-before.txt`, `longsoak-after.txt` | PASS, longsoak health=ok before/after USB re-enumeration |
| v166 Network Throughput | `docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md` | DEFERRED, host NCM setup requires local sudo/operator setup |
| v167 FS Exerciser | `tmp/soak/fs-exerciser/v167-fsx-20260509-020232/fs-exerciser-report.json` | PASS, 64 ops, failed_records 0, cleanup PASS |
| v168 Kselftest Feasibility | `tmp/soak/kselftest-feasibility/v168-kselftest-20260508T171140Z/kselftest-feasibility-report.json` | PASS, safe 4, conditional/unknown 5, blocked 6, mutation false |
| v169 Fault/Debug Feasibility | `tmp/soak/fault-debug-feasibility/v169-fault-debug-20260508T171514Z/fault-debug-feasibility-report.json` | PASS, mandatory 8/8, fault/LKDTM/watchdog/raw blocked |

## Roadmap Completion Criteria

| Criterion | Evidence | Result |
|---|---|---|
| Each v160-v169 has plan/report pair or documented deferral | file existence audit for all v160-v169 entries | PASS |
| Every boot image change is real-device flash verified before README promotion | no v160-v169 boot image bump; README still lists latest verified boot image `stage3/boot_linux_v159.img` | PASS |
| Stress helpers are bounded and constrained | v160 duration/cycles, v161 size set, v162 op counts, v163 cycles, v164 sample count, v165 cycles, v167 op count documented | PASS |
| Storage writes stay in safe paths | v161 `/mnt/sdext/a90/test-io`, v167 `/mnt/sdext/a90/test-fsx` reports | PASS |
| Longsoak or equivalent sensor logging accompanies network/storage/CPU/USB tests | v160/v161/v163 reports include longsoak; v165 supplemental before/after longsoak evidence added | PASS |
| Feasibility tests remain read-only | v168/v169 reports record `mutation_performed=False` and hard-block risky paths | PASS |
| Final v169 decides next track | task queue and next-work docs point to v170+ Wi-Fi baseline refresh | PASS |

## Static Validation

```text
python3 -m py_compile \
  scripts/revalidation/process_concurrency_validate.py \
  scripts/revalidation/cpu_mem_thermal_stability.py \
  scripts/revalidation/scheduler_latency_baseline.py \
  scripts/revalidation/usb_recovery_validate.py \
  scripts/revalidation/storage_iotest.py \
  scripts/revalidation/fs_exerciser_mini.py \
  scripts/revalidation/kselftest_feasibility.py \
  scripts/revalidation/fault_debug_feasibility.py

git diff --check
```

Result: PASS.

## Commits

```text
d77e58e Validate v160 NCM TCP stability
45215b9 Validate v161 storage IO integrity
c085fed Validate v162 process concurrency
7e63134 Validate v163 CPU memory thermal stability
75b5a3f Validate v164 scheduler latency baseline
b5a08f3 Validate v165 USB recovery stability
19daf49 Defer v166 network throughput pending host NCM
6f254fb Validate v167 filesystem exerciser mini
e4f64e7 Validate v168 kselftest feasibility
e5d6e57 Validate v169 fault debug feasibility
b81bfd7 Document v165 longsoak recovery evidence
```

## Remaining Gaps

- v166 throughput is intentionally not measured until the host NCM interface is configured with local sudo/operator setup.
- True cyclictest-style in-process latency remains future helper work; v164 is a PID1 run/cmdv1 latency proxy.
- Full LTP/kselftest execution remains blocked. Only bounded helper candidates should be considered next.

## Next

- v170+ Wi-Fi Baseline Refresh.
- v171+ Network Exposure Hardening before any non-USB-local control path.
