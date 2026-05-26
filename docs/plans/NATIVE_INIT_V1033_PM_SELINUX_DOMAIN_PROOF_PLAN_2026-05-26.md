# V1033 PM SELinux Domain Proof Plan

- date: `2026-05-26`
- type: current-boot SELinux diagnostic
- input: `docs/reports/NATIVE_INIT_V1032_PM_RUNTIME_DOMAIN_GUARD_LIVE_2026-05-26.md`
- helper: deployed `a90_android_execns_probe v175`

## Objective

Run a current-boot SELinux policy-load precondition and then test the PM
domains that V1032 blocked before actor `execv`.

The proof must not start PM actors. It only uses the static
`selinux-domain-proof` path to check whether these contexts can survive a
post-exec transition:

- `u:r:per_proxy_helper:s0`
- `u:r:vendor_per_mgr:s0`
- `u:r:vendor_per_proxy:s0`
- `u:r:vendor_mdm_helper:s0`
- control: `u:r:vendor_wcnss_service:s0`

## Gate

1. Mount or verify `selinuxfs`.
2. Run V490 current-boot Android split-policy load proof.
3. Run the PM domain proof matrix.
4. Stop before PM actor start, service-manager start, Wi-Fi HAL, scan/connect,
   DHCP/routes, or external ping.

## Guardrails

- no PM actor target `execv`
- no service-manager/CNSS/Wi-Fi HAL start
- no `wificond`
- no scan/connect/link-up
- no credentials
- no DHCP, route, or external ping
- no eSoC notify, BOOT_DONE, or `/dev/subsys_esoc0` open
- no boot image write, partition write, firmware mutation, GPIO/sysfs/debugfs write

## Commands

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
```

## Success Criteria

- V490 policy-load proof passes without init reexec or daemon start.
- PM domain proof either tests all PM contexts or explicitly classifies why it
  cannot test them.
- No actor, Wi-Fi, network, eSoC, boot, partition, firmware, GPIO, sysfs, or
  debugfs forbidden action occurs.

## Next

If the helper allowlist blocks PM contexts, repair the allowlist source/build
first. Do not rerun PM actor live gates until the PM domain proof can actually
test these contexts.
