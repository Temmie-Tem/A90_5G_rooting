# V890 Helper v141 Deploy-only Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper v141 deploy | `tmp/wifi/v890-execns-helper-v141-deploy-preflight/manifest.json` | `execns-helper-v141-deploy-pass` |

V890 deployed helper `v141` to `/cache/bin/a90_android_execns_probe`.

## Remote Verification

- remote path: `/cache/bin/a90_android_execns_probe`
- sha256:
  `e6909cbfee79a4a1f55a3f039cdc29dca57f31e00c19d63a1a452d633c060f21`
- helper marker: `a90_android_execns_probe v141`
- mode token:
  `wifi-companion-esoc-conditional-response-preflight`
- transfer method: `serial`
- serial chunks: `788`
- max line bytes: `3890`
- safe line limit: `3968`

Post-deploy `version`, `status`, `selftest`, `netservice-status`,
`stat-helper`, `sha-helper`, `ps`, and `proc-net-dev` were read-only and
passed. No-argument helper usage returned rc `2`, which is expected for usage
output; the output included the v141 marker.

## Guardrails

- no live eSoC ioctl
- no `/dev/subsys_esoc0` open
- no `ESOC_NOTIFY`
- no Android actor start
- no service-manager start
- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping
- no boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs
  write, module load/unload, or reboot

## Next

V891 can be a separate bounded conditional response proof. It should run only
the helper `v141` conditional response mode, capture all response markers, and
define reboot cleanup if the subsystem holder remains unkillable.
