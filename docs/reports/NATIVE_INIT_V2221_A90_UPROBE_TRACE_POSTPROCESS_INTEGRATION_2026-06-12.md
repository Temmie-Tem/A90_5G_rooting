# Native Init V2221 A90 Uprobe Trace Postprocess Integration

## Result

- decision: `v2221-collector-parser-integrated-current-window-nohit`
- pass: `true`
- runner: `workspace/public/src/scripts/revalidation/native_kernel_a90_uprobe_trace_postprocess_v2221.py`
- evidence: `workspace/private/runs/kernel/v2221-a90-uprobe-trace-postprocess-20260612-065218/`
- collector evidence: `workspace/private/runs/kernel/v2221-current-window-collector-20260612-065218/`
- parser evidence: `workspace/private/runs/kernel/v2221-a90-uprobe-trace-postprocess-20260612-065218/v2220-parser/`
- selftest: `fail=0`

## What Ran

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_kernel_v2220_helper_summary_trace_parser.py \
  workspace/public/src/scripts/revalidation/native_kernel_a90_uprobe_trace_postprocess_v2221.py
PYTHONPATH=workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/native_kernel_a90_uprobe_trace_postprocess_v2221.py
```

The wrapper ran the V2219 current-window trace-buffer collector, then parsed the
new collector `summary.json` with the V2220 parser using `--allow-nohit`.

The run did not create/enable tracefs events, attach BPF, execute
`probe_write_user`, scan/connect Wi-Fi, change routes, reboot, flash, or write
partitions.

## Evidence Summary

| Signal | Value |
| --- | ---: |
| collector decision | `v2219-a90-uprobe-trace-buffer-ready-current-window-nohit` |
| parser decision | `v2220-helper-summary-parser-nohit-allowed` |
| `a90*` events present | `21` |
| `a90*` events enabled | `21` |
| current-window collector hits | `0` |
| parser normalized events | `21` |
| parser hit events | `0` |
| selftest | `fail=0` |

Artifacts linked by the wrapper:

- collector summary: `workspace/private/runs/kernel/v2221-current-window-collector-20260612-065218/summary.json`
- parser summary: `workspace/private/runs/kernel/v2221-a90-uprobe-trace-postprocess-20260612-065218/v2220-parser/summary.json`
- wrapper summary: `workspace/private/runs/kernel/v2221-a90-uprobe-trace-postprocess-20260612-065218/summary.json`

## Interpretation

V2221 proves the artifact contract that was missing after V2219:

1. the current-window collector can still verify the active `a90*` event set;
2. the collector summary can be passed directly into the V2220 parser;
3. no-hit current-window output is represented as a successful parsed state
   when `--allow-nohit` is intentional;
4. future boot-window helper runs can reuse the same wrapper/postprocessor path
   without reintroducing BPF attach on dynamic `a90*` trace_uprobe events.

The no-hit result remains expected for this late idle window. It is not evidence
against boot-window WLFW/QMI activity; V2220 already validated the parser on
existing boot-window helper artifacts with `wlfw_start`, `wlfw_service_request`,
`wlfw_cap_qmi`, and `wlfw_bdf_entry` hits.

## Next

V2222 should prepare the approved boot-window execution wrapper around this
same contract:

1. run the helper-owned `a90*` uprobe registration/collection route in the
   early WLFW/QMI window;
2. feed the resulting helper summary or trace-buffer artifact into the V2220
   parser;
3. compare the parsed `wlfw_start → wlfw_service_request → cap_req → BDF`
   sequence against stock kernel observer state;
4. keep `a90*` BPF attach disabled and use stock BPF only for static kernel
   tracepoints when needed.
