# V1270 Execns Helper v265 Deploy

## Result

- decision: `execns-helper-v265-deploy-pass`
- evidence: `tmp/wifi/v1270-execns-helper-v265-deploy/manifest.json`
- helper: `a90_android_execns_probe v265`
- helper SHA256: `97ffa91a1aa7b8f4ab2c3a74716ae5664c703e98fe19a322351b1277fbd282b2`
- transfer: serial fallback, `1010` chunks, safe line check passed
- post-deploy direct SHA verification: passed
- post-deploy selftest: `fail=0`

## Scope

V1270 deployed only `/cache/bin/a90_android_execns_probe`.  It did not start
service-manager, CNSS, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or
external ping.  It did not write boot images or partitions.

## Next

V1271 should run the bounded value/power observer with helper v265.  The live
observer should use the same late `per_proxy` / PM-service `/dev/subsys_esoc0`
response window and parse the new `pmic_gpio1270_debugfs_*`,
`tlmm_gpio135_debugfs_*`, `tlmm_gpio142_debugfs_*`, `pmic9_pinconf_*`,
`pin135_pinconf_*`, and `pin142_pinconf_*` fields.
