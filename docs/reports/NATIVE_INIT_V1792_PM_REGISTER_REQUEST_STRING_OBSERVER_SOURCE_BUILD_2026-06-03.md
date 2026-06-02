# Native Init V1792 PM Register Request String Observer Source Build

## Summary

- Cycle: `V1792`
- Type: source/build-only rollbackable WLAN-PD PM register request string observer test boot artifact
- Decision: `v1792-pm-register-request-string-observer-source-build-pass`
- Result: PASS
- Reason: helper v338 keeps the V1790 PM-service devnode fetchargs and adds tracefs fetchargs to the PM-service register entry, string-compare, and no-peripheral return so the next live gate can capture the exact peripheral name requested by `cnss-daemon` before any private devnode repair.
- Manifest: `tmp/wifi/v1792-pm-register-request-string-observer-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1792-pm-register-request-string-observer-test-boot/boot_linux_v1792_pm_register_request_string_observer.img`
- Boot SHA256: `97684b05bed3ab302751ae9347475d8345530077b5b67652844208fdefdfdb61`
- Init: `A90 Linux init 0.9.147 (v1792-pm-register-request-string-observer)`
- Helper marker: `a90_android_execns_probe v338`
- Helper SHA256: `d1de658ad211a7de155ba48d83ddb2a3e928cb25f577ef88bf1bca05c5a61ddb`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1792/dev/__properties__`
- Base route remains the bounded V1790 service-object route: service managers, firmware-serve stack, `pm_proxy_helper`, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, and stock `cnss-daemon`.
- Added observer only: PM-service register tracefs fetchargs record the requested peripheral string, client string, string-compare operands, and no-peripheral return string.
- V1790 devnode observer remains present to correlate the requested peripheral with discovered PM-service candidate name/devnode records.
- Still excluded: full `pm-proxy`, `boot_wlan`, restart-PD request, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and external ping.

## Fetchargs

- `pm_server_register_entry`: `peripheral=+0(%x1):string client=+0(%x2):string out_client=%x4 out_state=%x5`
- `pm_server_register_strcmp_call`: `candidate=+0(%x0):string requested=+0(%x1):string`
- `pm_server_register_no_peripheral`: `peripheral=+0(%x26):string`
- `pm_service_add_peripheral_entry`: `record=%x1 name=+4(%x1):string devnode=+68(%x1):string`
- `pm_service_add_peripheral_known_name`: `record=%x25 name=+0(%x21):string devnode=+68(%x25):string`
- `pm_service_add_peripheral_init_fail`: `name=+0(%x21):string devnode=+0(%x25):string`

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Expected Live Discriminator

- V1793 should run one rollbackable live gate with this artifact and classify the exact PM register request string before any devnode repair.
- `pm-register-request-sdx50m`: CNSS requests `SDX50M`; host-only plan a private devnode-existence parity repair without opening `/dev/subsys_esoc0`.
- `pm-register-request-modem-or-other`: CNSS requests a different peripheral; classify list population and request/candidate mismatch before any repair.
- `pm-register-fetcharg-unavailable`: tracefs fetchargs cannot recover the string; fall back to a narrower host-only disassembly or non-mutating uprobe plan.
- `pm-register-list-commit-progress`: PM-service list commit appears and register progresses; stop and classify the new downstream label.
- The gate remains one-run: do not autonomously chain into PM repair, WLAN-PD cascade, Wi-Fi HAL, scan/connect, DHCP/routes, or external ping.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
