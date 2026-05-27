# V1116 Global Holder Immediate CNSS Live Plan

Date: `2026-05-27`

## Goal

Deploy helper `a90_android_execns_probe v210`, then run the V1115-selected
global firmware + `/dev/subsys_modem` holder gate with CNSS started immediately
after `per_mgr`.

V1114 showed that the old 1000 ms post-`per_mgr` probe misses the PM-service
lifetime window. V1115 added a 20 ms early sample and immediate-CNSS order.
V1116 validates that order on-device.

## Scope

- Deploy only `/cache/bin/a90_android_execns_probe` to helper `v210`.
- Use serial deploy fallback if NCM host IP is unavailable.
- Start the bounded global firmware mount + global modem-holder gate.
- Start PM observer actors and `cnss-daemon` only inside the tracefs observer
  window.
- Require cleanup reboot and native health after the gate.

## Guardrails

- No `/dev/subsys_esoc0` open.
- No Wi-Fi HAL, wificond, supplicant, scan/connect/link-up, credential use,
  DHCP/routes, or external ping.
- No partition write, boot image write, or flash.
- Tracefs writes are limited to the bounded uprobe observer and must be cleaned.
- Firmware partitions are mounted read-only.

## Success Criteria

V1116 passes if:

- helper `v210` is deployed or already current;
- global firmware mounts and global `/dev/subsys_modem` holder are proven;
- QRTR RX appears under holder;
- PM observer contract shows:
  - `start_cnss_immediate_after_per_mgr=1`;
  - `child.per_mgr.post_start_probe_wait_ms=20`;
  - `per_proxy_start_executed=0`;
  - `child.per_proxy.start_skipped=1`;
  - `cnss_daemon_start_executed=1`;
- cleanup reboot returns to healthy native init.

## Expected Branches

- PM connect or WLFW advances: classify lower PM/eSoC side effects before Wi-Fi
  HAL.
- PM register only: trace register-to-connect transition.
- PM client absent: start CNSS with a smaller or zero delay after `per_mgr`.
