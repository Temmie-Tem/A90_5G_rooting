# Native Init V586 QRTR Companion Blocker Classifier

- date: `2026-05-22 KST`
- objective: classify the post-V585 QRTR/control-plane blocker before any qcwlanstate, HAL, scan/connect, or boot-time retry
- status: `classified`; Wi-Fi external ping is **not** complete

## Scope

- Script: `scripts/revalidation/native_wifi_qrtr_companion_blocker_v586.py`
- Plan: `docs/plans/NATIVE_INIT_V586_QRTR_COMPANION_BLOCKER_PLAN_2026-05-22.md`
- Evidence: `tmp/wifi/v586-qrtr-companion-blocker/`
- Inputs:
  - V585 companion/private firmware mount proof: `tmp/wifi/v585-companion-firmware-mount-start-only/`
  - Android reference dmesg/process evidence: `tmp/wifi/v206-android-icnss-cnss-map/` and V521/V524 recapture evidence
  - V571/V582 QRTR/modem readiness classifiers

## Guardrails

- No boot image flash.
- No reboot or recovery handoff.
- No PID1/native-init boot hook.
- No daemon start from V586.
- No qcwlanstate/sysfs driver-state write.
- No Wi-Fi HAL or `IWifi.start()`.
- No supplicant/hostapd/wificond.
- No scan/connect/link-up/DHCP/routing.
- No external ping.

## V586 Result

```text
decision: v586-qrtr-control-plane-not-entered
pass: True
reason: V585 companions and private firmware mounts were alive, but QRTR proc table was absent, QIPCRTR sockets stayed 0, and Android-only QRTR/QMI/WLAN-PD/WLFW markers remain missing
next: do not retry qcwlanstate/HAL yet; next prove the modem/QRTR readiness input path in a host-controlled post-boot window
device_commands_executed: True
device_mutations: False
daemon_start_executed: False
wifi_bringup_executed: False
```

## QRTR State

```text
current_qipcrtr_protocol_present=True
current_qipcrtr_sockets=0
current_proc_net_qrtr_present=False
current_dev_qrtr_present=False
v585_private_firmware_mounts_ready=True
v585_qipcrtr_sockets_net_window=0
v585_qrtr_proc_open_error=True
v585_qrtr_nameservice_readback=0
```

## Companion Socket Counts

V585 companion children had sockets, but those sockets did not become a counted
`QIPCRTR` socket surface:

```text
qrtr_ns=1
rmt_storage=2
tftp_server=11
pd_mapper=2
cnss_diag=4
cnss_daemon=10
```

## Marker Delta

Android reference has all lower readiness markers:

```text
qrtr_modem_readiness_rx=1
qrtr_modem_readiness_tx=1
sysmon_qmi_ready=5
service_notifier_ready=2
wlan_pd_indication=2
wlfw_start=1
wlfw_thread=1
qmi_server_connected=1
bdf_regdb=1
bdf_bdwlan=1
wlan_fw_ready=2
wlan0_event=21
```

V585 and current native still lack the lower markers:

```text
qrtr_modem_readiness_rx=0
qrtr_modem_readiness_tx=0
sysmon_qmi_ready=0
service_notifier_ready=0
wlan_pd_indication=0
wlfw_start=0
wlfw_thread=0
qmi_server_connected=0
bdf_regdb=0
bdf_bdwlan=0
wlan_fw_ready=0
wlan0_event=0
```

CNSS netlink activity is present in native, but it remains insufficient because
it does not advance to QRTR modem readiness, WLFW, QMI server connected, BDF,
firmware ready, or `wlan0`.

## Interpretation

- V584/V585 resolved the firmware/modem mount visibility concern.
- V585 proved companion process launch, Android-like identities, SELinux exec
  contexts, private firmware mounts, and cleanup.
- V586 confirms the missing piece is still below qcwlanstate/HAL and below
  `cnss-daemon` netlink activity.
- Retrying qcwlanstate, HAL start, scan/connect, or external ping now would
  likely reproduce the same timeout/error path.
- The next useful gate is a host-controlled post-boot QRTR/modem readiness input
  proof, not another boot-time PID1 probe and not another same-window HAL retry.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_qrtr_companion_blocker_v586.py
python3 scripts/revalidation/native_wifi_qrtr_companion_blocker_v586.py plan
python3 scripts/revalidation/native_wifi_qrtr_companion_blocker_v586.py run
git diff --check -- scripts/revalidation/native_wifi_qrtr_companion_blocker_v586.py \
  docs/plans/NATIVE_INIT_V586_QRTR_COMPANION_BLOCKER_PLAN_2026-05-22.md
```

## References

- Linux QRTR AF_QIPCRTR implementation: `https://codebrowser.dev/linux/linux/net/qrtr/af_qrtr.c.html`
- Android common QRTR implementation reference: `https://android.googlesource.com/kernel/common/+/d4d74449367e/net/qrtr/qrtr.c`
- Android service-notifier reference: `https://android.googlesource.com/kernel/msm/+/refs/heads/android-msm-crosshatch-4.9-s-preview-1/drivers/soc/qcom/service-notifier.c`
- Android sysmon-qmi reference: `https://android.googlesource.com/kernel/msm/+/refs/heads/android-msm-crosshatch-4.9-s-preview-1/drivers/soc/qcom/sysmon-qmi.c`

## Next Gate

Recommended V587:

1. Stay post-boot and host-controlled; do not reintroduce PID1 bootprobe.
2. Capture modem/rpmsg/subsys/QRTR endpoint state immediately before, during,
   and after the bounded companion window.
3. Prove whether the missing readiness input is a kernel/modem event, namespace
   visibility issue, QRTR endpoint registration issue, or Android service-order
   dependency.
4. Keep qcwlanstate, HAL start, scan/connect, DHCP, routing, and external ping
   blocked until a lower QRTR/QMI/BDF/FW marker changes.
