# Native Init V472 Extended Property Runtime Live Plan

## Goal

Deploy the V471 extended private property layout into a versioned private SD
workspace and verify whether it removes the V470 property gap before retrying
Samsung Wi-Fi HAL registration.

This is still not a Wi-Fi credential/scan/connect step.

## Inputs

- Layout: `tmp/wifi/v471-extended-private-property-runtime/manifest.json`
- Helper: `a90_android_execns_probe v36`
- Target property root:
  `/mnt/sdext/a90/private-property-v317/v471/dev/__properties__`
- Registration proof: `scripts/revalidation/native_samsung_wifi_registration_v469.py`

## Allowed Scope

1. Create only `/mnt/sdext/a90/private-property-v317/v471`.
2. Copy the V471 generated layout under that private directory.
3. Verify copied file hashes.
4. Run read-only `property-lookup` against the V471 root.
5. If property lookup passes, rerun the bounded Samsung `ISehWifi/default`
   registration proof with the V471 root.

## Still Forbidden

- Global `/dev/__properties__` replacement or bind mount.
- `/dev/socket/property_service` creation.
- `setprop` or property mutation.
- Wi-Fi SSID/password use.
- Wi-Fi scan/connect/link-up/DHCP/routing/external ping.
- Persistent daemon/autostart changes.
- Android partition writes.

## Gates

| Gate | Pass Condition | Stop Condition |
| --- | --- | --- |
| native preflight | `a90ctl version/status` works and selftest has no fail | native control unstable |
| private deploy | all V471 files copied and SHA-256 verified | any hash mismatch or unsafe path |
| property lookup | V470 empty keys resolve from the V471 root, especially `ro.property_service.version=2` | missing context/access-denied warnings remain for selected keys |
| Samsung registration | at least one Samsung `ISehWifi/default` target registers within bounded wait | all Samsung targets still time out |
| cleanup | no residual private daemon process and postflight surface is safe | residual process or WLAN/rfkill unexpected state |

## Expected Outcome

If V471 property lookup succeeds but Samsung registration still times out, the
next blocker is no longer the minimal property runtime. Move to the remaining
HAL stderr/backchain issue, especially the `sh: no closing quote` signal and
vendor init/script import behavior.

If Samsung registration succeeds, proceed to a separate bounded Wi-Fi HAL
readiness gate before attempting scan/connect.
