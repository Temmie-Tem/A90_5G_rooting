# Native Init V1066 PM-Service Trigger Observer Live Plan

## Goal

Run the deployed helper `a90_android_execns_probe v184` in the new
`wifi-companion-pm-service-trigger-observer` mode and classify whether the PM
stack itself opens `/dev/subsys_modem` when only service-manager and PM actors
are started.

## Context

- V1063 proved native `pm-service` stays alive but idle with only binder-style
  readiness and no `/dev/subsys_modem` fd.
- V1064 added a helper mode that starts only `servicemanager`,
  `hwservicemanager`, `vndservicemanager`, `pm_proxy_helper`, `pm-service`, and
  `pm-proxy`, then snapshots `/proc/<pid>/fd` for PM modem handles.
- V1065 deployed helper `v181` over authenticated NCM/TCP and verified remote
  sha/usage parity.
- The first V1066 live attempts showed `v181` rejected the new mode at the
  top-level v235 allowlist and `v182` still missed the property-root allowlist.
  `v183` repaired allowlists, then `v184` compacted observer output so final
  `result` markers fit under the tcpctl transcript cap.

## Execution

1. Confirm native health and NCM/tcpctl availability.
2. Mount `/system` read-only and refresh `selinuxfs` for the current boot.
3. Verify helper `v181` remote sha/usage and Android runtime config files.
4. Execute the observer over NCM/tcpctl to avoid serial transcript bottlenecks.
5. Capture postflight process, netdev, subsystem, and Wi-Fi/eSoC dmesg tail.
6. Reboot only if the helper cannot prove all observer children stopped.

## Guardrails

- No `mdm_helper`, CNSS actor, Wi-Fi HAL, scan/connect, credential use,
  DHCP/route, external ping, eSoC ioctl/open, or subsystem trigger.
- No module load/unload, boot image write, partition write, firmware mutation,
  GPIO/sysfs/debugfs write, or Wi-Fi link-up.
- Helper output must keep forbidden markers at `0`.

## Success Criteria

- PASS if helper `v181` starts the intended observer mode and returns one of:
  `pm-service-subsys-modem-observed`,
  `pm-service-idle-input-gap-observed`, `observer-runtime-gap`, or
  `observer-reboot-required` with guardrails intact.
- FAIL if remote helper parity mismatches, forbidden action markers are true,
  required actors do not start, or cleanup cannot be verified.
