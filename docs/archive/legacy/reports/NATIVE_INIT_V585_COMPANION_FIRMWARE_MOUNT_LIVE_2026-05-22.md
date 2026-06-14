# Native Init V585 Companion Firmware Mount Live Proof

- date: `2026-05-22 KST`
- objective: run bounded companion start-only with helper-private `apnhlos`/`modem` firmware mounts
- status: `bounded pass`; Wi-Fi external ping is **not** complete

## Scope

- Deploy:
  - helper: `a90_android_execns_probe v97`
  - sha256: `82ef904d6fdadbd0954b0fdc016d64f733f802cbca954b143970f86a044bf812`
  - evidence: `tmp/wifi/v585-execns-helper-v97-deploy-preflight/`
- Policy load:
  - evidence: `tmp/wifi/v527-v490-current-run/`
- Live proof:
  - evidence: `tmp/wifi/v585-companion-firmware-mount-start-only/`

## Guardrails

- No service-manager.
- No Wi-Fi HAL or `IWifi.start()`.
- No qcwlanstate write.
- No supplicant/hostapd.
- No scan/connect/link-up/DHCP/routing.
- No external ping.
- Companion children are helper-owned and bounded.

## Deploy Result

Serial deploy used chunk size `1850` because `3000` and `1900` exceeded the native console line guard.

```text
decision: execns-helper-v97-deploy-pass
pass: True
reason: helper v97 deployed or already current; V500 preflight was rerun
device_mutations: True
daemon_start_executed: False
wifi_bringup_executed: False
```

## V490 Current Boot Policy Load

```text
decision: v490-selinux-policy-load-proof-pass
pass: True
reason: compiled Android split policy was written to /sys/fs/selinux/load without init reexec or daemon start
daemon_start_executed: False
wifi_hal_start_executed: False
wifi_bringup_executed: False
```

## V585 Live Result

```text
decision: v585-companion-firmware-mount-start-only-no-fw-marker
pass: True
reason: all companions were observable and cleaned, but no QRTR/QMI/WLFW/BDF/FW-ready marker appeared
next: inspect QRTR/proc-net delta and companion logs before qcwlanstate retry
device_mutations: True
daemon_start_executed: True
wifi_bringup_executed: False
```

Private firmware mount proof inside the helper namespace:

```text
private_firmware_mounts_ready=True
firmware_mnt_mount_source=/tmp/a90-v231-1212/firmware-block-apnhlos
firmware_modem_mount_source=/tmp/a90-v231-1212/firmware-block-modem
```

Lifecycle:

```text
helper_result=companion-window-pass
all_observable=True
all_postflight_safe=True
child_started=6
timed_out=1
scan_connect_linkup=0
external_ping=0
qmi_payload=0
```

Observed dmesg delta:

```text
cnss_diag_netlink=21
cnss_daemon_netlink=39
rmt_storage=2
qrtr_modem_readiness=0
wlfw_start=0
wlfw_thread=0
qmi_server_connected=0
bdf_regdb=0
bdf_bdwlan=0
wlan_fw_ready=0
wlan0_event=0
```

Post status stayed healthy:

```text
selftest: pass=11 warn=1 fail=0
netservice: disabled
tcpctl: stopped
rshell: stopped
wifi_bringup_executed=False
```

## Interpretation

- The V584 namespace concern is resolved: helper v97 can mount `apnhlos` and `modem` read-only inside the same private namespace used by the companion processes.
- The companion stack still reaches only netlink activity for `cnss_diag`/`cnss-daemon`; it does not reach QRTR modem readiness, WLFW, QMI server connected, BDF request, firmware ready, or wlan0 creation.
- The next blocker is therefore below qcwlanstate/HAL and likely around modem QRTR readiness/service locator/service notifier inputs, not firmware mount visibility alone.

## Next Gate

Recommended V586:

1. Compare V585 helper stdout/stderr and QRTR/proc-net delta against Android.
2. Inspect service locator / QRTR namespace / subsystem notification surfaces while companion window is active.
3. Keep qcwlanstate, Wi-Fi HAL, scan/connect, credentials, DHCP, routing, and external ping blocked until lower readiness markers change.
