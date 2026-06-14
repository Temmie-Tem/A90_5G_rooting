# Native Init V2149 Connect Tool Surface Handoff

## Summary

- Cycle: `V2149`
- Decision: `v2149-connect-tool-surface-ready-after-wlan0-scan-rollback-pass`
- Label: `connect-tool-surface-ready-after-wlan0-scan`
- Pass: `True`
- Reason: supplicant, DHCP, and ping tools are ready in the native wlan0 window
- Evidence: `tmp/wifi/v2149-connect-tool-surface-handoff`

## Gate Results

- `wlan0_seen`: `True` link_up_ok `True`
- `pre_operstate`: `down` flags `0x1002`
- `post_operstate`: `down` carrier `0` flags `0x1003`
- `scan_result`: `pass` scan_count `10`
- `surface_invoked`: `True` rc `0` result `connect-tools-ready`
- `supplicant_ready`: `True` dhcp_ready `True` ping_ready `True`
- `no_credentials`: `True`
- `helper_stage_ok`: `True` verify `True`
- `helper_sha256`: `94b3349001f4597c8b96b4250b239b09ea823ea181e508b39d43559d003d3f48`

## Reframe

- V2148 proved primary `wlan0` accepts link-up and returns redacted BSS entries through nl80211.
- V2149 keeps the same native window and only asks whether the real connect tools are available; it still does not read SSID/PSK or connect.
- If this passes, the next bounded unit can write a private `/cache/a90-wifi` config, start supplicant, run DHCP, and ping with redacted outputs.

## Steps

