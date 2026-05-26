# Native Init V1105 PM Server Raw Mutex Tracefs Plan

## Goal

Replay the V1095 PM provider + `pm-proxy` + bounded `cnss-daemon` observer
window while arming tracefs-only uprobes on the raw
`pthread_mutex_lock@plt`/`pthread_mutex_unlock@plt` entries in `pm-service`.

V1104 proved that the `pm-proxy` connect helper locks and unlocks the modem
record mutex before CNSS arrives. V1105 classifies whether CNSS is still
pending at the raw PLT lock level, rather than only at the higher-level helper
checkpoint.

## Scope

- Reuse deployed `a90_android_execns_probe v206`.
- Require V1104 predecessor evidence.
- Mount vendor read-only and tracefs only for the observation window.
- Keep `pm-proxy` as the positive control.
- Preserve V1104 connect-helper checkpoints at `0x95f4`.
- Add raw `pm-service` PLT checkpoints:
  - `pthread_mutex_lock@plt` at `0xa250` call/return
  - `pthread_mutex_unlock@plt` at `0xa270` call/return
- Pair raw lock call/return events per thread and record pending lock calls by
  Binder thread.

## Guardrails

- No BPF attach; this gate uses tracefs dynamic uprobes only.
- No `mdm_helper`.
- No Wi-Fi HAL, supplicant, hostapd, scan, connect, DHCP, route, credential use,
  or external ping.
- No `/dev/subsys_esoc0` open, eSoC ioctl, GPIO write, partition write, flash,
  or reboot.
- Tracefs events must be disabled and removed during cleanup.

## Success Criteria

- V1104 predecessor manifest is present and accepted.
- Remote helper sha/usage match `a90_android_execns_probe v206`.
- `libperipheral_client.so` and `pm-service` are visible under the read-only
  vendor mount.
- Raw lock/unlock call-return pairing is captured across `pm-service` threads.
- CNSS reaches the modem record `pm_server_name_helper_lock_call`.
- If CNSS has no raw lock return for the modem mutex while `pm-proxy` connect
  completed and unlocked, classify the next blocker as mutex owner/waiter state.
- Wi-Fi HAL/start/connect/link-up/credential/DHCP/external ping remain false.

## Decision Rules

- `v1105-cnss-raw-pthread-lock-pending-on-modem-mutex`: CNSS Binder thread has a
  raw `pthread_mutex_lock` call with no matching return while the CNSS PM
  register transaction does not return.
- `v1105-pm-proxy-connect-lock-leak`: `pm-proxy` connect helper locks but does
  not unlock.
- `v1105-pm-proxy-connect-unlocks-modem-cnss-lock-still-blocks`: fallback when
  only helper-level checkpoints reproduce V1104 without raw pending evidence.
- Any register/enable/cleanup failure, forbidden actor, Wi-Fi link, or helper
  mismatch is a failed gate requiring cleanup or predecessor repair.
