# Native Init V2051 Passive DIAG Pre-WLANMDSP Trigger Handoff

## Summary

- Cycle: `V2051`
- Decision: `v2051-passive-diag-bytes-mcfg-only-no-android-branch-rollback-pass`
- Label: `passive-diag-bytes-mcfg-only-no-android-branch`
- Pass: `True`
- Reason: native still selects only the off-branch mcfg TFTP path, but passive modem DIAG bytes are available for offline decoding of the pre-wlanmdsp decision
- Evidence: `tmp/wifi/v2051-passive-diag-pre-wlanmdsp-trigger-handoff`
- Inner handoff: `tmp/wifi/v2051-passive-diag-pre-wlanmdsp-trigger-handoff/v2050-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | passive-diag-bytes-mcfg-only-no-android-branch | native still selects only the off-branch mcfg TFTP path, but passive modem DIAG bytes are available for offline decoding of the pre-wlanmdsp decision |
| helper | True | a90_android_execns_probe v390 |
| route | True | hook=True order_ts=True holder=True cnss=True |
| readonly_fallback | True | path=/tmp/a90-v231-547/root/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn size=4251884 open_rc=0 |
| readwrite | True | server_check_file=1 tmpfs=1 path=/tmp/a90-v231-547/root/vendor/rfs/msm/mpss/readwrite |
| persist | True | rfs=/tmp/a90-v231-547/root/mnt/vendor/persist/rfs hlos=/tmp/a90-v231-547/root/mnt/vendor/persist/hlos_rfs |
| cascade |  | wlan_pd=1 icnss_qmi=1 fw_ready=0 wlan0=0 post_up=81.726246 |
| tftp_branch |  | datagrams=36 server_check=0 ota=0 mcfg=6 wlanmdsp=0 fallback=0 4251884=0 |
| passive_diag | True | begin=True bytes=2618 reads=4 samples=4 reason= errno= |
| cnss_order |  | wlfw_start=6.625799 wlfw_service_request=6.631291 wlan_pd_up=7.886523 |
| cap_bdf_cal | True | cap=0x0 bdf=0x0 cal=0x0 worker_cal= |

## Native Ordering

| event | monotonic_ms | delta_ms | line |
| --- | --- | --- | --- |
| tftp_sink_start | 3106 | delta=0 |  |
| first_tftp_relevant | 14205 | 11099 |  |
| first_tftp_server | 14205 | 11099 |  |
| first_server_check | 0 | 0 |  |
| first_ota_firewall | 0 | 0 |  |
| first_mcfg | 15693 | 12587 |  |
| first_wlanmdsp | 0 | 0 |  |
| cnss_wlfw_start |  |  | cnss-daemon-626   [003] ....     6.625799: wlfw_start: (0x5590584c00) |
| cnss_wlfw_service_request |  |  | cnss-daemon-637   [000] ....     6.631291: wlfw_service_request: (0x55905839fc) |
| wlan_pd_up |  |  | tmp/wifi/v2051-passive-diag-pre-wlanmdsp-trigger-handoff/v2050-handoff/test-v1393-dmesg.stdout.txt: [    7.886523] [0:  kworker/u16:1:   75] service-notifier: root_service_service_ind_cb: Indication received from msm/modem/wlan_pd, state: 0x1fffffff, trans-id: 1 |

## TFTP Records

| idx | delta_ms | server_check | ota | mcfg | wlanmdsp | fallback | rrq | wrq | payload |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 000 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83Z\x91GX\x17\x04tftp_server\x00Initializing tftp_server RING buffer\x00 |
| 001 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83Z\xb6\xb8[\x17\x04tftp_server\x00Starting...\n\x00 |
| 002 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83Z\xcb\xc5r\x17\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs/modem] [No such file or directory]\x00 |
| 003 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83Z\xefCs\x17\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs] [No such file or directory]\x00 |
| 004 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83Z\x0c\xa9s\x17\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [13] [/data/vendor/tombstones] [Permission denied]\x00 |
| 005 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83ZS\xf4s\x17\x06tftp_server\x00pid=561 tid=561 tftp-server : ERR :[tftp_server_folders_la.c, 174] Failed to auto_dir for(/data/vendor/tombstones/rfs/modem/) errno = -13 (Permission denied\x00 |
| 006 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83Zs}t\x17\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs/modem/] [No such file or directory]\x00 |
| 007 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83Z \xe0t\x17\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs/lpass] [No such file or directory]\x00 |
| 008 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83Z\xe6<u\x17\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs] [No such file or directory]\x00 |
| 009 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83ZC\x99u\x17\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [13] [/data/vendor/tombstones] [Permission denied]\x00 |
| 010 | 11099 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xf3\xb2\x83Z\xcb\xdbu\x17\x06tftp_server\x00pid=561 tid=561 tftp-server : ERR :[tftp_server_folders_la.c, 174] Failed to auto_dir for(/data/vendor/tombstones/rfs/lpass/) errno = -13 (Permission denied\x00 |
| 011 | 12587 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xff\xb2\x83Z\x1c\xc299\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_server.c, 659] rcvd request [1] [72] [1] [0] [104]\x00 |
| 012 | 12587 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | \x00\x8b\x02\xff\xb2\x83Z\xd9h?9\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server_utils.c, 113] file [readwrite/mcfg.tmp] : [/vendor/rfs/msm/mpss/readwrite/mcfg.tmp]\x00 |
| 013 | 12587 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x00\x8b\x02\xff\xb2\x83Z\xc4O@9\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server.c, 1203] OACK options [port: 104] : [7680, 200, 0, 10, 0, 0, 0, 0]\x00 |
| 014 | 12587 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | \x00\x8b\x02\xff\xb2\x83Z\x98\xbb@9\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readwrite/mcfg.tmp]\x00 |
| 015 | 12587 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x00\x8b\x02\xff\xb2\x83Z\t4A9\x06tftp_server\x00pid=561 tid=651 tftp-server : ERR :[tftp_os_la.c, 70] open failed: [2] [No such file or directory]\x00 |
| 016 | 12588 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x00\x8b\x02\xff\xb2\x83Zw\|A9\x06tftp_server\x00pid=561 tid=651 tftp-server : ERR :[tftp_server.c, 1742] open failed : [-2] [Unknown error -2]\x00 |
| 017 | 12588 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x00\x8b\x02\xff\xb2\x83ZwhB9\x06tftp_server\x00pid=561 tid=651 tftp-server : ERR :[tftp_protocol.c, 1231] sending error-pkt. Code = 1, Msg = Err=2 String=No such file or directory\x00 |
| 018 | 12588 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | \x00\x8b\x02\xff\xb2\x83Z\x1e\xb2B9\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server.c, 1809] RRQ Total API = 320\x00 |
| 019 | 12638 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xff\xb2\x83Z\xcc\xd1[9\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_server.c, 659] rcvd request [1] [64] [2] [0] [105]\x00 |
| 020 | 12638 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | \x00\x8c\x02\xff\xb2\x83Z\x94\xf2^9\x04tftp_server\x00pid=561 tid=652 tftp-server : INF :[tftp_server_utils.c, 113] file [readwrite/mcfg.tmp] : [/vendor/rfs/msm/mpss/readwrite/mcfg.tmp]\x00 |
| 021 | 12638 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x00\x8c\x02\xff\xb2\x83Z4\x99_9\x04tftp_server\x00pid=561 tid=652 tftp-server : INF :[tftp_server.c, 1203] OACK options [port: 105] : [7680, 200, 10, 0, 0, 0, 0, 0]\x00 |
| 022 | 12638 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | \x00\x8c\x02\xff\xb2\x83Z\xed\xf2_9\x04tftp_server\x00pid=561 tid=652 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [577] [/vendor/rfs/msm/mpss/readwrite/mcfg.tmp]\x00 |
| 023 | 12638 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x001\x02\xff\xb2\x83Z\xe1fn9\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_server.c, 659] rcvd request [1] [72] [1] [0] [106]\x00 |
| 024 | 12638 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | \x00\x8d\x02\xff\xb2\x83ZuXq9\x04tftp_server\x00pid=561 tid=653 tftp-server : INF :[tftp_server_utils.c, 113] file [readwrite/mcfg.tmp] : [/vendor/rfs/msm/mpss/readwrite/mcfg.tmp]\x00 |
| 025 | 12638 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x00\x8d\x02\xff\xb2\x83Z\xda\xb9r9\x04tftp_server\x00pid=561 tid=653 tftp-server : INF :[tftp_server.c, 1203] OACK options [port: 106] : [7680, 200, 1, 10, 0, 0, 0, 0]\x00 |
| 026 | 12638 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | \x00\x8d\x02\xff\xb2\x83Z\xff\x14s9\x04tftp_server\x00pid=561 tid=653 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readwrite/mcfg.tmp]\x00 |
| 027 | 12638 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x00\x8d\x02\xff\xb2\x83Z9\xaev9\x04tftp_server\x00pid=561 tid=653 tftp-server : INF :[tftp_protocol.c, 744] Recd END OF TRANSFER pkt. Code = 9, Msg = End of Transfer\x00 |
| 028 | 12638 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | \x00\x8d\x02\xff\xb2\x83Zc\x16w9\x04tftp_server\x00pid=561 tid=653 tftp-server : INF :[tftp_server.c, 1320] RRQ stats [port: 0]: sent_size = 106 total-blocks = 0 total-bytes = 0 timedout-pkts = 0, wrong-pkts\x00 |
| 029 | 12638 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | \x00\x8d\x02\xff\xb2\x83Z\x82Xw9\x04tftp_server\x00pid=561 tid=653 tftp-server : INF :[tftp_server.c, 1327] RRQ file stats [port: 106]: fread [Total, Max, Min] = [0, 0, 0]\x00 |
| 030 | 12889 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | \x00\x8c\x02\x00\xb3\x83Z\xb5\xc2\xb7\x0c\x04tftp_server\x00pid=561 tid=652 tftp-server : INF :[tftp_server.c, 1501] WRQ stats : total-blocks = 1 : total-bytes = 1 : 1 timedout-pkts = 0, wrong-pkts = 0\x00 |
| 031 | 12889 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | \x00\x8c\x02\x00\xb3\x83Z\x90G\xb8\x0c\x04tftp_server\x00pid=561 tid=652 tftp-server : INF :[tftp_server.c, 1509] WRQ file stats [port: 105]: Total : [fwrite, fflush] = [12, 32] max: 12 min: 0\x00 |

## Passive DIAG

- Mode: `private-node-open-readonly-nonblock-no-ioctl-no-write`
- Sysfs device: `505:0` major `505` minor `0`
- Node: `/tmp/a90-v231-547/root/dev/diag` rootfs_namespace_only `1` sda29_write `0`
- Safety: ioctl `0` write `0` qmi_send `0` log_mask_write `0` ptrace `0`
- Summary: started `True` reads `4` bytes `2618` samples `4` first_read_delta_ms `0` read_errors `1` read_error `Bad address` reason `` error ``

| idx | delta_ms | bytes | stored | truncated | payload |
| --- | --- | --- | --- | --- | --- |
| 000 | 11099 | 4 | 4 | 0 | \x01\x00\x00\x00 |
| 001 | 11099 | 517 | 96 | 1 | \x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 |
| 002 | 11099 | 1577 | 96 | 1 | \x02\x00\x00\x00\x00\x00\x00\x00\x00\x01\xe8\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 |
| 003 | 11099 | 520 | 96 | 1 | \x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 |

## Branch

- `mcfg` is not treated as the WLAN trigger; it is only a reachability marker.
- Android's normal branch is `server_check.txt` -> `ota_firewall/ruleset` -> `wlanmdsp.mbn`; this report classifies whether native enters that branch.
- If native remains `mcfg-only`, passive DIAG availability determines whether the next unit can decode the modem-side branch selection without AP-side strace/QRTR repeats.

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
- No rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR readback, QMI payload send, DIAG ioctl/write/log-mask, or `tftp_server` ptrace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2050 test-boot flash-handoff, namespace-local fallback readonly/readwrite RFS bridges, namespace-local persist-RFS tmpfs mirrors, private tmp-root `/dev/socket/logdw`, private tmp-root `/dev/diag` char node, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
