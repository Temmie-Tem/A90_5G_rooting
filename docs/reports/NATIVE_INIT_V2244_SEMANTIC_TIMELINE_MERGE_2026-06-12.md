# Native Init V2244 Semantic Timeline Merge

Date: `2026-06-12`

## Identity

| Field | Value |
| --- | --- |
| Run ID | `V2244` |
| Track | `T1 kernel observation` |
| Device baseline | `A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)` |
| Runner | `workspace/public/src/scripts/revalidation/a90_kernel_v2244_semantic_timeline_merger.py` |
| Private evidence | `workspace/private/runs/kernel/v2244-semantic-timeline-merge-20260612-113706/` |
| Device flash | no |
| Wi-Fi scan/connect/DHCP/ping | no |

## Track Selection

T1 remains the highest meaningful track. V2239 established the helper-owned
WLFW/QMI timeline contract, and V2243 added public semantic confidence for those
helper-owned user-space probes. The next bounded unit was to merge those two
contracts and decide whether the semantic WLFW/QMI edge set distinguishes the
V2233 `wlan0-ready` run from the V2229/V2231 `no-wlan0` runs.

No track transition occurred. T2 WLAN work was not selected because this unit is
host-only and directly reduces future T1 observer ambiguity.

## Question

When V2239 WLFW/QMI edge coverage is annotated with V2243 semantic confidence,
does the successful V2233 run differ from V2229/V2231 in helper-owned WLFW/QMI
edge presence or semantic strength?

## Method

The runner:

1. read V2239 `summary.json` and `timeline.json`;
2. read V2243 public semantic summary;
3. joined each V2239 edge to its V2243 semantic row by event name;
4. classified each edge as `strong`, `marker`, `weak`, or `missing_semantics`;
5. compared edge sets and semantic signatures across V2229, V2231, and V2233;
6. wrote a public-safe merged semantic timeline with no raw bytes or raw
   disassembly.

Inputs:

- `workspace/private/runs/kernel/v2239-scalar-uprobe-timeline-20260612-105944/summary.json`
- `workspace/private/runs/kernel/v2239-scalar-uprobe-timeline-20260612-105944/timeline.json`
- `workspace/private/runs/kernel/v2243-user-uprobe-semantic-classifier-20260612-113113/summary.json`

Validation commands:

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/a90_kernel_v2244_semantic_timeline_merger.py
python3 workspace/public/src/scripts/revalidation/a90_kernel_v2244_semantic_timeline_merger.py
```

## Result

Decision:

```text
v2244-semantic-timeline-merge-pass
```

Coverage:

| Metric | Value |
| --- | ---: |
| run count | `3` |
| edge observations | `27` |
| semantic coverage | `27` |
| weak edges | `0` |
| missing semantic edges | `0` |

Strength distribution:

| Strength | Count |
| --- | ---: |
| `strong` | `12` |
| `marker` | `15` |

Per-run summary:

| Run | Outcome | Edges | Strong | Marker | Weak | Missing semantics |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `v2229` | `observed-no-wlan0` | `9` | `4` | `5` | `0` | `0` |
| `v2231` | `observed-no-wlan0` | `9` | `4` | `5` | `0` | `0` |
| `v2233` | `wlan0-ready-fwclass-tail` | `9` | `4` | `5` | `0` | `0` |

Common semantic edge set:

| Event | Interpretation |
| --- | --- |
| `wlfw_start` | strong entry evidence |
| `wlfw_service_request` | marker protocol edge |
| `libqmi_loop_client_init_ret` | strong post-call/result evidence |
| `wlfw_cap_qmi` | marker protocol edge |
| `wlfw_bdf_entry` | strong entry evidence |
| `wlfw_bdf_send_ret` | strong post-call/result evidence |
| `wlfw_bdf_result_log` | marker log/result edge |
| `wlfw_worker_done_signal` | marker signal edge |
| `wlfw_worker_post_done_wait` | marker wait edge |

Outcome comparison:

| Check | Result |
| --- | --- |
| edge sets identical across runs | yes |
| semantic signatures identical across runs | yes |
| semantic WLFW/QMI edges distinguish `wlan0-ready` | no |

Output:

```text
workspace/private/runs/kernel/v2244-semantic-timeline-merge-20260612-113706/summary.json
workspace/private/runs/kernel/v2244-semantic-timeline-merge-20260612-113706/semantic_timeline.json
```

The merged timeline is public-safe metadata. It does not include raw bytes or raw
disassembly.

## Interpretation

V2244 strengthens the V2239 conclusion: the helper-owned WLFW/QMI sequence is not
the differentiator between the V2229/V2231 no-`wlan0` runs and the V2233
`wlan0-ready` run.

All three runs share:

- the same nine helper-owned WLFW/QMI edges;
- the same semantic strength pattern: four strong edges and five marker edges;
- no weak or missing semantic rows.

Therefore, a future T1 live observer should not spend another iteration
re-proving WLFW/QMI order. If live code-path identity is needed, the next
specific target is the downstream post-FWREADY tail: `boot_wlan` /
firmware-class / qcacld/HDD path, using exact-slide kernel PC/LR sampling or
other non-mutating read paths.

## Decision

Use this contract for future observer selection:

1. treat WLFW/QMI helper-owned edge order as stable across V2229/V2231/V2233;
2. use V2244 semantic strength to distinguish hard call/entry evidence from
   marker-only edges;
3. do not repeat WLFW/QMI order captures unless new evidence contradicts this
   contract;
4. focus new live T1 sampling on the post-FWREADY `boot_wlan` /
   firmware-class tail if code-path identity is needed.

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
