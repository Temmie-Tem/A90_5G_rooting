# Native Init V859 pm-service Property Delta Replay Plan

## Goal

Replay the V857 `pm-service`/`pm-proxy` start-only gate after V858 property delta
deploy, without helper redeploy, and classify whether the original property
context gap is gone.

## Steps

1. Verify V855 node parity evidence and V858 deploy evidence.
2. Verify remote helper v132 hash.
3. Refresh `mountsystem ro` and SELinuxfs visibility.
4. Materialize Android-equivalent `/dev/esoc-0`, `/dev/subsys_esoc0`, and `/dev/subsys_modem`.
5. Run only `pm-service`/`pm-proxy` property-contract start-only.
6. Parse property denials and fd targets.
7. Clean up nodes and verify postflight health.

## Guardrails

- No helper deployment.
- No `mdm_helper` or `ks` start.
- No Wi-Fi HAL, scan/connect, credential use, DHCP/routes, or external ping.
- No raw eSoC ioctl, GPIO/sysfs/debugfs/subsystem write, module load/unload, boot image, or partition write.

## Success Criteria

- V858 target denials are gone.
- If subsystem fd holds appear, route to `mdm_helper`/`ks` contract planning.
- If new denials appear, route to another property-context delta before actor escalation.
