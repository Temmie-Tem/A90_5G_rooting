# Native Init V1102 PM Server Early Register Tracefs Plan

## Goal

Replay the V1095 PM provider + `pm-proxy` + bounded `cnss-daemon` observer
window while arming tracefs-only instruction uprobes across the `pm-service`
register implementation between:

- entry: `0x6048`
- supported-peripheral match: `0x60cc`

V1101 proved that the CNSS register request enters `pm-service` at `0x6048`
but does not reach the `0x60cc` match checkpoint. V1102 classifies the precise
early instruction boundary.

## Scope

- Reuse deployed `a90_android_execns_probe v206`.
- Require V1101 predecessor evidence.
- Mount vendor read-only and tracefs only for the observation window.
- Keep `pm-proxy` as positive control for the same `pm-service` path.
- Trace client PM register/connect entry/return in `libperipheral_client.so`.
- Trace server register checkpoints in `pm-service`:
  - stack/output pointer setup at `0x6048`..`0x6068`
  - supported peripheral list load/empty check at `0x606c`..`0x6078`
  - list iteration and helper call at `0x6094`..`0x60a4`
  - `strcmp` call/result at `0x60ac`..`0x60b0`
  - loop advance/compare at `0x60b4`..`0x60b8`
  - branch targets at `0x60c0`, `0x60c4`, `0x60cc`

## Guardrails

- No BPF attach; this gate uses tracefs dynamic uprobes only.
- No `mdm_helper`.
- No Wi-Fi HAL, supplicant, hostapd, scan, connect, DHCP, route, credential use,
  or external ping.
- No `/dev/subsys_esoc0` open, eSoC ioctl, GPIO write, partition write, flash,
  or reboot.
- Tracefs events must be disabled and removed during cleanup.

## Success Criteria

- V1101 predecessor manifest is present and accepted.
- Remote helper sha/usage match `a90_android_execns_probe v206`.
- `libperipheral_client.so` and `pm-service` are visible under the read-only
  vendor mount.
- `pm-proxy` positive control reaches the `SDX50M` list entry, then the `modem`
  list entry, matches `modem`, and returns from PM register/connect.
- `cnss-daemon` server-side register progress is classified by the last
  chronological checkpoint before bounded cleanup.
- Wi-Fi HAL/start/connect/link-up/credential/DHCP/external ping remain false.

## Decision Rules

- Stop before `zero_out_client` means output pointer setup fault or block.
- Stop before `list_empty_cmp` means manager/list surface is invalid or blocked.
- Stop after the first `strcmp_result` with nonzero result means list iteration
  advances but the next entry path blocks.
- Stop at a repeated `name_helper_call` means the supported-peripheral entry
  helper blocks on that specific list entry.
- Reaching `pm_server_register_match` moves the next target below `0x60cc`.
