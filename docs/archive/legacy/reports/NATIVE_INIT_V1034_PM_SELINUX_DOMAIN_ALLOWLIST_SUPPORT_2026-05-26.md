# V1034 PM SELinux Domain Allowlist Support

- date: `2026-05-26`
- scope: source/build-only helper update
- decision: `v1034-pm-selinux-domain-allowlist-support-pass`
- pass: `True`
- evidence: `tmp/wifi/v1034-pm-selinux-domain-allowlist-support/manifest.json`
- artifact: `tmp/wifi/v1034-execns-helper-v176-build/a90_android_execns_probe`
- artifact sha256: `dff34476d956574be59628f1177179cb8ef87a04dda0c68e97cc5afcf5310f2d`

## Summary

V1034 bumps `a90_android_execns_probe` to helper `v176` and adds the PM contexts
needed by V1033 to the `selinux-domain-proof` allowlist.

No device command or deploy occurred in V1034.

## Checks

| Check | Result |
| --- | --- |
| helper version `v176` | pass |
| PM contexts in source allowlist | pass |
| `selinux-domain-proof` preserved | pass |
| `--require-android-selinux-exec-match` preserved | pass |
| PM full-contract mode preserved | pass |
| static build | pass |
| artifact strings contain PM contexts | pass |

## Guardrails

- no device command
- no helper deploy
- no actor start
- no daemon start
- no Wi-Fi HAL start
- no scan/connect/link-up
- no credentials
- no DHCP, route, or external ping
- no boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs write

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_selinux_domain_allowlist_support_v1034.py
python3 scripts/revalidation/native_wifi_pm_selinux_domain_allowlist_support_v1034.py
```

Result:

```text
decision: v1034-pm-selinux-domain-allowlist-support-pass
pass: True
artifact_sha256: dff34476d956574be59628f1177179cb8ef87a04dda0c68e97cc5afcf5310f2d
```

## Next

V1035 should deploy helper `v176` only. After deploy, rerun V1033 PM SELinux
domain proof with the current-boot V490 precondition. Do not retry PM actor live
execution until PM domain proof actually passes.
