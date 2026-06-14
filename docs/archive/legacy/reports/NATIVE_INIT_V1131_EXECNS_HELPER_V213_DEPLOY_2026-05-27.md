# Native Init V1131 Execns Helper v213 Deploy Report

Date: `2026-05-27`

## Result

- Decision: `execns-helper-v213-deploy-pass`
- Pass: `true`
- Evidence: `tmp/wifi/v1131-execns-helper-v213-deploy/manifest.json`
- Summary: `tmp/wifi/v1131-execns-helper-v213-deploy/summary.md`
- Deployed helper marker: `a90_android_execns_probe v213`
- Expected helper sha256:
  `d1c354b2b089ede50cc53d452666d119e9151b1e97b7bb1344dbd0431bd69356`
- Deploy wrapper:
  `scripts/revalidation/wifi_execns_helper_v213_deploy_preflight.py`

## Summary

V1131 deployed the V1130 helper artifact to the device, or confirmed it was
already current, without starting any daemon or Wi-Fi bring-up path.

The deploy wrapper pins the V213 helper contract:

```text
DEFAULT_LOCAL_HELPER=tmp/wifi/v1130-execns-helper-v213-build/a90_android_execns_probe
DEFAULT_HELPER_SHA256=d1c354b2b089ede50cc53d452666d119e9151b1e97b7bb1344dbd0431bd69356
HELPER_MARKER=a90_android_execns_probe v213
SERVICE_MODE_TOKEN=wifi-companion-pm-service-trigger-observer
```

Deploy result:

```text
method=ncm
rc=0
ok=True
```

The V373 post-deploy preflight advanced past helper contract checks and stopped
at the expected daemon-start approval boundary:

```text
decision=service-manager-start-only-smoke-approval-required
pass=True
```

## Safety

V1131 did not perform:

```text
daemon_start_executed=false
wifi_bringup_executed=false
service-manager start=false
cnss-daemon start=false
wifi_hal_start=false
scan_connect=false
dhcp_route=false
external_ping=false
partition_write=false
boot_image_write=false
flash=false
```

The only device mutation was the approved `/cache/bin/a90_android_execns_probe`
helper deployment.

## Interpretation

The V1130 source/build-only modem pre-holder support is now available on the
device. The V1071 exit-255/BPF direction remains obsolete for the current
branch; V1087 already closed that route, and V1128/V1129 moved the active
blocker to `/dev/subsys_modem` lower state after provider-positive CNSS PM
connect.

The next live unit should therefore use helper `v213` to enable:

```text
--allow-pm-observer-modem-pre-holder
--pm-observer-modem-pre-holder
```

inside the post-policy provider-positive global firmware PM observer window.

## Next

Run a bounded V1131 live gate with:

1. current-boot V401 selinuxfs mount;
2. current-boot V490 policy load;
3. global firmware mounts;
4. PM observer order with modem pre-holder enabled;
5. CNSS PM register/connect replay;
6. lower `mss`/`mdm3`/WLFW/`wlan0` classification;
7. cleanup reboot if any holder or PM actor remains active.

Continue forbidding Wi-Fi HAL, scan/connect, credentials, DHCP/route, external
ping, `/dev/subsys_esoc0`, partition writes, boot image writes, and flash.
