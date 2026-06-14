# Native Init V2109 TFTP Persist-RFS Leaf Precreate Handoff

## Summary

- Cycle: `V2109`
- Decision: `v2109-persist-rfs-leaf-precreate-clears-mkdir-post-up-server-check-rollback-pass`
- Label: `persist-rfs-leaf-precreate-clears-mkdir-post-up-server-check`
- Pass: `True`
- Reason: persist-RFS startup mkdir failures cleared, but native still only shows late post-UP server_check and no ota/wlanmdsp
- Evidence: `tmp/wifi/v2109-tftp-persist-rfs-leaf-precreate-handoff`
- Inner handoff: `tmp/wifi/v2109-tftp-persist-rfs-leaf-precreate-handoff/v2108-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| artifact | True | helper=a90_android_execns_probe v414 |
| leaf_precreate | True | marker={'enabled': 1, 'paths': '/mnt/vendor/persist/rfs/mdm/mpss,/mnt/vendor/persist/rfs/apq/gnss', 'owner': 'vendor_rfs:vendor_rfs', 'mode': '0770'} |
| namespace_audit | 1 | pid=560 root=/tmp/a90-v231-545/root |
| persist_targets_visible | True | mountinfo_matches=6 |
| persist_auto_dir | 0 | mkdir_failed=0 |
| server_check | hello | after_wlan_pd_ms=6455 |
| cascade |  | wlan_pd=1 icnss_qmi=1 fw_ready=0 wlan0=0 |

## Process-Root Paths

| path | exists | dir | mode | uid | gid | errno |
| --- | --- | --- | --- | --- | --- | --- |
| persist_rfs | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| persist_rfs_shared | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| persist_rfs_msm | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| persist_rfs_msm_mpss | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| persist_rfs_msm_adsp | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| vendor_rfs_readwrite | 1 | 1 | 0770 | 2903 | 2904 | 0 |
| data_tombstones_rfs | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| mnt | 1 | 1 | 0750 | 0 | 1000 | 0 |
| mnt_vendor | 1 | 1 | 0750 | 0 | 1000 | 0 |
| persist | 1 | 1 | 0750 | 0 | 1000 | 0 |
| persist_rfs_mdm_mpss | 1 | 1 | 0770 | 2903 | 2903 | 0 |
| persist_rfs_apq_gnss | 1 | 1 | 0770 | 2903 | 2903 | 0 |

## Interpretation

- V2107 proved parent traversal works and exposed two remaining stock `tftp_server` startup `mkdir failed: [2]` targets: `/mnt/vendor/persist/rfs/mdm/mpss` and `/mnt/vendor/persist/rfs/apq/gnss`.
- V2109 precreates only those namespace-local persist-RFS leaves as `vendor_rfs:vendor_rfs 0770`, preserving the existing RFS bridges and keeping `sda29` read-only.
- If mkdir failures clear without early `ota_firewall/wlanmdsp`, the remaining gate is modem-internal before the full WLAN-PD firmware fetch branch.

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
- Mutation scope: `/cache` one-shot clean-DSP flag, V2108 test-boot flash-handoff, namespace-local RFS bridges/tmpfs mirrors, namespace-local persist-RFS leaf precreate in the private rootfs, read-only tftp process-root audit, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
