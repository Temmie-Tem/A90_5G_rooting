# Native Init V692 Peripheral Registry Snapshot Plan

## Objective

V692 adds targeted provider registration observability after V691 classified
the current blocker: exact private property ack is clean, but `pm-service` and
`pm-proxy` do not persist after start. The goal is to capture the
vndservicemanager/binder registry surface around provider start before changing
any broader property, Binder, HAL, or Wi-Fi bring-up behavior.

## Scope

- Bump the static execns helper to `a90_android_execns_probe v116`.
- Add mode
  `wifi-companion-service74-gated-peripheral-manager-cnss-retry-registry-snapshot-start-only`.
- Preserve the V690 order through service `74`, service managers, exact private
  property root, provider pair, and one fresh `cnss-daemon` retry.
- Add bounded registry snapshots at:
  - `before_initial_cnss_cleanup`;
  - `after_initial_cnss_cleanup`;
  - `after_per_mgr_probe`;
  - `after_per_proxy_probe`;
  - `window`.
- Add V692 deploy, direct live, and orchestrated live wrappers that classify
  registry snapshot completeness and provider readiness.

## Guardrails

- no Wi-Fi HAL or `wificond` start;
- no supplicant or hostapd start;
- no Wi-Fi scan/connect/link-up;
- no credential use;
- no DHCP, route change, or external ping;
- no sysfs subsystem state write;
- no `esoc0` open or hold;
- no boot image or partition write.

## Success Criteria

- helper v116 builds as a static ARM64 binary and exposes the new mode string;
- plan-only checks pass for deploy, direct V692 proof, and orchestrator;
- live deploy places helper v116 on the device without daemon start or Wi-Fi
  bring-up;
- bounded live proof reaches service `74`, vndservicemanager readiness, exact
  private property ack, provider start, and all five registry snapshot phases;
- result classifies either provider registration captured, provider ready with
  no WLFW advance, or a concrete blocker without scan/connect/DHCP/ping.

## Validation Commands

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_peripheral_manager_registry_snapshot_v692.py \
  scripts/revalidation/native_wifi_peripheral_manager_registry_snapshot_orchestrator_v692.py \
  scripts/revalidation/wifi_execns_helper_v116_deploy_preflight.py

scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v692-execns-helper-v116-build/a90_android_execns_probe

python3 scripts/revalidation/native_wifi_peripheral_manager_registry_snapshot_v692.py \
  --out-dir tmp/wifi/v692-peripheral-manager-registry-snapshot-plan \
  plan

python3 scripts/revalidation/native_wifi_peripheral_manager_registry_snapshot_orchestrator_v692.py \
  --out-dir tmp/wifi/v692-peripheral-manager-registry-snapshot-orchestrator-plan \
  plan

python3 scripts/revalidation/wifi_execns_helper_v116_deploy_preflight.py \
  --out-dir tmp/wifi/v692-execns-helper-v116-deploy-plan \
  plan
```

## Live Approval Phrases

```text
approve v692 deploy execns helper v116 only; no daemon start and no Wi-Fi bring-up
approve v692 PeripheralManager provider registry snapshot proof only; no Wi-Fi HAL start, no scan/connect/link-up, no DHCP and no external ping
```

## Next Gate

If V692 captures all registry phases but provider processes still exit, inspect
whether `pm-service` registers anything with `vndservicemanager` before exit.
Only after that should the next unit decide between provider runtime repair,
Binder/property surface changes, or returning to the pre-WLFW cnss2 path.
