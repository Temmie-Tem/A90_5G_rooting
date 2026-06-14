# V1033 PM SELinux Domain Proof

- date: `2026-05-26`
- scope: current-boot SELinux policy-load precondition plus PM domain proof
- decision: `v1033-pm-selinux-domain-proof-helper-allowlist-blocked`
- pass: `True`
- V401 evidence: `tmp/wifi/v1033-v401-selinuxfs-mount/manifest.json`
- V490 evidence: `tmp/wifi/v1033-v490-policy-load/manifest.json`
- V1033 evidence: `tmp/wifi/v1033-pm-selinux-domain-proof/manifest.json`

## Summary

V1033 mounted `selinuxfs`, loaded the Android split policy for the current boot,
and attempted a PM-specific SELinux domain proof. The PM proof did not reach
policy transition testing for the PM domains because helper `v175`
`selinux-domain-proof` rejected all required PM contexts at its historical v37
allowlist.

The control context `u:r:vendor_wcnss_service:s0` is allowed and can transition,
which proves the proof path itself still works after V490. The immediate blocker
is the helper allowlist, not a proven PM policy transition failure.

## Result

| Item | Value |
| --- | --- |
| V401 selinuxfs mount | pass |
| V490 policy load | `v490-selinux-policy-load-proof-pass` |
| PM proof decision | `v1033-pm-selinux-domain-proof-helper-allowlist-blocked` |
| blocked PM contexts | `per_proxy_helper`, `vendor_per_mgr`, `vendor_per_proxy`, `vendor_mdm_helper` |
| control context | `vendor_wcnss_service` passed |
| daemon start | `False` |
| Wi-Fi HAL start | `False` |
| scan/connect | `False` |
| credential use | `False` |
| DHCP/route/external ping | `False` |

## Interpretation

V1032 correctly blocked unsafe PM actor execution, but V1033 shows the next
diagnostic tool could not yet test PM domains because its explicit allowlist
lacked those contexts.

The next useful unit is source/build-only: add the PM contexts to the helper
`selinux-domain-proof` allowlist, rebuild helper `v176`, then deploy it and rerun
V1033. Only if PM domain proof passes should V1032 PM actor guard be retried.

## Guardrails

- no PM actor target execution
- no service-manager/CNSS/Wi-Fi HAL start
- no `wificond`
- no scan/connect/link-up
- no credentials
- no DHCP, route, or external ping
- no eSoC notify, BOOT_DONE, or `/dev/subsys_esoc0` open
- no boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs write

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_selinux_domain_proof_v1033.py
python3 scripts/revalidation/wifi_selinuxfs_toybox_mount_live_executor.py \
  --out-dir tmp/wifi/v1033-v401-selinuxfs-mount \
  --approval-phrase "approve v401 toybox mount selinuxfs runtime surface only; no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/native_selinux_policy_load_proof_v490.py \
  --out-dir tmp/wifi/v1033-v490-policy-load \
  --helper-sha256 9036bb15ced9fb1098c4375c15c2c729502c841574ae14798fb331fc29c89e42 \
  --approval-phrase "approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/native_wifi_pm_selinux_domain_proof_v1033.py \
  --v490-manifest tmp/wifi/v1033-v490-policy-load/manifest.json \
  --approval-phrase "approve v1033 PM SELinux domain proof only; no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/a90ctl.py --timeout 5 bootstatus
python3 scripts/revalidation/a90ctl.py --timeout 5 selftest
```

Postflight:

```text
boot: BOOT OK shell
selftest: pass=11 warn=1 fail=0
```

## Next

V1034 should add PM contexts to the helper `selinux-domain-proof` allowlist and
produce a static helper build. Deployment and live proof rerun must be separate.
