# V946 Helper v157 Deploy Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| deploy-only wrapper | `scripts/revalidation/native_wifi_helper_v157_deploy_v946.py` | `py_compile pass` |
| bounded deploy | `tmp/wifi/v946-execns-helper-v157-deploy/manifest.json` | `execns-helper-v157-deploy-pass` |

Helper `v157` was deployed to `/cache/bin/a90_android_execns_probe`. No daemon
or Wi-Fi bring-up action was executed.

## Deployment

- Local artifact:
  `tmp/wifi/v945-execns-helper-v157-build/a90_android_execns_probe`
- Expected sha256:
  `308b0f37bfe1265874afdc141f07c8d0b638e6d80c5093af03641f54e96371c2`
- Remote helper marker: `a90_android_execns_probe v157`
- Transfer method: serial appendfile plus `uudecode`
- Safe serial chunk size: `1850`

## Guardrails

- No daemon start.
- No service-manager, CNSS, or Wi-Fi HAL start.
- No scan/connect/link-up.
- No credential use.
- No DHCP/route mutation or external ping.
- No boot image or partition write.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_helper_v157_deploy_v946.py
python3 scripts/revalidation/native_wifi_helper_v157_deploy_v946.py plan
python3 scripts/revalidation/native_wifi_helper_v157_deploy_v946.py preflight
python3 scripts/revalidation/native_wifi_helper_v157_deploy_v946.py \
  --approval-phrase "approve v946 deploy execns helper v157 only; no daemon start and no Wi-Fi bring-up" \
  --apply \
  --assume-yes \
  --serial-chunk-size 1850 \
  run
```

Final result:

- decision: `execns-helper-v157-deploy-pass`
- pass: `true`
- reason: `helper v157 deployed or already current; no daemon or Wi-Fi bring-up executed`
- device mutation: helper file replacement only
- daemon start: `false`
- Wi-Fi bring-up: `false`

## Next

Run bounded provider-readiness capture with helper `v157`.
