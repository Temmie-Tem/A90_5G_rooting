# V995 SELinux Domain Allowlist

- generated: `2026-05-26`
- scope: source/build-only helper support
- decision: `v995-selinux-domain-allowlist-build-pass`
- pass: `True`
- evidence: `tmp/wifi/v995-selinux-domain-allowlist/manifest.json`
- helper: `a90_android_execns_probe v169`
- helper sha256: `c47f0659178186d45cf5199fdad4d198f0c69b6998f2127ff420f9e0f0204a74`
- script: `scripts/revalidation/native_wifi_selinux_domain_allowlist_v995.py`

## Summary

V995 adds the missing source/build support needed by the V994-selected route.
The helper can now use `selinux-domain-proof` for the two service-window
domains that were not covered by the older V491 proof surface:

- `u:r:wificond:s0`
- `u:r:vndservicemanager:s0`

It also adds target profiles for:

- `/system/bin/wificond`
- `/vendor/bin/vndservicemanager`

No live device action occurred in V995.

## Checks

| Check | Result |
| --- | --- |
| helper version `v169` | PASS |
| `wificond` SELinux context allowed | PASS |
| `vndservicemanager` SELinux context allowed | PASS |
| `system-wificond` target profile | PASS |
| `vendor-vndservicemanager` target profile | PASS |
| custom target allowlist extended | PASS |
| `selinux-domain-proof` no-actor guardrails preserved | PASS |
| Android service-window no-Wi-Fi guardrails preserved | PASS |
| static build | PASS |
| artifact strings confirm new domains and targets | PASS |

## Validation

```bash
python3 scripts/revalidation/native_wifi_selinux_domain_allowlist_v995.py
```

Result:

```text
decision: v995-selinux-domain-allowlist-build-pass
pass: True
sha256: c47f0659178186d45cf5199fdad4d198f0c69b6998f2127ff420f9e0f0204a74
```

## Guardrails

- source/build-only
- no device command
- no helper deploy
- no SELinux policy load
- no actor start
- no service-manager start
- no Wi-Fi HAL start
- no scan/connect/link-up
- no credential use
- no DHCP/route/external ping

## Next

V996 should deploy helper `v169` only. After deploy parity passes, the next live
gate should refresh current-boot V401/V490 and run an expanded post-load domain
proof before another Android service-window retry.
