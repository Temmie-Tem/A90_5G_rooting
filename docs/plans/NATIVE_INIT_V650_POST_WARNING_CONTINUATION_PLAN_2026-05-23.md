# Native Init V650 Post-Warning Continuation Plan

- date: `2026-05-23 KST`
- cycle: `v650`
- scope: host-only classifier
- target: compare Android V649 and native V644 after the shared ASoC
  `pm_qos` warning

## Background

V649 proved Android also emits the ASoC duplicate `pm_qos_add_request` warning
shortly after service `74`, but Android still continues to WLFW, WLAN-PD, QMI,
BDF, firmware-ready, and `wlan0`. V650 determines whether native V644 stops at
the warning itself or continues through audio registration and then diverges at
WLFW.

## Inputs

- Android V649 replay manifest:
  `tmp/wifi/v649-final-live-replay-classifier/manifest.json`
- Native V644 dmesg:
  `tmp/wifi/v644-live-20260523-071610/native/dmesg-after-companion.txt`

## Guardrails

V650 is host-only and must not contact the device, write sysfs, start daemons,
start Wi-Fi HAL, run `qcwlanstate`, scan/connect, use credentials, run DHCP,
change routes, reboot, flash, or ping externally.

## Success Criteria

V650 passes if it proves:

- Android and native V644 both have service `74` followed by ASoC duplicate
  `pm_qos` warning;
- both continue through audio codec/sound-card registration after the warning;
- only Android continues to WLFW/WLAN-PD/QMI/BDF/`wlan0`;
- next work targets CNSS/WLFW continuation, not warning presence.

## Next Gate

Expected next gate is V651 CNSS/WLFW post-warning continuation guard:

- compare Android `cnss-daemon` state/logs/properties around WLFW start with
  native V644 child state;
- determine whether native misses a `cnss-daemon` runtime condition, binder/
  service-manager condition, property, socket, or namespace surface after the
  shared warning;
- keep Wi-Fi HAL, `qcwlanstate`, scan/connect, credentials, DHCP, route
  changes, and external ping blocked.
