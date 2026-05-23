# Native Init V665 Private Registry Snapshot Path Repair Plan

- date: `2026-05-23 KST`
- cycle: `v665`
- scope: helper path repair + bounded live proof
- target: make the V662/V664 registry snapshot read the helper private temp-root
  `/dev/__properties__` and `/dev/socket` paths, then prove the snapshot reaches
  those paths before enabling any fresh CNSS retry.

## Background

V664 proved that the private property root is visible inside the helper context
and that the property-service shim can start. The same live transcript also
showed the registry snapshot still opening host/global `/dev/__properties__` and
`/dev/socket`, so `dirs_captured` stayed `0` even though the private temp-root
paths existed.

## Guardrails

V665 must not:

- write DSP boot nodes directly or open `esoc0`;
- write `boot_wlan` or `qcwlanstate`;
- run the fresh CNSS retry tail;
- start Wi-Fi HAL, scan/connect/link-up, use credentials, run DHCP, change
  routes, or ping externally.

The only helper behavior change is read-only snapshot path selection. The helper
may still start the already bounded lower companion/service-manager sequence used
by V662/V664, and it must use reboot cleanup after live execution.

## Implementation

1. Bump `a90_android_execns_probe` to helper `v109`.
2. Pass `struct paths` into `append_wifi_registry_context_snapshot`.
3. Capture `paths->dev_properties` and `paths->dev_socket` instead of
   host/global `/dev/__properties__` and `/dev/socket`.
4. Emit explicit snapshot path keys:
   - `wifi_registry_snapshot.<phase>.dev_properties_capture_path`
   - `wifi_registry_snapshot.<phase>.dev_socket_capture_path`
5. Add `native_wifi_private_registry_snapshot_path_repair_v665.py` as a V665
   runner with helper `v109` defaults.
6. Add `wifi_execns_helper_v109_deploy_preflight.py` for bounded helper deploy.
7. Fix V664 materialization parsing so service `74` gate timeout is not
   misreported as property materialization failure.

## Success Criteria

V665 passes only if a live run shows:

- `context.dev_properties.exists=1`, readable, and executable;
- property-service shim started and postflight-safe;
- both before/after registry snapshot phases ended;
- both before/after registry snapshots captured at least two directories;
- snapshot capture paths point at the helper private temp-root `dev` paths;
- CNSS retry, Wi-Fi HAL, scan/connect, DHCP, route changes, and external ping
  remain disabled.

If service `74` does not appear, classify that as a lower publication/gating
regression and do not claim path repair failure.

## Next Gate

If V665 passes, plan V666 as a fresh CNSS retry using the repaired private
property/runtime snapshot surface. Wi-Fi HAL and actual connect/ping remain
blocked until the CNSS retry advances WLFW/WLAN-PD/BDF/`wlan0` evidence.
