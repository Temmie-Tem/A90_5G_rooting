# Native Init v405 Helper v23 Deploy Live Result

## Summary

The exact-approved V405 helper v23 deploy completed successfully.

Only `/cache/bin/a90_android_execns_probe` was deployed and verified. No service-manager start, Wi-Fi HAL start, scan/connect/link-up, or Wi-Fi bring-up was executed.

## Approval Used

```text
approve v405 deploy execns helper v23 only; no daemon start and no Wi-Fi bring-up
```

## Evidence

- approved deploy run: `tmp/wifi/v405-execns-helper-v23-deploy-live-20260520-092918/`
- deploy manifest: `tmp/wifi/v405-execns-helper-v23-deploy-live-20260520-092918/manifest.json`
- serial deploy transcript: `tmp/wifi/v405-execns-helper-v23-deploy-live-20260520-092918/host/serial-install-helper.txt`
- post-deploy V405 preflight: `tmp/wifi/v405-execns-helper-v23-deploy-live-20260520-092918/v405-composite-hal-preflight/`
- independent post-deploy helper check: `tmp/wifi/v405-execns-helper-v23-deploy-postcheck-20260520-093620/`
- independent post-deploy composite preflight: `tmp/wifi/v405-composite-hal-preflight-post-deploy-20260520-093529/`

Deploy result:

```text
decision: execns-helper-v23-deploy-pass
pass: True
reason: helper v23 deployed or already current; V405 composite HAL preflight is ready
device_mutations: True
daemon_start_executed: False
wifi_bringup_executed: False
```

Transfer details:

```text
method: serial
chunks_written: 783
encoded_bytes: 1094836
rc: 0
ok: True
```

## Helper Verification

The deployed helper matches v23:

```text
remote-helper-v23: pass
sha_match: True
marker_mode: True
sha256: 64c80e73d791b82e0b9f60b05db1df1781bf5033b1ffd76e323cf52ce3dbc520
```

The post-deploy helper check returned:

```text
decision: execns-helper-v23-deploy-preflight-ready
pass: True
device_mutations: False
```

The deploy run's pre-install check correctly showed `remote-helper-v23 needs-deploy` because the device still had helper v22 before the approved install. The independent post-deploy check proves the remote helper is now v23.

## Composite HAL Preflight

The post-deploy composite HAL runner preflight is ready:

```text
decision: composite-hal-start-only-preflight-ready
pass: True
reason: read-only preflight is ready; live run still needs approval
device_mutations: False
daemon_start_executed: False
wifi_hal_start_executed: False
wifi_bringup_executed: False
```

Confirmed preflight blockers are clear:

- V404 readiness pass.
- native version and health pass.
- helper v23 SHA and mode pass.
- runtime material inputs pass.
- `servicemanager` and `hwservicemanager` binaries pass.
- existing manager/HAL process surface is clean.
- Wi-Fi link surface is clean.

The remaining gate is approval only:

```text
approval-gate: needs-operator
```

## Not Executed

- Wi-Fi HAL start.
- `wificond`, supplicant, hostapd.
- `cnss-daemon` or `cnss_diag`.
- scan/connect/link-up.
- credentials, DHCP, routing.
- rfkill, ICNSS bind/unbind, module load/unload, firmware mutation.
- Android partition writes.
- persistence or boot/autostart changes.

## Next Target

The next step is the separate V405 composite Wi-Fi HAL start-only smoke approval.

Required future approval phrase:

```text
approve v405 composite Wi-Fi HAL start-only smoke only; no scan/connect/link-up and no Wi-Fi bring-up
```

That future step should still be bounded start-only only. Wi-Fi bring-up remains blocked until HAL start-only evidence is reviewed.
