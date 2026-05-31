# V1231 Execns Helper v256 Deploy

- date: 2026-05-31
- scope: deploy-only
- helper: `a90_android_execns_probe v256`
- helper binary: `stage3/linux_init/helpers/a90_android_execns_probe_v256`
- deploy wrapper: `scripts/revalidation/wifi_execns_helper_v256_deploy_preflight_v1231.py`
- evidence: `tmp/wifi/v1231-execns-helper-v256-deploy/manifest.json`
- result: `execns-helper-v256-deploy-pass`
- pass: `true`
- sha256: `56ab12b7c7951f2fd5ff9132d6d9662b77560fc2cd55da712115b99b2ec029e9`

## Purpose

V1230 added source/build-only support for the post-`ESOC_WAIT_FOR_REQ`
`ks`/MHI observer. V1231 deployed that exact static helper to
`/cache/bin/a90_android_execns_probe` for the next bounded live gate.

## Result

| field | value |
|---|---|
| transfer method | `ncm` |
| deploy rc | `0` |
| local helper check | pass |
| native version | `A90 Linux init 0.9.68 (v724)` |
| native selftest | `fail=0` |
| service-manager processes | clean |
| Wi-Fi link surface | clean |
| post-deploy preflight | pass / approval-required |

The helper was deployed without starting Android daemons and without Wi-Fi
bring-up.

## Safety Audit

- daemon start: `false`
- Wi-Fi HAL start: `false`
- scan/connect/link-up: `false`
- credential use: `false`
- DHCP/route: `false`
- external ping: `false`
- boot image write / flash / partition write: `false`

## Next

V1232 should run the bounded post-`ESOC_WAIT_FOR_REQ` observer using helper
`v256`.
