# V1036 PM SELinux Domain Proof v176 Plan

- date: `2026-05-26`
- type: bounded live domain proof
- input: `docs/reports/NATIVE_INIT_V1035_HELPER_V176_DEPLOY_2026-05-26.md`
- required precondition: current-boot V490 policy load
- helper: `/cache/bin/a90_android_execns_probe`
- helper version: `a90_android_execns_probe v176`
- helper sha256: `dff34476d956574be59628f1177179cb8ef87a04dda0c68e97cc5afcf5310f2d`

## Objective

Rerun the V1033 PM SELinux domain proof using deployed helper `v176`.

V1033 showed that PM contexts were blocked only by the helper's
`selinux-domain-proof` allowlist. V1036 proves whether, after V1034/V1035, the
required PM domains can survive static re-exec under the currently loaded
Android policy.

## Required Contexts

- `u:r:per_proxy_helper:s0`
- `u:r:vendor_per_mgr:s0`
- `u:r:vendor_per_proxy:s0`
- `u:r:vendor_mdm_helper:s0`

Control context:

- `u:r:vendor_wcnss_service:s0`

## Guardrails

- no actor start
- no daemon start
- no Wi-Fi HAL start
- no scan/connect/link-up
- no credentials
- no DHCP, route, or external ping
- no init re-exec
- no boot image write
- no partition write
- no firmware mutation
- no GPIO/sysfs/debugfs write

## Commands

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_selinux_domain_proof_v1036.py
python3 scripts/revalidation/native_wifi_pm_selinux_domain_proof_v1036.py plan
python3 scripts/revalidation/native_wifi_pm_selinux_domain_proof_v1036.py \
  --v490-manifest tmp/wifi/v1033-v490-policy-load/manifest.json \
  --approval-phrase "approve v1036 PM SELinux domain proof v176 only; no daemon start and no Wi-Fi bring-up" \
  --apply \
  --assume-yes \
  run
```

## Success Criteria

- Helper marker and sha256 match helper `v176`.
- V490 policy-load evidence is present and valid for the current boot.
- All required PM contexts survive static post-exec domain proof.
- No actor, daemon, Wi-Fi, network, boot, partition, firmware, GPIO, sysfs, or
  debugfs action occurs.

## Next

If all required PM domains pass, rerun the V1032 runtime-domain guard with
helper `v176` while the current-boot policy load is fresh.
