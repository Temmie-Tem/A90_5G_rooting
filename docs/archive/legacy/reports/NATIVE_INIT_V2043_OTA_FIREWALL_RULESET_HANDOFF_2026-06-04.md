# Native Init V2043 OTA Firewall Ruleset Handoff

## Summary

- Cycle: `V2043`
- Decision: `v2043-ota-firewall-ruleset-not-preserved-mcfg-still-no-wlanmdsp-rollback-pass`
- Label: `ota-firewall-ruleset-not-preserved-mcfg-still-no-wlanmdsp`
- Pass: `True`
- Reason: the pre-start ota_firewall/ruleset file was absent by the post-run snapshot, and native still stopped at mcfg.tmp before wlanmdsp
- Evidence: `tmp/wifi/v2043-ota-firewall-ruleset-handoff`
- Inner handoff: `tmp/wifi/v2043-ota-firewall-ruleset-handoff/v2042-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | ota-firewall-ruleset-not-preserved-mcfg-still-no-wlanmdsp | the pre-start ota_firewall/ruleset file was absent by the post-run snapshot, and native still stopped at mcfg.tmp before wlanmdsp |
| helper | True | a90_android_execns_probe v387 |
| route | True | service74=True service180=True holder=True cnss=True lower=True |
| rfs_probe | True | path=/tmp/a90-v231-546/root/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn open_rc=0 errno=0 |
| rfs_fallback | True | path=/tmp/a90-v231-546/root/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn exists=1 size=4251884 open_rc=0 |
| readwrite | True | server_check=1 tmpfs=1 |
| cascade |  | wlan_pd=1 icnss_qmi=1 wlfw69=0 fw_ready=0 wlan0=0 hold=81.79739900000001 |
| logdw | True | started=1 stopped=0 datagrams=27 stored=27 truncated=0 |
| logdw_tftp | False | server_check=0 mcfg=3 wlanmdsp=0 fallback=0 total_bytes=1 4251884=0 end=0 success=0 enoent=7 |
| cap_bdf_cal | True | cap=0x0 bdf=0x0 cal=0x0 worker_cal=0x0 |
| indication |  | cb_hits=2 first_msg=0x2b len=0x0 handle_type= fw_status= |

## Logdw Records

- `000` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x001\x02+\xa0\x83Z\xcfE\xe7\x17\x04tftp_server\x00Initializing tftp_server RING buffer\x00`
- `001` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x001\x02+\xa0\x83ZL\x90\xea\x17\x04tftp_server\x00Starting...\n\x00`
- `002` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=1 payload=`\x001\x02+\xa0\x83Z\xbd\x1c\x02\x18\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs/modem] [No such file or directory]\x00`
- `003` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=1 payload=`\x001\x02+\xa0\x83Z\xe2\xa6\x02\x18\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs] [No such file or directory]\x00`
- `004` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x001\x02+\xa0\x83Z\x93\n\x03\x18\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [13] [/data/vendor/tombstones] [Permission denied]\x00`
- `005` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x001\x02+\xa0\x83Z\x98R\x03\x18\x06tftp_server\x00pid=561 tid=561 tftp-server : ERR :[tftp_server_folders_la.c, 174] Failed to auto_dir for(/data/vendor/tombstones/rfs/modem/) errno = -13 (Permission denied\x00`
- `006` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=1 payload=`\x001\x02+\xa0\x83Z\x97\xb0\x03\x18\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs/modem/] [No such file or directory]\x00`
- `007` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=1 payload=`\x001\x02+\xa0\x83ZH\x14\x04\x18\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs/lpass] [No such file or directory]\x00`
- `008` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=1 payload=`\x001\x02+\xa0\x83Zmo\x04\x18\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [2] [/data/vendor/tombstones/rfs] [No such file or directory]\x00`
- `009` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x001\x02+\xa0\x83Z\xff\xcb\x04\x18\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_os_la.c, 118] mkdir failed: [13] [/data/vendor/tombstones] [Permission denied]\x00`
- `010` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x001\x02+\xa0\x83Z\x1a\r\x05\x18\x06tftp_server\x00pid=561 tid=561 tftp-server : ERR :[tftp_server_folders_la.c, 174] Failed to auto_dir for(/data/vendor/tombstones/rfs/lpass/) errno = -13 (Permission denied\x00`
- `011` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x001\x027\xa0\x83Z<{\x8d7\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_server.c, 659] rcvd request [1] [72] [1] [0] [103]\x00`
- `012` server_check=0 mcfg=1 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8a\x027\xa0\x83Z\x11\x04\x937\x04tftp_server\x00pid=561 tid=650 tftp-server : INF :[tftp_server_utils.c, 113] file [readwrite/mcfg.tmp] : [/vendor/rfs/msm/mpss/readwrite/mcfg.tmp]\x00`
- `013` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8a\x027\xa0\x83Z\xa8\x12\x947\x04tftp_server\x00pid=561 tid=650 tftp-server : INF :[tftp_server.c, 1203] OACK options [port: 103] : [7680, 200, 0, 10, 0, 0, 0, 0]\x00`
- `014` server_check=0 mcfg=1 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8a\x027\xa0\x83Z*\x83\x947\x04tftp_server\x00pid=561 tid=650 tftp-server : INF :[tftp_os_la.c, 63] open : [-1] [-1] [384] [0] [/vendor/rfs/msm/mpss/readwrite/mcfg.tmp]\x00`
- `015` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=1 payload=`\x00\x8a\x027\xa0\x83Z+\x05\x957\x06tftp_server\x00pid=561 tid=650 tftp-server : ERR :[tftp_os_la.c, 70] open failed: [2] [No such file or directory]\x00`
- `016` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8a\x027\xa0\x83Z\xa6P\x957\x06tftp_server\x00pid=561 tid=650 tftp-server : ERR :[tftp_server.c, 1742] open failed : [-2] [Unknown error -2]\x00`
- `017` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=1 payload=`\x00\x8a\x027\xa0\x83Z\xa4S\x967\x06tftp_server\x00pid=561 tid=650 tftp-server : ERR :[tftp_protocol.c, 1231] sending error-pkt. Code = 1, Msg = Err=2 String=No such file or directory\x00`
- `018` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8a\x027\xa0\x83Z\xb2\x9d\x967\x04tftp_server\x00pid=561 tid=650 tftp-server : INF :[tftp_server.c, 1809] RRQ Total API = 339\x00`
- `019` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x001\x027\xa0\x83Z3}\xb47\x04tftp_server\x00pid=561 tid=561 tftp-server : INF :[tftp_server.c, 659] rcvd request [1] [64] [2] [0] [104]\x00`
- `020` server_check=0 mcfg=1 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8b\x027\xa0\x83Z\xa1\xac\xb77\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server_utils.c, 113] file [readwrite/mcfg.tmp] : [/vendor/rfs/msm/mpss/readwrite/mcfg.tmp]\x00`
- `021` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8b\x028\xa0\x83Z\xbb\x92\x10\x0b\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server.c, 1501] WRQ stats : total-blocks = 1 : total-bytes = 1 : 1 timedout-pkts = 0, wrong-pkts = 0\x00`
- `022` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8b\x028\xa0\x83Zj\x19\x11\x0b\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server.c, 1509] WRQ file stats [port: 104]: Total : [fwrite, fflush] = [10, 32] max: 10 min: 0\x00`
- `023` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8b\x028\xa0\x83Z\x80Y\x11\x0b\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server.c, 1513] WRQ time stats : Total : [TX, RX] = [52, 168]\x00`
- `024` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8b\x028\xa0\x83Z\xbd\x96\x11\x0b\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server.c, 1517] WRQ time stats : Tx [Min, Max] = [25, 27]\x00`
- `025` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8b\x028\xa0\x83Z\x97\xd4\x11\x0b\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server.c, 1522] WRQ time stats [port : 104]: Rx [Min, Max] = [168, 168]\x00`
- `026` server_check=0 mcfg=0 wlanmdsp=0 fallback=0 end=0 success=0 bytes4251884=0 enoent=0 payload=`\x00\x8b\x028\xa0\x83Z\x98V\x12\x0b\x04tftp_server\x00pid=561 tid=651 tftp-server : INF :[tftp_server.c, 1809] WRQ Total API = 251023\x00`

