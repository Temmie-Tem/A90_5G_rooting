# Native Init v406 Helper v24 Deploy Live Result

## Summary

The exact-approved V406 helper v24 deploy completed successfully.

Only `/cache/bin/a90_android_execns_probe` was deployed and verified. No `servicemanager`, `hwservicemanager`, Wi-Fi HAL, `wificond`, supplicant, hostapd, CNSS/diag, scan/connect/link-up, or Wi-Fi bring-up was executed.

The deployed helper now exposes `a90_android_execns_probe v24` and the `v30-to-system-ext-v30` private APEX materialization mode needed for the next V406 linker-list proof.

## Approval Used

```text
approve v406 deploy execns helper v24 only; no daemon start and no Wi-Fi bring-up
```

## Evidence

- approved deploy run: `tmp/wifi/v406-execns-helper-v24-deploy-live-20260520-095625/`
- deploy manifest: `tmp/wifi/v406-execns-helper-v24-deploy-live-20260520-095625/manifest.json`
- serial deploy transcript: `tmp/wifi/v406-execns-helper-v24-deploy-live-20260520-095625/host/serial-install-helper.txt`
- deploy-run V406 preflight: `tmp/wifi/v406-execns-helper-v24-deploy-live-20260520-095625/v406-system-ext-vndk-preflight/`
- independent post-deploy helper check: `tmp/wifi/v406-execns-helper-v24-deploy-postcheck-20260520-100244/`
- independent post-deploy V406 runner preflight: `tmp/wifi/v406-system-ext-vndk-runner-post-deploy-preflight-20260520-100252/`

Deploy result:

```text
decision: execns-helper-v24-deploy-pass
pass: True
reason: helper v24 deployed or already current; V406 system_ext VNDK linker-list preflight is ready
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

The pre-install check correctly showed the device still had helper v23:

```text
remote-helper-v24: needs-deploy
sha_match: False
marker_mode: False
remote_sha: 64c80e73d791b82e0b9f60b05db1df1781bf5033b1ffd76e323cf52ce3dbc520
remote_version: a90_android_execns_probe v23
```

The independent post-deploy helper check proves the remote helper is now v24:

```text
decision: execns-helper-v24-deploy-preflight-ready
pass: True
remote-helper-v24: pass
sha_match: True
marker_mode: True
remote_sha: 7ec11d95085f1c3dc370884725b080b44150bf8b0a5f7d897df048188a815063
remote_version: a90_android_execns_probe v24
```

## V406 Runner Preflight

The post-deploy V406 runner preflight is ready:

```text
decision: system-ext-vndk-linker-list-preflight-ready
pass: True
reason: preflight complete; linker-list proof still requires exact approval
device_commands_executed: True
device_mutations: False
daemon_start_executed: False
wifi_hal_start_executed: False
wifi_bringup_executed: False
```

Confirmed checks:

- V405 runtime gap input is still confirmed.
- native version and health pass.
- helper v24 SHA/mode pass.
- real linkerconfig inputs are visible.
- `system_ext` VNDK v30 and `android.hardware.wifi@1.0.so` source are visible.
- vendor block source is available through `/sys/class/block/sda29/dev`.
- process surface is clean.
- Wi-Fi link surface is clean.

The remaining gate is approval only:

```text
approval-gate: needs-operator
```

## Not Executed

- V406 linker-list proof.
- `servicemanager`, `hwservicemanager`, or Wi-Fi HAL daemon start.
- `wificond`, supplicant, hostapd.
- `cnss-daemon` or `cnss_diag`.
- scan/connect/link-up.
- credentials, DHCP, routing.
- rfkill, ICNSS bind/unbind, module load/unload, firmware mutation.
- Android partition writes.
- persistence or boot/autostart changes.

## Next Target

The next step is the separate V406 system_ext VNDK APEX linker-list proof approval.

Required future approval phrase:

```text
approve v406 system_ext VNDK APEX linker-list proof only; no daemon start and no Wi-Fi bring-up
```

That future step should only run `linker-list` dependency closure proof. Wi-Fi HAL start-only retry and Wi-Fi bring-up remain blocked until this proof is reviewed.

