# V892 Helper v142 Allowlist Repair and Deploy Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| build | `tmp/wifi/v892-execns-helper-v142-build/manifest.json` | `v892-helper-v142-build-pass` |
| deploy | `tmp/wifi/v892-execns-helper-v142-deploy-preflight/manifest.json` | `execns-helper-v142-deploy-pass` |

V892 repaired the helper allowlist bug that blocked the first V891 attempt.
Helper `v142` is now deployed to `/cache/bin/a90_android_execns_probe`.

## Repair

- helper marker: `a90_android_execns_probe v142`
- source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- change: add `wifi-companion-esoc-conditional-response-preflight` to the
  global v235 mode allowlist
- artifact:
  `tmp/wifi/v892-execns-helper-v142-build/a90_android_execns_probe`
- sha256:
  `b11c346581292422328a64ec78d58dc0f8d7b7cbf958fbb3fcb54df81029de26`
- build: static ARM64, no dynamic section

## Deploy Verification

- remote path: `/cache/bin/a90_android_execns_probe`
- transfer method: `serial`
- remote helper marker: `a90_android_execns_probe v142`
- remote mode token:
  `wifi-companion-esoc-conditional-response-preflight`
- post-deploy read-only checks passed:
  `version`, `status`, `selftest`, `netservice-status`, `stat-helper`,
  `sha-helper`, `ps`, and `proc-net-dev`

## Guardrails

- no live eSoC ioctl
- no `/dev/subsys_esoc0` open
- no Android actor start
- no service-manager start
- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping
- no boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs
  write, module load/unload, or reboot

## Next

Rerun V891 bounded conditional response proof with helper `v142`.
