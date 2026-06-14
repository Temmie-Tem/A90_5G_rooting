# Native Init V741 Gated MDM Helper Live Report

- date: `2026-05-24 KST`
- helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- helper version: `a90_android_execns_probe v122`
- runner: `scripts/revalidation/native_wifi_mdm_helper_gated_live_v741.py`
- plan evidence: `tmp/wifi/v741-mdm-helper-gated-live-plan/`
- decision: `v741-mdm-helper-gated-live-plan-ready`
- pass: `true`

## Summary

V741 implements the gated `mdm_helper` proof selected by V740, but the live
proof is not executed in this commit. The current committed unit is:

1. helper v122 adds the new gated mode;
2. the V741 runner checks the V740 reference, helper contract, service `74`
   gate, `mdm_helper` lifecycle, lower marker progression, forbidden actions,
   and reboot cleanup;
3. static validation and plan-mode evidence pass.

The next operational unit is helper v122 deployment followed by the bounded
V741 live run.

## Implemented Helper Contract

New mode:

```text
wifi-companion-service74-gated-mdm-helper-start-only
```

Expected helper order:

```text
qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon,service74_gate,mdm_helper
```

`mdm_helper` identity:

```text
uid=0
gid=system
groups=system,wakelock,shell
capabilities=none
```

## Key Results

| check | result |
| --- | --- |
| Python compile | pass |
| helper static build | pass; static ARM64 artifact generated |
| helper hash | `032fe43041b908577bb1a2e4b3ff7a7dfea24958169723907df5d403f811e989` |
| helper marker | pass; `a90_android_execns_probe v122` present |
| mode marker | pass; gated `mdm_helper` mode present |
| order marker | pass; service74-gated `mdm_helper` order present |
| plan runner | pass; `v741-mdm-helper-gated-live-plan-ready` |
| device commands | not executed in plan/static unit |
| Wi-Fi HAL / scan / connect / ping | not executed |

## Validation

Executed:

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

Plan output:

```text
decision: v741-mdm-helper-gated-live-plan-ready
pass: True
device_commands_executed: False
mdm_helper_start_executed: False
service_manager_start_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Safety Boundary

V741 remains below Wi-Fi bring-up. It does not use credential material, does not
start Wi-Fi HAL, does not scan/connect, does not run DHCP/routes, and does not
external ping.

## Next Gate

Deploy helper v122, then run:

```bash
python3 scripts/revalidation/native_wifi_mdm_helper_gated_live_v741.py \
  --out-dir tmp/wifi/v741-mdm-helper-gated-live run
```

Interpretation after live run:

1. if WLFW/BDF/`wlan0` appears, capture interface state before HAL/connect;
2. if only WLAN-PD/MHI/QCA progresses, classify that lower marker before
   widening scope;
3. if `mdm_helper` starts cleanly but lower markers remain absent, route away
   from `mdm_helper` and classify the remaining lower trigger.
