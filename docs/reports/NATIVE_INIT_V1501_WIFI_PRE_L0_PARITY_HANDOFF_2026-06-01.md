# Native Init V1501 Wi-Fi Test Boot Handoff

## Summary

- Cycle: `V1501`
- Type: bounded live test-boot handoff with rollback
- Decision: `v1501-test-boot-downstream-progress-rollback-pass`
- Result: PASS
- Reason: test boot produced downstream Wi-Fi/PCIe evidence and rollback verified
- Evidence: `tmp/wifi/v1501-wifi-pre-l0-parity-handoff`
- Handoff/rollback pass: `True`
- Rollback attempt: `from-native`
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
- `debugfs_pci_msm_case_present`: `None`
- `helper_timed_out`: `None`
- `pid1_rc1_watcher_requested`: `None`
- `pid1_rc1_watcher_result_summary`: `None`
- `pid1_rc1_watcher_result_file`: `state=triggered source=/proc/kmsg write_rc=0 errno=0 detect_elapsed_ms=7384 write_elapsed_ms=8792 delay_ms=0 retry_count=0 retry_delay_ms=0 line=<3>[    9.189653]  [2:    cnss-daemon:  600] __netlink_sendskb(1245) skb:0000000061730393 queued sk: 0000000057916ce6`
- `pid1_rc1_window_sampler_requested`: `None`
- `pid1_rc1_window_result_summary`: `None`
- `pid1_rc1_window_result_file`: `state=armed sampler=auto-v1485-wifi-readiness-test detect_elapsed_ms=7384 delay_ms=0 exact_provider_line=0 long_provider_window=0 tracepoint_sampler=0 pil_tracepoint_sampler=0 line=<3>[ 9.189653] [2: cnss-daemon: 600] __netlink_sendskb(1245) skb:0000000061730393 queued sk: 0000000057916ce6 <3>[ 9.189678] [2: cnss-daemon: 60`
- `pid1_rc1_window_sample_count`: `1`
- `pid1_rc1_window_has_post_500ms`: `False`

## Safety Scope

No Wi-Fi scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, or blind eSoC notify/`BOOT_DONE` spoof was
performed by this runner.
Device mutation included flashing the test boot image, any bounded
in-boot actions declared by that test image's artifact contract, and
rolling back to `stage3/boot_linux_v724.img`. If enabled, native direct
rollback may restore the boot partition from a pre-staged `/cache`
rollback image when recovery ADB is unavailable.

## Images

- Test image: `tmp/wifi/v1499-wifi-auto-readiness-pre-l0-parity-test-boot/boot_linux_v1499_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Next

Treat `rc1-ltssm-link-failed-no-l0` as the active pre-L0 blocker. Do not
proceed to firmware/MHI/WLFW, scan/connect, credentials, DHCP/routes, or
external ping until RC1 L0 and PCI enumeration are proven.
