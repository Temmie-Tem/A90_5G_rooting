# Native Init V1104 PM Server Connect Mutex Tracefs Plan

## Goal

Replay the V1095 PM provider + `pm-proxy` + bounded `cnss-daemon` observer
window while arming tracefs-only instruction uprobes around the `pm-service`
connect helper at `0x95f4`.

V1103 proved that CNSS blocks inside `pthread_mutex_lock(entry + 0x18)` for the
second/modem supported peripheral record. V1104 classifies whether the earlier
`pm-proxy` connect path leaks that modem mutex or unlocks it cleanly before CNSS
arrives.

## Scope

- Reuse deployed `a90_android_execns_probe v206`.
- Require V1103 predecessor evidence.
- Mount vendor read-only and tracefs only for the observation window.
- Keep `pm-proxy` as positive control.
- Trace client PM register/connect entry/return in `libperipheral_client.so`.
- Trace `pm-service` name helper `0x9538` to preserve the V1103 CNSS blocker.
- Trace `pm-service` connect helper `0x95f4`:
  - helper entry and mutex derivation at `0x95f4`..`0x961c`
  - lock call/return at `0x9628`..`0x962c`
  - client-found/state/vote path at `0x9688`..`0x9728`
  - unlock call/return at `0x96f8`..`0x96fc`
  - helper return at `0x970c` and function return.

## Guardrails

- No BPF attach; this gate uses tracefs dynamic uprobes only.
- No `mdm_helper`.
- No Wi-Fi HAL, supplicant, hostapd, scan, connect, DHCP, route, credential use,
  or external ping.
- No `/dev/subsys_esoc0` open, eSoC ioctl, GPIO write, partition write, flash,
  or reboot.
- Tracefs events must be disabled and removed during cleanup.

## Success Criteria

- V1103 predecessor manifest is present and accepted.
- Remote helper sha/usage match `a90_android_execns_probe v206`.
- `libperipheral_client.so` and `pm-service` are visible under the read-only
  vendor mount.
- `pm-proxy` positive control reaches connect helper lock, lock-return,
  unlock, unlock-return, helper return, and outer connect return.
- CNSS still reaches the V1103 modem record helper lock blocker if the lower
  state has not advanced.
- Wi-Fi HAL/start/connect/link-up/credential/DHCP/external ping remain false.

## Decision Rules

- `pm-proxy` connect lock without unlock means the blocker is a connect-path
  mutex leak.
- `pm-proxy` connect unlock + return while CNSS later blocks means the blocker
  is not a simple connect-path missing unlock; next target is mutex owner/waiter
  state after `pm-proxy` returns.
- CNSS reaching register match or connect means the route has advanced below
  the current blocker.
