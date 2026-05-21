# Native Init V570 rmt/tftp Identity Report

Date: `2026-05-21`

## Goal

Apply Android-observed runtime identities to `rmt_storage` and `tftp_server`,
then rerun the bounded companion, dual-HAL, `wificond`, WLFW QRTR readback, and
`IWifi.start()` proof without scan/connect/link-up.

## Result

- Decision: `v570-rmt-tftp-identity-not-sufficient`
- Pass: `True`
- Reason: Android runtime identities were applied, but `IWifi.start()` still
  returned `WifiStatusCode.ERROR_UNKNOWN/9` and `QIPCRTR` sockets stayed `0`.
- Evidence:
  `tmp/wifi/v570-companion-dual-hal-wificond-rmt-tftp-identity`
- Helper: `a90_android_execns_probe v94`
- Helper SHA-256:
  `8030c00267a35581406f6faf487090e081133f5aca1967b6d2edeae737db3948`
- Wi-Fi bring-up: not executed

## Scope Confirmation

- Helper v94 was deployed through NCM by the V570 deploy wrapper.
- The live proof started only the bounded companion, service-manager, dual-HAL,
  CNSS, and `wificond` window.
- No QMI payload was sent.
- The proof did not run supplicant, hostapd, scan/connect/link-up, credentials,
  DHCP, route changes, external ping, reboot, or boot partition writes.
- Post-run residue check found no target process.
- Post-run `/proc/net/dev` check found no Wi-Fi network device.

## Validation

Static/local checks:

```text
python3 -m py_compile scripts/revalidation/wifi_execns_helper_v94_deploy_preflight.py \
  scripts/revalidation/native_wifi_companion_dual_hal_wificond_rmt_tftp_identity_v570.py
git diff --check -- stage3/linux_init/helpers/a90_android_execns_probe.c \
  scripts/revalidation/wifi_execns_helper_v94_deploy_preflight.py \
  scripts/revalidation/native_wifi_companion_dual_hal_wificond_rmt_tftp_identity_v570.py \
  docs/plans/NATIVE_INIT_V570_RMT_TFTP_IDENTITY_PLAN_2026-05-21.md docs/README.md
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v570-a90_android_execns_probe-v94/a90_android_execns_probe
```

Deploy/live commands:

```text
python3 scripts/revalidation/wifi_execns_helper_v94_deploy_preflight.py preflight
python3 scripts/revalidation/wifi_execns_helper_v94_deploy_preflight.py \
  --approval-phrase "approve v570 deploy execns helper v94 only; no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/native_wifi_companion_dual_hal_wificond_rmt_tftp_identity_v570.py preflight
python3 scripts/revalidation/native_wifi_companion_dual_hal_wificond_rmt_tftp_identity_v570.py \
  --approval-phrase "approve v570 rmt/tftp Android identity retry only; no QMI payload, no supplicant, no scan/connect/link-up and no external ping" \
  --apply --assume-yes run
```

## Identity Repair Evidence

The helper now applies the Android-observed identities:

| child | contract | uid | gid | groups | cap_count | ambient | match |
|---|---|---:|---:|---|---:|---:|---:|
| `rmt_storage` | `rmt_storage-android-runtime` | `9999` | `1000` | `1000,3010` | `2` | `1` | `1` |
| `tftp_server` | `tftp_server-android-runtime` | `2903` | `2903` | `1000,2903,2904,3010` | `2` | `1` | `1` |

Capability setup succeeded for both `CAP_NET_BIND_SERVICE` and
`CAP_BLOCK_SUSPEND`:

```text
wifi_hal_composite_child.rmt_storage.ambient_raise.cap10.ok=1
wifi_hal_composite_child.rmt_storage.ambient_raise.cap36.ok=1
wifi_hal_composite_child.tftp_server.ambient_raise.cap10.ok=1
wifi_hal_composite_child.tftp_server.ambient_raise.cap36.ok=1
```

## Live Evidence

`IWifi.start()` still reaches the HAL and returns a decoded HAL error:

```text
iwifi_start.start.reply.status_name=OK
iwifi_start.start.wifi_status.decoded=1
iwifi_start.start.wifi_status.code=9
iwifi_start.start.wifi_status.name=ERROR_UNKNOWN
iwifi_start.result=transaction-failed
```

QRTR/WLFW readiness is unchanged from V569:

```text
qipcrtr_sockets: before=0 after_spawn=0 window=0 cleanup=0
qrtr_readback_service_events=0
qmi_server_connected=0
qrtr_modem_readiness=0
bdf_regdb=0
bdf_bdwlan=0
wlan_fw_ready=0
```

Cleanup remained safe:

```text
wifi_companion_hal_order.all_postflight_safe=1
process residue: none
wifi netdev: none
```

## Interpretation

V570 proves the previous root identity mismatch was real and is now repaired in
helper v94. It also proves that this identity repair alone is not enough to make
WLFW visible or make `IWifi.start()` succeed.

The next blocker is therefore not raw hwbinder transport, `IWifi` handle
lifetime, SELinux domain assignment, `/data/vendor/wifi` directory creation, or
the rmt/tftp UID/GID/cap contract. The blocker remains earlier in the
QRTR/modem readiness chain, likely around native timing/order, service-notifier
state, modem-side QRTR availability, or a missing Android companion dependency
that Android boot provides before the Wi-Fi HAL starts.

## Next Gate

V571 should compare Android and native QRTR/modem readiness with exact timing
and process-state focus:

1. Android boot: capture `/proc/net/qrtr`, `QIPCRTR` sockets, service-notifier
   markers, modem readiness logs, and companion process readiness before
   `IWifi.start()`.
2. Native init: run the same bounded companion window and capture the same
   surfaces at before/after/window/cleanup phases.
3. Classify whether the missing surface is QRTR namespace, service-notifier,
   modem remoteproc/subsystem readiness, or another companion process before
   retrying Wi-Fi HAL start.

Wi-Fi objective remains incomplete until native init connects to Wi-Fi and
external ping passes.
