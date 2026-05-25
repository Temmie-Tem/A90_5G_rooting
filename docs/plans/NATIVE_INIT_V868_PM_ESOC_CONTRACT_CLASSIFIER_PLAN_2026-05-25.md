# V868 PM/eSoC Contract Classifier Plan

## Goal

Classify the blocker exposed by V867 before any more live actor starts. The
specific question is whether `pm_proxy_helper` can be retried safely on its own,
or whether the Android eSoC control contract requires `/dev/esoc-0` CMD/REQ
engine registration before `/dev/subsys_esoc0` is held.

## Inputs

- V867 report: `docs/reports/NATIVE_INIT_V867_PM_INIT_CONTRACT_START_ONLY_2026-05-25.md`
- V867 evidence: `tmp/wifi/v867-pm-init-contract-live-r3/manifest.json`
- eSoC/PeripheralManager research: `docs/overview/ESOC_PERIPHERAL_MANAGER_BRINGUP_RESEARCH_2026-05-25.md`
- Local Samsung OSRC UAPI: `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/include/uapi/linux/esoc_ctrl.h`
- Local Samsung OSRC SSR source: `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/subsystem_restart.c`

## Method

1. Parse V867 evidence for the residual `pm_proxy_helper` D-state outcome.
2. Parse local A90 OSRC `esoc_ctrl.h` for `ESOC_REG_REQ_ENG`,
   `ESOC_REG_CMD_ENG`, `ESOC_CMD_EXE`, `ESOC_WAIT_FOR_REQ`,
   `ESOC_NOTIFY`, and `ESOC_PWR_ON` values.
3. Confirm `subsystem_restart.c` has the Samsung `pm_proxy_helper` exception
   around eSoC shutdown dependency handling.
4. Compare the research document against the local OSRC values and reject stale
   public example ioctl offsets.
5. Select the next gate without contacting the device.

## Success Criteria

- Host-only classifier emits a manifest and summary.
- Decision is explicit about whether `pm_proxy_helper` alone is closed.
- Local A90 OSRC ioctl values are recorded.
- The next gate is narrower than Wi-Fi HAL/scan/connect and does not use
  credentials.

## Hard Gates

- No bridge/device contact.
- No daemon start, no `mdm_helper`, no `ks`, no Wi-Fi HAL.
- No scan/connect, credentials, DHCP/routes, or external ping.
- No raw live eSoC ioctl, GPIO/sysfs/debugfs/subsystem state write, module
  load/unload, boot image write, or partition write.

## Expected Branch

If V867 D-state and the local eSoC UAPI contract both line up, V869 should be a
source/build-only helper design for a safe A90 eSoC control preflight. Live
`ESOC_PWR_ON` remains blocked until a later separate gate.
