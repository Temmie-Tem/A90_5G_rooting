# Native Init V1413 Wi-Fi Test Boot Handoff

## Summary

- Cycle: `V1413`
- Type: bounded live test-boot handoff with rollback
- Decision: `v1413-test-boot-downstream-progress-rollback-pass`
- Result: PASS
- Reason: test boot produced downstream Wi-Fi/PCIe evidence and rollback verified
- Evidence: `tmp/wifi/v1413-wifi-test-boot-kmsg-fallback-handoff`
- Handoff/rollback pass: `True`
- Strict Wi-Fi progress mode: `True`
- Wi-Fi progress pass: `True`
- Progress decision: `rc1-ltssm-link-failed-no-l0`

## Progress Classification

- `provider_trigger`: `True`
- `rc1_progress`: `True`
- `rc1_l0`: `False`
- `rc1_link_failed`: `True`
- `mhi_progress`: `False`
- `wlfw_progress`: `False`
- `bdf_progress`: `False`
- `fw_ready_progress`: `False`
- `wlan0_present`: `False`
- `connect_ready`: `False`
- `debugfs_pci_msm_case_present`: `1`
- `helper_timed_out`: `1`
- `pid1_rc1_watcher_requested`: `1`
- `pid1_rc1_watcher_result_summary`: `state=triggered source=/proc/kmsg write_rc=0 errno=0 elapsed_ms=7427 line=<3>[ 9.109508] [3: cnss-daemon: 598] __netlink_sendskb(1245) skb:000000000a272229 queued sk: 00000000fac39465 <3`
- `pid1_rc1_watcher_result_file`: `state=triggered source=/proc/kmsg write_rc=0 errno=0 elapsed_ms=7427 line=<3>[    9.109508]  [3:    cnss-daemon:  598] __netlink_sendskb(1245) skb:000000000a272229 queued sk: 00000000fac39465`

## Timing Notes

- `esoc0`: `9.163220s`
- `TEST: 11`: `9.195302s`
- `esoc0_to_test11`: about `0.032s`
- Android reference `esoc0_to_assert`: about `0.255s`
- Interpretation: the `/proc/kmsg` fallback fixed the watcher execution path,
  but the trigger is now earlier than Android's reference window and still
  fails in LTSSM poll/compliance before L0.

## Safety Scope

No Wi-Fi scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, or blind eSoC notify/`BOOT_DONE` spoof was
performed by this runner.
Device mutation was limited to flashing the test boot image and
rolling back to `stage3/boot_linux_v724.img`.

## Images

- Test image: `tmp/wifi/v1411-wifi-test-boot-kmsg-fallback/boot_linux_v1411_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Next

V1414 should be source/build-only: add a configurable PID1 RC1 watcher delay
after the first `esoc0`/powerup marker, initially using the Android-derived
`250ms` window, then rebuild and sanity-check before any rollbackable live
handoff. Do not proceed to scan/connect, credentials, DHCP/routes, or external
ping until at least MHI/WLFW/`wlan0` progress is proven.
