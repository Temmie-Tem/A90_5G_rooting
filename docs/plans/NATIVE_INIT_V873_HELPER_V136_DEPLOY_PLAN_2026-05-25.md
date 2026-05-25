# V873 Helper v136 Deploy-only Plan

## Goal

Deploy helper `v136` to `/cache/bin/a90_android_execns_probe` and prove remote
checksum/version/mode parity without starting Android actors or bringing up
Wi-Fi.

## Inputs

- V872 report: `docs/reports/NATIVE_INIT_V872_ESOC_PREFLIGHT_HELPER_V136_BUILD_2026-05-25.md`
- Local helper: `tmp/wifi/v872-execns-helper-v136-build/a90_android_execns_probe`
- Deploy wrapper: `scripts/revalidation/wifi_execns_helper_v136_deploy_preflight.py`
- Remote target: `/cache/bin/a90_android_execns_probe`

## Method

1. Run plan and deploy preflight.
2. Verify native version, status, selftest, helper usage, process surface, and
   network surface.
3. Install only the helper binary with the V873 deploy phrase.
4. Verify remote SHA-256, helper marker, and eSoC preflight mode token.

## Success Criteria

- Deploy manifest decision is `execns-helper-v136-deploy-pass`.
- Remote SHA-256 equals
  `76dce733b8444073fc615a44df240aa7f8256dfb7f6c123c3f5e388907356980`.
- Remote helper usage includes `a90_android_execns_probe v136` and
  `wifi-companion-esoc-control-preflight`.
- No Android actor start and no Wi-Fi bring-up occur.

## Hard Gates

- No `mdm_helper`, no `ks`, no `pm_proxy_helper`, no CNSS, no service-manager
  trio, no Wi-Fi HAL.
- No scan/connect, credentials, DHCP/routes, or external ping.
- No live eSoC control preflight or mutating eSoC ioctl in V873.

## Next

V874 should run bounded live eSoC control preflight using helper `v136`.
