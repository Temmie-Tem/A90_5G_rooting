# Native Init V1164 PM Proxy Binder Delta Classifier Plan

Date: `2026-05-27`

## Goal

Classify the V1163-after-V490 gap between late `pm-proxy` start and missing
`pm-service` `/dev/subsys_esoc0` open by comparing already captured native
evidence with Android-good V1159 evidence.

## Scope

- Host-only evidence comparison.
- Inputs:
  - `tmp/wifi/v1159-pm-thread-sampler-live-20260527-191019`
  - `tmp/wifi/v1163-late-per-proxy-esoc-live-after-v490/manifest.json`
  - `tmp/wifi/v1163-late-per-proxy-esoc-live-after-v490/summary.md`
- Output:
  - `tmp/wifi/v1164-pm-proxy-binder-delta-classifier/manifest.json`
  - `tmp/wifi/v1164-pm-proxy-binder-delta-classifier/summary.md`

## Safety

- No device command.
- No daemon start, Wi-Fi HAL, scan/connect, credential use, DHCP, route,
  external ping, partition write, boot image write, flash, or reboot.
- Do not write Wi-Fi credentials into evidence, docs, or commits.

## Success Criteria

- Android V1159 reference proves `vendor.per_proxy` is followed by
  `pm-service` Binder `mdm_subsys_powerup` and `/dev/subsys_esoc0`.
- Native V1163-after-V490 proves late `pm-proxy` started, PM client/server
  register/connect returned success, and `pm-service` still never opened
  `/dev/subsys_esoc0`.
- The classifier produces a concrete next gate for the final Wi-Fi objective.

## Failure Criteria

- Android reference lacks the positive PM/eSoC path.
- Native reference lacks V401/V490-preconditioned late `pm-proxy` start.
- Any evidence shows forbidden Wi-Fi HAL, credential, DHCP, external ping, or
  flash action.

## Expected Next Gate

If the classifier passes, V1165 should instrument the late `pm-proxy` window
more precisely: `pm-proxy` stdout/stderr/exit, PM server connect state/action
arguments, and a longer bounded post-connect poll window.
