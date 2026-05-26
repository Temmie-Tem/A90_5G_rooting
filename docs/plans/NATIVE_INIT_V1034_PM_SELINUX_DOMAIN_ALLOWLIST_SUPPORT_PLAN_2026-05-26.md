# V1034 PM SELinux Domain Allowlist Support Plan

- date: `2026-05-26`
- type: source/build-only helper update
- input: `docs/reports/NATIVE_INIT_V1033_PM_SELINUX_DOMAIN_PROOF_2026-05-26.md`

## Objective

Update `a90_android_execns_probe` so `selinux-domain-proof` can test the PM
domains that V1033 needs:

- `u:r:per_proxy_helper:s0`
- `u:r:vendor_per_mgr:s0`
- `u:r:vendor_per_proxy:s0`
- `u:r:vendor_mdm_helper:s0`

This is observability support only. It must not deploy the helper or run live PM
actors.

## Guardrails

- source/build-only
- no device command
- no helper deploy
- no actor start
- no daemon start
- no Wi-Fi HAL, scan/connect, credentials, DHCP/route, or external ping
- no boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs write

## Commands

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_selinux_domain_allowlist_support_v1034.py
python3 scripts/revalidation/native_wifi_pm_selinux_domain_allowlist_support_v1034.py
```

## Success Criteria

- Helper version bumps to `a90_android_execns_probe v176`.
- PM contexts are present in the `selinux-domain-proof` allowlist.
- Existing PM full-contract and runtime-domain guard support remains present.
- Static helper build succeeds and artifact strings confirm the new contexts.

## Next

Deploy helper `v176`, rerun V1033 PM domain proof, then retry V1032 only if the
required PM domains pass.
