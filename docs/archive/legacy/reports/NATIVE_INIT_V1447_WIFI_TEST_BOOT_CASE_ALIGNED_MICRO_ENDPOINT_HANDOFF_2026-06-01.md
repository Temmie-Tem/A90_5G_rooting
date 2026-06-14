# Native Init V1447 Wi-Fi Test Boot Handoff

## Summary

- Cycle: `V1447`
- Type: bounded live test-boot handoff with rollback
- Decision: `v1447-test-boot-downstream-progress-rollback-pass`
- Result: PASS
- Reason: test boot produced downstream Wi-Fi/PCIe evidence and rollback verified
- Evidence: `tmp/wifi/v1447-wifi-test-boot-case-aligned-micro-endpoint-handoff`
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
- `pid1_rc1_watcher_result_file`: `state=triggered source=/proc/kmsg write_rc=0 errno=0 detect_elapsed_ms=7427 write_elapsed_ms=8096 delay_ms=250 retry_count=0 retry_delay_ms=0 line=<3>[    9.190503]  [2:    cnss-daemon:  601] __netlink_sendskb(1245) skb:0000000095f6deeb queued sk: 000000002d865d2f`
- `pid1_rc1_window_sampler_requested`: `None`
- `pid1_rc1_window_result_summary`: `None`
- `pid1_rc1_window_result_file`: `state=armed sampler=read-only-v1445-case-aligned-micro-endpoint detect_elapsed_ms=7427 delay_ms=250 line=<3>[ 9.190503] [2: cnss-daemon: 601] __netlink_sendskb(1245) skb:0000000095f6deeb queued sk: 000000002d865d2f <3>[ 9.190528] [2: cnss-daemon: 60`
- `pid1_rc1_window_sample_count`: `1`
- `pid1_rc1_window_has_post_500ms`: `False`

## Safety Scope

No Wi-Fi scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, or blind eSoC notify/`BOOT_DONE` spoof was
performed by this runner.
Device mutation was limited to flashing the test boot image and
rolling back to `stage3/boot_linux_v724.img`.

## Images

- Test image: `tmp/wifi/v1445-wifi-test-boot-case-aligned-micro-endpoint-sampler/boot_linux_v1445_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Case-Aligned Micro Endpoint Evidence Notes

- The V1445 image still reached corrected RC1/LTSSM and failed before
  `LTSSM L0`.
- No MHI, WLFW, BDF, FW-ready, or `wlan0` evidence appeared.
- The writer completed `rc_sel=2` and `case=11` successfully with
  `writer_wait_rc=0`, `status=0x0`, and `micro_writer rc=0`.
- The first parent sample landed after the actual case write:
  writer case elapsed was `7793ms` and
  `case_aligned_micro_after_case_0ms` landed at `7794ms`.
- All nine case-aligned micro samples landed after case completion.
- GPIO135 stayed `out 0` and GPIO142 stayed `in 0` from `0ms` through `150ms`
  after confirmed case completion.

## Next

Run a host-only classifier over the V1447 case-aligned micro endpoint evidence
before another live mutation. Do not proceed to scan/connect, credentials,
DHCP/routes, or external ping until at least L0/MHI/WLFW/`wlan0` progress is
proven.
