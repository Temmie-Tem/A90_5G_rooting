# V1111 Tagged PM Connect Path Capture Plan

Date: 2026-05-27

## Goal

Retry V1110 with helper `v209`, untagging AArch64 top-byte-tagged userspace pointers before `process_vm_readv`.

## Change

- Bump `a90_android_execns_probe` to `v209`.
- Add `a90_untag_user_ptr()`.
- Use the untagged address for `process_vm_readv` and ptrace memory reads.
- Emit both original `path.addr` and `path.untagged_addr` in syscall probe output.

## Success Criteria

- Reproduce V1108 no-pre-CNSS-`per_proxy` ordering.
- Reproduce CNSS PM register/connect success.
- Capture a valid syscall path value from the blocked owner thread.
- Keep all Wi-Fi bring-up actions disabled.

## Hard Gates

- No Wi-Fi HAL, scan/connect, DHCP, route, credential, or external ping.
- No `/dev/subsys_esoc0` open attempt.
- No partition write, flash, or reboot.

