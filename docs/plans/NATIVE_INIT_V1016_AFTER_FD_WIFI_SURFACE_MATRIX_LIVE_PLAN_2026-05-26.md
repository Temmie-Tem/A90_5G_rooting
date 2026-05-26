# V1016 After-Fd Wi-Fi Surface Matrix Live Plan

- date: `2026-05-26`
- type: bounded live gate
- selected after: V1015 helper `v172` deploy pass
- helper: `a90_android_execns_probe v172`
- order: `after-mdm-helper-esoc-fd-with-wifi-surface`

## Objective

Run the deployed helper `v172` in the combined after-fd Wi-Fi surface matrix:

```text
wifi-companion-mdm-helper-cnss-service-manager-matrix
```

The gate preserves the proven `mdm_helper` `/dev/esoc-0` fd predicate before
starting the Android upper Wi-Fi surface actors. It observes whether that
combined surface is sufficient for WLFW precondition materialization without
running scan/connect.

## Sequence

The helper order is:

```text
property-shim
per_mgr_light
mdm_helper
esoc0-fd-gate
servicemanager
hwservicemanager
vndservicemanager
wifi_hal_legacy
wifi_hal_ext
wificond
cnss_diag
cnss_daemon
wlfw-precondition-gate
subsys_esoc0-open-child
```

The `/dev/subsys_esoc0` child is gated on WLFW precondition. If WLFW is not
observed, the child must not open `/dev/subsys_esoc0`.

## Hard Gates

- current-boot SELinux/fs setup only
- no `IWifi.start`
- no `qcwlanstate` write
- no scan/connect/link-up
- no credential use
- no DHCP/route/external ping
- no eSoC controller ioctl
- no eSoC notify or BOOT_DONE
- no GPIO/sysfs/debugfs write
- no module load/unload
- no boot image, partition, or firmware write

## Success Criteria

Any of these terminal classifications is acceptable if the hard gates remain
clean:

- `v1016-wlfw-precondition-observed-trigger-clean`
- `v1016-upper-surface-started-wlfw-missing-no-open`
- `v1016-mdm-helper-esoc-fd-missing-no-open`

Required checks:

- remote helper sha and marker match helper `v172`
- `mdm_helper_esoc0_fd_seen=1` unless explicitly classified as fd-missing
- service-manager trio starts only after the fd gate
- Wi-Fi HAL legacy/ext and `wificond` start before CNSS
- `IWifi.start`, `qcwlanstate`, scan/connect, credentials, DHCP/routes, and
  external ping remain false
- cleanup is either not required or completes safely

## Validation

Run plan/static checks:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_after_fd_wifi_surface_matrix_live_v1016.py
python3 scripts/revalidation/native_wifi_after_fd_wifi_surface_matrix_live_v1016.py \
  --out-dir tmp/wifi/v1016-after-fd-wifi-surface-matrix-plan \
  plan
```

Run the bounded live gate:

```bash
python3 scripts/revalidation/native_wifi_after_fd_wifi_surface_matrix_live_v1016.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-cnss-service-manager-matrix \
  --allow-cleanup-reboot \
  --assume-yes \
  run
```
