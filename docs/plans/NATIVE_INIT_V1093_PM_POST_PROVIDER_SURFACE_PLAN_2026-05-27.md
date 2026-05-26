# Native Init V1093 PM Post-Provider Surface Plan

## Goal

Use the V1092 provider-positive PM observer path to capture the lower Wi-Fi
surface immediately after `vendor.qcom.PeripheralManager` appears.

## Scope

- Deploy `a90_android_execns_probe v203`.
- Keep the V490 SELinux policy-load precondition.
- Start only the service-manager trio, `pm_proxy_helper`, `pm-service`, and the
  bounded `vndservice list` query needed to prove provider registration.
- Stop at the first provider-positive window and capture mdm3, ICNSS, QRTR, and
  `wlan0` state.
- Write full helper output to a device-side file and return only compact key
  lines over tcpctl to avoid the 128 KiB tcpctl output cap.

## Guardrails

- No `mdm_helper`.
- No CNSS daemon.
- No Wi-Fi HAL, supplicant, hostapd, scan, connect, DHCP, route, or external
  ping.
- No `/dev/subsys_esoc0` open, eSoC ioctl, GPIO write, partition write, flash,
  or reboot.
- QRTR readback is limited to service lookup/readback for services `69`, `74`,
  and `180`; no QMI payload is sent.

## Implementation

1. Add `a90_android_execns_probe v203` post-provider surface capture.
2. Allow QRTR nameservice readback only for the PM observer gate.
3. Record mdm3 state, firmware name, crash count, restart level, ICNSS runtime
   status, `qcwlanstate`, `wlan0`, and compact klog counts.
4. Add a V1093 runner that writes a device-side shell script before executing
   the helper over NCM/tcpctl.
5. Add a V1093 deploy wrapper for helper v203.

## Success Criteria

- Helper v203 deploy/preflight passes.
- V490 policy-load proof passes before the live gate.
- `vndservicemanager_readiness.ready=1`.
- `vendor.qcom.PeripheralManager` is observed.
- Post-provider surface has `begin=1` and `end=1`.
- Wi-Fi HAL/start/connect/link-up/external ping remain `False`.

## Decision Rules

- `mdm3_state=ONLINE`, `wlan0_exists=1`, or WLFW service `69` readback events
  mean lower-surface progress and the next gate should classify the transition.
- Provider-positive with mdm3 still not online and no WLFW means PM provider
  registration is no longer the blocker; the next work returns to MDM3/eSoC
  lower trigger analysis.
