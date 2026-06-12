# Native Init V2239 Scalar/Uprobe Timeline Contract

Date: `2026-06-12`

## Identity

| Field | Value |
| --- | --- |
| Run ID | `V2239` |
| Track | `T1 kernel observation` |
| Device baseline | `A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)` |
| Runner | `workspace/public/src/scripts/revalidation/a90_kernel_v2239_scalar_uprobe_timeline.py` |
| Private evidence | `workspace/private/runs/kernel/v2239-scalar-uprobe-timeline-20260612-105944/` |
| Device flash | no |
| Wi-Fi scan/connect/DHCP/ping | no |

## Track Selection

The north-star order in `GOAL.md` still selects T1 before T2. V2238 closed the
static tracepoint object-chain path: stock `cfg80211`, `msm_pil_event`, and DFC
records are useful scalar lifecycle records, not raw object-pointer anchors.

T1 remained safely actionable because the next useful unit was to preserve the
correct merge contract for future observers: scalar static tracepoints for
lifecycle correlation, helper-owned `a90*` uprobes for WLFW/QMI edge sequencing,
and exact-slide live-register sampling for code-path identity.

No track transition occurred. T2 WLAN work was not selected because this unit is
host-only and directly reduces future T1 capture ambiguity.

## Question

Can the existing V2229/V2231/V2233 helper-owned WLFW/QMI timelines and V2238
static tracepoint audit be merged into one reusable observer contract?

Specifically:

1. are the WLFW/QMI edge timings stable across the service-object runs;
2. does the V2233 `wlan0` success differ by WLFW/QMI order or by the later
   post-FW_READY `boot_wlan` / firmware-class tail;
3. should static tracepoints be used as object-chain dereference anchors or only
   as scalar lifecycle tags?

## Method

The runner performed host-only postprocessing. It read existing private summary
JSON and wrote a new private summary/timeline. It did not touch the device.

Inputs:

- `workspace/private/runs/kernel/v2229-live-20260612-080114/parser/summary.json`
- `workspace/private/runs/kernel/v2231-live-20260612-081302/parser/summary.json`
- `workspace/private/runs/kernel/v2233-live-20260612-083738/parser/summary.json`
- `workspace/private/runs/kernel/v2238-static-tracepoint-object-chain-audit-20260612-104909/summary.json`

Validation commands:

```text
python3 -m py_compile workspace/public/src/scripts/revalidation/a90_kernel_v2239_scalar_uprobe_timeline.py
python3 workspace/public/src/scripts/revalidation/a90_kernel_v2239_scalar_uprobe_timeline.py
```

## Result

Decision:

```text
v2239-scalar-uprobe-timeline-contract-pass
```

Output:

```text
workspace/private/runs/kernel/v2239-scalar-uprobe-timeline-20260612-105944/summary.json
workspace/private/runs/kernel/v2239-scalar-uprobe-timeline-20260612-105944/timeline.json
```

WLFW/QMI edge delta statistics across V2229, V2231, and V2233:

| Delta | Mean sec | Min sec | Max sec | Spread sec |
| --- | ---: | ---: | ---: | ---: |
| `wlfw_service_request - wlfw_start` | `0.025409` | `0.025115` | `0.025749` | `0.000634` |
| `libqmi_loop_client_init_ret - wlfw_service_request` | `60.469388` | `60.398058` | `60.513462` | `0.115404` |
| `wlfw_cap_qmi - wlfw_service_request` | `60.657840` | `60.581664` | `60.704848` | `0.123184` |
| `wlfw_bdf_entry - wlfw_cap_qmi` | `0.044804` | `0.044747` | `0.044882` | `0.000135` |
| `wlfw_worker_done_signal - wlfw_bdf_result_log` | `0.016044` | `0.015938` | `0.016162` | `0.000224` |

Per-run outcome:

| Run | Outcome |
| --- | --- |
| `V2229` | `observed-no-wlan0` |
| `V2231` | `observed-no-wlan0` |
| `V2233` | `wlan0-ready-fwclass-tail` |

V2238 static tracepoint audit carried into the contract:

| Metric | Value |
| --- | ---: |
| `cfg80211` source events/classes resolved as events | `162` |
| `dfc` events | `11` |
| `msm_pil_event` events | `3` |
| `record-pointer-chain-possible` events | `0` |
| `caller-pointer-record-scalarized` events | `159` |
| `caller-pointer-not-retained` events | `1` |
| `scalar-only` events | `16` |
| QRTR static trace definitions | `0` |

## Interpretation

The helper-owned WLFW/QMI edge sequence is stable across all three compared
runs. The long `wlfw_service_request` to `wlfw_cap_qmi` gap is consistently about
`60.66s`; the post-capability BDF and worker-done tail is sub-50ms and tightly
clustered.

V2233 reaching `wlan0-ready` is not explained by a different WLFW/QMI ordering.
Its distinguishing tail remains the post-FW_READY `boot_wlan` write plus the
kernel firmware-class feeder path documented in V2233. Therefore future T1
observers should not spend a new run re-proving WLFW start/service/cap/BDF order
unless a new capture changes this contract.

The static tracepoint side stays bounded by V2238: stock `cfg80211`, PIL, and DFC
trace records are scalar lifecycle tags. They do not retain raw object pointers
for `bpf_probe_read()` object-chain traversal. For object identity, use
exact-slide live-register sampling or a different anchor class.

## Contract

Use this merge contract for future boot-window observer runs:

1. helper-owned `a90cnss` / `a90libqmi` / `a90pmsrv` uprobes provide WLFW/QMI
   edge sequencing;
2. static `cfg80211`, `msm_pil_event`, DFC, and net-stack tracepoints provide
   scalar lifecycle correlation only;
3. exact-slide live-register sampling supplies code-path identity when function
   names are required;
4. object-chain dereference should not be attempted from the scalarized static
   tracepoint record itself.

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
