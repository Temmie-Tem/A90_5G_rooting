# Native Init V2084 Macloader Pre-CNSS Source Build

## Summary

- Cycle: `V2084`
- Type: source/build-only native route that adds one Android-parity `macloader` active driver-start child before `cnss-daemon`.
- Decision: `v2084-macloader-pre-cnss-source-build-pass`
- Result: PASS
- Reason: helper v405 keeps the V2082 light internal-modem route and adds only `/vendor/bin/hw/macloader` with Android init parity (`user wifi`, `group wifi inet net_raw net_admin`, `NET_ADMIN NET_RAW SYS_MODULE`, `u:r:macloader:s0`) before `cnss-daemon`. This is an explicit active driver-start gate, not a read-only observer; it still excludes Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, DIAG, strace, QRTR matrix, QMI send, eSoC/PCIe/GDSC/PMIC/GPIO paths, and firmware/partition writes.
- Manifest: `tmp/wifi/v2084-macloader-pre-cnss-test-boot/manifest.json`
- Boot image: `tmp/wifi/v2084-macloader-pre-cnss-test-boot/boot_linux_v2084_macloader_pre_cnss.img`
- Boot SHA256: `413317f1127bfe62125028679866cd735a8ae0e5c1c870148edf3bfbeb923c8b`
- Init: `A90 Linux init 0.9.220 (v2084-macloader-pre-cnss)`
- Helper marker: `a90_android_execns_probe v405`
- Helper SHA256: `7fb0e09b064d854809f1e0e1b3bd602f65f9d9bd59d3183778ce7cd6971ed2fb`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-post-pm-lower-state-observer-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v2084/dev/__properties__`
- Light firmware trace: `True`
- Order: `qrtr_ns,pd_mapper,rmt_storage,tftp_server,subsys_modem_holder,cnss_diag,macloader,cnss_daemon`.
- Kept: clean-DSP companion, `pm-service`, `/dev/subsys_modem` holder, stock `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, `pd-mapper`, Android-parity RFS bridges, cap/BDF/cal probes, PerMgr/WLFW compact summaries, post-BDF surface summary, and long lower-window hold.
- Excluded: Wi-Fi HAL, wificond, supplicant, hostapd, scan/connect, credentials, DHCP/routes, external ping, DIAG mask/log-mode, passive DIAG, boot-time QRTR matrix, rild/cnss/pm-service strace, `tftp_server` ptrace, private SDX50M route, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan/bind, platform unbind, PMIC/GPIO/GDSC/regulator writes, forced RC1/case, and firmware/partition writes.

## Property Runtime

- `persist.vendor.cnss-daemon.kmsg_logging`: `1` in `u:object_r:vendor_default_prop:s0`
- `persist.vendor.cnss-daemon.debug_level`: `4` in `u:object_r:vendor_default_prop:s0`

## Safety Scope

This build script performed host-side source/build work only. The eventual V2085 live handoff is rollbackable and intentionally permits the Android `macloader` driver-start action while still forbidding Wi-Fi HAL/scan/connect/credentials/DHCP/routes/external ping and off-path modem/PCIe/GDSC/PMIC/GPIO actions.
