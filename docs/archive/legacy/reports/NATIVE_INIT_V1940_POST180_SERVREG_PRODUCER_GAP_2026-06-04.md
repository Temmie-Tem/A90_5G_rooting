# Native Init V1940 Post-180 SERVREG Producer Gap

## Summary

- Cycle: `V1940`
- Type: host-only classifier over existing Android-good/native captures and service-notifier source
- Decision: `v1940-post180-remote-servreg-stateup-producer-missing-host-pass`
- Label: `post180-remote-servreg-stateup-producer-missing`
- Pass: `True`
- Reason: Android and native both reach modem SSCTL/service180, but only Android later receives the passive SERVREG state-up indication for msm/modem/wlan_pd instance 180; Android does so without pre-wlanmdsp JSN or restart-PD evidence, while native has tftp running but no wlan_pd indication, wlanmdsp request, WLFW69, or wlan0
- Evidence: `tmp/wifi/v1940-post180-servreg-producer-gap`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | post180-remote-servreg-stateup-producer-missing | Android and native both reach modem SSCTL/service180, but only Android later receives the passive SERVREG state-up indication for msm/modem/wlan_pd instance 180; Android does so without pre-wlanmdsp JSN or restart-PD evidence, while native has tftp running but no wlan_pd indication, wlanmdsp request, WLFW69, or wlan0 |
| Android post-180 chain | True | modem SSCTL + service180 + wlan_pd indication/ACK + wlanmdsp |
| Android order | True | service180=7.264381 wlanpd_ind=9.580204 |
| Android exclusions | True | no pre-wlanmdsp JSN/modemuw and no restart-PD text |
| Native same upstream | True | tftp_running=True |
| Native producer missing | True | early=uninit late=uninit ind=0 |
| Native downstream absent | True | requested_wlanmdsp=0 wlfw69=False wlan0=False |
| Source passive path | True | SERVREG state-up indication handler plus ACK; restart-PD source exists but is excluded |

## Counts

| marker | Android | Native | meaning |
| --- | --- | --- | --- |
| modem_ssctl | 1 | 1 | same upstream modem SSCTL publication |
| service180 | 1 | 1 | same SERVREG instance 180 server publication |
| service74 | 1 | 1 | sibling clean-DSP path present but not sufficient |
| wlanpd_ind | 1 | 0 | missing remote WLAN-PD state-up producer edge |
| wlanpd_ack | 1 | 0 | ACK only follows received state-up indication |
| wlanmdsp_request | 10 | 0 | downstream firmware request |
| pre_wlanmdsp_jsn | 0 | n/a | V1919 label=android-modem-no-jsn-read |
| restart_pd_text | 0 | 0 | no evidence Android uses forbidden host restart-PD path |

## Timing

| marker | Android time | Native time | first line |
| --- | --- | --- | --- |
| modem_ssctl | 7.17457 | 5.484811 | [    7.174570]  [6: kworker/u16:10:  340] sysmon-qmi: ssctl_new_server: Connection established between QMI handle and modem's SSCTL service |
| service180 | 7.264381 | 5.484788 | [    7.264381]  [3:  kworker/u16:4:  245] service-notifier: service_notifier_new_server: Connection established between QMI handle and 180 service |
| service74 | 7.270067 | 4.440743 | [    7.270067]  [6:  kworker/u16:2:  241] service-notifier: service_notifier_new_server: Connection established between QMI handle and 74 service |
| wlanpd_ind | 9.580204 | None | [    9.580204]  [5:  kworker/u16:1:   75] service-notifier: root_service_service_ind_cb: Indication received from msm/modem/wlan_pd, state: 0x1fffffff, trans-id: 1 |
| wlanpd_ack | 9.580513 | None | [    9.580513]  [6:  kworker/u17:1:  729] service-notifier: send_ind_ack: Indication ACKed for transid 1, service msm/modem/wlan_pd, instance 180! |
| audio_ind | None | 4.467428 | [    4.467428] [0:  kworker/u16:2:  245] service-notifier: root_service_service_ind_cb: Indication received from msm/adsp/audio_pd, state: 0x1fffffff, trans-id: 1 |
| audio_ack | None | 4.468464 | [    4.468464] [1:  kworker/u17:1:  571] service-notifier: send_ind_ack: Indication ACKed for transid 1, service msm/adsp/audio_pd, instance 74! |

## Source Anchors

| anchor | path | line | text |
| --- | --- | --- | --- |
| servreg_ind_handler | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 224 | static void root_service_service_ind_cb(struct qmi_handle *qmi, |
| servreg_state_updated_msg | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 45 | #define SERVREG_NOTIF_STATE_UPDATED_IND_MSG	\ |
| servreg_ind_log | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 237 | pr_info("Indication received from %s, state: 0x%x, trans-id: %d\n", |
| servreg_ack_sender | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 149 | static void send_ind_ack(struct work_struct *work) |
| servreg_ack_log | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 217 | pr_info("Indication ACKed for transid %d, service %s, instance %d!\n", |
| servreg_new_server | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 327 | static int service_notifier_new_server(struct qmi_handle *qmi, |
| servreg_register_listener | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 319 | static int register_notif_listener(struct service_notif_info *service_notif, |
| icnss_register_notifier | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/icnss.c | 2010 | service_notif_register_notifier(pd->domain_list[i].name, |
| icnss_restart_pd | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/icnss.c | 2603 | ret = service_notif_pd_restart(priv->service_notifier[0].name, |

## Interpretation

- The normal Android path has modem SSCTL and service180 before the WLAN-PD state indication; native reaches those same upstream publications.
- The missing edge is not service74, modem SSCTL, tftp availability, JSN/RFS config, or host restart-PD text in the retained captures.
- The missing edge is the remote SERVREG state-up producer for `msm/modem/wlan_pd` instance 180. Without that indication, native never ACKs WLAN-PD state-up, requests `wlanmdsp.mbn`, publishes WLFW69, or creates `wlan0`.
- Next live unit should be read-only and observe the service180/SERVREG RX producer side and modem child-PD state timing. Do not invoke `service_notif_pd_restart`, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, eSoC/PCIe/GDSC, PMIC/GPIO, or regulator paths.

## Inputs

- Android dmesg: `tmp/wifi/v1934-android-libqmi-service69-positive-control-live-20260603-170139/android-postfs-evidence/a90-v1934-libqmi69/dmesg-filtered.txt`
- Android logcat: `tmp/wifi/v1934-android-libqmi-service69-positive-control-live-20260603-170139/android-postfs-evidence/a90-v1934-libqmi69/logcat-filtered.txt`
- Native dmesg: `tmp/wifi/v1937-icnss-ipc-service69-integration/v1936-handoff/test-v1393-dmesg.stdout.txt`
- Native inner manifest: `tmp/wifi/v1937-icnss-ipc-service69-integration/v1936-handoff/manifest.json`
- Native V1937 manifest: `tmp/wifi/v1937-icnss-ipc-service69-integration/manifest.json`
- V1939 manifest: `tmp/wifi/v1939-servnotif-root-indication-gap/manifest.json`
- V1919 JSN/RFS manifest: `tmp/wifi/v1919-modem-jsn-rfs-gate/manifest.json`

## Safety Scope

Host-only parser. No live device command, flash, reboot, firmware/partition write, remount-write, `/dev/subsys_esoc0`, eSoC/PCIe/GDSC/PMIC/GPIO/regulator action, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, or restart-PD request was used.
