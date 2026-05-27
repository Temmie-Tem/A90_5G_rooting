# Native Init V1176 PM State3 Dependency Classifier Plan

Date: `2026-05-27`

## Goal

Classify why V1175 reaches PM-service state `3` after opening fd `8`, but still
does not open `/dev/subsys_esoc0`, publish mdm3/WLFW, or create `wlan0`.

## Inputs

- V1175 live evidence:
  `tmp/wifi/v1175-pm-ack-fd-target-live-after-v490/manifest.json`
- V1165 late `pm-proxy` actionability evidence:
  `tmp/wifi/v1165-late-per-proxy-actionability-live-after-v490/manifest.json`
- Android-good PM thread sampler evidence:
  `tmp/wifi/v1159-pm-thread-sampler-live-20260527-191019`
- Extracted vendor binary:
  `tmp/wifi/v1073-host-only/vendor-extract/files/pm-service`

## Method

V1176 is host-only:

1. Parse V1175 PM ack body events and fd-target samples.
2. Reconstruct the native PM ack invocation order.
3. Disassemble `pm-service+0x8788` state-transition body.
4. Check whether state `3` has any eSoC action path.
5. Check whether the state-2 dependency branch was skipped by a zero dependency
   flag.
6. Compare the result to Android-good evidence where `pm-service` reaches
   `__subsystem_get(esoc0)`.

## Success Criteria

- Manifest decision is `v1176-dependency-flag-state-order-gap-classified` or a
  precise input-incomplete label.
- No device command is executed.
- No PM actor, `mdm_helper`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes,
  external ping, boot image write, partition write, or flash is executed.
- The next live gate is narrowed to PM dependency flag/state-order parity rather
  than another broad PM actor retry.

## Expected Branch

If V1175 state `3` is a no-op and state `2` skipped the dependency path because
the dependency flag was zero, V1177 should trace the state-0 dependency flag
setter and Android/native PM state order before attempting any broader Wi-Fi
bring-up.
