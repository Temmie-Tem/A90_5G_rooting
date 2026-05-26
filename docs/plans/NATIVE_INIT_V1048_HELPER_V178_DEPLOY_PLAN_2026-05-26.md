# V1048 Helper v178 Deploy Plan

## Goal

Deploy the V1047 `a90_android_execns_probe v178` helper to
`/cache/bin/a90_android_execns_probe` and verify it without starting daemons or
Wi-Fi bring-up.

## Inputs

- V1047 source/build report:
  `docs/reports/NATIVE_INIT_V1047_PM_FULL_CONTRACT_WITH_MODEM_HOLDER_SOURCE_BUILD_2026-05-26.md`
- Local helper artifact:
  `tmp/wifi/v1047-execns-helper-v178-build/a90_android_execns_probe`
- Expected sha256:
  `7df75c618f58d599ece1a6017f66040aff57badb8955a70e07de2a77a3561c75`
- Deploy wrapper:
  `scripts/revalidation/native_wifi_helper_v178_deploy_v1048.py`

## Method

1. Preflight native health, selftest, process surface, Wi-Fi link surface, local
   helper sha/marker, and current remote helper state.
2. Deploy only `/cache/bin/a90_android_execns_probe` via serial appendfile when
   the exact V1048 approval phrase is present.
3. Verify remote sha256, helper marker, native health, actor-clean state, and
   Wi-Fi-link-clean state after deploy.
4. Treat remote sha256 equality as authoritative for v178-specific parser
   contract because V1047 added the parser strings but did not add the new
   flag/order token to the no-argument usage text.

## Hard Gates

- No service-manager, CNSS daemon, Wi-Fi HAL, `wificond`, scan/connect,
  credentials, DHCP/routes, external ping, eSoC ioctl, subsystem open, GPIO
  write, sysfs write, debugfs write, boot image write, partition write, or
  firmware mutation.
- Only `/cache/bin/a90_android_execns_probe` may be replaced.

## Success Criteria

- Remote sha256 equals the V1047 v178 artifact sha256.
- Native `bootstatus` and `selftest` stay clean.
- No service-manager/CNSS/Wi-Fi actor remains running.
- No Wi-Fi link surface appears.
- V1049 can use the deployed helper for a bounded live PM full-contract gate.

## Next

V1049 should run the bounded PM full-contract-with-modem-holder live gate after
current-boot SELinux policy/domain preconditions are refreshed.
