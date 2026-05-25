# V876 eSoC Engine Register Helper v137 Plan

## Goal

Add source/build-only helper support for a fail-closed CMD/REQ engine
registration preflight. This prepares the next live gate without deploying the
helper or executing any eSoC ioctl in V876.

## Inputs

- V875 report: `docs/reports/NATIVE_INIT_V875_ESOC_STATE_MACHINE_PRECONDITION_2026-05-25.md`
- Helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- Build script: `scripts/revalidation/build_android_execns_probe_helper.sh`
- Local A90 UAPI: `kernel_build/SM-A908N_KOR_12_Opensource/Kernel/include/uapi/linux/esoc_ctrl.h`

## Implementation

1. Bump helper marker to `a90_android_execns_probe v137`.
2. Add mode `wifi-companion-esoc-engine-register-preflight`.
3. Add allow flag `--allow-esoc-engine-register-preflight`.
4. Reuse private eSoC node materialization for `/dev/esoc-0`,
   `/dev/subsys_esoc0`, and `/dev/subsys_modem`.
5. Add guarded CMD/REQ registration preflight body for a later live gate.
6. Keep `CMD_EXE`, `PWR_ON`, `WAIT_FOR_REQ`, `NOTIFY`, `/dev/subsys_esoc0`
   open, actor start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and
   external ping blocked.

## Validation

- Static ARM64 build must pass.
- Artifact must be statically linked with no dynamic section.
- `strings` must show:
  - `a90_android_execns_probe v137`
  - `wifi-companion-esoc-engine-register-preflight`
  - `--allow-esoc-engine-register-preflight`
  - fail-closed markers for `cmd_exe_attempted=0`, `pwr_on_attempted=0`,
    `wait_for_req_attempted=0`, `notify_attempted=0`,
    `subsys_esoc0_open_attempted=0`, `credentials=0`, and `external_ping=0`.

## Hard Gates

- Source/build only: no deploy and no bridge/device live run.
- No `REG_CMD_ENG`, `REG_REQ_ENG`, `CMD_EXE`, `PWR_ON`, `WAIT_FOR_REQ`, or
  `NOTIFY` execution in V876.
- No `mdm_helper`, `ks`, `pm_proxy_helper`, CNSS, service-manager trio,
  Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Next

V877 should deploy helper `v137` only with checksum/version/mode proof. V878
can then be a bounded live CMD/REQ registration preflight, still without
`CMD_EXE`, `PWR_ON`, `WAIT_FOR_REQ`, `NOTIFY`, `/dev/subsys_esoc0` open, or any
actor/Wi-Fi bring-up path.
