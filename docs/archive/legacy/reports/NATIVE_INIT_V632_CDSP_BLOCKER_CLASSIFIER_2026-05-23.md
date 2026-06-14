# Native Init V632 CDSP Blocker Classifier Report

- date: `2026-05-23 KST`
- status: `classified/host-only`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_cdsp_blocker_classifier_v632.py`
- decision: `v632-cdsp-prerequisite-gap-classified`
- pass: `True`
- reason: V631 isolates CDSP as the only per-node boot write that blocks in the native post-ACM window; Android reaches CDSP SSCTL and service 74 from early-boot vendor init, so the next gate must classify CDSP loader/firmware/readiness prerequisites before another write.
- next: V633 should be a read-only native CDSP surface collector; do not repeat ADSP/SLPI or attempt Wi-Fi bring-up

## Scope

V632 is host-only. It reads existing V631 live proof evidence, Android V622
same-boot lower timing, V629 sibling-SSCTL classification, and V614 vendor
init snapshot evidence.

No device command, sysfs write, boot image build/flash, daemon start,
service-manager start, Wi-Fi HAL start, scan/connect/link-up, credential,
DHCP, route change, or external ping was executed.

## V631 Per-Node Result

| node | path | write_rc | parent_rc | status | reaped | duration_ms | classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| adsp | /sys/kernel/boot_adsp/boot | 0 | 0 | 0x0 | yes | 100 | write-returned |
| cdsp | /sys/kernel/boot_cdsp/boot | missing | -110 | 0x9 | yes | 5106 | write-blocked-timeout |
| slpi | /sys/kernel/boot_slpi/boot | 0 | 0 | 0x0 | yes | 102 | write-returned |

## Android V622 Lower Timing

| key | value |
| --- | --- |
| sysmon_cdsp_count | 1 |
| service_notifier_74_count | 1 |
| wlan_pd_count | 2 |
| wlan_fw_ready_count | 1 |
| sysmon_modem_to_sysmon_cdsp_ms | 1.811 |
| service_notifier_180_to_service_notifier_74_ms | 6.561 |
| service_notifier_180_to_wlan_pd_ms | 2427.362 |

## Vendor Init Contract

| surface | line |
| --- | --- |
| adsp_line | /tmp/a90-v614-20180201-102958/vendor/etc/init/hw/init.qcom.rc:112:    write /sys/kernel/boot_adsp/boot 1 |
| cdsp_line | /tmp/a90-v614-20180201-102958/vendor/etc/init/hw/init.qcom.rc:113:    write /sys/kernel/boot_cdsp/boot 1 |
| slpi_line | /tmp/a90-v614-20180201-102958/vendor/etc/init/init.vendor.sensors.rc:34:    write /sys/kernel/boot_slpi/boot 1 |
| early_boot_exec_line | exec u:r:vendor_qti_init_shell:s0 -- /vendor/bin/init.qcom.early_boot.sh |
| boot_wlan_line | /tmp/a90-v614-20180201-102958/vendor/etc/init/wifi_qcom.rc:3:    chown wifi wifi /sys/kernel/boot_wlan/boot_wlan |

## Classification

| check | value |
| --- | --- |
| cdsp_timeout | yes |
| adsp_ok | yes |
| slpi_ok | yes |
| android_cdsp_ready | yes |
| android_service74 | yes |
| vendor_cdsp_write | yes |
| v629_classified | yes |

V631 proves the current post-ACM proof window is too late or missing a
CDSP-specific prerequisite: ADSP and SLPI return, but CDSP remains inside
the write path until killed at the bounded timeout. Android evidence proves
CDSP SSCTL and service `74` are reachable during early boot, so the next
action should not be Wi-Fi HAL, `boot_wlan`, `qcwlanstate`, or an external
ping attempt.

The next gate should collect CDSP loader state read-only under native v319:
`/sys/kernel/boot_cdsp`, CDSP subsystem state, firmware mount/files,
fastrpc/CDSP kernel threads, and relevant dmesg markers. A later write proof
should target CDSP only and run only after those prerequisites are mapped.

## External References

| title | url | relevance |
| --- | --- | --- |
| Android kernel msm CDSP loader driver | https://android.googlesource.com/kernel/msm/+/9f8c2d8438a7f0cd3d65a588bb60f10b67adf2a8%5E%21/ | The CDSP loader loads compute DSP firmware images and brings the subsystem out of reset. |
| Google Coral init.insmod boot devices | https://android.googlesource.com/device/google/coral/+/2c5e9cd2569af264f59bec8354e1ec20636871bb/init.insmod.coral.cfg | Adjacent Qualcomm Android config enables ADSP, CDSP, and SLPI only after module setup is complete. |
| Google Crosshatch init hardware early-boot | https://android.googlesource.com/device/google/crosshatch/+/refs/tags/android-10.0.0_r17/init.hardware.rc | Adjacent Qualcomm Android init waits for module readiness before writing ADSP/CDSP boot nodes. |

## Guardrails

- device command
- sysfs write
- boot image build/flash
- DSP boot-node retry
- daemon start
- service-manager start
- Wi-Fi HAL start
- scan/connect/link-up
- credential/DHCP/routing/external ping
