# V982 Android Service-Window Live v165

- generated: `2026-05-26`
- scope: bounded live proof retry with helper `v165`
- decision: `v970-android-service-window-runtime-gap`
- pass: `True`
- evidence: `tmp/wifi/v982-android-service-window-live-v165/manifest.json`

## Summary

V982 reran the Android service-window live proof with helper `v165`.

The V980 binder-device repair worked. Service-manager, hardware service-manager, vendor service-manager, and both Wi-Fi HAL service processes stayed observable until cleanup instead of aborting on missing `/dev/binder`.

The remaining runtime gap changed to:

- `wificond` exits early with `SIGABRT`
- `per_mgr` exits early with code `0`
- `cnss_daemon` remains observable but requires cleanup `SIGKILL` after `SIGTERM`
- `wlfw_precondition_observed=0`
- `wlan0` remains absent

## Key Stderr

```text
libc: Using old property service protocol ("ro.property_service.version" is not set)
libc: Using old property service protocol ("ro.property_service.version" is not set)
libc: Fatal signal 6 (SIGABRT), code -1 (SI_QUEUE) in tid ... (wificond)
```

The helper output also shows:

```text
wifi_hal_composite_start.property_service_shim.mode=disabled
wifi_hal_composite_start.property_service_shim.started=0
```

## Actor Outcome

Actors observable until cleanup:

- `servicemanager`
- `hwservicemanager`
- `vndservicemanager`
- `qrtr_ns`
- `rmt_storage`
- `tftp_server`
- `pd_mapper`
- `wifi_hal_legacy`
- `wifi_hal_ext`
- `cnss_diag`
- `mdm_helper`
- `cnss_daemon`

Actors that exited before the observe window:

- `per_mgr`: exit code `0`
- `wificond`: `SIGABRT`

## Guardrails

- no `qcwlanstate`
- no `IWifi.start`
- no `/dev/subsys_esoc0` open
- no eSoC ioctl
- no scan/connect/link-up
- no credential use
- no DHCP/route/external ping
- no cleanup reboot needed

## Interpretation

V982 moves the service-window proof past the binder device blocker. The next blocker is property service parity for Android userspace actors, especially `wificond`.

The existing property service shim is present in the helper but disabled for the dedicated Android service-window mode because the shim gate still keys off generic companion allow flags.

## Next

V983 should enable the property service shim for:

```text
wifi-companion-android-wifi-service-window-start-only
--allow-android-wifi-service-window
```

without enabling scan/connect, `qcwlanstate`, eSoC open, or Wi-Fi bring-up.
