# V1192 Per-Proxy Spawn + PM Subsystem Open Plan

- **cycle**: V1192
- **date**: 2026-05-29
- **type**: live (host-only preflight recommended first)
- **prior**: V1191 live PASS — per_mgr domain fixed (`u:r:vendor_per_mgr:s0`), vndservice gate open in 30ms

## V1191 Evidence

| metric | value |
|---|---|
| `policy_load_result` | `policy-load-pass` |
| `policy_load_bytes` | `1329357` |
| `policy_load_enforce_written` | `1` |
| `gate_result` | `ready` |
| `gate_poll_count` | `1` |
| `gate_elapsed_ms` | `30ms` |
| `per_mgr_domain_value` | `u:r:vendor_per_mgr:s0` |
| `per_mgr_domain_fixed` | `True` |
| `per_proxy_skipped` | `` (not observed — gate passed before proxy start) |

## Analysis

V1191 confirms:
1. per_mgr now runs in `vendor_per_mgr` SELinux domain
2. vndservice gate opens immediately (30ms) — per_mgr registers with vndservicemanager
3. per_proxy_skipped field is empty — timing of per_proxy spawn relative to gate open is unknown

Next blocker candidates:
- per_proxy not spawned, or spawned in wrong domain
- per_proxy opens `/dev/subsys_esoc0`/`/dev/subsys_modem` (Android pm-service behavior)
- pm_proxy_helper interaction with per_proxy

## Gate for V1192

Extend the V1191 chain to observe:
1. per_proxy spawn (after vndservice gate open)
2. per_proxy SELinux domain (`u:r:vendor_per_mgr:s0` or `vendor_per_proxy`)
3. `/dev/subsys_esoc0` and `/dev/subsys_modem` fd holds in per_proxy or per_mgr
4. pm_proxy_helper interaction

The V1183 chain already has per_proxy spawn logic after the gate. V1191 passed with
`per_proxy_skipped=` (empty) — need to check if per_proxy was actually triggered.

## Constraints

- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping
- No `/dev/esoc-0` CMD/REQ engine mutations
- No `mdm_helper`, `ks`, CNSS daemon beyond current chain
- Policy load (precompiled_sepolicy) + enforce=0 must remain in chain (from V1191)

## Script

Extend `native_wifi_pm_per_mgr_policy_load_v1191.py` pattern with per_proxy
observation. Alternatively read V1191 full child output to check whether per_proxy
was spawned and what its domain was.

Check evidence: `tmp/wifi/v1191-pm-per-mgr-policy-load/`
