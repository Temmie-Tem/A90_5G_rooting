# Native Init V741 Gated MDM Helper Live Plan

- date: `2026-05-24 KST`
- helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- helper version: `a90_android_execns_probe v122`
- runner: `scripts/revalidation/native_wifi_mdm_helper_gated_live_v741.py`
- evidence target: `tmp/wifi/v741-mdm-helper-gated-live/`

## Goal

Turn the V740 host-only `mdm_helper` conclusion into a bounded live proof:

```text
firmware mounts
  -> subsys_modem holder
    -> lower companions + cnss_diag/cnss-daemon
      -> service74 gate
        -> mdm_helper start-only
          -> observe mdm3/WLAN-PD/MHI/WLFW/BDF/wlan0
```

The proof is intentionally below service-manager, Wi-Fi HAL, scan/connect,
credentials, DHCP/routes, external ping, boot writes, and partition writes.

## Scope

V741 adds one helper mode:

```text
wifi-companion-service74-gated-mdm-helper-start-only
```

This mode starts the existing lower companion stack and `cnss_diag` /
`cnss-daemon`, waits for the service `74` gate, and only then starts
`/vendor/bin/mdm_helper` with the Android init identity contract:

```text
uid=0
gid=system
groups=system,wakelock,shell
capabilities=none
```

## Explicit Non-Goals

V741 must not:

- start `servicemanager`, `hwservicemanager`, or `vndservicemanager`;
- start Wi-Fi HAL, `wificond`, supplicant, or any connect tool;
- scan, connect, use credentials, run DHCP, change routes, or external ping;
- open `esoc0`, write subsystem state, write DSP boot nodes, or load/unload
  modules;
- write a boot image, write a partition, or persist network configuration.

## Success Criteria

V741 passes as a safe proof if:

1. helper v122 exposes the new mode and the exact order
   `qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon,service74_gate,mdm_helper`;
2. V740 reference decision remains
   `v740-mdm-helper-post-notifier-gated-proof-selected`;
3. the live run executes only after the service `74` gate opens;
4. `mdm_helper` is observable and postflight-safe;
5. no forbidden HAL/connect/network action appears in helper output or manifest;
6. reboot cleanup proves the native baseline is healthy afterward.

The result is classified by whether `mdm_helper` advances any lower marker:
`mdm3`, WLAN-PD, MHI/QCA6390, WLFW/service `69`, BDF, or `wlan0`.

## Validation Commands

Static validation:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_gated_live_v741.py

mkdir -p tmp/wifi/v741-execns-helper-v122-build
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v741-execns-helper-v122-build/a90_android_execns_probe

strings tmp/wifi/v741-execns-helper-v122-build/a90_android_execns_probe | \
  rg 'a90_android_execns_probe v122|wifi-companion-service74-gated-mdm-helper-start-only|mdm_helper'

python3 scripts/revalidation/native_wifi_mdm_helper_gated_live_v741.py \
  --out-dir tmp/wifi/v741-mdm-helper-gated-live-plan plan
```

Live validation after helper v122 deployment:

```bash
python3 scripts/revalidation/native_wifi_mdm_helper_gated_live_v741.py \
  --out-dir tmp/wifi/v741-mdm-helper-gated-live run
```
