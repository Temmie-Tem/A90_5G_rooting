# Native Init V609 Post-Sysmon Observer Live Report

- date: `2026-05-23 KST`
- status: `classified`; Wi-Fi external ping is **not** complete
- run evidence: `tmp/wifi/v609-post-sysmon-20260523-004918/`
- deploy evidence: `tmp/wifi/v609-post-sysmon-20260523-004918/v103-deploy-run/`
- V401 evidence: `tmp/wifi/v609-post-sysmon-20260523-004918/v401-current/`
- V490 evidence: `tmp/wifi/v609-post-sysmon-20260523-004918/v490-current/`
- preflight evidence: `tmp/wifi/v609-post-sysmon-20260523-004918/v609-observer-preflight/`
- live evidence: `tmp/wifi/v609-post-sysmon-20260523-004918/v609-observer-live/`

## Scope

V609 deployed helper v103, refreshed current-boot SELinux prerequisites, and ran
a bounded post-sysmon observer window without CNSS children.

The observer started only:

```text
qrtr_ns,rmt_storage,tftp_server,pd_mapper
```

It did not start `cnss_diag`, `cnss-daemon`, service-manager, Wi-Fi HAL,
`wificond`, supplicant, or hostapd. It did not write `qcwlanstate`, send QMI
payloads, scan/connect/link-up, use credentials, run DHCP, change routes, ping
externally, flash boot images, or write persistent partitions.

## Preconditions

```text
helper_v103_sha256: a63758a4cd10a4d0b227e2b85516ecc65575cca30fe863d332b802fabae4f57e
helper_v103_marker: a90_android_execns_probe v103
v401_decision: toybox-selinuxfs-mount-live-executor-run-pass
v490_decision: v490-selinux-policy-load-proof-pass
v609_preflight_decision: v609-post-sysmon-observer-preflight-ready
```

The deploy wrapper exited non-zero because its post-deploy preflight correctly
noticed that V490 was not fresh for the current boot yet. The actual helper
transfer succeeded, and the remote helper SHA and marker were verified before
V401/V490 were refreshed and the V609 observer was run.

## Result

```text
decision: v609-service-notifier-pre-cnss-missing
pass: True
reason: QRTR TX and modem sysmon-qmi appeared, but service-notifier did not appear in the no-CNSS observer window
wifi_bringup_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Marker Counts

```text
qrtr_rx: 1
qrtr_tx: 1
sysmon_qmi: 1
service_notifier: 0
wlan_pd: 0
qmi_server_connected: 0
wlfw: 0
bdf: 0
wlan_fw_ready: 0
wlan0: 0
kernel_warning: 0
```

The native lower modem path still reaches QRTR RX, QRTR TX, and modem
`sysmon-qmi`. It does not publish the service-notifier marker before CNSS,
service-manager, or Wi-Fi HAL enter.

## QRTR Readback

```text
allowed: 1
send_attempted: 1
result: complete
service_events: 0
timeouts: 0
end_of_list: 2
qmi_attempted: 0
```

WLFW service `69` instances `0` and `1` both returned clean end-of-list with no
service events. The helper also observed `QIPCRTR` present but zero QRTR sockets
before, during, and after the companion window.

## Observer Contract

```text
observed_order: qrtr_ns,rmt_storage,tftp_server,pd_mapper
child_started: 4
cnss_diag_started: False
cnss_daemon_started: False
service_manager_started: False
wifi_bringup_executed: False
```

All four lower companion processes were observable and postflight-safe. They
were stopped by the bounded window cleanup, not left resident.

## Runtime State

```text
mss_after_holder: ONLINE
mss_after_companion: ONLINE
mdm3_after_companion: OFFLINING
firmware_class_path: /vendor/firmware_mnt/image
mounted_firmware_mnt: True
mounted_firmware_modem: True
modem_blob_visible_under_firmware_modem: True
```

This keeps the modem/PIL fix from V594-V596 intact: the system reaches modem
`ONLINE` and `sysmon-qmi`. The remaining blocker is no longer basic firmware
visibility or QRTR RX/TX.

## Cleanup State

V609 used reboot cleanup. The reboot command lost its final END marker because
the device restarted, but post-reboot verification saw the expected native
version and healthy status.

```text
post_reboot_version_seen: true
post_reboot_status_healthy: true
```

## Interpretation

V609 confirms that the missing `service-notifier` marker is not caused by CNSS
children starting too early. Even with only `qrtr-ns`, `rmt_storage`,
`tftp_server`, and `pd-mapper`, native reaches `sysmon-qmi` but does not produce
the pre-CNSS service-notifier publication that Android shows shortly after
sysmon.

The current blocker is therefore a lower modem QMI publication precondition gap:

1. modem firmware loading and `subsys_modem` hold are sufficient for QRTR
   RX/TX and modem `sysmon-qmi`;
2. WLFW QRTR service `69` remains unregistered;
3. service-notifier does not appear without CNSS, so another Wi-Fi HAL or
   scan/connect retry remains premature;
4. the next proof should compare Android/native lower modem publication
   surfaces before starting more userspace.

## Next Gate

Recommended V610:

1. Run a host-only classifier over Android reference dmesg and V609 native
   evidence.
2. Compare the exact post-`sysmon-qmi` publication window for service-notifier,
   QRTR services, `QIPCRTR` socket counts, rpmsg/service-registry surfaces, and
   subsystem state.
3. Identify which lower precondition Android has and native lacks before
   retrying CNSS, service-manager, Wi-Fi HAL, or link-up.
