# Native Init V1142 Execns Helper v215 Deploy Report

Date: `2026-05-27`

## Result

- Decision: `execns-helper-v215-deploy-pass`
- Pass: `true`
- Deploy gate: `scripts/revalidation/wifi_execns_helper_v215_deploy_preflight.py`
- Evidence: `tmp/wifi/v1142-execns-helper-v215-deploy`
- Remote helper: `/cache/bin/a90_android_execns_probe`
- Expected helper SHA256: `7bf107db54e4e3b2f9bbee196d40564ab4c62b2de1bcaa392ba843a6a6f3419e`
- Helper marker: `a90_android_execns_probe v215`

## Summary

V1142 deploys the V1141 helper build to `/cache/bin/a90_android_execns_probe`.
The deployment is deploy-only: it does not start PM/CNSS actors, `mdm_helper`,
service-manager actors, Wi-Fi HAL, scan/connect/link-up, DHCP, routes, external
ping, reboot, flash, or partition writes.

The first deploy attempt used the wrapper default serial chunk size `3000` and
failed before transfer because the generated command line exceeded the native
console safety limit. The successful run forced serial transfer with chunk size
`1800`.

## Deploy Result

Successful deploy result:

```text
method=serial
chunk_size=1800
chunks=960
chunks_written=960
line_check_ok=True
max_cmdv1_line_bytes=3788
safe_line_limit=3968
rc=0
```

The post-deploy preflight advanced past the helper-mode blocker and stopped at
the expected live approval gate.

```text
decision=service-manager-start-only-smoke-approval-required
pass=True
```

## Guardrails

- Daemon/service-manager start: not executed.
- PM/CNSS live actors: not executed.
- `mdm_helper`: not started.
- Wi-Fi HAL: not executed.
- Scan/connect/link-up: not executed.
- Credentials: not used.
- DHCP/route/external ping: not executed.
- Reboot/flash/partition write: not executed.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/wifi_execns_helper_v215_deploy_preflight.py
python3 scripts/revalidation/wifi_execns_helper_v215_deploy_preflight.py \
  --transfer-method serial \
  --serial-chunk-size 1800 \
  --apply \
  --assume-yes \
  --approval-phrase 'approve v1142 deploy execns helper v215 only; no daemon start and no Wi-Fi bring-up' \
  run
```

The deploy evidence reports:

```text
decision: execns-helper-v215-deploy-pass
pass: True
device_mutations: True
daemon_start_executed: False
wifi_bringup_executed: False
```

## Next

V1143 should run a bounded post-PM lower-trace live gate using helper `v215`.
It should add the explicit lower-trace flag, keep `ptrace-lite` scoped to
`mdm_helper`, and classify whether post-PM `/dev/esoc-0` reaches
`/dev/subsys_esoc0`, MHI pipe, `ks`, WLFW service69, or `wlan0`.
