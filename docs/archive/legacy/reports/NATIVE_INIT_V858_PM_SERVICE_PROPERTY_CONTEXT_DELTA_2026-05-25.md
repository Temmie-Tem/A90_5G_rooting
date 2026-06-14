# Native Init V858 pm-service Property Context Delta Report

## Result

- classifier decision: `v858-pm-service-private-property-runtime-ready`
- deploy decision: `v858-pm-service-property-incremental-deploy-pass`
- pass: `true`
- classifier: `scripts/revalidation/native_property_runtime_pm_service_v858.py`
- deployer: `scripts/revalidation/native_property_runtime_incremental_v858.py`
- classifier evidence: `tmp/wifi/v858-pm-service-private-property-runtime/manifest.json`
- deploy evidence: `tmp/wifi/v858-pm-service-property-incremental-live/manifest.json`

## Findings

V858 parsed V857 residual property denials and mapped all eight keys into the
captured Android property contexts:

| Key group | Context |
| --- | --- |
| `debug.ld.app.pm-service`, `debug.ld.app.pm-proxy` | `u:object_r:debug_prop:s0` |
| `arm64.memtag.process.pm-service`, `arm64.memtag.process.pm-proxy` | `u:object_r:arm64_memtag_prop:s0` |
| `persist.log.tag.PerMgrSrv`, `log.tag.PerMgrSrv` | `u:object_r:log_tag_prop:s0` |
| `persist.log.tag.PerMgrProxy`, `log.tag.PerMgrProxy` | `u:object_r:log_tag_prop:s0` |

The generated private property layout contains `111` properties across `20`
contexts, and roundtrip validation had `0` failures.

## Live Deploy

V858 updated only the private V535 property root:

```text
/mnt/sdext/a90/private-property-v317/v535/dev/__properties__
```

Selected files were uploaded and device-side hashes verified, including
`property_info`, `arm64_memtag_prop`, `debug_prop`, `log_tag_prop`, and related
context prop-area files. No lookup was run for the new keys because the helper's
read-only `property-lookup` allowlist intentionally does not include these
service-specific keys.

## Guardrails

- `daemon_start_executed=false`
- `wifi_bringup_executed=false`
- no Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping
- no global property root replacement
- no raw eSoC ioctl, GPIO/sysfs/debugfs/subsystem write, module load/unload, boot image, or partition write

## Next

Run a bounded `pm-service`/`pm-proxy` replay against the updated private root to
verify whether the V857 denials are removed and whether subsystem fd holds
appear.
