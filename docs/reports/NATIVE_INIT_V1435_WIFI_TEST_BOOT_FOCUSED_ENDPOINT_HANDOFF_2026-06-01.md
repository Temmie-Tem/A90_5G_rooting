# Native Init V1435 Wi-Fi Test Boot Handoff

## Summary

- Cycle: `V1435`
- Type: bounded live test-boot handoff with rollback
- Decision: `v1435-test-boot-downstream-progress-rollback-pass`
- Result: PASS
- Reason: test boot produced downstream Wi-Fi/PCIe evidence and rollback verified
- Evidence: `tmp/wifi/v1435-wifi-test-boot-focused-endpoint-handoff`
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
- `debugfs_pci_msm_case_present`: `None`
- `helper_timed_out`: `None`
- `pid1_rc1_watcher_requested`: `None`
- `pid1_rc1_watcher_result_summary`: `None`
- `pid1_rc1_watcher_result_file`: `state=triggered source=/proc/kmsg write_rc=0 errno=0 detect_elapsed_ms=7425 write_elapsed_ms=8952 delay_ms=250 retry_count=0 retry_delay_ms=0 line=<3>[    9.129418]  [3:    cnss-daemon:  600] __netlink_sendskb(1245) skb:00000000d3d14711 queued sk: 00000000bdf53c20`
- `pid1_rc1_window_sampler_requested`: `None`
- `pid1_rc1_window_result_summary`: `None`
- `pid1_rc1_window_result_file`: `state=armed sampler=read-only-v1433-focused-endpoint-prereq detect_elapsed_ms=7425 delay_ms=250 line=<3>[ 9.129418] [3: cnss-daemon: 600] __netlink_sendskb(1245) skb:00000000d3d14711 queued sk: 00000000bdf53c20 <3>[ 9.129443] [3: cnss-daemon: 60`
- `pid1_rc1_window_sample_count`: `5`
- `pid1_rc1_window_has_post_500ms`: `True`

## Safety Scope

No Wi-Fi scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, or blind eSoC notify/`BOOT_DONE` spoof was
performed by this runner.
Device mutation was limited to flashing the test boot image and
rolling back to `stage3/boot_linux_v724.img`.

## Images

- Test image: `tmp/wifi/v1433-wifi-test-boot-focused-endpoint-sampler/boot_linux_v1433_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Focused Endpoint Evidence Notes

- RC1/LTSSM downstream progress occurred, but the link still failed before
  `LTSSM L0`.
- No MHI, WLFW, BDF, FW-ready, or `wlan0` progress appeared.
- GPIO103/CLKREQ remained high/pull-up in the sampled windows; GPIO142/MDM2AP
  remained low.
- The broad `pre_rc1` regulator/clock reads captured pcie1 enable activity, but
  later focused exact `pre_rc1` reads had the same pcie1 lines back off. Treat
  this as sampling-window timing sensitivity, not as a stable contradiction.

## Next

Run a host-only V1436 classifier over this V1435 evidence before any new live
mutation. Do not proceed to scan/connect, credentials, DHCP/routes, or external
ping until at least L0/MHI/WLFW/`wlan0` progress is proven.
