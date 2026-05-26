# Native Init V1082 PM Service Instruction Trace Live Plan

## Goal

Confirm the V1081 inferred early failure path with instruction-level dynamic
uprobes on live native v724, without using BPF or starting Wi-Fi bring-up.

## Background

V1081 classified the likely `pm-service` path: `main` calls an early helper,
the helper calls `get_system_info`, the `get_system_info` success branch is not
taken, the helper logs failure and returns nonzero, and `main` closes pipe fds
before Binder/QMI setup.

## Gate

- Require V1081 host-only classification PASS.
- Reuse the V1079/V1080 tracefs-only collector.
- Register instruction-level offsets:
  - main entry, pipe call, helper call, helper return branch, close calls
  - Binder driver call as a negative control
  - helper entry, `get_system_info` call, branch, failure log, failure return,
    and success path
- Verify the failure path offsets hit and the success/Binder offsets remain
  zero.

## Forbidden

- No BPF attach.
- No Wi-Fi HAL start, scan/connect/link-up, credentials, DHCP, route changes, or
  external ping.
- No `mdm_helper`, CNSS daemon, `/dev/esoc*` open, `wlan.ko` load, boot image
  write, partition write, flash, or reboot.

## Success Criteria

- Dynamic instruction uprobes register, enable, disable, and clean up.
- Failure-path instruction hits are present.
- `helper_get_system_info_success_path=0`.
- `main_binder_driver_call=0`.
- PM observer contract remains `observer-runtime-gap`.
- Postflight has no forbidden actors, no Wi-Fi link, no persistent tracefs or
  vendor mount, and native selftest remains `fail=0`.
