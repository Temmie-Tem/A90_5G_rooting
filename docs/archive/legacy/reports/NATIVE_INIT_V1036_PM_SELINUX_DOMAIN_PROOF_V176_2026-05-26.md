# V1036 PM SELinux Domain Proof v176 Report

- date: `2026-05-26`
- scope: bounded live domain proof
- helper: `a90_android_execns_probe v176`
- decision: `v1036-pm-selinux-domain-handoff-present`
- pass: `True`
- evidence: `tmp/wifi/v1036-pm-selinux-domain-proof-v176/manifest.json`

## Summary

V1036 reran the PM SELinux domain proof with deployed helper `v176`.

The V1033 allowlist blocker is removed: all required PM contexts survive static
re-exec after the V490 policy-load precondition. This means V1032's earlier
`attr/exec=kernel` result was not a permanent PM-domain impossibility; the next
live gate can require Android SELinux exec match again.

## Result

| Item | Value |
| --- | --- |
| decision | `v1036-pm-selinux-domain-handoff-present` |
| required PM contexts matched | `4/4` |
| PM allowlist blocked contexts | `0` |
| actor start | `False` |
| daemon start | `False` |
| Wi-Fi HAL start | `False` |
| scan/connect | `False` |
| credential use | `False` |
| DHCP/route | `False` |
| external ping | `False` |
| Wi-Fi bring-up | `False` |

## Findings

- `u:r:per_proxy_helper:s0` passed.
- `u:r:vendor_per_mgr:s0` passed.
- `u:r:vendor_per_proxy:s0` passed.
- `u:r:vendor_mdm_helper:s0` passed.
- Control context `u:r:vendor_wcnss_service:s0` still passed.

## Interpretation

Helper `v176` is sufficient for PM domain proof coverage. The next blocker must
be tested in the actual PM actor runtime path, not in static domain proof.

Do not start Wi-Fi HAL or attempt scan/connect yet. The next bounded live unit
should rerun the PM runtime-domain guard and stop before any unsafe lower
contract action.

## Guardrails

- no actor start
- no daemon start
- no Wi-Fi HAL start
- no scan/connect/link-up
- no credentials
- no DHCP, route, or external ping
- no init re-exec
- no boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs write

## Validation

Commands:

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

## Next

V1037 should rerun the PM runtime-domain guard with helper `v176` and the fresh
current-boot policy-load state.
