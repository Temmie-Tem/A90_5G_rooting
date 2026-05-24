# Native Init V708 Provider-First CNSS v120 Stall Plan

- date: `2026-05-24 KST`
- cycle: `v708`
- type: bounded live proof

## Goal

Run the provider-first CNSS path with helper v120 so that the post-provider
`cnss_daemon_retry` process is captured before cleanup:

```text
service 180/74 -> provider registration -> cnss_daemon_retry -> stall snapshot
```

## Scope

Allowed:

- helper v120 contract verification by SHA and marker;
- clean native reboot/prep through the existing V641/V401/V490 path;
- lower firmware mount + `subsys_modem` holder inside the existing bounded
  replay path;
- service-manager trio and provider pair inside the private namespace;
- exactly one provider-confirmed `cnss-daemon` retry;
- read-only proc/socket stall snapshot for the retry process;
- reboot cleanup.

Forbidden:

- Wi-Fi HAL, wificond, supplicant, or hostapd start;
- scan/connect/link-up;
- Wi-Fi credential use;
- DHCP, route change, or external ping;
- `qcwlanstate`, `boot_wlan`, or subsystem sysfs writes;
- `esoc0` open/hold;
- boot image or partition writes.

## Implementation

Add wrappers:

- `scripts/revalidation/native_wifi_provider_first_cnss_v708.py`
- `scripts/revalidation/native_wifi_provider_first_cnss_orchestrator_v708.py`

The wrappers reuse the proven V700 provider-first path but replace the helper
contract with:

```text
helper marker: a90_android_execns_probe v120
helper sha256: acc43d21f948c88350099e1a652a26c7a5f4f0352e06396c6d30dd6908d1ba28
```

## Success Criteria

- service-notifier `180` and `74` are positive in the live window;
- `vendor.qcom.PeripheralManager` is visible through `vndservice`;
- initial pre-provider `cnss-daemon` is suppressed;
- one post-provider `cnss_daemon_retry` starts;
- `cnss_daemon_retry` stall snapshot is captured;
- Wi-Fi HAL/connect/DHCP/external ping remain unexecuted;
- reboot cleanup returns native health.

## Next Gate

If WLFW/BDF/`wlan0` remain absent, classify the captured `wchan`, `syscall`,
task, QRTR, and netlink state before attempting any Wi-Fi HAL or connect path.
