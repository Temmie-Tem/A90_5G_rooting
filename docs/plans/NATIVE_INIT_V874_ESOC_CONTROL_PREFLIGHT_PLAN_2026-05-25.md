# V874 eSoC Control Preflight Plan

## Goal

Use deployed helper `v136` to prove `/dev/esoc-0` visibility and read-only eSoC
status ioctl behavior in a bounded live window. This is still not an mdm3
bring-up attempt.

## Inputs

- V873 report: `docs/reports/NATIVE_INIT_V873_HELPER_V136_DEPLOY_2026-05-25.md`
- Live runner: `scripts/revalidation/native_wifi_esoc_control_preflight_v874.py`
- eSoC research: `docs/overview/ESOC_PERIPHERAL_MANAGER_BRINGUP_RESEARCH_2026-05-25.md`

## Method

1. Verify helper `v136` local and remote SHA/mode parity.
2. Materialize Android-equivalent private eSoC nodes for the helper namespace.
3. Open `/dev/esoc-0` only.
4. Issue read-only status ioctls only: `GET_STATUS`, `GET_ERR_FATAL`, and
   `GET_LINK_ID`.
5. Clean up created nodes and capture postflight health plus actor/network
   surfaces.

## Hard Gates

- No `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, `WAIT_FOR_REQ`, `NOTIFY`, or
  `PWR_ON`.
- No `mdm_helper`, `ks`, `pm_proxy_helper`, CNSS, service-manager trio,
  Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.
- No module load/unload, boot image write, partition write, or firmware
  mutation.

## Success Criteria

- Decision is `v874-esoc-readonly-ioctl-probe-pass`.
- Helper reports `read-only-ioctl-probe-complete`.
- Forbidden-action markers remain `0`.
- Created nodes are removed and postflight selftest stays `fail=0`.
- Actor process hits and Wi-Fi link hits remain empty.

## Next

If V874 passes, V875 should classify the minimum mutating eSoC state-machine
preconditions for a later `REG_CMD_ENG`/`REG_REQ_ENG` gate. `PWR_ON` remains a
separate later gate.
