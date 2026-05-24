# Native Init V778 BPF Attach Feasibility Plan

## Goal

Classify whether the V777 target can move directly to a bounded BPF tracepoint
attach proof, or whether a custom loader build gate is required first.

## Inputs

- V777 report: `docs/reports/NATIVE_INIT_V777_TRACEPOINT_FORMAT_CLASSIFIER_2026-05-25.md`
- V777 evidence: `tmp/wifi/v777-tracepoint-format-classifier/manifest.json`
- selected target: `msm_pil_event:pil_notif`

## Rules

- No BPF attach in V778.
- No trace control writes, Wi-Fi trigger, service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, reboot, boot image write, or partition write.
- Check only existing device loaders, kernel sysctls, tracefs presence, and host build surface.

## Success Criteria

- Manifest identifies whether `bpftool`/`bpftrace` already exists on device.
- Manifest records `perf_event_paranoid` and `unprivileged_bpf_disabled`.
- Manifest records whether host can build a static aarch64 C helper with BPF/perf headers.
- Next gate is either existing-loader review or custom-loader build. Attach proof remains blocked until one of those exists.
