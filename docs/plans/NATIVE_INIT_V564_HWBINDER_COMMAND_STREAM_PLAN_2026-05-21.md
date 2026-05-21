# Native Init V564 Hwbinder Command-Stream Repair Plan

Date: `2026-05-21`

## Goal

V563 fixed the HIDL interface-token framing but still produced
`BR_FAILED_REPLY`.  The dmesg delta showed the kernel interpreted impossible
transaction sizes, which points to C struct padding in the helper's binder
command stream rather than a service runtime issue.

V564 repairs the hwbinder command writer:

1. write `BC_TRANSACTION_SG` as `uint32_t command` followed immediately by
   `struct binder_transaction_data_sg`;
2. write `BC_FREE_BUFFER` as `uint32_t command` followed immediately by
   `binder_uintptr_t`;
3. keep the V563 String16 interface-token repair;
4. rerun the same bounded dual-HAL + `wificond` + `lshal wait` precheck;
5. attempt raw `IServiceManager.get(IWifi/default)` and `IWifi.start()` only if
   a non-null handle is returned.

## Non-Goals

- no supplicant or hostapd start;
- no scan, connect, link-up, credential use, DHCP, route change, or external
  ping;
- no boot image flash, reboot, partition write, or persistent service install.

## Artifact

- helper: `a90_android_execns_probe v89`
- local artifact:
  `tmp/wifi/v564-a90_android_execns_probe-v89/a90_android_execns_probe`
- SHA256:
  `0279d7de60366ef8f51e71599e90fc71d5db9402b500d6c93f9c39e094311568`
- mode: `wifi-companion-dual-hal-wificond-lshal-then-iwifi-start`

## Success Criteria

Accept one bounded evidence-backed result:

1. raw `IWifi.start()` transaction completes and cleanup is safe;
2. raw `get` still fails/nulls, but dmesg no longer shows impossible binder
   transaction sizes from the helper and cleanup is safe;
3. `lshal wait IWifi/default` fails and raw start is correctly skipped.

The final native Wi-Fi objective remains incomplete until Wi-Fi connects and an
external ping succeeds.
