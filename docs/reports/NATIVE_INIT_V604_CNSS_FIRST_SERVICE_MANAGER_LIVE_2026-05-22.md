# Native Init V604 CNSS-First Service-Manager Live Report

- date: `2026-05-22 KST`
- status: `classified`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_modem_holder_cnss_first_service_manager_v604.py`
- evidence: `tmp/wifi/v604b-cnss-first-service-manager-live/`

## Scope

V604 live proof deployed helper v102, refreshed current boot SELinux/runtime
prerequisites, ran a bounded `subsys_modem` holder window, started CNSS before
service-manager, performed WLFW QRTR nameservice readback, and reboot-cleaned
the device.

It did not start Wi-Fi HAL, `wificond`, supplicant, or hostapd. It did not write
`qcwlanstate`, scan, connect, use credentials, run DHCP, change routes, ping
externally, write a boot image, or perform persistent partition writes.

## Preconditions

```text
helper_v102_deploy_decision: execns-helper-v102-deploy-pass
helper_v102_sha256: 8214098f750c77f982975f46a8b6af2a8461b6e4520962488b7daf9e013251d3
v401_selinuxfs_decision: toybox-selinuxfs-mount-live-executor-run-pass
v490_policy_load_decision: v490-selinux-policy-load-proof-pass
v604_preflight_decision: v604-cnss-first-service-manager-preflight-ready
```

## Result

```text
decision: v604-cnss-first-no-service-notifier-binder-gap
pass: True
device_mutations: True
daemon_start_executed: True
wifi_bringup_executed: False
cnss_first_delayed_order_executed: True
```

Observed order:

```text
qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon,servicemanager,hwservicemanager,vndservicemanager
```

## Key Counts

```text
qrtr_rx: 1
qrtr_tx: 1
sysmon_qmi: 1
service_notifier_180: 0
service_notifier_74: 0
wlan_pd: 0
wlfw_start: 0
qmi_server_connected: 0
bdf: 0
wlan_fw_ready: 0
wlan0: 0
binder_transaction_failed: 3
binder_ioctl_unsupported: 2
cnss_daemon_binder_mentions: 3
perfd_client_failed: 1
wl_fw_qrtr_service_events: 0
```

WLFW QRTR nameservice readback:

```text
send_attempted: 1
service_events: 0
end_of_list: 2
timeouts: 0
qmi_attempted: 0
```

## Interpretation

V604 did not recover the V598 service-notifier path:

- QRTR RX, QRTR TX, and `sysmon-qmi` appeared.
- service-notifier `180` did not appear.
- WLFW service `69` remained absent from QRTR nameservice readback.

V604 also showed that CNSS-first delayed service-manager does not keep the V601
binder improvement:

- `cnss-daemon` emitted three binder transaction failures before/around the
  delayed service-manager start.
- Service-manager children were observable and cleaned safely, but their later
  start did not rescue the current CNSS window.

This points away from simply changing service-manager order by a short fixed
delay. The next gate should compare V598/V604 timing and either test a longer
CNSS-only window before service-manager or isolate what else differed in V598's
service-notifier-producing run.

## Counter Fix

During V604 review, the shared service-manager count helper was fixed to count
both observed binder log formats:

```text
binder transaction failed
binder: ... transaction failed
```

The corrected V604b rerun is the authoritative evidence for this report.

## Cleanup State

The live proof used reboot cleanup. The reboot command lost the final END marker
because the device restarted, but post-reboot verification saw the expected
native version and healthy status.

```text
post_reboot_version_seen: true
post_reboot_status_healthy: true
post_reboot_wifi_bringup_executed: false
```

## Next Gate

Recommended V605:

1. Build a host-only timing classifier over V598, V603, V604, and V604b dmesg
   deltas and helper transcripts.
2. Identify whether V598's service-notifier `180` appeared before any equivalent
   CNSS binder transaction failure.
3. If timing supports it, test a longer CNSS-only window before service-manager.
4. Continue blocking Wi-Fi HAL, `qcwlanstate`, scan/connect, credentials, DHCP,
   routing, and external ping until service-notifier `180` plus binder-clean are
   observed together, or WLFW/BDF/FW-ready/`wlan0` appears.
