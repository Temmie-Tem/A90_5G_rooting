# Native Init V1830 QIPCRTR Local-Node Bind Source Build

## Summary

- Cycle: `V1830`
- Type: source/build-only rollbackable QIPCRTR observed-local-node bind observer test boot artifact
- Decision: `v1830-qipcrtr-local-node-bind-source-build-pass`
- Result: PASS
- Reason: helper v351 keeps the bounded lower publication route and adds one observed-local-node AF_QIPCRTR bind-state snapshot at `net_window`.
- Manifest: `tmp/wifi/v1830-qipcrtr-local-node-bind-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1830-qipcrtr-local-node-bind-test-boot/boot_linux_v1830_qipcrtr_local_node_bind.img`
- Boot SHA256: `2763b697b96c76e21920e7af93ea04441255c492786cc1159042b5a17eaf6a33`
- Init: `A90 Linux init 0.9.160 (v1830-qipcrtr-local-node-bind)`
- Helper marker: `a90_android_execns_probe v351`
- Helper SHA256: `07d6a372705631917f82223f9187d39b945c862b6b8aac7f4cb9f8fd7967c941`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1830/dev/__properties__`
- Base route remains the bounded lower handoff observer and retains the unbound plus node-zero bind snapshots.
- Added local-node bind prefix: `wlan_pd_qipcrtr_local_node_bind_state.net_window.*`.
- Added observed-local-node bind operations: protocol summary before open, AF_QIPCRTR/SOCK_DGRAM open, pre-bind `getsockname`, bind using observed local node and port `0`, post-bind `getsockname`, protocol summary while bound, close, and protocol summary after close.
- Explicit non-actions: `no_connect=1`, `no_send=1`, `no_qrtr_lookup_send=1`, `no_qrtr_control_payload=1`, and `no_service_start=1`.
- Still excluded: direct `/dev/subsys_esoc0` open, fake-ONLINE, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC writes, `boot_wlan`, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Expected Live Discriminator

- V1831 should run one rollbackable live gate with this artifact only if the observed-local-node bind snapshot is accepted as the next bounded surface.
- `qipcrtr-local-node-bind-gets-local-port-passive`: bind succeeds, `getsockname` returns a non-zero local port, and service74/wlan_pd still remain absent.
- `qipcrtr-local-node-bind-fails`: open succeeds but observed-local-node bind fails; capture errno and stop.
- `lower-publication-progress`: service 74, wlan_pd, WLFW service 69, MHI, or `wlan0` appears; stop before Wi-Fi HAL/scan/connect.
- `safety-regression`: any forbidden side effect appears; stop and roll back.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
