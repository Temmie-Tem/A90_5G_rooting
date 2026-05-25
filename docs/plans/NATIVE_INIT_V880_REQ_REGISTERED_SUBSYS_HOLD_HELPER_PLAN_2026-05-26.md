# V880 REQ-registered Subsystem Hold Helper Plan

## Goal

Build helper `v138` source-only support for the next mdm3/eSoC gate: hold a
successful `REG_REQ_ENG` fd while a bounded child attempts `/dev/subsys_esoc0`.
This is preparation only; V880 does not deploy the helper or contact the
device.

## Inputs

- V878 live result:
  `tmp/wifi/v878-esoc-engine-register-preflight-live/manifest.json`
- V879 classifier:
  `docs/reports/NATIVE_INIT_V879_CMD_ENGINE_OWNERSHIP_CLASSIFIER_2026-05-26.md`
- eSoC / PeripheralManager overview:
  `docs/overview/ESOC_PERIPHERAL_MANAGER_BRINGUP_RESEARCH_2026-05-25.md`
- helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`

## Method

1. Bump the helper marker from `v137` to `v138`.
2. Repair stale successful-open `errno` reporting for `/dev/esoc-0` open paths.
3. Add fail-closed mode
   `wifi-companion-esoc-req-registered-subsys-hold-preflight`.
4. Add explicit allow flag
   `--allow-esoc-req-registered-subsys-hold-preflight`.
5. Keep the new mode separate from service-manager, actor, HAL, scan/connect,
   DHCP, route, credential, and external ping paths.
6. Build a static ARM64 artifact and check marker/mode/flag strings.

## Hard Gates

- Source/build-only.
- No helper deploy.
- No bridge or device command.
- No live eSoC ioctl.
- No live `/dev/subsys_esoc0` open.
- No actor start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or
  external ping.
- No boot image, partition, firmware, GPIO, sysfs, debugfs, module, or reboot
  action.

## Success Criteria

- Static build succeeds with no dynamic section.
- Artifact contains marker `a90_android_execns_probe v138`.
- Artifact contains the new mode and allow flag strings.
- The default path is fail-closed without opens/ioctls.
- The live-capable path explicitly records `REG_REQ_ENG`, child lifecycle,
  timeout, cleanup, and reboot-required evidence markers.

## Next

If V880 passes, V881 should be deploy-only helper `v138` checksum/version/mode
proof. V881 must still avoid live eSoC ioctls and `/dev/subsys_esoc0` open.
