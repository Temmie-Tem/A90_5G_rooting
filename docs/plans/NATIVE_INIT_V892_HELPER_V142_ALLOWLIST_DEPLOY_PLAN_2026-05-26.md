# V892 Helper v142 Allowlist Repair and Deploy Plan

## Goal

Repair the helper `v141` allowlist bug found by the first V891 attempt, build
helper `v142`, and deploy it to `/cache/bin/a90_android_execns_probe`.

## Finding

The first V891 live attempt stopped before any live eSoC operation:

- evidence: `tmp/wifi/v891-esoc-conditional-response-live/manifest.json`
- decision: `v891-step-failed`
- helper rc: `2`
- message: `arguments do not match v235 allowlist`

The conditional mode existed and had a dedicated allow flag, but it was missing
from the global v235 mode allowlist.

## Method

1. Bump helper marker to `a90_android_execns_probe v142`.
2. Add `wifi-companion-esoc-conditional-response-preflight` to the global
   v235 allowlist.
3. Build a static ARM64 helper.
4. Deploy helper `v142` only.
5. Verify remote sha, marker, mode token, selftest, actor-clean, and
   Wi-Fi-link-clean state.

## Hard Gates

- Deploy-only mutation: `/cache/bin/a90_android_execns_probe` replacement only.
- No live eSoC ioctl.
- No `/dev/subsys_esoc0` open.
- No Android actor start, service-manager, Wi-Fi HAL, scan/connect,
  credentials, DHCP/routes, external ping, boot image write, partition write,
  firmware mutation, GPIO/sysfs/debugfs write, module load/unload, or reboot.

## Success Criteria

- Build decision is `v892-helper-v142-build-pass`.
- Deploy decision is `execns-helper-v142-deploy-pass`.
- Remote sha256 matches the v142 artifact.
- Remote helper advertises `a90_android_execns_probe v142`.
- Remote helper advertises
  `wifi-companion-esoc-conditional-response-preflight`.

## Next

After V892 passes, rerun the V891 bounded conditional response proof with
helper `v142`.
