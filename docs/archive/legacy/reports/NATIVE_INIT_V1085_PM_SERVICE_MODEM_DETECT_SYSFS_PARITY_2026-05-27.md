# Native Init V1085 PM Service Modem Detect Sysfs Parity Report

## Summary

V1085 passed. The helper now exposes the existing read-only modem-detect sysfs
surface to the bounded `pm-service` observer mode. After deploying v197,
`libmdmdetect.so::get_system_info()` advanced past the V1084 blocker and
returned success.

This closes the `get_system_info()` blocker. The new blocker is later:
`pm-service` exits cleanly before the observe window and still does not hold
`/dev/subsys_modem`.

## Change

- Bumped `a90_android_execns_probe` to v197.
- Added PM-service-observer-only use of the existing
  `materialize_rmt_modem_detect_surface()` read-only sysfs binder.
- Added `scripts/revalidation/wifi_execns_helper_v197_deploy_preflight.py`.
- Built static helper:
  `tmp/wifi/v1085-execns-helper-v197-build/a90_android_execns_probe`.

## Evidence

| item | path / value |
| --- | --- |
| source | `stage3/linux_init/helpers/a90_android_execns_probe.c` |
| deploy wrapper | `scripts/revalidation/wifi_execns_helper_v197_deploy_preflight.py` |
| build artifact | `tmp/wifi/v1085-execns-helper-v197-build/a90_android_execns_probe` |
| artifact sha256 | `8dbf5aed1a3d087fc59c308bd674132e19c9cf2da0c42843b64c9c4efaf1672f` |
| deploy manifest | `tmp/wifi/v1085-execns-helper-v197-deploy/manifest.json` |
| live replay manifest | `tmp/wifi/v1085-mdmdetect-sysfs-parity-live/manifest.json` |
| live replay summary | `tmp/wifi/v1085-mdmdetect-sysfs-parity-live/summary.md` |

## Deploy Result

```text
decision: execns-helper-v197-deploy-pass
pass: True
reason: helper v197 deployed or already current; V373 preflight advanced past helper-mode blocker
device_mutations: True
daemon_start_executed: False
wifi_bringup_executed: False
```

Transfer used NCM and installed only `/cache/bin/a90_android_execns_probe`.

## Live Replay Result

```text
decision: v1084-mdmdetect-success-return-observed
pass: True
reason: libmdmdetect get_system_info branch captured: mdmdetect-success-return-observed
```

Important counts:

```json
{
  "mdm_get_system_info_entry": 2,
  "mdm_stat_esoc_call": 2,
  "mdm_msm_opendir_call": 2,
  "mdm_msm_readdir_first": 2,
  "mdm_get_subsystem_info_modem_call": 2,
  "subsys_info_entry": 2,
  "subsys_device_path_format": 2,
  "subsys_success_return": 2,
  "mdm_success_return": 2,
  "mdm_failure_after_msm_open": 0,
  "mdm_msm_opendir_fail_log": 0
}
```

## Remaining Blocker

The PM observer still reports:

```text
pm_service_trigger_observer.result=observer-runtime-gap
pm_service_trigger_observer.reason=child-exited-before-observe-window
pm_service_trigger_observer.child.per_mgr.exit_code=0
pm_service_trigger_observer.per_mgr_subsys_modem_seen=0
pm_service_trigger_observer.pm_proxy_helper_subsys_modem_seen=0
```

This is a different failure class from V1071/V1084. `pm-service` no longer dies
on `get_system_info()` failure; it now exits successfully without staying alive
or opening `/dev/subsys_modem`.

## Safety

- `daemon_start_executed=False` during helper deploy.
- `wifi_bringup_executed=False` during helper deploy.
- `wifi_hal_start_executed=False` during live replay.
- `scan_connect_executed=False`.
- `credential_use_executed=False`.
- `dhcp_route_executed=False`.
- `external_ping_executed=False`.
- `partition_write_executed=False`.
- `flash_executed=False`.
- `reboot_executed=False`.
- Postflight forbidden actors: none.
- Postflight Wi-Fi links: none.
- Temporary vendor, tracefs, and SELinuxfs mounts were cleaned up.
- Final selftest: `pass=11 warn=1 fail=0`.

## Next Gate

The next cycle should trace or classify `pm-service` immediately after
successful `get_system_info()` return. The target is the clean exit path:
determine why `pm-service` returns `0` instead of registering/holding the PM
service and whether it requires a voter/client, `pm-proxy` handshake, or a
different Android init property/service state.
