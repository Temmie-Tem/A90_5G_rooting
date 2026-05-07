# Native Init v150 Host Disconnect Classifier Plan

Date: `2026-05-08`
Target: `A90 Linux init 0.9.50 (v150)` / `0.9.50 v150 HOST DISCONNECT CLASSIFIER`
Baseline: `A90 Linux init 0.9.49 (v149)`

## Summary

v150 adds a host-side disconnect classifier for long-soak runs. Device-side
recorder health from v149 tells whether the phone-side observer is alive; v150
adds the host view needed to distinguish serial bridge, ACM control, NCM ping,
and broader device/USB reachability failures.

## Key Changes

- Add `scripts/revalidation/native_disconnect_classify.py`.
- Probe serial bridge `cmdv1 version`, `status`, `longsoak status verbose`, and
  `netservice status`.
- Probe NCM reachability with `ping -c 1 -W 2 192.168.7.2`.
- Emit Markdown and JSON reports with per-probe duration, rc/status, detail, and
  final classification.
- Keep v149 longsoak supervisor behavior unchanged.

## Classifications

- `all-paths-ok`: serial bridge, command protocol, longsoak status, and NCM ping
  all responded.
- `serial-ok-ncm-down-or-inactive`: ACM/cmdv1 is healthy, but NCM ping is down or
  netservice is inactive.
- `serial-bridge-down-ncm-ok`: USB NCM is reachable while ACM/bridge command path
  is failing.
- `host-control-down-device-recorder-alive`: control path is down, but previous
  recorder evidence indicates the device observer may still be running.
- `partial-serial-control`: some serial command evidence exists, but not enough
  for a full healthy classification.
- `device-or-usb-unreachable`: no useful host-side path responded.

## Validation

- Static ARM64 build with v150 marker strings.
- `git diff --check` and host Python `py_compile`.
- Real-device flash with `native_init_flash.py`.
- `native_disconnect_classify.py` should produce JSON/Markdown and return PASS
  when the serial version probe matches v150.
- Regression: short longsoak correlation, integrated validation, quick soak, and
  local security rescan.

## Acceptance

- The classifier records evidence even when optional NCM is down.
- The classifier exit code is tied to v150 serial version verification, not NCM
  availability.
- v150 docs record the observed classification from the real device.
