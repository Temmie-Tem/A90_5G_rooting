# Native Init V2121 Dual-RFS Shared Server Info Handoff

## Summary

- Cycle: `V2121`
- Decision: `v2121-shared-server-info-post-bdf-no-fw-ready-rollback-pass`
- Label: `shared-server-info-post-bdf-no-fw-ready`
- Pass: `True`
- Reason: server_info startup errors cleared and WLFW cap/BDF/cal succeeded, but FW_READY/wlan0 still never appeared
- Evidence: `tmp/wifi/v2121-dual-rfs-shared-server-info-handoff`
- Inner handoff: `tmp/wifi/v2121-dual-rfs-shared-server-info-handoff/v2120-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| artifact | True | helper=a90_android_execns_probe v419 |
| dual_rfs | True | bridge={'android_parity': 'firmware_mnt_probe_present_firmware_fallback_present', 'fallback_exists': 1, 'fallback_nonzero': 1, 'fallback_open_rc': '0', 'probe_exists': 1, 'probe_nonzero': 1, 'probe_open_rc': '0', 'rootfs_namespace_only': 1, 'sda29_write': 0} |
| shared_server_info | True | shared={'dir_exists': 1, 'dir_gid': '2904', 'dir_is_dir': 1, 'dir_mode': '0770', 'dir_uid': '2903', 'exists': 1, 'gid': '2904', 'is_reg': 1, 'mode': '0660', 'rootfs_namespace_only': 1, 'sda29_write': 0, 'size': '0', 'source': 'tmp/wifi/v2121-dual-rfs-shared-server-info-handoff/v2120-handoff/test-v1393-helper-result.stdout.txt', 'stat_errno': 0, 'stat_error': 'none', 'tmpfs_requested': 1, 'uid': '2903'} |
| startup_error | 0 | payloads=[] |
| tftp_branch |  | server_check={'delta_ms': 12559, 'exists': 1, 'index': 1, 'monotonic_ms': 15705, 'payload': 'hello', 'phase': 'drain-pre', 'size': 5} ota=False wlanmdsp=False |
| post_bdf | True | cap=True bdf_rc=0x0 bdf_qmi=0x0 cal=True fw_mem_ind=True worker_done=True dms_addr_qmi=0xd |
| cascade |  | wlan_pd=1 icnss_qmi=1 wlfw69=0 fw_ready=0 wlan0=0 |

## Shared Snapshot

| field | value |
| --- | --- |
| tmpfs_requested | 1 |
| dir_exists | 1 |
| dir_mode | 0770 |
| dir_uid_gid | 2903:2904 |
| file_exists | 1 |
| file_mode | 0660 |
| file_uid_gid | 2903:2904 |
| stat_errno | 0 |
| rootfs_namespace_only | 1 |
| sda29_write | 0 |
| source | tmp/wifi/v2121-dual-rfs-shared-server-info-handoff/v2120-handoff/test-v1393-helper-result.stdout.txt |

## Process-Root Paths

| path | exists | dir | mode | uid | gid | errno |
| --- | --- | --- | --- | --- | --- | --- |
| vendor_rfs_readwrite | 1 | 1 | 0770 | 2903 | 2904 | 0 |
| persist_rfs_shared | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| persist_rfs_msm_mpss | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| persist_rfs_mdm_mpss | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| persist_rfs_apq_gnss | 1 | 1 | 0770 | 2903 | 2903 | 0 |

## Interpretation

- V2121 tests only whether the missing `/vendor/rfs/msm/mpss/shared/server_info.txt` startup path was blocking stock `tftp_server` from the Android-order TFTP branch.
- A `wlanmdsp`/FW-ready/`wlan0` label is progress toward the final native Wi-Fi goal; a cleared-but-post-UP-only label falsifies this startup file as the producer trigger.
- This run remains light/passive: no `tftp_server` ptrace, no boot-time QRTR matrix, no AP QMI send, and no Wi-Fi HAL/scan/connect.

## Remaining Blocker

- `server_info.txt` is no longer a startup error, and native now reaches WLFW client init, FW-mem indication, cap success, BDF send/return success, and cal-only success.
- The remaining blocker moved downstream: after post-BDF/cal success, native still has no FW_READY and no `wlan0`; the next useful gate is the missing post-BDF FW-ready/status transition, not another mcfg/server_info/AP-side strace loop.

## Steps

- `pre-version` rc `0` ok `True` evidence `host/pre-version.txt`
- `pre-selftest` rc `0` ok `True` evidence `host/pre-selftest.txt`
- `pre-flags` rc `0` ok `True` evidence `host/pre-flags.txt`
- `arm-clean-dsp-flag` rc `0` ok `True` evidence `host/arm-clean-dsp-flag.txt`
- `cleanup-leftover-clean-dsp-flag` rc `0` ok `True` evidence `host/cleanup-leftover-clean-dsp-flag.txt`
- `post-selftest` rc `0` ok `True` evidence `host/post-selftest.txt`
- `post-status` rc `0` ok `True` evidence `host/post-status.txt`
- `post-flags` rc `0` ok `True` evidence `host/post-flags.txt`

## Safety

- No Wi-Fi HAL, wificond, supplicant, hostapd, scan/connect, credentials, DHCP/routes, or external ping was used.
- No macloader retry, DIAG, rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR readback, QMI payload send, or `tftp_server` ptrace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2120 test-boot flash-handoff, namespace-local RFS bridges/tmpfs mirrors, namespace-local shared `server_info.txt` tmpfs, namespace-local persist-RFS leaf precreate in the private rootfs, read-only tftp process-root audit, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
