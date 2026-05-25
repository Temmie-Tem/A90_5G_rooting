# V872 eSoC Preflight Helper v136 Plan

## Goal

Repair helper `v135` classification so the eSoC control preflight mode can run
as a bounded `/dev/esoc-0` read-only probe without being treated as a
service-manager/SELinuxfs runtime mode.

## Inputs

- V870 deploy report: `docs/reports/NATIVE_INIT_V870_HELPER_V135_DEPLOY_2026-05-25.md`
- eSoC research: `docs/overview/ESOC_PERIPHERAL_MANAGER_BRINGUP_RESEARCH_2026-05-25.md`
- Helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- V871 evidence: `tmp/wifi/v871-esoc-control-preflight-live-r3/manifest.json`

## Implementation

1. Bump helper marker to `a90_android_execns_probe v136`.
2. Split PeripheralManager service-node materialization from generic private
   eSoC node materialization.
3. Keep `wifi-companion-esoc-control-preflight` eligible for private
   `/dev/esoc-0`, `/dev/subsys_esoc0`, and `/dev/subsys_modem` node creation.
4. Stop classifying eSoC control preflight as a service-manager mode.
5. Keep the mode fail-closed: no daemon start, no Wi-Fi bring-up, and no
   mutating eSoC ioctl.

## Validation

- Static ARM64 build must pass with no dynamic section.
- Artifact strings must include `a90_android_execns_probe v136` and
  `wifi-companion-esoc-control-preflight`.
- The next deploy gate must prove remote checksum and mode token before any
  live preflight run.

## Hard Gates

- Source/build only: no helper deploy in V872.
- No `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, `WAIT_FOR_REQ`, `NOTIFY`, or
  `PWR_ON`.
- No `mdm_helper`, `ks`, `pm_proxy_helper`, CNSS, service-manager trio,
  Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Next

V873 should deploy helper `v136` only. V874 should rerun bounded read-only eSoC
control preflight after remote parity is proven.
