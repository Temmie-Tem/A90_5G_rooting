# Native Init V1417 RC1 Semantics Classifier

## Summary

- Cycle: `V1417`
- Type: host-only RC1 semantics classifier
- Decision: `v1417-delayed-rc1-timing-aligned-test11-semantics-gap`
- Result: PASS for classification; still BLOCKED for Wi-Fi connect readiness
- Reason: V1416 aligns corrected RC1 timing with Android within 50ms, but the test-boot debugfs TEST:11 path still lacks Android reset/release markers and fails before L0.
- Evidence: `tmp/wifi/v1417-rc1-semantics-classifier`

## Timing Comparison

| Path | esoc0→trigger | reset/release markers | L0 | link fail |
|---|---:|---|---|---|
| Android reference | 0.254929s | assert+release present | yes | no |
| V1413 immediate kmsg watcher | 0.032082s | not required for this classifier | no | yes |
| V1416 delayed kmsg watcher | 0.275121s | absent | no | yes |

## Classification

- `v1416_trigger_error_vs_android_sec`: `0.020192`
- `v1416_timing_aligned_with_android_50ms`: `True`
- `v1416_test_path_lacks_reset_markers`: `True`
- `v1416_link_failed_no_l0`: `True`
- `v1416_test11_to_phy_ready_sec`: `0.005814`
- `v1416_test11_to_link_failed_sec`: `0.11479`

V1416 removes the major timing objection from V1413: the corrected RC1
action now lands close to the Android reference window. The remaining
difference is that Android's normal path contains explicit endpoint
reset/release markers and reaches L0/GEN2, while the test-boot debugfs
`TEST: 11` path reaches PHY/LTSSM but stalls in poll-compliance.

## Safety Scope

This cycle is host-only. It executes no device command, flash, Wi-Fi
scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC write, or blind eSoC notify/`BOOT_DONE` spoof.

## Next

V1418 should be source/host-only: inspect the stock msm_pcie debugfs TEST:11 path against Android's normal RC1 bring-up path and decide whether the next test boot needs a different RC1 trigger, not another blind delay retry.
