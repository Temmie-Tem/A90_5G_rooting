# Native Init V738 Modem/WLAN/MHI Observer Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_modem_wlan_mhi_observer_v738.py`
- evidence: `tmp/wifi/v738-modem-wlan-mhi-observer/`
- decision: `v738-mss-online-mdm3-wlan-mhi-gap-classified`
- pass: `true`

## Summary

V738 executed the V737-selected bounded live observer. It refreshed current-boot
SELinux prerequisites, ran the firmware-mounted `subsys_modem` holder window,
started lower companions plus `cnss_diag`/`cnss-daemon` start-only, and rebooted
for cleanup.

The safe window did not reach Wi-Fi bring-up. It did sharpen the blocker:

```text
mss: OFFLINING -> ONLINE -> ONLINE
mdm3: OFFLINING -> OFFLINING -> OFFLINING
QCA6390 device: captured
QCA6390 driver link: absent
MHI devices: 0
PCI devices: 0
WLFW/service 69: 0
BDF: 0
wlan0: 0
```

## Key Results

| check | result |
| --- | --- |
| V737 reference | pass; routing stayed on modem/WLAN/MHI prerequisite observer |
| base observer | pass; CNSS-only window completed below HAL/connect |
| safety boundary | pass; no service-manager, no Wi-Fi HAL, no scan/connect, no external ping |
| WLAN static surface | pass; `/sys/module/wlan` exists, `/proc/modules` has no `wlan` |
| lower state | finding; `mss` reaches `ONLINE`, `mdm3` does not continue |
| MHI/WLFW surface | finding; QCA surface captured but MHI/WLFW/BDF/`wlan0` absent |
| cleanup | pass; reboot returned to healthy native init |

## Evidence Summary

V738 lower state:

```text
mss_before=OFFLINING
mss_after_holder=ONLINE
mss_after_companion=ONLINE
mdm3_before=OFFLINING
mdm3_after_holder=OFFLINING
mdm3_after_companion=OFFLINING
qrtr_rx_seen=True
qrtr_services={180: 0, 74: 0, 69: 0}
service69_readback_events=0
qmi_attempted=0
```

MHI/QCA surface:

```text
icnss_driver_link=True
qca6390_device_captured=True
qca6390_driver_link=False
mhi_devices_count=0
pci_devices_count=0
wlan0_netdev=False
wlan_params_captured=True
kernel_warning=0
```

The base V735-compatible observer decision inside V738 was:

```text
v735-current-cnss-only-sysmon-gap-classified
```

That means this current run restored QRTR TX/sysmon but did not reproduce
service publication, MHI, WLFW, or `wlan0`.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_modem_wlan_mhi_observer_v738.py

python3 scripts/revalidation/native_wifi_modem_wlan_mhi_observer_v738.py \
  --out-dir tmp/wifi/v738-modem-wlan-mhi-observer-plan plan

python3 scripts/revalidation/a90ctl.py --timeout 10 hide

python3 scripts/revalidation/wifi_selinuxfs_toybox_mount_live_executor.py \
  --out-dir tmp/wifi/v738-v401-current-run-retry \
  --approval-phrase 'approve v401 toybox mount selinuxfs runtime surface only; no daemon start and no Wi-Fi bring-up' \
  --apply --assume-yes run

python3 scripts/revalidation/a90ctl.py --timeout 30 mountsystem ro

python3 scripts/revalidation/native_selinux_policy_load_proof_v490.py \
  --out-dir tmp/wifi/v738-v490-current-run \
  --expect-version 'A90 Linux init 0.9.68 (v724)' \
  --helper-sha256 547232ddb352740bb7a7f1d0f9116162584e34a536b9d9b77869ed8d838e7c89 \
  --approval-phrase 'approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up' \
  --apply --assume-yes run

python3 scripts/revalidation/native_wifi_modem_wlan_mhi_observer_v738.py \
  --out-dir tmp/wifi/v738-modem-wlan-mhi-observer \
  --v490-manifest tmp/wifi/v738-v490-current-run/manifest.json \
  run
```

Final V738 output:

```text
decision: v738-mss-online-mdm3-wlan-mhi-gap-classified
pass: True
service_manager_start_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

Post-cleanup native status returned:

```text
init: A90 Linux init 0.9.68 (v724)
selftest: pass=11 warn=1 fail=0
```

## Next Gate

V739 should stay below HAL/connect and compare Android/native lower trigger
state for the `mdm3`/WLAN-PD continuation:

1. capture Android `mss`/`mdm3` state, firmware names, and early `mdm3`/WLAN-PD
   dmesg timing from existing Android references if sufficient;
2. compare native V738 `mss=ONLINE, mdm3=OFFLINING` against Android;
3. identify whether the missing native edge is `mdm3` activation, WLAN-PD
   publication, or CNSS2/MHI transition;
4. keep Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping
   blocked until WLFW/BDF/`wlan0` appears.
