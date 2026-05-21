# Native Init V562 Lshal-Then-IWifi.start Plan

Date: `2026-05-21`

## Goal

Prove whether V561's raw hwbinder service-null result is a timing issue or a
raw client contract issue by checking `lshal wait IWifi/default` immediately
before the raw `IServiceManager.get` path in the same bounded live window.

## Scope

Allowed:

- deploy one helper binary to `/cache/bin/a90_android_execns_probe`;
- start the bounded dual-HAL companion/wificond window;
- run `lshal wait android.hardware.wifi@1.0::IWifi/default`;
- attempt raw hwbinder get/start only if `lshal wait` succeeds;
- collect cleanup and surface evidence.

Forbidden:

- supplicant or hostapd start;
- scan/connect/link-up;
- credential handling;
- DHCP, route changes, or external ping.

## Success Criteria

Pass if same-window `lshal` succeeds but raw hwbinder get still fails, because
that isolates the blocker to the raw client contract. Pass also if raw get
succeeds and `IWifi.start()` reaches a bounded result. Block only on cleanup
failure or unexpected scan/connect/link-up.
