# Native Init V1085 PM Service Modem Detect Sysfs Parity Plan

## Objective

Repair the V1084 blocker by exposing the read-only modem-detect sysfs surface
inside the private Android namespace used by the bounded `pm-service` observer.

## Background

V1084 showed that `libmdmdetect.so::get_system_info()` fails at the MSM
subsystem fallback root: `/sys/bus/msm_subsys/devices` is not visible inside
the private namespace. The helper already has a read-only modem-detect surface
used by rmt-storage/companion modes, but the `wifi-companion-pm-service-trigger-
observer` mode did not enable it.

## Scope

- Bump `a90_android_execns_probe` to v197.
- Add a PM-service-observer-only call to the existing read-only modem-detect
  sysfs materializer.
- Build a static aarch64 helper.
- Deploy only `/cache/bin/a90_android_execns_probe`.
- Rerun the V1084 branch trace with v197.

## Guardrails

- Bind sysfs read-only only.
- No new eSoC open/ioctl, subsystem trigger, service-manager expansion, Wi-Fi
  HAL start, scan/connect, credentials, DHCP, external ping, partition write,
  flash, or reboot.
- Deploy is limited to `/cache/bin/a90_android_execns_probe`.
- Live validation must cleanup tracefs/vendor/SELinuxfs mounts and leave
  selftest passing.

## Success Criteria

- v197 helper builds static and has the expected marker.
- v197 deploy passes through NCM without daemon or Wi-Fi start.
- V1084 trace replay with v197 shows `mdm_success_return > 0`.
- Negative controls remain clean: no Wi-Fi link, no forbidden actors, no flash
  or reboot.
- If PM-service still exits, the report records the new blocker separately.
