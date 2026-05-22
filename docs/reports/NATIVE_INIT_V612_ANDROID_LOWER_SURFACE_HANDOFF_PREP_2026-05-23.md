# Native Init V612 Android Lower-Surface Handoff Prep Report

- date: `2026-05-23 KST`
- status: `prepared`; live Android handoff is **not** executed yet
- wrapper: `scripts/revalidation/android_lower_surface_recapture_handoff_v612.py`
- collector: `scripts/revalidation/native_wifi_android_lower_surface_recapture_v611.py`
- plan evidence: `tmp/wifi/v612-android-lower-surface-handoff-plan/`
- dry-run evidence: `tmp/wifi/v612-android-lower-surface-handoff-dryrun/`

## Scope

V612 adds a bounded handoff wrapper for V611:

1. verify native init state;
2. boot recovery;
3. temporarily flash a known Android boot image;
4. wait for Android and `sys.boot_completed=1`;
5. run the V611 read-only lower-surface collector;
6. reboot recovery;
7. restore native init boot image.

The wrapper does not enable Wi-Fi, start native daemons, start service-manager,
start Wi-Fi HAL, write subsystem sysfs, write `qcwlanstate`, send QMI payloads,
scan/connect/link-up, use credentials, run DHCP, change routes, or ping
externally.

## Static Validation

```text
py_compile(android_lower_surface_recapture_handoff_v612.py): pass
py_compile(native_wifi_android_lower_surface_recapture_v611.py): pass
plan decision: v612-handoff-plan-ready
dry-run decision: v612-handoff-dryrun-ready
```

## Selected Images

```text
native rollback image: stage3/boot_linux_v319.img
Android candidate: backups/baseline_a_20260423_025322/boot.img
```

The plan/dry-run evidence records the full step list without device mutation.

## Live Gate

The next gate may run V612 with the existing bypass-approved safety flags:

```text
--allow-android-boot-flash
--assume-yes
--i-understand-native-rollback
```

Success requires:

1. Android boot-complete;
2. V611 collector pass or a precise V611 failure label;
3. rollback to native init v319;
4. no Wi-Fi bring-up, credentials, DHCP, routing, or external ping during this
   handoff.
