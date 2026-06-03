# Native Init V1858 SDX50M Bridge Host Preflight

## Summary

- Cycle: `V1858`
- Type: host-only availability preflight for a future one-run SDX50M bridge gate
- Decision: `v1858-host-ready-device-command-missing-host-pass`
- Label: `host-ready-device-command-missing`
- Result: PASS
- Reason: Host/NCM/USB surfaces are present, but adb has no listed device and a90ctl is unavailable, so a future live bridge gate cannot be attempted from this shell yet
- Evidence: `tmp/wifi/v1858-sdx50m-bridge-host-preflight`

## Host State

- git clean: `True`
- NCM up/IPv4/default route: `True` / `True` / `True`
- NCM lines: `['enx0000000005e1  UP             192.168.0.8/24 fe80::f944:4e7a:2cb2:efcd/64']`
- USB Android present: `True` lines `['Bus 002 Device 042: ID 04e8:6861 Samsung Electronics Co., Ltd SAMSUNG_Android']`
- adb available/device count: `True` / `0`
- a90ctl available: `False`

## Input

- V1857: `v1857-artifact-plumbing-dry-run-ready-host-pass` / `artifact-plumbing-dry-run-ready` / pass `True`

## Safety Scope

Host-only. This preflight did not issue live device commands, flash, reboot, stage properties, start actors, open `/dev/subsys_esoc0`, start `boot_wlan`, issue restart-PD request, force RC1, fake ONLINE state, write PMIC/GPIO/GDSC controls, perform eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, or external ping.

## Next

- Do not proceed to Wi-Fi HAL/scan/connect unless WLFW service 69 and `wlan0` are present.
- Before any future live bridge gate, restore a usable device command surface from this shell: `a90ctl` path or another reviewed transport plus a visible target device.
