# V1127 Private Firmware Policy Refresh Classifier Report

Date: `2026-05-27`

## Result

- Decision: `v1127-policy-load-repairs-private-firmware-addservice`
- Pass: `true`
- Classifier evidence: `tmp/wifi/v1127-private-firmware-policy-refresh-classifier/manifest.json`
- Classifier summary: `tmp/wifi/v1127-private-firmware-policy-refresh-classifier/summary.md`
- Classifier: `scripts/revalidation/native_wifi_private_firmware_policy_refresh_classifier_v1127.py`

## Evidence Inputs

- V1126 baseline: `tmp/wifi/v1126-private-firmware-addservice-status-trace/manifest.json`
- V401 selinuxfs mount: `tmp/wifi/v1127-v401-selinuxfs-mount/manifest.json`
- V490 policy load: `tmp/wifi/v1127-v490-policy-load-v212-r2/manifest.json`
- V1127 post-policy replay: `tmp/wifi/v1127-post-policy-private-firmware-addservice-status-trace/manifest.json`
- Post-reboot process check: `tmp/wifi/v1127-current-post-reboot-ps.txt`

## Summary

V1127 compared the V1126 private-firmware provider failure against a same-boot
post-V490 replay.

Baseline V1126:

```json
{
  "addService": "PERMISSION_DENIED",
  "signed32": -1,
  "pm_add_service_fail_log": 1,
  "vndservice_provider_seen": 0
}
```

V490 current-boot policy load:

```json
{
  "decision": "v490-selinux-policy-load-proof-pass",
  "result": "policy-load-pass",
  "policy_load_executed": true
}
```

Post-policy private-firmware replay:

```json
{
  "addService": "OK",
  "signed32": 0,
  "pm_add_service_fail_log": 0,
  "vndservice_provider_seen": 1
}
```

The post-policy replay still preserved the runtime contract:

```text
private_firmware_mounts_requested=1
private_firmware_mnt_mounted=1
private_firmware_modem_mounted=1
vndservicemanager_readiness.ready=1
cnss_daemon_start_executed=0
wifi_hal_start_executed=0
scan_connect_linkup=0
external_ping=0
subsys_esoc0_open_attempted=0
```

## Interpretation

The private-firmware provider regression is repaired by loading the Android
SELinux policy into the current native boot.

Resolved branch:

```text
private firmware mounts active
  -> vndservicemanager ready
  -> pm-service reaches get_system_info success
  -> addService("vendor.qcom.PeripheralManager", ...) before V490 returns -1
  -> V490 loads compiled Android split policy
  -> addService("vendor.qcom.PeripheralManager", ...) after V490 returns 0
  -> provider becomes visible
```

This closes the V1126 `PERMISSION_DENIED` blocker. The next useful gate is not
another addService trace; it is a post-policy replay of the private-firmware
CNSS PM path.

## Safety

- Classifier device commands: `false`
- Classifier tracefs writes: `false`
- Classifier policy load: `false`
- Classifier PM actor start: `false`
- Classifier CNSS daemon start: `false`
- Classifier Wi-Fi HAL start: `false`
- Classifier scan/connect: `false`
- Classifier external ping: `false`
- Classifier reboot: `false`

The post-policy live replay itself ended with `observer-reboot-required` because
`pm_proxy_helper` remained in D-state after the observation window. Cleanup
reboot was performed before classification. Current post-reboot checks show:

```text
version: A90 Linux init 0.9.68 (v724)
selftest: pass=11 warn=1 fail=0
netservice: ncm0=absent tcpctl=stopped
residual PM/service-manager/CNSS actors: none matched
```

## Next

V1128 should integrate V490 as an explicit precondition and replay the
private-firmware CNSS PM path. Expected outcomes:

1. CNSS reaches PM register/connect after provider repair; or
2. the blocker advances back to lower `mdm3`/eSoC state, which should be
   handled separately from service-manager policy.
