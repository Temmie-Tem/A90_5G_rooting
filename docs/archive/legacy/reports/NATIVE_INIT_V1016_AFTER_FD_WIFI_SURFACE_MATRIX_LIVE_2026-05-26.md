# V1016 After-Fd Wi-Fi Surface Matrix Live

- date: `2026-05-26`
- scope: bounded live after-fd Wi-Fi surface matrix
- decision: `v1016-upper-surface-started-wlfw-missing-no-open`
- pass: `True`
- evidence: `tmp/wifi/v1016-after-fd-wifi-surface-matrix-live/manifest.json`

## Summary

V1016 proved that the combined after-fd upper Wi-Fi surface can be started in
native init without scan/connect:

```text
mdm_helper /dev/esoc-0 fd
service-manager trio
Wi-Fi HAL legacy/ext
wificond
cnss_diag
cnss-daemon
```

The WLFW precondition still did not appear. Because the WLFW-gated child never
opened `/dev/subsys_esoc0`, the result narrows the remaining gap below the
upper userspace surface.

## Live Result

| Item | Value |
| --- | --- |
| helper | `a90_android_execns_probe v172` |
| service-manager order | `after-mdm-helper-esoc-fd-with-wifi-surface` |
| `mdm_helper_esoc0_fd_seen` | `1` |
| `service_manager_start_executed` | `True` |
| `wifi_hal_start_executed` | `True` |
| `wificond_start_executed` | `True` |
| `cnss_diag_start_executed` | `True` |
| `cnss_daemon_start_executed` | `True` |
| `wlfw_precondition_observed` | `False` |
| `subsys_esoc0_open_attempted` | `False` |
| `cleanup_reboot_executed` | `False` |

## Contract Highlights

- order:
  `property-shim,per_mgr_light,mdm_helper,esoc0-fd-gate,servicemanager,hwservicemanager,vndservicemanager,wifi_hal_legacy,wifi_hal_ext,wificond,cnss_diag,cnss_daemon,wlfw-precondition-gate,subsys_esoc0-open-child`
- result: `wlfw-precondition-missing-no-open`
- reason: `cnss-daemon-did-not-emit-wlfw-precondition`
- `surface_poll_count=32`
- `all_postflight_safe=1`
- `timed_out=1`

## Guardrails

All forbidden live actions remained false:

- no `IWifi.start`
- no `qcwlanstate` write
- no scan/connect/link-up
- no credential use
- no DHCP/route/external ping
- no eSoC controller ioctl
- no eSoC notify or BOOT_DONE
- no boot image, partition, firmware, GPIO, sysfs, or debugfs write

## Interpretation

V1016 removes the previous split between fd-positive lower state and
upper-surface actor parity. The remaining blocker is not simply missing
service-manager, Wi-Fi HAL, `wificond`, or CNSS startup.

The next unit should classify the lower WLFW gap after upper-surface parity,
with emphasis on Android-positive evidence around `mdm_helper`, `ks`, MHI
device/image timing, eSoC GPIO/PMIC/PCIe timing, and the point where Android
produces WLFW while native init does not.

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_after_fd_wifi_surface_matrix_live_v1016.py
python3 scripts/revalidation/native_wifi_after_fd_wifi_surface_matrix_live_v1016.py \
  --out-dir tmp/wifi/v1016-after-fd-wifi-surface-matrix-plan \
  plan
python3 scripts/revalidation/native_wifi_after_fd_wifi_surface_matrix_live_v1016.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-cnss-service-manager-matrix \
  --allow-cleanup-reboot \
  --assume-yes \
  run
```

Result:

```text
decision: v1016-upper-surface-started-wlfw-missing-no-open
pass: True
next_step: classify remaining lower WLFW blocker after upper surface parity
```
