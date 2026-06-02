# Native Init V1682 WLAN-PD Service-window Merge Plan

## Summary

- Cycle: `V1682`
- Type: source/build-only plan for the next helper/test-boot unit
- Target decision: `v1682-wlan-pd-service-window-merge-source-build-pass`

V1681 reclassifies the valid V1680 `firmware-not-requested` label as an
upstream `cnss-daemon wlfw_start` trigger-surface gap.  The two closest prior
routes each cover only half of the needed setup:

- V1564: Android Wi-Fi service-window route started userspace actors, but did
  not include the corrected internal-modem `/dev/subsys_modem` holder /
  WLAN-PD firmware-serve gate.
- V1680: corrected internal-modem holder and firmware-serve observation were
  valid, but the Android pre-CNSS service/provider surface was absent.

V1682 should build a source-only merged route that preserves the V1680 internal
modem path and adds the minimum Android service-window surface needed to
classify `cnss-daemon wlfw_start` / `wlfw_service_request`.

## Scope

Implement source/build support only.  Do not run live in V1682.

The next helper/test-boot route should:

1. keep the V1680 firmware-mount overlay and WLAN-PD firmware-serve snapshots;
2. start `qrtr-ns`, `pd-mapper`, `rmt_storage`, and `tftp_server`;
3. start a modem-only `/dev/subsys_modem` holder;
4. add the bounded Android service-window surface used by V1564 only as needed
   to make `cnss-daemon` reach the Android-good pre-WLFW contract;
5. start `cnss_diag` and `cnss-daemon -n -l`;
6. capture `wlfw_start`, `wlfw_service_request`, WLFW service 69, WLAN-PD state,
   tftp requests, and child postflight safety;
7. classify and stop without scan/connect or network routing.

## Proposed Helper Contract

Add a new helper mode, for example:

```text
wifi-companion-wlan-pd-service-window-trigger-start-only
```

The mode should emit explicit evidence keys:

```text
wlan_pd_service_window_trigger.begin=1
wlan_pd_service_window_trigger.no_esoc0=1
wlan_pd_service_window_trigger.no_forced_rc1=1
wlan_pd_service_window_trigger.no_fake_online=1
wlan_pd_service_window_trigger.no_scan_connect=1
wlan_pd_service_window_trigger.no_credentials=1
wlan_pd_service_window_trigger.no_dhcp_routes=1
wlan_pd_service_window_trigger.no_external_ping=1
wlan_pd_service_window_trigger.subsys_modem_holder_opened=0|1
wlan_pd_service_window_trigger.tftp_running=0|1
wlan_pd_service_window_trigger.cnss_daemon_started=0|1
wlan_pd_service_window_trigger.wlfw_start_seen=0|1
wlan_pd_service_window_trigger.wlfw_service_request_seen=0|1
wlan_pd_service_window_trigger.wlfw_service69_seen=0|1
wlan_pd_service_window_trigger.requested_wlanmdsp=0|1
wlan_pd_service_window_trigger.label=<label>
```

## Labels

- `wlfw-start-reached`: `cnss-daemon wlfw_start` or
  `wlfw_service_request` appears.  This proves the V1681 trigger-surface gap is
  closed and the next gate may inspect WLFW service 69 / WLAN-PD / firmware
  serving.
- `service-window-still-no-wlfw`: service-window actors and modem holder are
  safe and observable, but no `wlfw_start` / `wlfw_service_request` appears.
  Next work should inspect the missing Android property/binder/service input,
  not tftp timing.
- `modem-holder-regression`: `/dev/subsys_modem` holder, mss loading/reset, or
  `rmt_storage` EFS evidence regresses from V1680.
- `service-window-child-failed`: a required service-window child exits early or
  is not postflight-safe.

## Implementation Steps

1. Add the new mode predicate to `stage3/linux_init/helpers/a90_android_execns_probe.c`.
2. Add an allow flag specific to this merged route so existing Android
   service-window and WLAN-PD firmware-serve modes stay fail-closed.
3. Factor the V1680 modem-holder start/stop and firmware-serve summary into the
   service-window route, without opening `/dev/subsys_esoc0`.
4. Extend `scripts/revalidation/build_native_init_wifi_test_boot_v1393.py` with
   a new `--wifi-test-helper-mode` selector for the merged route.
5. Build helper/test boot only, then verify:
   - helper is static aarch64 and has no dynamic interpreter;
   - test boot contains the new mode and allow flag;
   - forbidden route strings for forced RC1/eSoC writes are absent from the PID1
     argv contract;
   - credential-like bytes are absent;
   - generated artifacts are private.

## Future Live Gate

V1682 should not run live.  A later V1683/V1684 handoff may run one rollbackable
live gate only after source/build and artifact sanity pass.

Future live success target is only `wlfw_start` / `wlfw_service_request` or a
fixed failure label.  It is not a scan/connect or external connectivity test.

## Guardrails

Still forbidden:

- `/dev/subsys_esoc0` open;
- raw eSoC controller ioctl;
- forced RC1 enumerate or pci-msm `case` writes;
- fake-ONLINE/system-info spoof;
- PMIC/GPIO/GDSC writes;
- eSoC notify or `BOOT_DONE` spoof;
- PCI rescan or platform bind/unbind;
- Wi-Fi scan/connect;
- credentials;
- DHCP/routes;
- external ping;
- firmware or partition writes.

Only source/build artifacts are in scope for V1682.
