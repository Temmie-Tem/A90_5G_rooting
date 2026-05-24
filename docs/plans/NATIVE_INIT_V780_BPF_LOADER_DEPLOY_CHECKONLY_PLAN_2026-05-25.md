# Native Init V780 BPF Loader Deploy Check-Only Plan

## Goal

Deploy the reviewed V779 static BPF tracepoint helper to the recovered stock
v724 native init environment and prove only non-attach execution paths.

## Scope

- local artifact: `tmp/wifi/v779-bpf-loader-build/a90_bpf_trace_probe-aarch64-static`
- remote artifact: `/cache/bin/a90_bpf_trace_probe`
- expected sha256: `9d8fdfeaa9281ba814db62ddc588b37959021d68fbd08164ae366dde3f08b1c3`
- run mode: serial `appendfile + uudecode` deploy using `/cache/a90-runtime/bin` staging, then `--check-only` and default execution
- serial safety: default chunk size is capped at 1800 bytes so encoded cmdv1x lines remain below the native console safety margin

## Safety Contract

- no `--allow-attach`
- no BPF attach
- no ftrace control writes
- no Wi-Fi HAL/service-manager start
- no Wi-Fi scan/connect/link-up
- no credential use
- no DHCP, route changes, or external ping
- no reboot, flash, boot partition write, or custom kernel retry

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_bpf_loader_deploy_checkonly_v780.py
python3 scripts/revalidation/native_wifi_bpf_loader_deploy_checkonly_v780.py plan
python3 scripts/revalidation/native_wifi_bpf_loader_deploy_checkonly_v780.py \
  --allow-serial-deploy \
  --assume-yes \
  run
```

## Success Criteria

- V779 input manifest is `v779-bpf-loader-build-pass`.
- Local helper sha256 matches the expected reviewed artifact.
- Remote helper sha256 matches the expected reviewed artifact after deploy.
- `a90_bpf_trace_probe --check-only` prints the V779 marker and `attach_attempted=0`.
- `a90_bpf_trace_probe` with no arguments remains default check-only and prints `attach_attempted=0`.

## Next

If V780 passes, V781 can be planned as a separate bounded idle tracepoint attach
proof for `msm_pil_event:pil_notif`. V781 must remain independent from Wi-Fi
scan/connect and from any modem/WLAN trigger.
