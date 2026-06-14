# Native Init V2023 TFTP Early All-Task Handoff

## Summary

- Cycle: `V2023`
- Decision: `v2023-tftp-early-wlanmdsp-progress-rollback-pass`
- Label: `tftp-early-wlanmdsp-progress`
- Pass: `True`
- Reason: early tftp trace exposed a native wlanmdsp request/load edge with cnss-daemon running
- Evidence: `tmp/wifi/v2023-tftp-early-alltask-handoff`
- Inner handoff: `tmp/wifi/v2023-tftp-early-alltask-handoff/v2022-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | tftp-early-wlanmdsp-progress | early tftp trace exposed a native wlanmdsp request/load edge with cnss-daemon running |
| helper | True | a90_android_execns_probe v380 |
| route | True | service74=True service180=True holder=True |
| bridges | True | readonly=True readwrite=True |
| cascade |  | wlan_pd=1 icnss_qmi=1 wlfw69=0 fw_ready=0 wlan0=0 hold=124.49762 |
| tftp_trace | True | compiled=1 attach_rc=0 detach_rc=0 records=78 packet=68 fs=10 stops=7961 ms=45003 truncated=0 |
| packet_ops | {'RRQ': 29, 'WRQ': 12, 'OACK': 25, 'ERROR': 2} | directions={'recvfrom': 41, 'sendto': 27} errors={'Err=2 String=No such file or directory': 2} |
| packet_paths | True | paths={'/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn': 13, '/readwrite/mcfg.tmp': 28} token={'server_check': 0, 'ota_firewall': 0, 'mcfg': 28, 'mbn_hw': 0, 'wlanmdsp': 13, 'modem': 0} |
| fs_paths | 10 | success={'/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn': 2, '/vendor/rfs/msm/mpss/readwrite/mcfg.tmp': 4} errors={'/vendor/rfs/msm/mpss/readwrite/mcfg.tmp': 4} token={'server_check': 0, 'ota_firewall': 0, 'mcfg': 8, 'mbn_hw': 0, 'wlanmdsp': 2, 'modem': 0} |
| initial_branch |  | server_check=False ota_firewall=False mcfg=True mbn_hw=False |
| wlanmdsp |  | summary=0 trace=True dmesg=15 pd_load=0 |
| cap_bdf_cal |  | cap=0x0 bdf=0x0 cal=0x0 worker_cal= |

## Interpretation

- Early all-task tracing reached a native `wlanmdsp` TFTP edge with the full downstream consumer chain running.
- Next bounded unit is downstream-only: follow WLFW 69 / BDF / FW-ready / `wlan0`, still without HAL scan/connect.

## First TFTP Packets

- `tftp_server_t560.packet_000 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_001 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_002 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_003 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_004 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_005 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_006 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_007 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_008 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_009 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_010 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_011 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_012 recvfrom RRQ /readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t560.packet_013 recvfrom RRQ /readwrite/mcfg.tmp`
- `tftp_server_t560.packet_014 recvfrom RRQ /readwrite/mcfg.tmp`
- `tftp_server_t560.packet_015 recvfrom RRQ /readwrite/mcfg.tmp`

## First TFTP Errors

- `tftp_server_t658.packet_002 code=1 msg=Err=2 String=No such file or directory`
- `tftp_server_t661.packet_002 code=1 msg=Err=2 String=No such file or directory`

## First Focused FS Results

- `tftp_server_t641.fs_000 openat ret=17 err=0/none path=/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t641.fs_001 openat ret=17 err=0/none path=/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`
- `tftp_server_t658.fs_000 openat ret=-2 err=2/No such file or directory path=/vendor/rfs/msm/mpss/readwrite/mcfg.tmp`
- `tftp_server_t658.fs_001 openat ret=-2 err=2/No such file or directory path=/vendor/rfs/msm/mpss/readwrite/mcfg.tmp`
- `tftp_server_t661.fs_000 openat ret=-2 err=2/No such file or directory path=/vendor/rfs/msm/mpss/readwrite/mcfg.tmp`
- `tftp_server_t661.fs_001 openat ret=-2 err=2/No such file or directory path=/vendor/rfs/msm/mpss/readwrite/mcfg.tmp`
- `tftp_server_t671.fs_000 openat ret=21 err=0/none path=/vendor/rfs/msm/mpss/readwrite/mcfg.tmp`
- `tftp_server_t671.fs_001 openat ret=23 err=0/none path=/vendor/rfs/msm/mpss/readwrite/mcfg.tmp`
- `tftp_server_t678.fs_000 openat ret=20 err=0/none path=/vendor/rfs/msm/mpss/readwrite/mcfg.tmp`
- `tftp_server_t678.fs_001 openat ret=21 err=0/none path=/vendor/rfs/msm/mpss/readwrite/mcfg.tmp`

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

- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping was used.
- No rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR readback, or QMI payload send was run.
- The only ptrace was the bounded compact all-task syscall trace of stock `tftp_server`; no AP-side multi-strace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2022 test-boot flash-handoff, namespace-local RFS tmpfs/symlink bridges, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
