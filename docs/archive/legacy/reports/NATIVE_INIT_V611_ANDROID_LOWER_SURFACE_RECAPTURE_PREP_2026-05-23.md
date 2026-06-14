# Native Init V611 Android Lower-Surface Recapture Prep Report

- date: `2026-05-23 KST`
- status: `prepared`; Android live recapture is **not** executed yet
- collector: `scripts/revalidation/native_wifi_android_lower_surface_recapture_v611.py`
- plan evidence: `tmp/wifi/v611-android-lower-surface-plan-static/`
- preflight evidence: `tmp/wifi/v611-android-lower-surface-preflight/`

## Scope

V611 prep adds an Android-only read-only collector for lower modem publication
surfaces that V610 could not prove from filtered Android evidence.

It does not enable Wi-Fi, start native daemons, start service-manager, start
Wi-Fi HAL, write subsystem sysfs, open `esoc0` from native, send QMI payloads,
scan/connect/link-up, use credentials, run DHCP, change routes, ping
externally, flash boot images, or write partitions.

## Collector Targets

The collector captures:

```text
sys.boot_completed and relevant init.svc properties
mss/mdm3 subsystem state files
/proc/net/protocols
/proc/net/qrtr if present
/sys/bus/rpmsg/devices
/sys/kernel/debug lower-surface candidate listing
/sys/kernel/debug/esoc read-only files if present
dmesg lower-surface filtered tail
dmesg unfiltered tail
```

The lower dmesg filter now includes terms that V610 marked as missing from the
older Android reference:

```text
memshare
cma_alloc
servloc/service_locator
QIPCRTR
rpmsg
rmt_storage
tftp
pd-mapper
sysmon-qmi
service-notifier
```

## Validation

```text
py_compile: pass
plan decision: v611-android-lower-surface-plan-ready
preflight decision: v611-android-adb-unavailable
```

Current preflight result is expected because the device is in native init, not
Android ADB:

```text
decision: v611-android-adb-unavailable
pass: False
reason: no Android ADB device is currently visible
device_commands_executed: True
device_mutations: False
wifi_bringup_executed: False
```

## Interpretation

V611 prep closes the tooling gap, not the evidence gap. The next live step must
temporarily boot Android or otherwise make Android ADB available, run this
collector, and return to native. Until then, V610 remains the current
classification:

```text
Android: mss/mdm3 ONLINE + sibling sysmon + service-notifier
Native V609: mss ONLINE + mdm3 OFFLINING + no sibling sysmon/service-notifier
```

## Next Gate

Recommended V611 live sequence:

1. Use the established Android handoff/rollback path.
2. Run `native_wifi_android_lower_surface_recapture_v611.py run` after
   `sys.boot_completed=1`.
3. Restore native init and verify rollback health.
4. Compare the V611 Android lower surfaces against V609 before any native
   `esoc0`, CNSS, service-manager, HAL, scan/connect, credential, DHCP, route,
   or external ping action.
