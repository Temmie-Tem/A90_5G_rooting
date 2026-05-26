# Native Init V1094 PM Per-Proxy Surface Plan

## Goal

Extend the V1093 provider-positive PM observer window past `pm-service` provider
registration, start `pm-proxy`, and capture whether the PM stack opens
`/dev/subsys_modem` or advances mdm3/WLFW after the full PM pair is present.

## Scope

- Deploy and use `a90_android_execns_probe v205`.
- Keep the V490 SELinux policy-load precondition.
- Start only the service-manager trio, `pm_proxy_helper`, `pm-service`,
  `pm-proxy`, and bounded `vndservice list` queries.
- Capture provider-positive lower surface both after `pm-service` and after
  `pm-proxy`.
- Use serial `a90ctl` for the long helper script because `a90_tcpctl run` has a
  10 second device-side timeout.

## Guardrails

- No `mdm_helper`.
- No CNSS daemon.
- No Wi-Fi HAL, supplicant, hostapd, scan, connect, DHCP, route, credential use,
  or external ping.
- No `/dev/subsys_esoc0` open, eSoC ioctl, GPIO write, partition write, flash,
  or reboot unless cleanup is explicitly required.
- QRTR readback is limited to nameservice lookup/readback for services `69`,
  `74`, and `180`; no QMI payload is sent.

## Implementation

1. Add `--pm-observer-continue-after-provider` to the PM observer mode.
2. Continue from the first provider-positive query to `pm-proxy` instead of
   ending at `pm-service`.
3. Capture `after_per_proxy` fd matches for `pm-service` and `pm_proxy_helper`
   against `/dev/subsys_modem` and `/dev/vndbinder`.
4. Capture `after_per_proxy` mdm3, `wlan0`, ICNSS, QRTR, and compact klog state.
5. Add V1094 deploy/live wrappers using serial for remote helper checks,
   post-surface checks, and the long helper script.

## Success Criteria

- Helper v205 deploy/preflight passes.
- V490 policy-load proof passes before the live gate.
- `vndservicemanager_readiness.ready=1`.
- `vendor.qcom.PeripheralManager` is observed after both `pm-service` and
  `pm-proxy` phases.
- `after_per_proxy` lower-surface snapshot has `begin=1` and `end=1`.
- Wi-Fi HAL/start/connect/link-up/credential/DHCP/external ping remain false.

## Decision Rules

- `mdm3_state=ONLINE`, `wlan0_exists=1`, or WLFW service `69` readback events
  mean lower-surface progress and the next gate should classify the transition.
- Any `/dev/subsys_modem` fd on `pm-service` or `pm_proxy_helper` means the PM
  fd contract advanced and the next gate should classify the post-fd lower
  blocker.
- Provider-positive with `pm-proxy`, no PM subsystem fd, `mdm3=OFFLINING`, and
  no WLFW means the missing piece is still a lower PM client/voter or eSoC
  trigger, not `pm-service` provider registration.
