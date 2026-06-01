# Native Init V1495 Wi-Fi Test Boot Handoff

## Summary

- Cycle: `V1495`
- Type: bounded live test-boot handoff with rollback
- Decision: `v1495-test-boot-version-missing`
- Result: BLOCKED
- Reason: test boot returned through bridge but expected version marker was missing
- Evidence: `tmp/wifi/v1495-wifi-auto-readiness-rc1-window-handoff`
- Handoff/rollback pass: `True`
- Rollback attempt: `from-native`
- Strict Wi-Fi progress mode: `True`
- Wi-Fi progress pass: `False`
- Progress decision: `no-provider-no-downstream`

## Progress Classification

- `provider_trigger`: `False`
- `rc1_progress`: `False`
- `rc1_l0`: `False`
- `rc1_link_failed`: `False`
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
- `pid1_rc1_watcher_result_file`: ``
- `pid1_rc1_window_sampler_requested`: `None`
- `pid1_rc1_window_result_summary`: `None`
- `pid1_rc1_window_result_file`: ``
- `pid1_rc1_window_sample_count`: `0`
- `pid1_rc1_window_has_post_500ms`: `False`

## Safety Scope

No Wi-Fi scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, or blind eSoC notify/`BOOT_DONE` spoof was
performed by this runner.
Device mutation was limited to flashing the test boot image and
rolling back to `stage3/boot_linux_v724.img`. If enabled, native
direct rollback may restore the boot partition from a pre-staged
`/cache` rollback image when recovery ADB is unavailable.

## Images

- Test image: `tmp/wifi/v1493-wifi-auto-readiness-rc1-window-test-boot/boot_linux_v1493_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Next

Treat this as a test-boot communication loss, not Wi-Fi bring-up progress. The
flash verifier saw the V1493 boot marker immediately after reboot, but all
post-hold `cmdv1` evidence commands failed with bridge connection reset or
missing END marker before the rollback path restored v724. Do not proceed to
scan/connect, credentials, DHCP/routes, or external ping. Next isolate whether
the RC1 watcher/window path wedges the serial command loop, then rerun with
shorter/earlier evidence collection or a PID1-persisted sidecar that survives
rollback collection failure.
