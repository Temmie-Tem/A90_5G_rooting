# V875 eSoC State-machine Precondition Classifier Plan

## Goal

Classify the next eSoC state-machine gate after V874 without executing any live
mutating ioctl. The output must decide whether the project can move to helper
support for `REG_CMD_ENG`/`REG_REQ_ENG`, or whether more source/evidence is
needed first.

## Inputs

- V874 report: `docs/reports/NATIVE_INIT_V874_ESOC_CONTROL_PREFLIGHT_2026-05-25.md`
- V849 evidence: `tmp/wifi/v849-subsys-esoc0-wait-state-sampler/manifest.json`
- V874 evidence: `tmp/wifi/v874-esoc-control-preflight-live/manifest.json`
- Local A90 OSRC:
  - `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/include/uapi/linux/esoc_ctrl.h`
  - `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/include/linux/esoc_client.h`
  - `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/drivers/soc/qcom/subsystem_restart.c`
  - `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/include/soc/qcom/subsystem_restart.h`

## Method

1. Parse local eSoC UAPI constants and enum values.
2. Confirm SSR source contract: `/dev/subsys_esoc0` open calls
   `subsystem_get_with_fwname`, `subsys_start` calls provider `powerup`, and
   startup waits for `err_ready`.
3. Confirm V849 shows blind `/dev/subsys_esoc0` open blocks before the observed
   Wi-Fi path advances.
4. Confirm V874 proves `/dev/esoc-0` read-only control path visibility.
5. Classify each candidate operation by risk and next gate.

## Hard Gates

- Host-only only: no bridge/device command.
- No `REG_CMD_ENG`, `REG_REQ_ENG`, `CMD_EXE`, `PWR_ON`, `WAIT_FOR_REQ`, or
  `NOTIFY`.
- No `mdm_helper`, `ks`, `pm_proxy_helper`, CNSS, service-manager trio,
  Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Success Criteria

- Manifest decision is `v875-esoc-state-machine-precondition-pass`.
- Manifest records `live_device_contact=false` and
  `mutating_esoc_ioctl_executed=false`.
- Next gate is source/build-only helper support for CMD/REQ registration.
- `PWR_ON`, `/dev/subsys_esoc0` open, `WAIT_FOR_REQ`, and `NOTIFY` remain
  blocked until later gates.
