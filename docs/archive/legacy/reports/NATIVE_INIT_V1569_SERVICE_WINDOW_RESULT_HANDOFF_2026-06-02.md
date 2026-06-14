# Native Init V1569 Wi-Fi Test Boot Handoff

## Summary

- Cycle: `V1569`
- Type: bounded live test-boot handoff with rollback
- Decision: `v1569-test-boot-no-downstream-wifi-progress-blocked`
- Result: BLOCKED
- Reason: test boot ran and rollback verified, the helper result artifact was preserved, and strict Wi-Fi progress markers were absent because the service-window gate never observed `mdm_helper` holding `/dev/esoc-0`
- Evidence: `tmp/wifi/v1569-service-window-result-handoff`
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
- `helper_timed_out`: `0`
- `helper_result_file_seen`: `True`
- `helper_result_contract_seen`: `True`
- `helper_result_size`: `563961`
- `helper_result_subsys_open_attempted`: `0`
- `helper_result_subsys_trigger_started`: `0`
- `helper_result_subsys_trigger_gate_open`: `0`
- `helper_result_mdm_helper_esoc0_fd_count`: `0`
- `helper_result_final_result`: `subsys-trigger-not-attempted-no-mdm-helper-esoc-fd`
- `helper_result_final_reason`: `service-window-gate-did-not-see-dev-esoc-0`
- `pid1_rc1_watcher_requested`: `0`
- `pid1_rc1_watcher_result_summary`: `None`
- `pid1_rc1_watcher_result_file`: ``
- `pid1_rc1_window_sampler_requested`: `0`
- `pid1_rc1_window_result_summary`: `None`
- `pid1_rc1_window_result_file`: ``
- `pid1_rc1_window_sample_count`: `0`
- `pid1_rc1_window_has_post_500ms`: `False`

## Live Evidence

- Test boot flash and verify completed with `A90 Linux init 0.9.69 (v1568-service-window-subsys-trigger-result)`.
- Rollback to `stage3/boot_linux_v724.img` completed from native init and post-rollback verification passed.
- The V1568 helper-result repair worked: `/cache/native-init-wifi-test-boot-v1393-helper.result` was collected and the result file was `563961` bytes.
- Helper result file was complete enough to classify the service-window contract: `A90_EXECNS_RESULT_FILE_BEGIN` and `android_wifi_service_window.begin=1` were present.
- The helper entered `guarded-subsys-trigger-capture`, started all 14 planned Android service-window children, and then timed out internally without downstream Wi-Fi progress.
- `mdm_helper` was started as child order 13, but repeated fd polling after `mdm_helper` spawn and after `cnss-daemon` spawn saw `/dev/esoc-0` count `0`.
- Because `mdm_helper_esoc0_fd_count=0`, the gated `/dev/subsys_esoc0` trigger child was not started: `subsys_trigger_start_attempted=0`, `subsys_trigger_started=0`, `subsys_esoc0_open_attempted=0`.
- Focused dmesg again showed generic `cnss_diag`, `cnss-daemon`, and `wificond` netlink/binder activity, but no provider, RC1, MHI, WLFW, BDF, FW-ready, or `wlan0` marker.

## Interpretation

V1569 closes the V1567 evidence gap.  The service-window subsystem-trigger
artifact does not fail because the result was missing; it fails because the
trigger gate condition is false.  Native service-window userspace starts
`mdm_helper`, but `mdm_helper` does not acquire `/dev/esoc-0`, so the scoped
`/dev/subsys_esoc0` open is correctly not attempted.

This places the current blocker before the V1496-style RC1/LTSSM branch for
this route.  There is no meaningful firmware/MHI/WLFW/connect work to do in
V1569's path until the Android-good `mdm_helper -> /dev/esoc-0` contract is
reproduced or a bounded equivalent is proven.

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

- Test image: `tmp/wifi/v1568-service-window-subsys-trigger-result-test-boot/boot_linux_v1393_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Next

Treat `subsys-trigger-not-attempted-no-mdm-helper-esoc-fd` as the current
service-window blocker.  Next gate should be V1570 source/build-only or
host-only: compare the Android-good `mdm_helper` launch contract against the
native service-window launch contract and add a bounded mdm-helper fd
acquisition classifier if needed.  Do not proceed to scan/connect, credentials,
DHCP/routes, external ping, firmware/MHI deep dive, or RC1 retry until the
`mdm_helper` `/dev/esoc-0` fd predicate is satisfied or deliberately replaced
by a new reviewed gate.
