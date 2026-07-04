# Server Distro Wi-Fi STA Upstream WSTA23 Uplink Service Live Pass

- Date: `2026-07-04`
- Decision: `wsta23-native-uplink-service-live-pass`
- Final resident: `A90 Linux init 0.11.143 (v3387-wifi-uplink-service-redacted)`
- Final resident boot SHA256: `ebebf4384f408c5cd20630b12cfd94d56d4d484664612b692de986fdecf6da5d`
- Helper SHA256: `fa395d3ecb6944a57487f3966948a634596157e4de3fdc39575a2fc502d1ceef`
- Commit under test: `0d871343 Redact V3387 Wi-Fi uplink profile labels`

## Scope

Prove the native-owned Wi-Fi uplink service boundary without credentials or public exposure:

- flash V3387 through the checked `native_init_flash.py` helper;
- health-check `version`, `status`, and `selftest`;
- start `wifi uplink-service`;
- prove `op=status` returns redacted native-owned uplink status;
- prove `op=autoconnect` without confirm is denied before connect/DHCP;
- cleanup and finish with `selftest fail=0`.

No association, DHCP, ping, public tunnel, userdata, switch-root, forbidden partition, or raw
credential operation ran.

## Preflight

- Rollback image SHA checks passed:
  - v2321: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - v2237: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - v48: `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
- TWRP artifacts were present:
  - recovery image: `b1ef377a52ec8ab43b49a5fcc7a0b27e8efff91bf2d8cccdc565ecadadcc646c`
  - recovery tar: `6d9e929462ea4c85f257b080431d387d5bfb787ff800bd4178c823c3874d862a`
- Starting resident V3386 was healthy before V3387 flash: `selftest fail=0`.

## V3386 Interlock Finding

V3386 flashed and booted cleanly, but the first `op=status` response exposed a configured profile
label value.  No secret file contents, association, DHCP, ping, or public tunnel ran.  The temporary
service was stopped, and V3387 was built to replace profile label values with present booleans before
closing the live gate.

## V3387 Flash

- Command path: `native_init_flash.py --from-native`
- Expected version: `0.11.143`
- Expected SHA256: `ebebf4384f408c5cd20630b12cfd94d56d4d484664612b692de986fdecf6da5d`
- Remote image SHA256 matched expected.
- Boot block prefix readback SHA256 matched expected.
- Flash elapsed: `62.555s`
- Post-boot `version` and `status` verification passed.
- Post-boot `selftest`: `pass=12 warn=1 fail=0`

## Uplink Service Status

Temporary service:

- Command: `wifi uplink-service start /tmp/a90-uplink-wsta23-v3387b 120000 100`
- Result: `wifi-uplink-service-start-pass`

`op=status` response summary:

- `version=a90-native-wifi-uplink-service-v1`
- `owner=native-init`
- `credentials=0`
- `connect=0`
- `dhcp_routing=observed-only`
- `external_ping_execution=0`
- `public_tunnel=0`
- `raw_values_redacted=1`
- `secret_values_logged=0`
- `config_profile_present=1`
- `autoconnect_profile_present=1`
- `decision=wifi-uplink-service-status-pass`

The response did not emit the configured profile label value.

## No-Confirm Autoconnect Denial

Request:

```text
seq=301
op=autoconnect
```

Response summary:

- `version=a90-native-wifi-uplink-service-v1`
- `owner=native-init`
- `credentials=private-config-gated`
- `connect=confirm-gated`
- `dhcp_routing=config-gated`
- `external_ping_execution=0`
- `public_tunnel=0`
- `secret_values_logged=0`
- `rc=-13`
- `decision=wifi-uplink-service-confirm-required`

No confirm token was supplied, so native init denied the request before connect/DHCP.

## Cleanup

- `wifi uplink-service stop /tmp/a90-uplink-wsta23-v3387b`: `wifi-uplink-service-stop-pass`
- Final `selftest`: `pass=12 warn=1 fail=0`
- Device remains on V3387 for the next bounded gate.

## Next

WSTA24 should add a Debian-side uplink-service client/helper for `status` and no-confirm denial
proofs.  Full confirmed autoconnect/DHCP remains a separate credential-gated live unit.
