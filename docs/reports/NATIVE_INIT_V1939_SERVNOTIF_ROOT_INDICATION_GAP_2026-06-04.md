# Native Init V1939 Service-notifier Root Indication Gap

## Summary

- Cycle: `V1939`
- Type: host-only classifier over existing normal Android and native V1937/V1938 evidence
- Decision: `v1939-native-servnotif-wlanpd-root-indication-missing-host-pass`
- Label: `native-servnotif-wlanpd-root-indication-missing`
- Pass: `True`
- Reason: Android normal receives and ACKs the service-notifier state indication for msm/modem/wlan_pd instance 180 before wlanmdsp; native has service74/180 and ICNSS registration but only the sibling audio_pd indication appears, with no wlan_pd indication or WLFW69 publication
- Evidence: `tmp/wifi/v1939-servnotif-root-indication-gap`

## Matrix

| area | value | detail |
| --- | --- | --- |
| label | native-servnotif-wlanpd-root-indication-missing | Android normal receives and ACKs the service-notifier state indication for msm/modem/wlan_pd instance 180 before wlanmdsp; native has service74/180 and ICNSS registration but only the sibling audio_pd indication appears, with no wlan_pd indication or WLFW69 publication |
| Android positive | True | 180/74 servers, wlan_pd indication+ACK, wlanmdsp request |
| Native registered | True | service74/180, PM open, holder, ICNSS PD registration |
| Native sibling-only | True | audio_pd instance74 indication+ACK present |
| Native WLAN-PD indication | False | late_state=uninit indication=0 |
| Native WLFW publication | False | wlfw69=False wlan_pd=False wlanmdsp=False wlan0=False |
| Source anchors | True | state indication callback, ACK, server lookup, ICNSS notifier registration |

## Counts

| marker | Android V1917 | Android V1934 | Native V1937 |
| --- | --- | --- | --- |
| new_server_180 | 1 | 1 | 1 |
| new_server_74 | 1 | 1 | 1 |
| root_ind_wlanpd | 1 | 1 | 0 |
| ack_wlanpd_180 | 1 | 1 | 0 |
| root_ind_audio | 0 | 0 | 1 |
| ack_audio_74 | 0 | 0 | 1 |
| modem_ssctl | 1 | 1 | 1 |
| wlanmdsp | 0 | 10 | 0 |

## First Lines

| marker | line |
| --- | --- |
| android_v1934_wlanpd_ind | [    9.580204]  [5:  kworker/u16:1:   75] service-notifier: root_service_service_ind_cb: Indication received from msm/modem/wlan_pd, state: 0x1fffffff, trans-id: 1 |
| android_v1934_wlanpd_ack | [    9.580513]  [6:  kworker/u17:1:  729] service-notifier: send_ind_ack: Indication ACKed for transid 1, service msm/modem/wlan_pd, instance 180! |
| android_v1934_wlanmdsp | 06-04 02:03:51.389   965  1419 I tftp_server: pid=965 tid=1419 tftp-server : INF :[tftp_server_utils.c, 113] file [readonly/vendor/firmware_mnt/image/wlanmdsp.mbn] : [/vendor/rfs/msm/mpss/readonly/vendor |
| native_audio_pd_ind | [    4.467428] [0:  kworker/u16:2:  245] service-notifier: root_service_service_ind_cb: Indication received from msm/adsp/audio_pd, state: 0x1fffffff, trans-id: 1 |
| native_audio_pd_ack | [    4.468464] [1:  kworker/u17:1:  571] service-notifier: send_ind_ack: Indication ACKed for transid 1, service msm/adsp/audio_pd, instance 74! |
| native_modem_180 | [    5.484788] [3:  kworker/u16:6:  253] service-notifier: service_notifier_new_server: Connection established between QMI handle and 180 service |
| native_wlanpd_ind | missing |

## Source Anchors

| anchor | path | line | text |
| --- | --- | --- | --- |
| root_service_service_ind_cb | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 224 | static void root_service_service_ind_cb(struct qmi_handle *qmi, |
| state_ind_log | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 237 | pr_info("Indication received from %s, state: 0x%x, trans-id: %d\n", |
| send_ind_ack | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 149 | static void send_ind_ack(struct work_struct *work) |
| ack_log | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 217 | pr_info("Indication ACKed for transid %d, service %s, instance %d!\n", |
| new_server | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 327 | static int service_notifier_new_server(struct qmi_handle *qmi, |
| new_server_log | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 337 | pr_info("Connection established between QMI handle and %d service\n", |
| register_listener | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/service-notifier.c | 319 | static int register_notif_listener(struct service_notif_info *service_notif, |
| icnss_domain_log | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/icnss.c | 2005 | icnss_pr_dbg("%d: domain_name: %s, instance_id: %d\n", i, |
| icnss_register_notifier | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/icnss.c | 2010 | service_notif_register_notifier(pd->domain_list[i].name, |
| icnss_restart_pd | tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/icnss.c | 2603 | ret = service_notif_pd_restart(priv->service_notifier[0].name, |

## Interpretation

- `service74` in the native combined route is the sibling clean-DSP path: the captured indication is `msm/adsp/audio_pd` instance 74.
- Android's normal internal-modem path receives `msm/modem/wlan_pd` state-up on instance 180 and ACKs it before `wlanmdsp.mbn` is requested.
- Native reaches ICNSS registration for `msm/modem/wlan_pd` but never receives that root-service indication, so WLFW service69 never publishes and `cnss-daemon` remains in the libqmi wait.
- Next live work should observe the remote modem WLAN-PD state-up producer inputs only; do not call `service_notif_pd_restart`, start Wi-Fi HAL, scan/connect, use credentials, or touch eSoC/PCIe/GDSC/PMIC/GPIO.

## Inputs

- Android V1917 dmesg: `tmp/wifi/v1917-android-icnss-ipc-log-edge-handoff/android-postfs-evidence/a90-v1917-icnss-ipc-log-edge/dmesg-filtered.txt`
- Android V1934 dmesg: `tmp/wifi/v1934-android-libqmi-service69-positive-control-live-20260603-170139/android-postfs-evidence/a90-v1934-libqmi69/dmesg-filtered.txt`
- Native V1937 dmesg: `tmp/wifi/v1937-icnss-ipc-service69-integration/v1936-handoff/test-v1393-dmesg.stdout.txt`
- Native V1937 manifest: `tmp/wifi/v1937-icnss-ipc-service69-integration/manifest.json`
- Native V1938 manifest: `tmp/wifi/v1938-wlan-pd-stateup-before-wlfw-arrive/manifest.json`

## Safety Scope

Host-only parser. No live device command, flash, reboot, firmware/partition write, remount-write, `/dev/subsys_esoc0`, eSoC/PCIe/GDSC/PMIC/GPIO/regulator action, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping was used.
