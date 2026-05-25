# V898 mdm_helper/ks Contract Helper v144 Plan

## Goal

Add source/build-only helper support for the Android-equivalent
`mdm_helper`/`ks` image/link contract selected by V897.

V898 must not deploy the helper and must not execute the new live actor path.

## Inputs

- V897 contract classifier:
  `docs/reports/NATIVE_INIT_V897_MDM_HELPER_KS_CONTRACT_DESIGN_2026-05-26.md`
- helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`
- build script:
  `scripts/revalidation/build_android_execns_probe_helper.sh`

## Method

1. Bump helper marker to `a90_android_execns_probe v144`.
2. Add mode `wifi-companion-mdm-helper-ks-image-contract-preflight`.
3. Add allow flag `--allow-mdm-helper-ks-contract-preflight`.
4. Reuse private Android node materialization for `/dev/esoc-0`,
   `/dev/subsys_esoc0`, and `/dev/subsys_modem`.
5. Add fail-closed live logic for a later gate:
   - start `/vendor/bin/mdm_helper`;
   - open `/dev/subsys_esoc0` only after `mdm_helper` is observable;
   - do not `REG_REQ_ENG`, `ESOC_NOTIFY`, or `BOOT_DONE` from the controller;
   - observe `/vendor/bin/ks` and `/dev/mhi_0305_01.01.00_pipe_10`;
   - classify cleanup as reboot-required if actors are not proven stopped.
6. Build a static ARM64 artifact and verify required marker strings.

## Hard Gates

- Source/build-only.
- No helper deploy.
- No bridge or device command for the new mode.
- No live eSoC ioctl.
- No `/dev/subsys_esoc0` open.
- No `mdm_helper` start.
- No `ks` start.
- No live `ESOC_NOTIFY` or `ESOC_BOOT_DONE`.
- No service-manager, CNSS daemon, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, boot image write, partition write, firmware
  mutation, GPIO/sysfs/debugfs write, module load/unload, reboot, or Wi-Fi
  link-up.

## Success Criteria

- Static ARM64 build succeeds.
- Artifact has no dynamic section.
- Artifact advertises helper marker `a90_android_execns_probe v144`.
- Artifact advertises mode
  `wifi-companion-mdm-helper-ks-image-contract-preflight`.
- Artifact advertises allow flag
  `--allow-mdm-helper-ks-contract-preflight`.
- Artifact includes markers for:
  - `mdm_helper` before `subsys_esoc0`;
  - `/vendor/bin/ks`;
  - `/dev/mhi_0305_01.01.00_pipe_10`;
  - `REG_REQ_ENG=0`, `NOTIFY=0`, and `BOOT_DONE=0` in this mode.
- V897 classifier re-run sees helper contract support present.

## Next

If V898 passes, V899 should be deploy-only helper `v144` parity. The first
live `mdm_helper`/`ks` contract proof remains a separate bounded cycle.
