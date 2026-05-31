# Native Init V1308 Execns Helper v274 Deploy

## Summary

- Cycle: `V1308`
- Type: deploy-only helper update
- Decision: `execns-helper-v274-deploy-pass`
- Result: PASS
- Evidence:
  - `tmp/wifi/v1308-execns-helper-v274-deploy/manifest.json`
  - `tmp/wifi/v1308-execns-helper-v274-deploy/summary.md`
  - `tmp/wifi/v1308-execns-helper-v274-deploy/native/sha-helper.txt`
  - `tmp/wifi/v1308-execns-helper-v274-deploy/host/serial-install-helper.txt`
- Script: `scripts/revalidation/wifi_execns_helper_v274_deploy_preflight_v1308.py`
- Helper: `a90_android_execns_probe v274`
- Remote path: `/cache/bin/a90_android_execns_probe`
- SHA256: `eb96072631ca38c3296f5da1756a93765e198e8fdd4dc010d087bc4b3b5fc180`

V1308 deployed the V1307-built helper `v274` to the native device cache path. The deploy used the serial fallback path because NCM was not active during preflight.

## Checks

| check | result |
| --- | --- |
| native version | `A90 Linux init 0.9.68 (v724)` |
| native health | `status/selftest rc=0`, `fail=0` |
| local helper marker | `a90_android_execns_probe v274` |
| remote helper sha | `eb96072631ca38c3296f5da1756a93765e198e8fdd4dc010d087bc4b3b5fc180` |
| service-manager processes | clean |
| Wi-Fi link surface | clean |
| V373 post-deploy preflight | pass; approval still required for daemon-start smoke |

`helper-usage` exits with rc `2`, which is expected for usage output. The output still confirms the `v274` marker and the `--pm-observer-late-per-proxy-pmic-gdsc-transition-sampler` option.

## Validation

```bash
python3 scripts/revalidation/wifi_execns_helper_v274_deploy_preflight_v1308.py \
  --transfer-method auto \
  --serial-chunk-size 1800 \
  --apply \
  --assume-yes \
  --approval-phrase 'approve v1308 deploy execns helper v274 only; no daemon start and no Wi-Fi bring-up' \
  run
```

The deploy completed with `rc=0` and `device_mutations=True` limited to the approved `/cache/bin/a90_android_execns_probe` helper update.

## Next

V1309 should run the bounded no-write PMIC/GDSC transition sampler live using helper `v274`. It should parse `pmic_gdsc_focus=1` samples and decide whether PM8150L soft-reset and PCIe GDSC state remain unconfigured during the focused `mdm_subsys_powerup` window.

## Safety

- No daemon-start smoke was executed in V1308.
- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, flash, boot image write, or partition write occurred.
- No PMIC write, userspace GPIO request/hold, or direct eSoC ioctl occurred.
