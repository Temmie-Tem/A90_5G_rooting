# Native Init V1748 WLAN-PD Tracefs Delta Classifier

## Summary

- Cycle: `V1748`
- Type: host/source-only tracefs target-path delta classifier
- Decision: `v1748-tracefs-delta-debugfs-mount-flag-missing`
- Result: PASS
- Reason: V1702 worked with debugfs mounted, V1745 omitted that mount, and V1747 failed before target probing because no tracefs source was available
- Evidence: `tmp/wifi/v1748-wlan-pd-tracefs-delta-classifier`

## Delta

- V1701 source `mount_debugfs`: `True`; build flag present: `True`
- V1702 live tracefs path/available/uprobe hits: `/sys/kernel/debug/tracing` / `1` / `1`
- V1745 source `mount_debugfs`: `False`; build flag present: `False`
- V1747 live tracefs path/available/errno/uprobe attempted: `none` / `0` / `2` / `0`
- V1747 selected target path: `none`

## Source Contract

- `materialize_wlan_pd_cnss_tracefs_surface`: `9794`
- source `/sys/kernel/debug/tracing`: `9798`
- fallback `/sys/kernel/tracing`: `9806`
- bind existing tracefs source: `9825`
- helper mounts tracefs/debugfs itself: `False`
- private roots searched first: `12247`

## Checks

- `v1701_source_passed_with_debugfs_mount`: `True`
- `v1702_live_tracefs_and_uprobe_worked`: `True`
- `v1745_source_omitted_debugfs_mount`: `True`
- `v1747_live_tracefs_failed_before_target_probe`: `True`
- `helper_only_binds_existing_tracefs_source`: `True`
- `v1745_path_repair_did_not_explain_missing_source_mount`: `True`

## Interpretation

- V1745 fixed tracefs path selection but did not restore the source tracefs mount that made V1702 work.
- Because V1747 failed before target probing, the remaining immediate bug is not the cnss-daemon uprobe target path.
- The next source/build unit should restore the V1701 `--wifi-test-mount-debugfs` contract on the pure internal-modem route, then run artifact sanity before any live retry.
- This does not justify adding PM/service-window actors, `boot_wlan`, eSoC/RC1, Wi-Fi HAL, scan/connect, DHCP/routes, or external ping.

## Safety Scope

This classifier performed host-side reads only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
