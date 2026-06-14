# Native Init V2240 Code-Path Identity Boundary

Date: `2026-06-12`

## Identity

| Field | Value |
| --- | --- |
| Run ID | `V2240` |
| Track | `T1 kernel observation` |
| Device baseline | `A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)` |
| Runner | `workspace/public/src/scripts/revalidation/a90_kernel_v2240_codepath_identity_boundary.py` |
| Private evidence | `workspace/private/runs/kernel/v2240-codepath-identity-boundary-20260612-110740/` |
| Device flash | no |
| Wi-Fi scan/connect/DHCP/ping | no |

## Track Selection

T1 remains the highest meaningful track. V2239 established the merge contract:
static tracepoints are scalar lifecycle tags, helper-owned `a90*` uprobes provide
WLFW/QMI edge sequencing, and exact-slide live-register sampling provides kernel
code-path identity.

The remaining ambiguity was the identity boundary itself: whether V2216/V2217
kernel exact-slide symbolization should be applied to `a90*` `__probe_ip` values
from the V2229/V2231/V2233 helper-owned trace lines.

No track transition occurred. T2 WLAN work was not selected because T1 had a
safe host-only interpretation boundary to close before adding new observer
complexity.

## Question

Are helper-owned `a90cnss`, `a90libqmi`, and `a90pmsrv` `__probe_ip` values
kernel addresses that should be symbolized with the V2216/V2217 kernel exact
slide, or user-space addresses that need a different identity model?

## Method

The runner performed host-only postprocessing over existing private summaries:

- `workspace/private/runs/kernel/v2229-live-20260612-080114/parser/summary.json`
- `workspace/private/runs/kernel/v2231-live-20260612-081302/parser/summary.json`
- `workspace/private/runs/kernel/v2233-live-20260612-083738/parser/summary.json`
- `workspace/private/runs/kernel/v2217-exact-slide-resymbolization-audit/result.json`
- `workspace/private/runs/kernel/v2239-scalar-uprobe-timeline-20260612-105944/summary.json`

For each first-hit `a90*` timeline record, the runner extracted the parenthesized
probe IP, classified the virtual address domain, and tested whether `a90cnss`
events retain a stable relative offset signature across the three compared
boot-window runs.

Validation commands:

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/a90_kernel_v2240_codepath_identity_boundary.py
python3 workspace/public/src/scripts/revalidation/a90_kernel_v2240_codepath_identity_boundary.py
```

## Result

Decision:

```text
v2240-codepath-identity-boundary-pass
```

Address-domain counts:

| Domain | Samples |
| --- | ---: |
| `user_pie_executable` | `267` |
| `user_shared_library` | `57` |
| `kernel_canonical` | `0` |

Group counts:

| Group | Samples |
| --- | ---: |
| `a90cnss` | `228` |
| `a90libqmi` | `57` |
| `a90pmsrv` | `39` |

Kernel exact-slide context:

| Field | Value |
| --- | --- |
| V2217 exact slide | `0x84ef4` |
| Source decision | `v2217-live-resymbolized-ropp-still-ambiguous` |
| Applies to | kernel canonical PC/LR samples, kernel function-pointer anchors, stock kernel addresses from BPF/perf read paths |
| Does not apply to | `a90cnss`/`a90libqmi`/`a90pmsrv` user-space trace-uprobe `__probe_ip`, scalar-only static tracepoint records |

Stable `a90cnss` relative signature, anchored at `wlfw_start`:

| Event | Delta from `wlfw_start` | Low 12 bits | Runs | Stable |
| --- | ---: | ---: | ---: | --- |
| `wlfw_start` | `0x0` | `0xc00` | `3` | yes |
| `wlfw_service_request` | `-0x1204` | `0x9fc` | `3` | yes |
| `wlfw_cap_qmi` | `0x860` | `0x460` | `3` | yes |
| `wlfw_bdf_entry` | `0xb6c` | `0x76c` | `3` | yes |
| `wlfw_bdf_send_ret` | `0x1048` | `0xc48` | `3` | yes |
| `wlfw_bdf_result_log` | `0x1108` | `0xd08` | `3` | yes |
| `wlfw_worker_done_signal` | `-0xc08` | `0xff8` | `3` | yes |
| `wlfw_worker_post_done_wait` | `-0xb90` | `0x70` | `3` | yes |

Additional stable user-space signatures:

| Event | Domain | Low 12 bits | Runs | Stable |
| --- | --- | ---: | ---: | --- |
| `a90libqmi:libqmi_loop_client_init_ret` | `user_shared_library` | `0x944` | `3` | yes |
| `a90pmsrv:pm_service_main_supported_list_init` | `user_pie_executable` | `0x7bc` | `3` | yes |

## Interpretation

The `a90*` `__probe_ip` values are not kernel addresses. They are user-space
instruction pointers from the probed process mappings:

- `a90cnss` and `a90pmsrv` samples land in PIE executable ranges;
- `a90libqmi` samples land in shared-library ranges;
- no helper-owned `a90*` probe IP in the compared boot-window summaries lands in
  the kernel canonical address range.

Therefore subtracting the kernel KASLR slide from `a90*` probe IP values would
be incorrect. V2216/V2217 exact-slide symbolization remains valid for kernel
PC/LR samples and kernel function-pointer anchors, but not for these user-space
trace-uprobe records.

The `a90cnss` event sequence still has stable code-path identity: event names
plus relative offsets from `wlfw_start` are identical across V2229, V2231, and
V2233. This is the correct identity model for the current WLFW/QMI helper-owned
trace data.

## Decision

Use this boundary for future observers:

1. apply V2216/V2217 exact slide only to kernel canonical addresses;
2. do not apply kernel System.map or kernel slide to `a90*` user-space
   `__probe_ip`;
3. use `a90*` event name plus stable relative offset signature for WLFW/QMI
   code-path identity;
4. if finer user-space symbol names are needed, build a user-ELF ASLR/base mapper
   for `cnss-daemon`, `pm-service`, and libqmi rather than extending the kernel
   slide solver.

## Safety

- `host_only`: true.
- `device_io`: false.
- `bpf_attach`: false.
- `tracefs_control_write`: false.
- `probe_write_user_executed`: false.
- `wifi_scan_connect`: false.
- `network_route_change`: false.
- `flash_reboot`: false.
- `partition_write`: false.
- public output contains only metadata and summary values; private raw artifacts
  remain under `workspace/private/`.
