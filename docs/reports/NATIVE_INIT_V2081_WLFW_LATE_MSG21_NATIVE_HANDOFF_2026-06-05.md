# Native Init V2081 WLFW Late Msg21 Native Handoff

## Summary

- Cycle: `V2081`
- Decision: `v2081-wlfw-late-msg21-native-msg21-no-fw-ready-rollback-pass`
- Label: `wlfw-late-msg21-native-msg21-no-fw-ready`
- Pass: `True`
- Reason: native captured the Android-good late WLFW msg_id 0x21 edge, but FW-ready/wlan0 did not follow
- Evidence: `tmp/wifi/v2081-wlfw-late-msg21-native-handoff`
- Inner handoff: `tmp/wifi/v2081-wlfw-late-msg21-native-handoff/v2080-handoff/manifest.json`

## Matrix

| area | value | detail |
| --- | --- | --- |
| route | True | hook=True late_safe=True |
| per_mgr | True | cnss=True peripheral=True |
| late_msg21 | True | qmi_hit=2 sample_ids=['0x2b', '0x21'] first=0x2b |
| msg2b_seen | True | cal_return=1 queue=0 cond=1 |
| tftp_branch |  | server_check=0 ota=0 mcfg=3 wlanmdsp=0 |
| cascade |  | wlan_pd=1 icnss_qmi=1 fw_ready=0 wlan0=0 |

## PerMgr Vote Edge

| field | value |
| --- | --- |
| label | cnss-permgr-register-connect-server-accepted |
| cnss_register_success | 1 |
| cnss_connect_success | 1 |
| pm_server_register_success | 1 |
| peripheral_register_success | 1 |
| pm_vote_ack_seen | 1 |
| cnss_register_ret | cnss-daemon-622   [003] ....     8.089777: pm_init_pm_client_register_retcheck: (0x555bb2d628) rc=0x0 |
| cnss_connect_ret | cnss-daemon-622   [003] ....     8.090810: pm_init_pm_client_connect_retcheck: (0x555bb2d654) rc=0x0 |

## Late WLFW Edge

| field | value |
| --- | --- |
| mode | compact-post-cal-wlfw-ready-edge |
| qmi_hit_count | 2 |
| qmi_sample_count | 2 |
| saw_msg21 | 1 |
| saw_msg2b | 1 |
| first_line | cnss-daemon-647   [000] ....     9.176355: wlfw_qmi_ind_cb_entry: (0x555bb2f100) msg_id=0x2b payload_len=0x0 |
| sample_0 | cnss-daemon-647   [000] ....     9.176355: wlfw_qmi_ind_cb_entry: (0x555bb2f100) msg_id=0x2b payload_len=0x0 |
| sample_1 | cnss-daemon-647   [002] ....    14.133249: wlfw_qmi_ind_cb_entry: (0x555bb2f100) msg_id=0x21 payload_len=0x0 |
| sample_2 | none |
| sample_3 | none |
| status_version | status=0 version=0 handle=0 |

## Comparator

- Android V2079 reached `wlanmdsp`/BDF/FW-ready/`wlan0` and captured late `wlfw_qmi_ind_cb_entry msg_id=0x21 payload_len=0x0`.
- Native V2081 confirms cnss-daemon PerMgr register/connect returned `rc=0`, pm-service accepted the cnss client, and the PM vote ACK path was seen.
- Native V2081 uses the same internal-modem route without DIAG/strace/QRTR matrix and emits compact samples before stdout truncation.
- If native remains `0x2b`-only after cap/BDF/cal, the missing edge is the modem/WLFW ready-publication condition, not AP PerMgr registration.

## Branch

- `wlfw-late-msg21-native-post-cal-msg2b-only-no-msg21`: target why the WLAN PD/modem never publishes the Android-good late `0x21` ready indication.
- `wlfw-late-msg21-native-msg21-no-fw-ready`: chase the immediate kernel FW-ready publication after `0x21`.
- `wlfw-late-msg21-native-wlan0-progress`: stop before scan/connect and run the dedicated connectivity gate.

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
- No passive DIAG, active DIAG mask/log-mode, rild/cnss/pm-service strace, boot-time QRTR matrix, service-locator probe, service-notifier listener, active QRTR readback, QMI payload send, or `tftp_server` ptrace was run.
- No `/dev/subsys_esoc0`, forced RC1/case, PMIC/GPIO/GDSC/regulator write, PCI rescan, bind/unbind, fake ONLINE, or eSoC notify/BOOT_DONE action was used.
- Mutation scope: `/cache` one-shot clean-DSP flag, V2080 test-boot flash-handoff, namespace-local fallback readonly/readwrite RFS bridges, namespace-local persist-RFS tmpfs mirrors, private tmp-root `/dev/socket/logdw`, tracefs uprobes, compact WLFW late-edge summary, and rollback to `stage3/boot_linux_v724.img` with selftest fail=0.
