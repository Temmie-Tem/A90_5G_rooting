# Native Init V1096 PM CNSS Peripheral Tracefs Plan

## Goal

Replay the V1095 PM provider + `pm-proxy` + bounded `cnss-daemon` observer
window while arming tracefs-only dynamic uprobes on
`/mnt/vendor/lib64/libperipheral_client.so`. The purpose is to classify whether
`cnss-daemon` actually enters the PeripheralManager client/vote path before
mdm3 remains `OFFLINING`.

## Scope

- Reuse deployed `a90_android_execns_probe v206`.
- Keep V1095 as the predecessor gate.
- Mount tracefs and vendor read-only only for the bounded observation window.
- Register uprobes on selected `libperipheral_client.so` offsets:
  `pm_client_register`, `pm_register_connect`, `pm_client_connect`,
  `pm_client_ack`, and adjacent cleanup/disconnect functions.
- Parse tracefs lines by process comm so `cnss-daemon` hits are separated from
  `pm-service`, `pm-proxy`, and Binder thread hits.
- Use serial `a90ctl run` for the collector because `a90_tcpctl run` has a
  10 second device-side timeout.

## Guardrails

- No BPF attach; this gate uses tracefs dynamic uprobes only.
- No `mdm_helper`.
- No Wi-Fi HAL, supplicant, hostapd, scan, connect, DHCP, route, credential use,
  or external ping.
- No `/dev/subsys_esoc0` open, eSoC ioctl, GPIO write, partition write, flash,
  or reboot.
- `cnss-daemon` is allowed only inside the V1095 post-provider bounded window.
- Tracefs events must be disabled and removed during cleanup.

## Implementation

1. Add `native_wifi_pm_cnss_peripheral_tracefs_live_v1096.py`.
2. Load V1095 manifest and require a known V1095 decision.
3. Generate a child script that runs the same V1095 helper command.
4. Generate a collector script that registers tracefs uprobes on
   `libperipheral_client.so`, runs the child, captures trace lines/counts, and
   removes events.
5. Classify total PM client hits and `cnss-daemon`-specific hits separately.

## Success Criteria

- V1095 predecessor manifest is present and accepted.
- Remote helper sha/usage match `a90_android_execns_probe v206`.
- `libperipheral_client.so` is visible from the read-only vendor mount.
- Tracefs registers/enables/removes all events cleanly.
- The child reaches the V1095 CNSS phase.
- Wi-Fi HAL/start/connect/link-up/credential/DHCP/external ping remain false.

## Decision Rules

- `cnss-daemon` hits on PM client symbols mean the CNSS process does enter the
  PeripheralManager client path; the next blocker is PM service response/vote
  semantics or lower eSoC trigger.
- Only `pm-proxy`/Binder hits and no `cnss-daemon` hits mean `cnss-daemon`
  opened Binder/runtime surfaces but did not issue the expected PM client call.
- No uprobe hits means the file/offset/inode mapping must be fixed before any
  interpretation.
