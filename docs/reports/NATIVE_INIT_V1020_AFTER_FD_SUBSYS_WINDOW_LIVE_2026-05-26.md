# V1020 After-Fd Subsystem Window Live

- date: `2026-05-26`
- scope: bounded live scoped `/dev/subsys_esoc0` gate
- decision: `v1020-reboot-required-cleaned`
- pass: `True`
- evidence: `tmp/wifi/v1020-after-fd-subsys-window-live/manifest.json`

## Summary

V1020 successfully reached the intended upper-surface gate and attempted the
scoped `/dev/subsys_esoc0` child open after:

- `mdm_helper` held `/dev/esoc-0`
- service-manager trio started
- Wi-Fi HAL legacy/ext started
- `wificond` started
- `cnss_diag` started
- `cnss-daemon` started
- WLFW was still absent

The `/dev/subsys_esoc0` child did not exit. It entered uninterruptible sleep
inside the SDX50M reset path and required a cleanup reboot. The cleanup reboot
completed and post-reboot health passed.

## Key Evidence

| Item | Value |
| --- | --- |
| helper | `a90_android_execns_probe v173` |
| order | `after-mdm-helper-esoc-fd-with-wifi-surface-subsys-window` |
| gate | `post-upper-surface-no-wlfw` |
| `mdm_helper_esoc0_fd_seen` | `1` |
| `service_manager_started` | `1` |
| `wifi_hal_started` | `1` |
| `wificond_started` | `1` |
| `cnss_diag_started` | `1` |
| `cnss_daemon_started` | `1` |
| `wlfw_precondition_observed` | `0` |
| `subsys_esoc0_open_attempted` | `1` |
| child state | `D (disk sleep)` |
| child `wchan` | `sdx50m_toggle_soft_reset` |
| cleanup reboot | executed |
| post-reboot health | healthy |

Captured child stack:

```text
sdx50m_toggle_soft_reset
mdm4x_do_first_power_on
mdm_cmd_exe
mdm_subsys_powerup
__subsystem_get
subsys_device_open
```

Post-window dmesg only showed the subsystem get start:

```text
subsys-restart: __subsystem_get(): __subsystem_get: esoc0 count:0
subsys-restart: __subsystem_get(): Changing subsys fw_name to esoc0
```

There was no WLFW, BDF, `FW_READY`, MHI pipe, or `wlan0` evidence.

## Interpretation

V1020 closes the earlier circular-gate concern: the failure is not simply that
native init waited for WLFW before opening `/dev/subsys_esoc0`. Even after the
fd-positive upper surface and CNSS stack were present, the scoped
`/dev/subsys_esoc0` open blocked in the SDX50M soft-reset path.

The remaining blocker is below the Wi-Fi HAL/CNSS userspace surface:

- the SDX50M reset/status handshake is not completing
- MDM status IRQ remained at zero in the captured tail
- `mdm3` remained `OFFLINING`
- no QCA/WLFW/service 69 continuation appeared

This points back to an Android-only side condition around the SDX50M eSoC
power/reset handshake, PeripheralManager/`pm-service`/`pm-proxy`, or PMIC/GPIO
sequencing rather than a missing Wi-Fi scan/connect step.

## Guardrails

- no `IWifi.start`
- no `qcwlanstate` write
- no scan/connect/link-up
- no credential use
- no DHCP/route/external ping
- no raw eSoC controller ioctl
- no controller notify or BOOT_DONE
- no GPIO/sysfs/debugfs write
- no module load/unload
- no boot image, partition, or firmware write

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_after_fd_subsys_window_live_v1020.py
python3 scripts/revalidation/native_wifi_after_fd_subsys_window_live_v1020.py \
  --out-dir tmp/wifi/v1020-after-fd-subsys-window-plan \
  plan
python3 scripts/revalidation/native_wifi_after_fd_subsys_window_live_v1020.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-cnss-service-manager-matrix \
  --allow-cleanup-reboot \
  --assume-yes \
  run
```

Result:

```text
decision: v1020-reboot-required-cleaned
pass: True
next: inspect pre-reboot matrix evidence
```

Post-reboot device health:

```text
boot: BOOT OK shell
selftest: pass=11 warn=1 fail=0
```

## Next

Proceed to V1021 as a host-only classifier. Do not retry the same
`/dev/subsys_esoc0` open blindly.

Recommended V1021 questions:

- In Android-good evidence, what happens immediately before
  `sdx50m_toggle_soft_reset` returns?
- Are `pm-service`, `pm-proxy`, or PeripheralManager client registration present
  before the subsystem get completes?
- Does Android show PMIC GPIO9 de-assert, GPIO135/AP2MDM assertion, or
  GPIO142/MDM2AP IRQ activity that native does not?
- Can existing V968/V1000 Android dmesg evidence answer this, or is a fresh
  Android read-only `adb shell dmesg` capture needed?

