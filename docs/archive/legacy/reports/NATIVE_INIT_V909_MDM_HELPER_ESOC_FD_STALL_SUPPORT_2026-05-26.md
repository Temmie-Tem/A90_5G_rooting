# Native Init V909 mdm_helper eSoC FD Stall Support Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| source/build verifier | `tmp/wifi/v909-mdm-helper-esoc-fd-stall-support/manifest.json` | `v909-mdm-helper-esoc-fd-stall-support-pass` |

V909 adds helper `v149` source/build support for the next live classifier. The
new support is passive: it records fdinfo and proc stall snapshots for
`mdm_helper` around the `/dev/esoc-0` boundary observed in V908.

## Implemented

- Bumped helper marker to `a90_android_execns_probe v149`.
- Added fdinfo capture to matching fd scans.
- Added `mdm_helper_runtime_window` generic stall snapshot.
- Added `mdm_helper_runtime_final` generic stall snapshot.
- Preserved the existing runtime-contract mode and guardrails.

## Build

- artifact: `tmp/wifi/v909-execns-helper-v149-build/a90_android_execns_probe`
- sha256: `b615aa127e130e8b285642b34992102fa6d0c15702479bc1265dd4c5f06dff49`
- static check: `statically linked`, `There is no dynamic section`

## Guardrails

- No device contact, helper deployment, actor start, eSoC ioctl, subsystem open,
  daemon start, Wi-Fi HAL, scan/connect, credential use, DHCP/routes, external
  ping, reboot, boot image write, partition write, firmware mutation,
  GPIO/sysfs/debugfs write, or Wi-Fi bring-up occurred in V909.

## Validation

Executed:

```bash
scripts/revalidation/build_android_execns_probe_helper.sh tmp/wifi/v909-execns-helper-v149-build/a90_android_execns_probe
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_esoc_fd_stall_support_v909.py
python3 scripts/revalidation/native_wifi_mdm_helper_esoc_fd_stall_support_v909.py
```

## Next

Deploy helper `v149` and rerun the bounded runtime-contract capture to classify
the `/dev/esoc-0` fd stall without starting Wi-Fi bring-up.
