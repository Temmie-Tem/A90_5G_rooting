# V1110 PM Connect Path Capture Plan

Date: 2026-05-27

## Goal

Capture the exact syscall path used by the `pm-service` Binder owner thread after successful CNSS PeripheralManager connect.

## Method

- Extend helper `a90_android_execns_probe v208` with read-only syscall probing for `pm-service` threads.
- Reuse the V1108 no-pre-CNSS-`per_proxy` order.
- During the `after_cnss_daemon` window, enumerate `/proc/<pm-service>/task/*/syscall`.
- For path-taking syscalls, read the path pointer by `process_vm_readv`.

## Hard Gates

- No Wi-Fi HAL.
- No scan/connect/link-up.
- No DHCP, route, credential use, or external ping.
- No `/dev/subsys_esoc0` open attempt.
- No partition write, flash, or reboot.

