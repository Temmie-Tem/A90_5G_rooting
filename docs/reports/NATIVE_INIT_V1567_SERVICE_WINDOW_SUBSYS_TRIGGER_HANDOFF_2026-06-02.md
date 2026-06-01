# Native Init V1567 Wi-Fi Test Boot Handoff

## Summary

- Cycle: `V1567`
- Type: bounded live test-boot handoff with rollback
- Decision: `v1567-test-boot-no-downstream-wifi-progress-blocked`
- Result: BLOCKED
- Reason: test boot ran and rollback verified, strict Wi-Fi progress markers were absent, and the persisted PID1 log did not preserve the service-window trigger contract fields needed to classify whether `/dev/subsys_esoc0` was attempted
- Evidence: `tmp/wifi/v1567-service-window-subsys-trigger-handoff`
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
- `pid1_rc1_watcher_requested`: `0`
- `pid1_rc1_watcher_result_summary`: `None`
- `pid1_rc1_watcher_result_file`: ``
- `pid1_rc1_window_sampler_requested`: `0`
- `pid1_rc1_window_result_summary`: `None`
- `pid1_rc1_window_result_file`: ``
- `pid1_rc1_window_sample_count`: `0`
- `pid1_rc1_window_has_post_500ms`: `False`

## Live Evidence

- Test boot flash and verify completed with `A90 Linux init 0.9.69 (v1566-service-window-subsys-trigger)`.
- Rollback to `stage3/boot_linux_v724.img` completed from native init and the post-rollback selftest passed.
- The PID1 supervisor launched `wifi-companion-android-wifi-service-window-subsys-trigger-capture`; the helper exited normally with `helper_exit_code=0` and `helper_timed_out=0`.
- The persisted test summary reports `wlan0_present=0`, `helper_exited=1`, `helper_exit_code=0`, `helper_timed_out=0`, and `log_size=573`.
- The persisted PID1 log contains only supervisor lifecycle lines (`child stdio attached`, helper spawn, helper done), not the detailed `android_wifi_service_window.*`, `cnss_before_esoc.*`, or `subsys_trigger.*` contract fields emitted by the helper source.
- Focused dmesg showed `cnss_diag`, `cnss-daemon`, and `wificond` generic netlink/binder activity, proving the selected service-window userspace surface started.
- Focused dmesg did not show `wlfw_start`, `wlfw_service_request`, ICNSS-QMI, BDF/regdb, FW-ready, MHI, RC1, or `wlan0` progress.

## Interpretation

V1567 proves the V1566 rollbackable test boot runs and rolls back cleanly, but
it does not prove the scoped service-window subsystem trigger executed.  The
helper mode is correct and exits successfully, yet the persisted PID1 log is too
sparse to determine whether the helper reached the gated `/dev/subsys_esoc0`
open attempt, skipped it because the mdm-helper eSoC fd predicate was false, or
attempted it without downstream provider/RC1 progress.

The correct next step is therefore not credentials, scan/connect, DHCP/routes,
external ping, firmware/MHI deep-dive, or another blind live retry.  The next
source/build gate must repair the evidence path so the service-window helper
contract is preserved in a private result file or equivalent PID1-captured
stdout/stderr artifact.

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

- Test image: `tmp/wifi/v1566-android-wifi-service-window-subsys-trigger-test-boot/boot_linux_v1393_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Next

Treat `no-provider-no-downstream` as diagnostic evidence, not Wi-Fi bring-up
progress.  Next gate should be V1568 source/build-only: preserve the helper
contract output for `wifi-companion-android-wifi-service-window-subsys-trigger-
capture` in a private artifact, then sanity-check the new test boot before any
live rerun. Do not proceed to scan/connect, credentials, DHCP/routes, or
external ping until at least RC1/MHI/WLFW/`wlan0` progress is proven.
