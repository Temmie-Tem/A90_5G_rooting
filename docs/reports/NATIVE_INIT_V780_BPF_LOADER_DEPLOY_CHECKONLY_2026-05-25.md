# Native Init V780 BPF Loader Deploy Check-Only Report

## Result

- decision: `v780-bpf-loader-deploy-checkonly-pass`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_bpf_loader_deploy_checkonly_v780.py`
- evidence: `tmp/wifi/v780-bpf-loader-deploy-checkonly/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_bpf_loader_deploy_checkonly_v780.py
python3 scripts/revalidation/native_wifi_bpf_loader_deploy_checkonly_v780.py plan
python3 scripts/revalidation/native_wifi_bpf_loader_deploy_checkonly_v780.py \
  --allow-serial-deploy \
  --assume-yes \
  run
```

## Evidence Summary

| Signal | Value |
| --- | --- |
| local helper | `tmp/wifi/v779-bpf-loader-build/a90_bpf_trace_probe-aarch64-static` |
| remote helper | `/cache/bin/a90_bpf_trace_probe` |
| expected sha256 | `9d8fdfeaa9281ba814db62ddc588b37959021d68fbd08164ae366dde3f08b1c3` |
| remote sha256 | `9d8fdfeaa9281ba814db62ddc588b37959021d68fbd08164ae366dde3f08b1c3` |
| transfer method | serial `appendfile + uudecode` |
| serial chunks | `458/458` |
| serial chunk size | `1800` bytes |
| max cmdv1 line | `3778` bytes |
| safety line limit | `3968` bytes |
| encoded bytes | `823863` |

Both execution modes remained non-attach:

| Mode | Marker | Result | Attach |
| --- | --- | --- | --- |
| `--check-only` | `a90_bpf_trace_probe v779` | `result=check-only` | `attach_attempted=0` |
| default | `a90_bpf_trace_probe v779` | `result=check-only` | `attach_attempted=0` |

## Interpretation

V780 proves the reviewed V779 helper can be deployed and executed on the stock
v724 native environment without attempting BPF attach. This closes the binary
delivery and default-mode safety gate. It does not prove that tracepoint BPF
attach is accepted by the kernel; that remains a separate V781 gate.

The first live run exposed two deploy harness constraints, both fixed before the
passing run:

1. `appendfile` refuses staging directly under `/cache/bin`; V780 now stages in
   `/cache/a90-runtime/bin`.
2. `1900` byte serial chunks exceeded the conservative cmdv1x line margin on
   this path; V780 now caps chunks at `1800` bytes.

## Safety

- BPF attach: not executed
- `--allow-attach`: not passed
- ftrace control write: not executed
- Wi-Fi HAL/service-manager start: not executed
- Wi-Fi scan/connect/link-up: not executed
- credential use: not executed
- DHCP/routes/external ping: not executed
- reboot/flash/partition write: not executed

## Next

V781 may be planned as a separate bounded idle attach/detach proof for
`msm_pil_event:pil_notif`. It should still avoid modem/WLAN triggers, Wi-Fi
scan/connect, DHCP, routes, external ping, reboot, flash, and partition writes.