## OTA Firewall Ruleset

| field | value |
| --- | --- |
| ok | False |
| requested | False |
| ruleset | /tmp/a90-v231-546/root/vendor/rfs/msm/mpss/readwrite/ota_firewall/ruleset exists=0 is_reg=0 size=0 mode=0000 uid=-1 gid=-1 |
| ruleset_errno | 2 No such file or directory |
| persist_mirrors_ok | True |
| lchown_failures | 0 |
| rfs | /tmp/a90-v231-546/root/mnt/vendor/persist/rfs exists=1 mode=0770 uid=2903 gid=2903 |
| hlos_rfs | /tmp/a90-v231-546/root/mnt/vendor/persist/hlos_rfs exists=1 mode=0770 uid=2903 gid=2904 |
| rfs_readwrite | /tmp/a90-v231-546/root/mnt/vendor/persist/rfs/msm/mpss/readwrite exists=1 is_dir=1 |
| hlos_readwrite | /tmp/a90-v231-546/root/mnt/vendor/persist/hlos_rfs/msm/mpss/readwrite exists=1 is_dir=1 |
| safety | rootfs_namespace_only=1 sda29_write=0 |

## MCFG Readback

| idx | phase | exists | size | open_rc | read_len | payload |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | mcfg-log | 0 | 0 | -1 | -1 |  |
| 1 | mcfg-log | 0 | 0 | -1 | -1 |  |
| 2 | mcfg-log | 0 | 0 | -1 | -1 |  |
| 3 | post-wrq-stats | 0 | 0 | -1 | -1 |  |

