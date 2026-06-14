# Native Init V1929 Libqmi CCI Service-ID Observer Source Build

## Summary

- Cycle: `V1929`
- Type: source/build-only rollbackable internal-modem libqmi CCI service-ID observer test boot artifact
- Decision: `v1929-libqmi-service-id-uprobe-observer-source-build-pass`
- Result: PASS
- Reason: V1925 localized the live stall inside `qmi_client_init_instance`; V1926 mapped the libqmi wait loop; helper v362 adds read-only service-list and new-server service-ID fetches to the `libqmi_cci.so` uprobe target group.
- Manifest: `tmp/wifi/v1929-libqmi-service-id-uprobe-observer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1929-libqmi-service-id-uprobe-observer-test-boot/boot_linux_v1929_libqmi_service_id_uprobe_observer.img`
- Boot SHA256: `a56c7adce92d0b460dff77b8d05c55f7516c2151fc6545afbb89bfad04378c74`
- Init: `A90 Linux init 0.9.175 (v1929-libqmi-service-id-uprobe-observer)`
- Helper marker: `a90_android_execns_probe v362`
- Helper SHA256: `7d1488e7979d6530050c7d2de000517dccad5cc86078d7697114dbd899bf8730`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1929/dev/__properties__`
- Base route remains the bounded internal-modem post-PM lower observer: clean firmware mounts, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, service-locator/domain-list, service-notifier listener, and WLFW QRTR readback.
- Added libqmi labels: `libqmi_get_service_list_entry`, `libqmi_get_service_list_lookup_call`, `libqmi_get_service_list_lookup_ret`, `libqmi_client_init_instance_entry`, `libqmi_initial_get_service_instance_ret`, `libqmi_initial_client_init_ret`, `libqmi_notifier_init_call`, `libqmi_notifier_init_ret`, `libqmi_wait_call`, `libqmi_wait_return`, `libqmi_loop_get_service_instance_ret`, `libqmi_loop_client_init_ret`, `libqmi_init_timeout_path`, `libqmi_init_return`, `libqmi_signal_wait_entry`, `libqmi_signal_wait_timedwait`, `libqmi_signal_wait_timeout_store`, `libqmi_xport_new_server_entry`, `libqmi_xport_new_server_service`, `libqmi_xport_new_server_signal`, `libqmi_xport_new_server_callback_call`.
- New discriminator separates WLFW service-list lookup for service 69 from non-WLFW transport new-server wake edges.
- Stop condition: WLFW service 69, `wlan_pd`, requested `wlanmdsp`, `wlfw_ind_register_qmi`, `wlfw_cap_qmi`, or `wlan0` appears; do not proceed to HAL/scan/connect in this unit.
- Excluded by construction: private SDX50M mount, `/dev/subsys_esoc0` open, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, restart-PD request, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Expected Live Discriminator

- `qmi-client-init-instance-waiting-no-new-server`: WLFW worker is blocked in libqmi wait and no libqmi new-server edge arrived.
- `qmi-client-init-instance-new-server-no-wake`: libqmi saw a new-server edge but the wait loop did not wake/progress.
- `wlfw-service69-not-published-libqmi`: WLFW service-list lookups ask for service 69, but no service-69 new-server publication arrives.
- `qmi-client-init-instance-timeout`: timeout path at `libqmi_cci.so+0x7954` hit.
- `qmi-client-init-instance-returned`: libqmi returned; classify the caller/downstream state before any HAL work.
- `safety-regression`: any hard-stop side effect appears; stop and roll back.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
