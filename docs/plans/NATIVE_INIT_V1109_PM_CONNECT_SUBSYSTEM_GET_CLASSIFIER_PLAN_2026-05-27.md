# V1109 PM Connect Subsystem-Get Classifier Plan

Date: 2026-05-27

## Goal

Use V1108 evidence to classify the lower blocker after successful CNSS PeripheralManager connect, without running any new device-side actors.

## Background

- V1108 proved that skipping pre-CNSS `per_proxy` lets `cnss-daemon` reach PM register/connect.
- Both `pm_client_register` and `pm_client_connect` returned `0x0`.
- `mdm3` still remained `OFFLINING`.
- The V1108 trace also contained a later pending `pm-service` mutex wait that needed ownership reconstruction.

## Method

- Parse `tmp/wifi/v1108-pm-ordering-no-pre-cnss-per-proxy-live/manifest.json`.
- Reconstruct raw mutex ownership using the V1107 classifier logic.
- Target the post-connect pending `pm-service` main-thread raw mutex lock.
- Compare owner/waiter thread states from the V1108 sampler.
- Disassemble the owner return offset from the staged `pm-service` binary.

## Success Criteria

- V1108 ordering contract is still proven:
  - `per_proxy_start_executed=0`
  - `child.per_proxy.start_skipped=1`
  - `start_cnss_before_per_proxy=1`
- CNSS PM success is still proven:
  - `pm_client_register_ret=['0x0']`
  - `pm_client_connect_ret=['0x0']`
- The post-connect pending mutex owner and waiter are identified.

## Hard Gates

- Host-only.
- No device command.
- No tracefs write.
- No PM actor, CNSS actor, Wi-Fi HAL, scan/connect, DHCP, route, credential, or external ping.
- No partition write, flash, or reboot.