- Path: `/tmp/a90-v231-546/root/vendor/rfs/msm/mpss/readwrite/mcfg.tmp`
- Samples: `4` post_wrq=`1`

## Indication Events

| event | hits | fetch | first |
| --- | --- | --- | --- |
| wlfw_worker_second_bdf_branch | 1 | bdf_rc=%x19 | cnss-daemon-637   [001] ....     7.961893: wlfw_worker_second_bdf_branch: (0x55892c5c98) bdf_rc=0x0 |
| wlfw_worker_cal_only_call | 1 | none | cnss-daemon-637   [001] ....     7.961897: wlfw_worker_cal_only_call: (0x55892c5fe0) |
| wlfw_worker_cal_only_retcheck | 1 | rc=%x0 | cnss-daemon-637   [001] ....     7.962299: wlfw_worker_cal_only_retcheck: (0x55892c5fe4) rc=0x0 |
| wlfw_worker_done_signal | 1 | none | cnss-daemon-637   [001] ....     7.962303: wlfw_worker_done_signal: (0x55892c5ff8) |
| wlfw_worker_post_done_wait | 1 | none | cnss-daemon-637   [001] ....     7.962332: wlfw_worker_post_done_wait: (0x55892c6070) |
| wlfw_worker_handle_ind_call | 0 | none | none |
| wlfw_qmi_ind_cb_entry | 2 | msg_id=%x1 payload_len=%x3 | cnss-daemon-649   [002] ....     7.909373: wlfw_qmi_ind_cb_entry: (0x55892c6100) msg_id=0x2b payload_len=0x0 |
| wlfw_qmi_ind_msg_unknown | 0 | msg_id=%x21 | none |
| wlfw_qmi_ind_decode_0x28_ok | 0 | none | none |
| wlfw_qmi_ind_decode_0x2a_ok | 0 | none | none |
| wlfw_qmi_ind_decode_0x41_ok | 0 | none | none |
| wlfw_qmi_ind_fw_mem_flag | 1 | msg_id=%x21 | cnss-daemon-649   [002] ....     7.909418: wlfw_qmi_ind_fw_mem_flag: (0x55892c62f0) msg_id=0x2b |
| wlfw_qmi_ind_msa_flag | 0 | msg_id=%x21 | none |
| wlfw_qmi_ind_queue_link | 0 | none | none |
| wlfw_qmi_ind_cond_signal | 1 | none | cnss-daemon-649   [002] ....     7.909446: wlfw_qmi_ind_cond_signal: (0x55892c6450) |
| wlfw_handle_ind_entry | 0 | none | none |
| wlfw_handle_ind_type | 0 | ind_type=%x3 | none |
| wlfw_handle_ind_type_0x28 | 0 | fw_status=%x4 | none |
| wlfw_handle_ind_type_0x2a | 0 | arg0=%x4 arg1=%x5 | none |
| wlfw_handle_ind_type_0x41 | 0 | arg0=%x4 arg1=%x5 | none |

## Interpretation

- V2043 keeps the dual-RFS/readwrite bridge, adds namespace-only ota_firewall ruleset bridge, and uses only the private logdw datagram sink.
- A transfer-complete label requires `wlanmdsp.mbn` plus `END OF TRANSFER`, successful processing, or `total-bytes=4251884` in stock `tftp_server` logs.
- If logdw captures zero datagrams, the observer did not prove transfer completion; do not reinterpret that as no modem TFTP request without another light serve-side signal.
- V2043 tests whether adding Android's pre-`wlanmdsp.mbn` `readwrite/ota_firewall/ruleset` surface moves native past the early readwrite branch.

## Next Candidate

- Next bounded unit depends on this result: if `ota_firewall/ruleset` is requested but no `wlanmdsp.mbn` follows, the gate remains modem-internal after the Android-style readwrite branch; if it is not requested and `mcfg.tmp` remains first visible traffic, stay on `mcfg.tmp` visibility semantics.
- Branches: if `mcfg.tmp` is absent or empty after native WRQ, fix tmpfs/write semantics; if present with the expected one-byte payload yet no follow-up RRQ, the blocker is modem-side transition after the mcfg write ACK.

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
- No rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR readback, QMI payload send, or `tftp_server` ptrace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2042 test-boot flash-handoff, namespace-local RFS tmpfs/symlink bridges, namespace-local ota_firewall tmpfs mirrors, private tmp-root `/dev/socket/logdw`, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
