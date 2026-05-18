# Native Init v253 Private Data Wi-Fi Materialization Plan

## Summary

- target: v253 private `/data/vendor/wifi` materialization probe
- baseline: v252 `cnss-data-wifi-surface-missing`
- helper update: `a90_android_execns_probe v9`
- new host tool: `scripts/revalidation/wifi_cnss_private_data_wifi_probe.py`
- boot image change: none
- daemon start: not executed

v252 proved native root lacks `/data/vendor/wifi`. v253 adds a helper-only
`--data-wifi-mode private-empty` option that creates `/data/vendor/wifi/sockets`
inside the temporary private namespace only, then verifies the guarded no-allow
`cnss-start-only` path still blocks execution.

## Scope

- create private temp-root directories only:
  - `/data`
  - `/data/vendor`
  - `/data/vendor/wifi`
  - `/data/vendor/wifi/sockets`
- assign private directory ownership suitable for a system/wifi process where
  possible
- print context evidence for these paths
- preserve no-allow `cnss_start.result=start-only-blocked`

## Non-Goals

- do not create real `/data/vendor/wifi`
- do not mount/remount userdata
- do not start `cnss-daemon`
- do not scan/connect/link-up Wi-Fi
- do not write Android partitions

## Validation

```bash
scripts/revalidation/build_android_execns_probe_helper.sh
python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_android_execns_probe \
  --toybox /cache/bin/toybox \
  install --local-binary stage3/linux_init/helpers/a90_android_execns_probe
python3 -m py_compile scripts/revalidation/wifi_cnss_private_data_wifi_probe.py
git diff --check
python3 scripts/revalidation/wifi_cnss_private_data_wifi_probe.py \
  --out-dir tmp/wifi/v253-private-data-wifi-probe
```
