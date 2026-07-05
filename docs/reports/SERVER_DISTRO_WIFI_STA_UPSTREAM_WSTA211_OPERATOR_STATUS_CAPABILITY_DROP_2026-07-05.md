# WSTA211 Operator Status Capability Drop

Date: 2026-07-05

## Verdict

PASS.  WSTA211 promotes the existing no-new-privs and zero-effective-capability
live evidence into a first-class operator status proof.  The status now records
non-root service capability-drop as live-proven for `dpublic-smoke-httpd`,
`cloudflared-quick-tunnel`, and the `dpublic-hud` intent producer.  The only
remaining launcher profile is the native boundary helper.

Private evidence:

```text
workspace/private/runs/server-distro/wsta211-operator-status-capability-drop-20260705T1956KST/wsta108_operator_server_status.json
workspace/private/runs/server-distro/wsta211-operator-status-capability-drop-20260705T1956KST/wsta108_operator_server_status.md
```

Decision:

```text
wsta108-operator-server-status-source-pass
```

## Capability State

The accepted status contains:

```text
capability_state=NONROOT_SERVICE_CAPABILITY_DROP_LIVE_PROVEN
capability_drop_nonroot_services_live_proven=true
proven_services=dpublic-smoke-httpd,cloudflared-quick-tunnel,dpublic-hud
remaining_nonroot_services=
remaining_launcher_profiles=wsta-native-uplink-helper
root_boundary_services=dropbear-admin-usb,wsta-native-uplink-helper
```

The proof is status aggregation only; it relies on the existing live artifacts
that proved `NoNewPrivs=1` and `CapEff=0` for the non-root service processes.

## Next Actions

The generated operator next-action list now ends with:

```text
continue-root-boundary-policy-for-wsta-native-uplink-helper
continue-containment-hardening-with-nftables-or-apparmor
move-to-nftables-default-drop-or-apparmor-hardening
```

This retires capability-drop as the primary next D-harden item for non-root
services.  Remaining work is boundary policy for the native uplink helper and
the next containment lever.

## Safety

This was host-only status aggregation.  No device action, boot flash, native
reboot, Wi-Fi connect, DHCP, public tunnel, public smoke, packet-filter
mutation, userdata write, or switch-root occurred.

Safety fields from the accepted result:

```text
device_action=false
boot_flash=false
native_reboot=false
wifi_connect=false
dhcp=false
public_tunnel=false
public_smoke=false
packet_filter_mutation=false
userdata_touch=false
switch_root=false
public_url_value_logged=false
secret_values_logged=0
```

## Code Changes

- Added `capability_drop_proof` compaction to the WSTA108 operator status.
- Retired `dpublic-hud` from stale remaining launcher profiles when the HUD
  intent producer proof has `no_new_privs` and `CapEff=0`.
- Updated operator next actions to prefer nftables/AppArmor once seccomp and
  non-root capability-drop are both live-proven.
- Added focused WSTA108 tests for WSTA211 capability status.
