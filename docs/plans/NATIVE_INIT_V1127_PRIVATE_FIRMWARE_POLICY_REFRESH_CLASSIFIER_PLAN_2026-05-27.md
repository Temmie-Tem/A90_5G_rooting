# V1127 Private Firmware Policy Refresh Classifier Plan

Date: `2026-05-27`

## Goal

Classify whether the current-boot V490 Android SELinux policy load repairs the
private-firmware `pm-service` Binder `addService()` denial captured in V1126.

## Rationale

V1126 proved the helper-private firmware path reached
`IServiceManager::addService("vendor.qcom.PeripheralManager", ...)`, but
`vndservicemanager` returned `PERMISSION_DENIED (-1)`. V490 can load the
compiled Android split policy into the current native boot without init reexec
or daemon start. V1127 compares the baseline V1126 denial with a same-boot
post-policy replay.

## Scope

- Use existing V1126 baseline addService status trace evidence.
- Use V401 selinuxfs mount evidence as the SELinux load surface precondition.
- Use V490 current-boot policy-load proof evidence.
- Use the post-policy private-firmware addService trace evidence.
- Use post-reboot process evidence to confirm cleanup.
- Produce a host-only classifier manifest and summary.

## Guardrails

- Classifier executes no device command.
- No firmware mount, PM actor, CNSS daemon, Wi-Fi HAL, scan/connect,
  credentials, DHCP/route, external ping, eSoC control, partition write, boot
  image write, flash, or reboot.
- Existing live evidence remains immutable input.
- Credentials must not appear in the classifier, report, or evidence summary.

## Success Criteria

V1127 passes if:

- V1126 baseline has `addService` status `PERMISSION_DENIED (-1)`;
- baseline provider visibility is absent and addService failure log is seen;
- V401 selinuxfs mount passed;
- V490 policy load passed and actually wrote to `/sys/fs/selinux/load`;
- post-policy replay has `addService` status `OK (0)`;
- post-policy addService failure log is absent;
- post-policy provider visibility is present;
- private firmware mounts and `vndservicemanager` readiness remain active;
- forbidden CNSS/Wi-Fi/scan/network actions remain false;
- post-reboot process surface is clean.

## Expected Next

If V1127 passes, V1128 should make V490 policy load an explicit precondition and
replay the private-firmware CNSS PM path. The next blocker should then be
classified as either CNSS PM register/connect progress or the known lower
`mdm3`/eSoC path.
