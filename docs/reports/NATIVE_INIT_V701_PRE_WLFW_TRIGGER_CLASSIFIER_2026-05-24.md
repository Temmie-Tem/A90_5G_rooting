# Native Init V701 Pre-WLFW Trigger Classifier Report

- date: `2026-05-24 KST`
- status: `host-only-pass`; Wi-Fi external ping is **not** complete
- classifier: `scripts/revalidation/native_wifi_pre_wlfw_trigger_classifier_v701.py`
- evidence: `tmp/wifi/v701-pre-wlfw-trigger-classifier/`
- decision: `v701-pre-wlfw-kernel-progression-gap-classified`

## Scope

V701 consumed existing V700 evidence only. It did not contact the device, mount
filesystems, start daemons or service managers, start Wi-Fi HAL, scan/connect,
use credentials, run DHCP, change routes, ping externally, write sysfs/debugfs,
or write boot images/partitions.

## Result

| check | result |
| --- | --- |
| V700 provider-first gate input | pass |
| initial CNSS suppressed | pass |
| `vendor.qcom.PeripheralManager` exact query | pass |
| post-provider CNSS retry started | pass |
| CNSS Binder failure removed | finding |
| `cnss-daemon` reaches netlink/`cld80211` only | finding |
| ICNSS/QCA/WLFW/BDF/`wlan0` progression | absent |
| `pm_qos` warning attribution | audio deferred-probe secondary signal |
| Wi-Fi bring-up safety gate | pass: still blocked |

## Key Evidence

V700 counts:

```text
service_notifier_180=1
service_notifier_74=1
cnss_daemon_netlink=5
cnss_daemon_cld80211=2
cnss_binder_transaction_failed=0
binder_transaction_failed=0
qmi_server_connected=0
wlfw_start=0
bdf_bdwlan=0
wlan_fw_ready=0
wlan0=0
```

Timeline:

```text
service_74 first_ts=83.708442
pm_qos_warning first_ts=83.716217
cnss_diag_netlink first_ts=83.928730
cnss_daemon_netlink first_ts=87.540813
cnss_cld80211 first_ts=87.540955
icnss_qmi_connected=0
pcie_mhi_wlan=0
wlfw_start=0
bdf_bdwlan=0
wlan0=0
```

The `pm_qos` warning call trace is not a WLAN/cnss2 trace. It is tied to audio
deferred probe:

```text
msm_asoc_machine_probe
platform_drv_probe
driver_probe_device
deferred_probe_work_func
```

Read-only state after the companion run:

```text
mss=ONLINE
mdm3=OFFLINING
rpmsg_has_modem_ipcrtr=True
proc_net_dev_has_wlan0=False
```

## Interpretation

V701 moves the blocker past the old Binder hypothesis:

- the V698 initial pre-provider CNSS Binder confounder is removed;
- the V700 post-provider CNSS retry does not emit a CNSS Binder failure;
- userspace reaches `cld80211` via netlink;
- no kernel-side ICNSS/QCA/WLFW/BDF/`wlan0` marker follows.

The remaining likely blocker is a kernel/platform progression gap between
provider-confirmed CNSS retry and WLFW service `69`, not a scan/connect or Wi-Fi
HAL problem. Wi-Fi bring-up remains unsafe because no `wlan0` exists.

## Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_pre_wlfw_trigger_classifier_v701.py

python3 scripts/revalidation/native_wifi_pre_wlfw_trigger_classifier_v701.py \
  --out-dir tmp/wifi/v701-pre-wlfw-trigger-plan-check plan

python3 scripts/revalidation/native_wifi_pre_wlfw_trigger_classifier_v701.py \
  --out-dir tmp/wifi/v701-pre-wlfw-trigger-classifier run
```

Results:

```text
v701-pre-wlfw-trigger-classifier-plan-ready
v701-pre-wlfw-kernel-progression-gap-classified
```

## Next Gate

Plan V702 as a bounded read-only cnss2/icnss/QCA platform-state capture in the
provider-first retry window:

- capture `/sys/bus/platform/drivers/cnss2`, ICNSS, WLAN, MHI, PCIe, and related
  read-only sysfs surfaces where present;
- capture dmesg around service `180/74`, CNSS retry, and any ICNSS/QCA marker;
- do not start Wi-Fi HAL or attempt scan/connect/DHCP/external ping until
  WLFW/BDF/`wlan0` advances.
