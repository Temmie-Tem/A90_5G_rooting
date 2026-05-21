# Native Init V565 Hwbinder Mmap Repair Plan

Date: `2026-05-21`

## Goal

V564 fixed the hwbinder command-stream padding bug: the impossible transaction
sizes disappeared.  The remaining dmesg failure is now `binder_alloc_buf, no
vma` when `hwservicemanager` tries to reply to the raw helper.  AOSP
`libhwbinder` opens `/dev/hwbinder` and mmaps a binder VM area before receiving
transactions.

V565 adds that missing client setup:

1. mmap `/dev/hwbinder` with a libhwbinder-style read-only VM window;
2. keep the V563 String16 interface-token repair;
3. keep the V564 packed command stream repair;
4. rerun the same bounded dual-HAL + `wificond` + `lshal wait` precheck;
5. attempt raw `IServiceManager.get(IWifi/default)` and `IWifi.start()` only if
   a non-null handle is returned.

## Non-Goals

- no supplicant or hostapd start;
- no scan, connect, link-up, credential use, DHCP, route change, or external
  ping;
- no boot image flash, reboot, partition write, or persistent service install.

## Artifact

- helper: `a90_android_execns_probe v90`
- local artifact:
  `tmp/wifi/v565-a90_android_execns_probe-v90/a90_android_execns_probe`
- SHA256:
  `0b150699f737479a3a3d970016a51d9308fb7fa47b35ba3965dbc6ac91c32907`
- mode: `wifi-companion-dual-hal-wificond-lshal-then-iwifi-start`

## Reference

- AOSP `ProcessState.cpp` uses `DEFAULT_BINDER_VM_SIZE`, opens
  `/dev/hwbinder`, and mmaps transaction memory with `PROT_READ` and
  `MAP_PRIVATE | MAP_NORESERVE`.
  <https://android.googlesource.com/platform/system/libhwbinder/+/3332ca8f16491193c58fcafa8d6105925f2aad43/ProcessState.cpp>

## Success Criteria

Accept one bounded evidence-backed result:

1. raw `IWifi.start()` transaction completes and cleanup is safe;
2. raw `get` still fails/nulls, but dmesg no longer shows `no vma` for the raw
   helper reply path and cleanup is safe;
3. `lshal wait IWifi/default` fails and raw start is correctly skipped.

The final native Wi-Fi objective remains incomplete until Wi-Fi connects and an
external ping succeeds.
