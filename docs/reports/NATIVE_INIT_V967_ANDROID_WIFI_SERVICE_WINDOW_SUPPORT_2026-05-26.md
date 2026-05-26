# V967 Android Wi-Fi Service Window Support

- generated: `2026-05-26`
- scope: source/build-only
- decision: `v967-android-wifi-service-window-support-pass`
- helper: `a90_android_execns_probe v161`
- evidence: `tmp/wifi/v967-android-wifi-service-window-support/manifest.json`
- build artifact: `tmp/wifi/v967-execns-helper-v161-build/a90_android_execns_probe`
- build sha256: `1d936d9117e68b97c1449d9ed357560ec7ae1901eeb179da474f1dacbc837643`

## Summary

V967 adds a guarded helper mode for the Android Wi-Fi service-window parity candidate selected by V966:

```text
wifi-companion-android-wifi-service-window-start-only
```

The mode starts only the Android-like service window below active Wi-Fi bring-up:

```text
servicemanager
hwservicemanager
vndservicemanager
qrtr_ns
rmt_storage
tftp_server
pd_mapper
wifi_hal_legacy
wifi_hal_ext
per_mgr
cnss_diag
wificond
mdm_helper
cnss_daemon
```

The gate is intentionally source/build-only in V967. No deploy, live execution, scan, connect, DHCP, credential use, route change, or external ping was performed.

## Guardrails

- `--allow-android-wifi-service-window` is accepted only with `wifi-companion-android-wifi-service-window-start-only`.
- The mode rejects unrelated actor/HAL/scan/connect/eSoC proof flags.
- Missing allow flag returns `start-only-blocked` with no child execution.
- The helper records `qcwlanstate_write=0`, `iwifi_start=0`, `subsys_esoc0_open_attempted=0`, `esoc_ioctl_attempted=0`, `scan_connect_linkup=0`, `credentials=0`, `dhcp_routing=0`, and `external_ping=0`.
- Runtime materialization defaults to private `/data/misc/wifi`, `/dev/null`, real linkerconfig copy, VNDK APEX alias, and Android service SELinux defaults.

## Validation

| Check | Result |
| --- | --- |
| helper source version `v161` | PASS |
| new mode and allow flag exposed | PASS |
| mode-specific validation and allowlist | PASS |
| Android service-window child order | PASS |
| no-qcwlanstate/no-eSoC/no-scan/no-connect guard markers | PASS |
| static ARM64 helper build | PASS |
| artifact strings confirm mode, version, and result taxonomy | PASS |

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_android_service_window_support_v967.py
python3 scripts/revalidation/native_wifi_android_service_window_support_v967.py
```

Result:

```text
decision: v967-android-wifi-service-window-support-pass
pass: True
```

## Next

- V968 should deploy helper `v161` only, or run a separate Android dmesg GPIO/eSoC timing classifier first.
- The latest Android dmesg direction should be kept separate from V967 because it is read-only Android evidence collection, while V967 is native helper source/build support.
