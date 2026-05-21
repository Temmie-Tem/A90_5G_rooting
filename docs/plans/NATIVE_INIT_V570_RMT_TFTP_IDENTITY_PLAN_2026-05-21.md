# Native Init V570 rmt/tftp Identity Plan

Date: `2026-05-21`

## Goal

V569 proved that raw hwbinder reaches `IWifi.start()` and gets a decoded
`WifiStatusCode.ERROR_UNKNOWN/9`, while WLFW QRTR readback still has no service
events and `QIPCRTR` socket count remains zero.

V570 tests the most concrete native/Android delta found in the evidence:
`rmt_storage` and `tftp_server` were started by the native helper as root, but
Android runs them with dedicated runtime identities, groups, and capabilities.
The helper is rebuilt as v94 to apply those Android-observed identities before
retrying the same bounded dual-HAL/`wificond`/`IWifi.start()` proof.

## Non-Goals

- no QMI payload;
- no supplicant or hostapd start;
- no Wi-Fi scan, connect, link-up, credential use, DHCP, route change, or
  external ping;
- no boot image flash, reboot, partition write, or persistent service install.

## Evidence Basis

- V569: `IWifi.start()` transport completed, HAL returned `ERROR_UNKNOWN/9`,
  WLFW QRTR readback returned no service events, and `QIPCRTR` sockets stayed
  `0`.
- V525/V526 Android identity capture: `rmt_storage` runs as uid `9999`, gid
  `1000`, groups `1000,3010`, caps `CAP_NET_BIND_SERVICE` and
  `CAP_BLOCK_SUSPEND`; `tftp_server` runs as uid/gid `2903`, groups
  `1000,2903,2904,3010`, with the same two caps.
- V569 helper stdout: native helper still reported
  `rmt_storage-init-root` and `tftp_server-init-root`, proving the mismatch.

## Implementation

Files:

- `stage3/linux_init/helpers/a90_android_execns_probe.c`
- `scripts/revalidation/wifi_execns_helper_v94_deploy_preflight.py`
- `scripts/revalidation/native_wifi_companion_dual_hal_wificond_rmt_tftp_identity_v570.py`

Helper artifact:

- marker: `a90_android_execns_probe v94`
- SHA256:
  `8030c00267a35581406f6faf487090e081133f5aca1967b6d2edeae737db3948`
- build output:
  `tmp/wifi/v570-a90_android_execns_probe-v94/a90_android_execns_probe`
- mode: `wifi-companion-dual-hal-wificond-lshal-then-iwifi-start`

Runtime contract applied by v94:

| child | uid | gid | groups | caps |
|---|---:|---:|---|---|
| `rmt_storage` | `9999` | `1000` | `1000,3010` | `CAP_NET_BIND_SERVICE,CAP_BLOCK_SUSPEND` |
| `tftp_server` | `2903` | `2903` | `1000,2903,2904,3010` | `CAP_NET_BIND_SERVICE,CAP_BLOCK_SUSPEND` |

## Classification Criteria

Acceptable bounded outcomes:

1. `IWifi.start()` returns `SUCCESS`: stop before scan/connect and move to a
   separate scan-only gate.
2. WLFW service events or readiness markers appear: classify identity repair as
   progress and inspect the delayed firmware/netdev surface before any scan.
3. `IWifi.start()` remains `ERROR_UNKNOWN`, WLFW service events stay zero, and
   `QIPCRTR` sockets stay zero: identity repair was necessary but not
   sufficient; inspect QRTR/modem timing, service-notifier, and qmiproxy-like
   dependencies next.
4. Identity contract does not match the Android-observed values or cleanup is
   unsafe: stop and inspect evidence before retrying.

Wi-Fi objective remains incomplete until native init connects to Wi-Fi and
external ping passes.
