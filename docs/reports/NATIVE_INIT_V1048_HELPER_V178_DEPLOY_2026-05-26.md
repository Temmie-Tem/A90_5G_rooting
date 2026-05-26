# V1048 Helper v178 Deploy Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| deploy-only wrapper | `tmp/wifi/v1048-execns-helper-v178-deploy/manifest.json` | `execns-helper-v178-deploy-pass` |

V1048 deployed or confirmed `a90_android_execns_probe v178` at
`/cache/bin/a90_android_execns_probe`. No daemon start or Wi-Fi bring-up was
executed.

## Evidence

- Wrapper: `scripts/revalidation/native_wifi_helper_v178_deploy_v1048.py`
- Summary: `tmp/wifi/v1048-execns-helper-v178-deploy/summary.md`
- Serial install transcript:
  `tmp/wifi/v1048-execns-helper-v178-deploy/host/serial-install-helper.txt`
- Latest pointer: `tmp/wifi/latest-v1048-execns-helper-v178-deploy.txt`

## Findings

- Local helper artifact:
  - marker: `a90_android_execns_probe v178`
  - sha256: `7df75c618f58d599ece1a6017f66040aff57badb8955a70e07de2a77a3561c75`
  - local strings include the new modem-holder order and allow flag.
- Initial approved deploy wrote the helper by serial appendfile:
  - chunks: `996`
  - chunks written: `996`
  - remote sha256 matched after install.
- First postflight was blocked only because the generic deploy checker expected
  the new v178 flag/order token in no-argument usage output.
- The V1048 wrapper was tightened to use remote sha256 equality as authoritative
  for v178-specific parser contract; this is valid because the local artifact
  strings were verified and the remote sha matches exactly.
- Final postflight:
  - remote sha256 match: `true`
  - native health: pass
  - service-manager processes: clean
  - Wi-Fi link surface: clean

## Guardrails

No service-manager, CNSS daemon, Wi-Fi HAL, `wificond`, scan/connect,
credentials, DHCP/routes, external ping, eSoC ioctl, subsystem open, GPIO write,
sysfs write, debugfs write, boot image write, partition write, or firmware
mutation occurred in V1048.

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_helper_v178_deploy_v1048.py
python3 scripts/revalidation/native_wifi_helper_v178_deploy_v1048.py preflight
python3 scripts/revalidation/native_wifi_helper_v178_deploy_v1048.py \
  --approval-phrase "approve v1048 deploy execns helper v178 only; no daemon start and no Wi-Fi bring-up" \
  --apply \
  --assume-yes \
  run
```

Result:

```text
decision: execns-helper-v178-deploy-pass
pass: True
remote sha256: 7df75c618f58d599ece1a6017f66040aff57badb8955a70e07de2a77a3561c75
```

## Next

V1049 should run the bounded live gate with the deployed helper v178. Because
V1043 showed stale current-boot SELinux policy can block PM domains, V1049
should first refresh the V401/V490 current-boot policy/domain precondition.
