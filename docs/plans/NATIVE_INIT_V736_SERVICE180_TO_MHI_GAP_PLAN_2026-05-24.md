# Native Init V736 Service-180 to MHI Gap Plan

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_service180_to_mhi_gap_v736.py`
- evidence target: `tmp/wifi/v736-service180-to-mhi-gap/`

## Goal

Classify the new V735 state without another live mutation:

```text
native V735 reaches service-notifier 180
  -> Android reaches service 74, WLAN-PD, WLFW, BDF, wlan0
  -> native still has no service 74, WLAN-PD, MHI, service 69, or wlan0
```

V736 decides whether the next gate should remain below Wi-Fi HAL/connect and
target the lower service-74/WLAN-PD publisher path.

## Inputs

| input | purpose |
| --- | --- |
| V735 | current-build CNSS-only live result |
| Android V622 | successful service `180 -> 74 -> WLAN-PD -> WLFW -> wlan0` reference |
| V627 | older warning-free native post-180 result showing service `74` remains absent |

## Scope

V736 is host-only.

It does not contact the device, open `subsys_modem`, open `esoc0`, write sysfs,
start daemons, start service-manager, start Wi-Fi HAL, scan/connect, use
credentials, run DHCP, change routes, external ping, write a boot image, or
write a partition.

## Expected Classification

If V735 confirms service `180` but no service `74`/WLAN-PD/MHI/WLFW/`wlan0`,
and Android V622 confirms service `74` appears `6.561ms` after service `180`,
then the next gate is not HAL/connect. It is a lower publisher/MHI trigger
classifier.

## Validation Commands

```bash
python3 -m py_compile scripts/revalidation/native_wifi_service180_to_mhi_gap_v736.py

python3 scripts/revalidation/native_wifi_service180_to_mhi_gap_v736.py \
  --out-dir tmp/wifi/v736-service180-to-mhi-gap-plan plan

python3 scripts/revalidation/native_wifi_service180_to_mhi_gap_v736.py \
  --out-dir tmp/wifi/v736-service180-to-mhi-gap run
```
