# Native Init V858 pm-service Property Context Delta Plan

## Goal

Classify and repair only the V857 `pm-service`/`pm-proxy` property-context gap
inside the private property runtime. This is still below `mdm_helper`, `ks`,
Wi-Fi HAL, scan/connect, DHCP/routes, credentials, and external ping.

## Inputs

- V857 evidence: `tmp/wifi/v857-pm-service-property-contract-start-only/manifest.json`
- Existing property root model: `tmp/wifi/v535-rmt-storage-private-property-runtime/manifest.json`
- Android property contexts: `tmp/wifi/v295-property-snapshot-live-20260519-142740/`

## Steps

1. Parse V857 stderr for `Could not find context` and `Access denied finding property` keys.
2. Map those keys through captured Android `property_contexts`.
3. Generate a host-only private `/dev/__properties__` layout with exact seed entries.
4. Deploy only the required delta files into the existing private V535 property root.
5. Verify device-side hashes; do not run daemons during deploy.
6. Route to a separate bounded replay gate to test runtime effect.

## Guardrails

- No global `/dev/__properties__` replacement or global property-service socket.
- No `mdm_helper`, `ks`, CNSS retry, Wi-Fi HAL, wificond, supplicant, hostapd.
- No scan/connect, credential use, DHCP/routes, or external ping.
- No raw eSoC ioctl, GPIO/sysfs/debugfs/subsystem write, module load/unload, boot image, or partition write.

## Success Criteria

- All V857 residual property keys map to Android property contexts.
- Host layout roundtrip passes.
- V858 deploy verifies selected file hashes on device.
- All mutation flags remain below Wi-Fi bring-up scope.
