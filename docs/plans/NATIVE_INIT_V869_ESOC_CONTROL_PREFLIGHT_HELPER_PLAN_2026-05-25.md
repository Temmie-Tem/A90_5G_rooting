# V869 eSoC Control Preflight Helper Plan

## Goal

Add source/build-only helper support for the next safe eSoC gate after V868.
The helper must model the A90 `/dev/esoc-0` control path and expose local
Samsung OSRC ioctl constants without starting `mdm_helper`, `ks`,
`pm_proxy_helper`, CNSS, Wi-Fi HAL, scan/connect, DHCP, routes, or external
networking.

## Inputs

- V868 report: `docs/reports/NATIVE_INIT_V868_PM_ESOC_CONTRACT_CLASSIFIER_2026-05-25.md`
- eSoC research: `docs/overview/ESOC_PERIPHERAL_MANAGER_BRINGUP_RESEARCH_2026-05-25.md`
- Helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- Build script: `scripts/revalidation/build_android_execns_probe_helper.sh`

## Implementation

1. Bump helper marker to `a90_android_execns_probe v135`.
2. Add local A90 eSoC UAPI constants:
   `ESOC_CMD_EXE`, `ESOC_WAIT_FOR_REQ`, `ESOC_NOTIFY`, `ESOC_GET_STATUS`,
   `ESOC_GET_ERR_FATAL`, `ESOC_WAIT_FOR_CRASH`, `ESOC_REG_REQ_ENG`,
   `ESOC_REG_CMD_ENG`, `ESOC_GET_LINK_ID`, `ESOC_PWR_ON`,
   `ESOC_IMG_XFER_DONE`, and `ESOC_BOOT_DONE`.
3. Add mode `wifi-companion-esoc-control-preflight`.
4. Add `--allow-esoc-control-preflight` as the only flag that permits the
   read-only live probe path.
5. In blocked mode, emit constants and node status, but do not open
   `/dev/esoc-0`.
6. In allowed mode, limit action to `/dev/esoc-0` open plus read-only
   `GET_STATUS`, `GET_ERR_FATAL`, and `GET_LINK_ID`; never issue
   `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, `WAIT_FOR_REQ`, `NOTIFY`, or
   `PWR_ON`.

## Validation

- Static ARM64 build must pass.
- Artifact must be statically linked with no dynamic section.
- `strings` must show helper `v135`, the new mode, A90 eSoC UAPI markers, and
  fail-closed markers:
  `mdm_helper_start_executed=0`, `wifi_hal_start_executed=0`,
  `external_ping=0`, and `pwr_on_attempted=0`.

## Hard Gates

- Source/build only: no helper deploy, bridge/device contact, or live run.
- No live eSoC ioctl, no `ESOC_PWR_ON`, no `mdm_helper`, no `ks`.
- No `pm_proxy_helper`, CNSS, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, module load/unload, boot image write, or
  partition write.

## Next

If V869 passes, V870 should be deploy-only for helper `v135` with checksum,
usage marker, mode marker, selftest, and actor-clean proof. The first live
eSoC control preflight must remain a separate later gate.
