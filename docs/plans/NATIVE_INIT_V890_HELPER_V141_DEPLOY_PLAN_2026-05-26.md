# V890 Helper v141 Deploy-only Plan

## Goal

Deploy helper `v141` to `/cache/bin/a90_android_execns_probe` and prove remote
checksum/version/mode parity. V890 must not execute the conditional response
mode; it only installs the helper needed for a later bounded live proof.

## Inputs

- V889 build report:
  `docs/reports/NATIVE_INIT_V889_ESOC_CONDITIONAL_RESPONSE_HELPER_BUILD_2026-05-26.md`
- local helper artifact:
  `tmp/wifi/v889-execns-helper-v141-build/a90_android_execns_probe`
- deploy wrapper:
  `scripts/revalidation/wifi_execns_helper_v141_deploy_preflight.py`

## Method

1. Run plan mode with no device command.
2. Run read-only preflight against current native v724.
3. If preflight passes, install helper `v141` only.
4. Verify remote sha256, helper marker, conditional response mode token,
   selftest, actor-clean, and Wi-Fi-link-clean state.
5. Do not execute the conditional response mode or any live eSoC operation.

## Hard Gates

- Deploy-only mutation: `/cache/bin/a90_android_execns_probe` replacement only.
- No live eSoC ioctl.
- No `/dev/subsys_esoc0` open.
- No `ESOC_NOTIFY`.
- No Android actor start, service-manager, Wi-Fi HAL, scan/connect,
  credentials, DHCP/routes, external ping, boot image write, partition write,
  firmware mutation, GPIO/sysfs/debugfs write, module load/unload, or reboot.

## Success Criteria

- Decision is `execns-helper-v141-deploy-pass`.
- Remote sha256 matches V889 artifact.
- Remote helper advertises `a90_android_execns_probe v141`.
- Remote helper advertises
  `wifi-companion-esoc-conditional-response-preflight`.
- Native health and Wi-Fi surfaces stay clean.

## Next

If V890 passes, V891 can be a separate bounded conditional response proof with
explicit timeout and reboot cleanup criteria.