- `pre-status` rc `0` ok `True` evidence `pre-status.stdout.txt`
- `pre-selftest` rc `0` ok `True` evidence `pre-selftest.stdout.txt`
- `set-sibling-fwssctl-flag` rc `0` ok `True` evidence `set-sibling-fwssctl-flag.stdout.txt`
- `test-flash-from-native` rc `0` ok `True` evidence `test-flash-from-native.stdout.txt`
- `host-build-nl80211-scan-helper` rc `0` ok `True` evidence `host-build-nl80211-scan-helper.stdout.txt`
- `scan-helper-stage-clean` rc `0` ok `True` evidence `scan-helper-stage-clean.stdout.txt`
- `scan-helper-stage-touch` rc `0` ok `True` evidence `scan-helper-stage-touch.stdout.txt`
- `scan-helper-stage-b64-chunks` rc `0` ok `True` evidence `scan-helper-stage-b64-chunks.stdout.txt`
- `scan-helper-stage-decode` rc `0` ok `True` evidence `scan-helper-stage-decode.stdout.txt`
- `mac-assign-begin-hide-on-busy` rc `0` ok `True` evidence `mac-assign-begin-hide-on-busy.stdout.txt`
- `mac-assign-begin` rc `0` ok `True` evidence `mac-assign-begin.stdout.txt`
- `mac-assign-mkdir-dev-block` rc `0` ok `True` evidence `mac-assign-mkdir-dev-block.stdout.txt`
- `mac-assign-mkdir-efs` rc `0` ok `True` evidence `mac-assign-mkdir-efs.stdout.txt`
- `mac-assign-efs-uevent` rc `0` ok `True` evidence `mac-assign-efs-uevent.stdout.txt`
- `mac-assign-efs-block-rm` rc `0` ok `True` evidence `mac-assign-efs-block-rm.stdout.txt`
- `mac-assign-efs-block-mknod` rc `0` ok `True` evidence `mac-assign-efs-block-mknod.stdout.txt`
- `mac-assign-efs-ro-mount` rc `0` ok `True` evidence `mac-assign-efs-ro-mount.stdout.txt`
- `mac-assign-efs-mounted-check` rc `0` ok `True` evidence `mac-assign-efs-mounted-check.stdout.txt`
- `mac-assign-source-readable-test` rc `0` ok `True` evidence `mac-assign-source-readable-test.stdout.txt`
- `mac-assign-source-wc` rc `0` ok `True` evidence `mac-assign-source-wc.stdout.txt`
- `mac-assign-target-exists-test` rc `0` ok `True` evidence `mac-assign-target-exists-test.stdout.txt`
- `mac-assign-target-writable-test` rc `0` ok `True` evidence `mac-assign-target-writable-test.stdout.txt`
- `mac-assign-target-stat` rc `0` ok `True` evidence `mac-assign-target-stat.stdout.txt`
- `mac-assign-write-sysfs` rc `1` ok `False` evidence `mac-assign-write-sysfs.stdout.txt`
- `mac-assign-dmesg-proof` rc `0` ok `True` evidence `mac-assign-dmesg-proof.stdout.txt`
- `scan-helper-verify-prestaged` rc `0` ok `True` evidence `scan-helper-verify-prestaged.stdout.txt`
- `surface-script-clean` rc `0` ok `True` evidence `surface-script-clean.stdout.txt`
- `surface-script-touch` rc `0` ok `True` evidence `surface-script-touch.stdout.txt`
- `surface-script-line-00` rc `0` ok `True` evidence `surface-script-line-00.stdout.txt`
- `surface-script-line-01` rc `0` ok `True` evidence `surface-script-line-01.stdout.txt`
- `surface-script-line-02` rc `0` ok `True` evidence `surface-script-line-02.stdout.txt`
- `surface-script-line-03` rc `0` ok `True` evidence `surface-script-line-03.stdout.txt`
- `surface-script-line-04` rc `0` ok `True` evidence `surface-script-line-04.stdout.txt`
- `surface-script-line-05` rc `0` ok `True` evidence `surface-script-line-05.stdout.txt`
- `surface-script-line-06` rc `0` ok `True` evidence `surface-script-line-06.stdout.txt`
- `surface-script-line-07` rc `0` ok `True` evidence `surface-script-line-07.stdout.txt`
- `surface-script-line-08` rc `0` ok `True` evidence `surface-script-line-08.stdout.txt`
- `surface-script-line-09` rc `0` ok `True` evidence `surface-script-line-09.stdout.txt`
- `surface-script-line-10` rc `0` ok `True` evidence `surface-script-line-10.stdout.txt`
- `surface-script-line-11` rc `0` ok `True` evidence `surface-script-line-11.stdout.txt`
- `surface-script-line-12` rc `0` ok `True` evidence `surface-script-line-12.stdout.txt`
- `surface-script-line-13` rc `0` ok `True` evidence `surface-script-line-13.stdout.txt`
- `surface-script-line-14` rc `0` ok `True` evidence `surface-script-line-14.stdout.txt`
- `surface-script-line-15` rc `0` ok `True` evidence `surface-script-line-15.stdout.txt`
- `surface-script-line-16` rc `0` ok `True` evidence `surface-script-line-16.stdout.txt`
- `surface-script-line-17` rc `0` ok `True` evidence `surface-script-line-17.stdout.txt`
- `surface-script-line-18` rc `0` ok `True` evidence `surface-script-line-18.stdout.txt`
- `surface-script-line-19` rc `0` ok `True` evidence `surface-script-line-19.stdout.txt`
- `surface-script-line-20` rc `0` ok `True` evidence `surface-script-line-20.stdout.txt`
- `surface-script-line-21` rc `0` ok `True` evidence `surface-script-line-21.stdout.txt`
- `surface-script-line-22` rc `0` ok `True` evidence `surface-script-line-22.stdout.txt`
- `surface-script-line-23` rc `0` ok `True` evidence `surface-script-line-23.stdout.txt`
- `surface-script-line-24` rc `0` ok `True` evidence `surface-script-line-24.stdout.txt`
- `surface-script-line-25` rc `0` ok `True` evidence `surface-script-line-25.stdout.txt`
- `surface-script-line-26` rc `0` ok `True` evidence `surface-script-line-26.stdout.txt`
- `surface-script-line-27` rc `0` ok `True` evidence `surface-script-line-27.stdout.txt`
- `surface-script-line-28` rc `0` ok `True` evidence `surface-script-line-28.stdout.txt`
- `surface-script-line-29` rc `0` ok `True` evidence `surface-script-line-29.stdout.txt`
- `surface-script-chmod` rc `0` ok `True` evidence `surface-script-chmod.stdout.txt`
- `surface-script-start` rc `0` ok `True` evidence `surface-script-start.stdout.txt`
- `test-helper-wait-polls` rc `0` ok `True` evidence `test-helper-wait-polls.txt`
- `test-version` rc `0` ok `True` evidence `test-version.stdout.txt`
- `test-status` rc `0` ok `True` evidence `test-status.stdout.txt`
- `test-selftest` rc `0` ok `True` evidence `test-selftest.stdout.txt`
- `test-bootstatus` rc `0` ok `True` evidence `test-bootstatus.stdout.txt`
- `test-v2137-log` rc `0` ok `True` evidence `test-v2137-log.stdout.txt`
- `test-v2137-summary` rc `0` ok `True` evidence `test-v2137-summary.stdout.txt`
- `test-v2137-helper-result` rc `0` ok `True` evidence `test-v2137-helper-result.stdout.txt`
- `test-dmesg-full` rc `0` ok `True` evidence `test-dmesg-full.stdout.txt`
- `test-dmesg-wifi-filter` rc `0` ok `True` evidence `test-dmesg-wifi-filter.stdout.txt`
- `test-icnss-stats` rc `1` ok `False` evidence `test-icnss-stats.stdout.txt`
- `test-icnss-debugfs-ls` rc `1` ok `False` evidence `test-icnss-debugfs-ls.stdout.txt`
- `test-wlan0-state` rc `0` ok `True` evidence `test-wlan0-state.stdout.txt`
- `test-wlan0-ifconfig` rc `0` ok `True` evidence `test-wlan0-ifconfig.stdout.txt`
- `test-sys-wifi-mac-node` rc `0` ok `True` evidence `test-sys-wifi-mac-node.stdout.txt`
- `rollback-from-native` rc `0` ok `True` evidence `rollback-from-native.stdout.txt`
- `rollback-status` rc `0` ok `True` evidence `rollback-status.stdout.txt`
- `rollback-selftest` rc `0` ok `True` evidence `rollback-selftest.stdout.txt`
- `post-rollback-connect-surface-result-hide-on-busy` rc `0` ok `True` evidence `post-rollback-connect-surface-result-hide-on-busy.stdout.txt`
- `post-rollback-connect-surface-result` rc `0` ok `True` evidence `post-rollback-connect-surface-result.stdout.txt`
- `post-rollback-connect-surface-cleanup` rc `0` ok `True` evidence `post-rollback-connect-surface-cleanup.stdout.txt`

## Cleanup

- `cache_artifacts_removed`: `True`

## Safety

- No SSID/PSK/credential file or environment value was read.
- No association/connect, DHCP, route change, or external ping was attempted.
- EFS was mounted read-only only for pre-HDD MAC assignment; no EFS, persist, firmware, boot, or partition file was written.
