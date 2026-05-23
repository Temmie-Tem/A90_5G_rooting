# Native Init V677 V676-residual Property Plan

## Objective

Extend the private property runtime with the residual property keys observed
after V676. V676 reduced the original V675 property denial set from `16916`
lookups to `370`, but still left `20` unique property keys missing. V677 closes
that property surface before moving to Binder repair.

## Inputs

- V676 live replay:
  `tmp/wifi/v676-v535-property-android-order-orchestrated-live/manifest.json`
- V535 private property layout:
  `tmp/wifi/v535-rmt-storage-private-property-runtime/manifest.json`
- Android property contexts:
  `tmp/wifi/v295-property-snapshot-live-20260519-142740/native/cat-context-*.txt`
- Android full getprop:
  `tmp/wifi/v297-android-property-capture-android/commands/all-getprop.txt`

## Gate

V677 has two host/live units:

1. `scripts/revalidation/native_property_runtime_overlay_v677.py`
   - parses the V676 helper transcript;
   - extracts the full residual property-denial set;
   - extends the V535 layout with those keys;
   - roundtrips property_info and prop_area on host.
2. `scripts/revalidation/native_property_runtime_incremental_v677.py`
   - uploads only changed property files to the versioned private V535 root;
   - keeps global `/dev/__properties__` untouched;
   - verifies preflight and can run private-root lookup proof.

The final effect is checked by rerunning the V676-style Android userspace-order
live arm against the updated private root.

## Forbidden Actions

- No global `/dev/__properties__` replacement.
- No global bind over `/dev/__properties__`.
- No global `/dev/socket/property_service` creation.
- No supplicant or hostapd start.
- No scan/connect/link-up.
- No credential, DHCP, route change, or external ping.
- No boot image or partition write.

## Success Criteria

- V677 host layout maps all V676 residual keys.
- V677 host layout roundtrips property_info and prop_area.
- V677 delta deploy writes only versioned private property-root files.
- Post-delta replay shows property denial count reaches zero.
- Cleanup reboot returns to healthy native control.
- WLFW/BDF/`wlan0` state is classified before any connection attempt.

## Commands

```sh
python3 -m py_compile \
  scripts/revalidation/native_property_runtime_overlay_v677.py \
  scripts/revalidation/native_property_runtime_incremental_v677.py

python3 scripts/revalidation/native_property_runtime_overlay_v677.py \
  --out-dir tmp/wifi/v677-v676-residual-private-property-runtime \
  run

python3 scripts/revalidation/native_property_runtime_incremental_v677.py \
  --out-dir tmp/wifi/v677-v676-residual-property-incremental-preflight-postfix \
  preflight

python3 scripts/revalidation/native_wifi_v535_property_android_order_orchestrator_v676.py \
  --out-dir tmp/wifi/v677-v676-residual-property-replay-live \
  --apply \
  --assume-yes \
  run
```

## Expected Routing

If V677 drops property denials to zero while WLFW/BDF/`wlan0` stays absent, the
next blocker is Binder registration/transaction behavior, not more property
layout work or Wi-Fi credentials.
