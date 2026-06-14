# V956 Helper v159 Deploy Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| deploy-only wrapper | `scripts/revalidation/native_wifi_helper_v159_deploy_v956.py` | `py_compile pass` |
| bounded deploy | `tmp/wifi/v956-execns-helper-v159-deploy/manifest.json` | `execns-helper-v159-deploy-pass` |

Helper `v159` was deployed to `/cache/bin/a90_android_execns_probe`. No daemon
or Wi-Fi bring-up action was executed.

## Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_helper_v159_deploy_v956.py \
  scripts/revalidation/native_wifi_pm_proxy_matrix_capture_v957.py
python3 scripts/revalidation/native_wifi_helper_v159_deploy_v956.py plan
python3 scripts/revalidation/native_wifi_helper_v159_deploy_v956.py preflight
python3 scripts/revalidation/native_wifi_pm_proxy_matrix_capture_v957.py plan
python3 scripts/revalidation/native_wifi_helper_v159_deploy_v956.py \
  --approval-phrase "approve v956 deploy execns helper v159 only; no daemon start and no Wi-Fi bring-up" \
  --apply \
  --assume-yes \
  --serial-chunk-size 1850 \
  run
```

Final result:

- decision: `execns-helper-v159-deploy-pass`
- pass: `true`
- reason: `helper v159 deployed or already current; no daemon or Wi-Fi bring-up executed`
- expected sha256:
  `c4eb155c9fa1e105d80a040689dcedc9370b0340b60ac624980ccaf20e9c94d6`
- daemon start: `false`
- Wi-Fi bring-up: `false`

## Next

Run the bounded `after-mdm-helper-esoc-fd-with-pm-proxy` matrix comparator.
