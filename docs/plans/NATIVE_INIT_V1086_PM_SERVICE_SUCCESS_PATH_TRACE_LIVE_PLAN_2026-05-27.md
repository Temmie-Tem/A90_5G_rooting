# Native Init V1086 PM Service Success Path Trace Live Plan

## Objective

After V1085 made `libmdmdetect::get_system_info()` return success, trace the
next `pm-service` path and classify why `per_mgr` exits with code 0 before the
observer window.

## Background

V1085 closed the sysfs parity blocker. The PM observer now shows
`child.per_mgr.exit_code=0`, `signal=0`, and `term_sent=0`, with no
`/dev/subsys_modem` hold. That means `pm-service` is not dying from the earlier
mdmdetect failure; it is returning through a later clean path.

## Scope

- Reuse the existing bounded PM observer.
- Register tracefs uprobes on `/mnt/vendor/bin/pm-service`.
- Trace the path after `get_system_info()` success:
  - Binder driver init
  - default service manager lookup
  - `addService`
  - QMI thread creation
  - signal wait / clean shutdown path
- Keep the same no-Wi-Fi-bring-up guardrails.

## Guardrails

- No BPF attach.
- No Wi-Fi HAL start, scan/connect, credentials, DHCP, route change, external
  ping, partition write, flash, or reboot.
- PM actor execution is limited to the existing bounded observer.
- Tracefs events and temporary mounts must be cleaned up.

## Success Criteria

- v197 helper is present.
- V1085 mdmdetect success predecessor is present.
- `pm_success_branch_after_get_system_info` fires.
- One terminal branch is classified.
- Postflight forbidden actor and Wi-Fi link checks remain clean.
