# Native Init V712 Execns Helper v121 ICNSS Edge Prep Report

- date: `2026-05-24 KST`
- status: `prep-pass`; Wi-Fi external ping is **not** complete
- helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- helper artifact: `tmp/wifi/v712-execns-helper-v121-build/a90_android_execns_probe`
- helper sha256: `547232ddb352740bb7a7f1d0f9116162584e34a536b9d9b77869ed8d838e7c89`
- deploy preflight evidence: `tmp/wifi/v712-execns-helper-v121-deploy-preflight-current/`

## Scope

V712 prep changed helper observability and host-side wrappers only. It did not
start daemons, start service-manager, start Wi-Fi HAL, scan/connect, use
credentials, run DHCP, change routes, ping externally, write sysfs/debugfs, or
write boot images/partitions.

The only live device action was deploy preflight/readiness checking; no helper
install was executed in this prep unit.

## Helper Build

Build command:

```bash
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v712-execns-helper-v121-build/a90_android_execns_probe
```

Result:

| item | value |
| --- | --- |
| static AArch64 ELF | pass |
| stripped size | `969K` |
| dynamic section | absent |
| helper marker | `a90_android_execns_probe v121` |
| sha256 | `547232ddb352740bb7a7f1d0f9116162584e34a536b9d9b77869ed8d838e7c89` |

Static strings contract passed for the v121 marker, provider-first mode, and
ICNSS edge capture markers.

## Added Capture Surface

Helper v121 extends the existing `cnss2_focus` capture at `service74_open` and
`window` phases with:

- ICNSS driver-link, QCA6390 driver-link, `wlan0`, and `shutdown_wlan` path
  status;
- MHI, PCI, RPMSG, ICNSS module, WLAN module, ICNSS power, and QCA6390 power
  directory snapshots;
- ICNSS `quirks` and `dynamic_feature_mask` values;
- WLAN `fwpath`, `con_mode`, `country_code`, and `prealloc_disabled` values;
- bounded `/proc/interrupts` capture.

## Wrapper Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_provider_first_icnss_edge_v712.py \
  scripts/revalidation/native_wifi_provider_first_icnss_edge_orchestrator_v712.py \
  scripts/revalidation/wifi_execns_helper_v121_deploy_preflight.py

python3 scripts/revalidation/native_wifi_provider_first_icnss_edge_v712.py \
  --out-dir tmp/wifi/v712-provider-first-icnss-edge-plan-check-2 \
  --helper tmp/wifi/v712-execns-helper-v121-build/a90_android_execns_probe \
  --helper-sha256 547232ddb352740bb7a7f1d0f9116162584e34a536b9d9b77869ed8d838e7c89 \
  --helper-marker 'a90_android_execns_probe v121' \
  plan

python3 scripts/revalidation/native_wifi_provider_first_icnss_edge_orchestrator_v712.py \
  --out-dir tmp/wifi/v712-provider-first-icnss-edge-orchestrator-plan-check-2 \
  plan

python3 scripts/revalidation/wifi_execns_helper_v121_deploy_preflight.py \
  --out-dir tmp/wifi/v712-execns-helper-v121-deploy-plan-check-2 \
  plan
```

All passed.

## Deploy Preflight

Readiness preflight:

```bash
python3 scripts/revalidation/wifi_execns_helper_v121_deploy_preflight.py \
  --out-dir tmp/wifi/v712-execns-helper-v121-deploy-preflight-current \
  preflight
```

Result:

```text
decision: execns-helper-v121-deploy-preflight-ready
pass: True
reason: preflight complete; helper v121 deploy still requires exact approval
next: deploy helper v121, then run V712 provider-first ICNSS edge proof
```

## Next Gate

Deploy helper v121, then run the V712 provider-first ICNSS edge proof. The next
live proof remains below Wi-Fi bring-up: no Wi-Fi HAL, scan/connect,
credentials, DHCP, or external ping until WLFW/BDF or `wlan0` advances.
