# Native Init V929 CNSS Service-Manager Matrix Support

## Scope

V929 is source/build-only. It adds helper `v154` support for testing CNSS Binder
and lower-publication behavior under the same repaired runtime namespace without
deploying the helper or starting any live daemon.

## Evidence

- Verifier: `scripts/revalidation/native_wifi_cnss_service_manager_matrix_support_v929.py`
- Manifest: `tmp/wifi/v929-cnss-service-manager-matrix-support/manifest.json`
- Summary: `tmp/wifi/v929-cnss-service-manager-matrix-support/summary.md`
- Build artifact: `tmp/wifi/v929-execns-helper-v154-build/a90_android_execns_probe`
- Build log: `tmp/wifi/v929-execns-helper-v154-build/build.log`
- Artifact sha256: `f87fb6032a4333f4b3dfabc9766b8620bf6e3f2acc9c1081b09738933cc7c9ab`

## Result

- Decision: `v929-cnss-service-manager-matrix-support-pass`
- Helper marker: `a90_android_execns_probe v154`
- New mode: `wifi-companion-mdm-helper-cnss-service-manager-matrix`
- New allow flag: `--allow-mdm-helper-cnss-service-manager-matrix`
- Order enum: `--service-manager-order none|before-cnss|after-cnss|after-mdm-helper-esoc-fd`
- Build: ARM64 static helper build passed.

## Implementation

- Reuses the V927 repaired runtime namespace defaults: real linkerconfig copy,
  `v30-to-system-ext-v30` VNDK APEX alias, Android service defaults context,
  private property root support, and compact CNSS surface.
- Adds a service-manager trio start helper for `servicemanager`,
  `hwservicemanager`, and `vndservicemanager /dev/vndbinder`.
- Keeps the old CNSS-before-eSoC path intact and adds matrix-only branching for
  service-manager start timing.
- Reports compact final contract keys for selected order, service-manager
  start state, CNSS actor state, postflight safety, WLFW precondition, and
  forbidden Wi-Fi bring-up surfaces.

## Guardrails

- No helper deploy was performed.
- No device command was executed.
- No daemon/service-manager live start was performed in V929.
- No Wi-Fi HAL, scan/connect/link-up, credential use, DHCP, route change, or
  external ping was performed.
- No eSoC ioctl, subsystem open, GPIO/sysfs/debugfs write, boot image write, or
  partition write was performed.

## Next

V930 should deploy helper `v154` only, then the first live matrix run should
test one order variant at a time below Wi-Fi HAL and below scan/connect.
