# Native Init V995 SELinux Domain Allowlist Plan

## Goal

Add source/build-only support for the V994-selected fresh SELinux proof route.

The current `selinux-domain-proof` mode can prove several Android domains, but
it does not allow `u:r:wificond:s0` or `u:r:vndservicemanager:s0`. V995 extends
the proof surface so the next live gate can test the service-window critical
domains before starting any Android service-window actors.

## Scope

- Bump `a90_android_execns_probe` to helper `v169`.
- Allow `u:r:wificond:s0` and `u:r:vndservicemanager:s0` in
  `selinux-domain-proof`.
- Add target profiles for `/system/bin/wificond` and
  `/vendor/bin/vndservicemanager`.
- Preserve the existing no-daemon/no-HAL/no-scan/no-credential guardrails.
- Build a static helper artifact and record its sha256.

## Guardrails

- No device command.
- No helper deploy.
- No SELinux policy load.
- No service-manager, Wi-Fi HAL, `wificond`, daemon, scan/connect, credentials,
  DHCP/routes, external ping, boot image write, partition write, firmware
  mutation, GPIO write, sysfs write, or debugfs write.

## Success Criteria

- Helper source contains the new SELinux contexts and target profiles.
- Static helper build passes.
- Artifact strings contain helper `v169`, `system-wificond`,
  `vendor-vndservicemanager`, `u:r:wificond:s0`, and
  `u:r:vndservicemanager:s0`.
- V995 verifier emits a PASS manifest.

## Next

If V995 passes, V996 should deploy helper `v169` only. The live current-boot
policy-load/domain proof remains a separate bounded gate after deployment.
