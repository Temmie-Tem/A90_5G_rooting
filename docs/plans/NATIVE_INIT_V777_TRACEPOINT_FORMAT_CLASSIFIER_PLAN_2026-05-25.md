# Native Init V777 Tracepoint Format Classifier Plan

## Goal

Classify selected V776 tracepoint candidates by reading only their `format` and
`id` files, before any BPF attach proof.

## Inputs

- V776 report: `docs/reports/NATIVE_INIT_V776_TRACEPOINT_INVENTORY_2026-05-25.md`
- V776 evidence: `tmp/wifi/v776-tracepoint-inventory/manifest.json`
- live native bridge on recovered `A90 Linux init 0.9.68 (v724)`

## Rules

- Stock v724 only; no custom kernel flash.
- Temporary tracefs mount/read/cleanup is allowed only with explicit gate flags.
- Read only selected `format` and `id` files.
- No trace control writes, BPF attach, `boot_wlan`, `qcwlanstate`, service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, reboot, boot image write, or partition write.

## Targets

- `msm_pil_event:pil_event`
- `msm_pil_event:pil_notif`
- `msm_pil_event:pil_func`
- `dfc:dfc_qmi_tc`
- `cfg80211:cfg80211_report_wowlan_wakeup`

## Success Criteria

- Evidence is written privately under `tmp/wifi/v777-tracepoint-format-classifier/`.
- Manifest proves no BPF attach, Wi-Fi action, credential use, network route change, external ping, reboot, flash, or partition write.
- Each selected tracepoint has readable `format` or is explicitly classified as unavailable.
- If event-specific fields are useful, V778 can plan a single bounded BPF tracepoint attach proof against the lowest-risk candidate.
