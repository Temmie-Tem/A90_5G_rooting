# Native Init V736 Service-180 to MHI Gap Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_service180_to_mhi_gap_v736.py`
- evidence: `tmp/wifi/v736-service180-to-mhi-gap/`
- latest pointer: `tmp/wifi/latest-v736-service180-to-mhi-gap.txt`
- decision: `v736-service180-to-service74-mhi-gap-classified`
- status: `pass`

## Scope Result

V736 was host-only. It used V735, Android V622, and V627 manifests only.

It did not contact the device, write sysfs, open `subsys_modem`, open `esoc0`,
start daemons, start service-manager, start Wi-Fi HAL, scan/connect, use
credentials, run DHCP, change routes, external ping, write a boot image, or
write a partition.

## Key Results

| check | result |
| --- | --- |
| V735 service line | service-notifier connected to `180 service` |
| V735 service `74` | absent |
| V735 WLAN-PD/MHI/QCA6390/WLFW/BDF/`wlan0` | all absent |
| V735 service `69` readback | service events `0`, end-of-list `2`, QMI payloads `0` |
| V735 QCA surface | ICNSS bound, QCA6390 device visible but driver link absent |
| V735 MHI/PCI surface | MHI devices `0`, PCI devices `0` |
| Android V622 | service `74` appears `6.561ms` after service `180`; WLAN-PD/WLFW/BDF/`wlan0` follow |
| V627 | service `180` reproduced for `31.65s`, but service `74`/WLAN-PD/WLFW stayed absent |

## Interpretation

V736 narrows the blocker:

```text
service 180 appears
  + service 74 is absent
  + WLAN-PD is absent
  + QCA6390 is visible but unbound
  + MHI/PCI devices are absent
  + service 69 readback is empty
  => lower service-74/WLAN-PD publisher or MHI trigger gap
```

This is still below HAL/connect. Starting Wi-Fi HAL, scan/connect, using
credentials, DHCP, route changes, or external ping would be premature until
service `74`/WLAN-PD/MHI/WLFW advances.

## Evidence Summary

Current V735:

```text
service_notifier_180=1
service_notifier_74=0
wlan_pd=0
mhi=0
qca6390=0
wlfw=0
bdf=0
wlan0=0
qca6390_driver_link=false
mhi_devices_count=0
pci_devices_count=0
```

Android V622 timing:

```text
service_180_to_74=6.561ms
service_180_to_wlan_pd=2427.362ms
service_180_to_wlfw_start=1415.75ms
wlan_pd_to_qmi_server_connected=2.509ms
```

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_service180_to_mhi_gap_v736.py

python3 scripts/revalidation/native_wifi_service180_to_mhi_gap_v736.py \
  --out-dir tmp/wifi/v736-service180-to-mhi-gap-plan plan

python3 scripts/revalidation/native_wifi_service180_to_mhi_gap_v736.py \
  --out-dir tmp/wifi/v736-service180-to-mhi-gap run
```

The final run returned:

```text
decision: v736-service180-to-service74-mhi-gap-classified
pass: True
device_commands_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Next Gate

V737 should stay below HAL/connect and classify the lower service-74/WLAN-PD
publisher trigger:

1. identify what Android has between service `180` and service `74` that native
   lacks;
2. avoid raw `esoc0`, DSP boot-node writes, and blind HAL retries;
3. use existing Android V622/V614/V620 evidence before choosing any live action;
4. keep scan/connect, credentials, DHCP, routes, and external ping blocked until
   WLFW/BDF/`wlan0` appears.
