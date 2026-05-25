# V922 Helper v152 Deploy

- generated: `2026-05-25T21:27:49+00:00`
- decision: `execns-helper-v152-deploy-pass`
- pass: `True`
- reason: helper `v152` was deployed to `/cache/bin/a90_android_execns_probe` and the final parity run proved the remote helper is current.
- next_step: run bounded V923 CNSS-before-eSoC precondition gate.

## Scope

V922 is deploy-only. The only intended device mutation is replacement of:

```text
/cache/bin/a90_android_execns_probe
```

V922 does not start service-manager, Wi-Fi HAL, CNSS actors, `mdm_helper`,
scan/connect, use credentials, request DHCP, mutate routes, ping externally,
write boot/partition/firmware state, fake `ESOC_NOTIFY`, fake
`ESOC_BOOT_DONE`, or write GPIO/sysfs/debugfs controls.

## Result

| field | value |
| --- | --- |
| local helper | `tmp/wifi/v921-execns-helper-v152-build/a90_android_execns_probe` |
| remote helper | `/cache/bin/a90_android_execns_probe` |
| expected sha256 | `cdaa1adde9774e90e1d1e9f5f4eca43be4643b7ff0be2c8a0a08da5bf3e52105` |
| remote sha256 | `cdaa1adde9774e90e1d1e9f5f4eca43be4643b7ff0be2c8a0a08da5bf3e52105` |
| helper marker | `a90_android_execns_probe v152` |
| mode token | `wifi-companion-mdm-helper-cnss-before-subsys-trigger-capture` |
| deploy method | serial `appendfile` + `uudecode` |
| serial chunk size | `1800` |
| serial chunks written | `860` |
| max encoded command line | `3790` bytes |
| safe command line limit | `3968` bytes |

The helper usage command exits with rc `2` when called without required
arguments. That is expected for usage output; the marker and mode token are the
parity evidence.

## Post-Deploy Health

| check | result |
| --- | --- |
| bootstatus | pass |
| selftest | pass |
| remote helper sha | pass |
| remote helper marker/mode | pass |
| service-manager process clean | pass |
| Wi-Fi link surface clean | pass |
| daemon start executed | false |
| Wi-Fi bring-up executed | false |

NCM was absent during this unit, so the deploy intentionally used the serial
path. A first serial line-limit guard attempt rejected chunk size `3000` before
any write. The wrapper now defaults to chunk size `1800`.

## Evidence

- `tmp/wifi/v922-execns-helper-v152-deploy-preflight/manifest.json`
- `tmp/wifi/v922-execns-helper-v152-deploy-preflight/summary.md`
- `tmp/wifi/v922-execns-helper-v152-deploy-preflight/host/serial-install-helper.txt`
- `tmp/wifi/v922-execns-helper-v152-deploy-preflight/native/sha-helper.txt`
- `tmp/wifi/v922-execns-helper-v152-deploy-preflight/native/helper-usage.txt`
- `tmp/wifi/v922-execns-helper-v152-deploy-preflight/native/status.txt`
- `tmp/wifi/v922-execns-helper-v152-deploy-preflight/native/selftest.txt`

## Decision

V922 passes. The deployed helper is now suitable for V923:

```text
wifi-companion-mdm-helper-cnss-before-subsys-trigger-capture
```

V923 must remain bounded: start the minimal `mdm_helper` + CNSS precondition
gate, only open `/dev/subsys_esoc0` if `cnss_before_esoc.wlfw_precondition_observed=1`,
capture cleanup evidence, and still avoid service-manager, Wi-Fi HAL,
scan/connect, credentials, DHCP/routes, external ping, fake notify/boot-done,
and boot/partition/firmware mutation.
