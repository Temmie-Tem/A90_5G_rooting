# Native Init V762 Source Target Verification Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_source_staging_v760.py`
- run evidence: `tmp/wifi/v760-source-staging/`
- decision: `v760-source-targets-verified`
- status: `pass`

## Summary

The staged Samsung OSRC package is now usable for kernel log instrumentation
planning. The extracted top-level source directory contains `Kernel.tar.gz` and
`Platform.tar.gz`; V760 was tightened to auto-detect that nested kernel archive,
accept the actual Samsung QCACLD path, and require all target source groups
instead of passing on partial hits.

Verified source archive:

```text
kernel_build/SM-A908N_KOR_12_Opensource/Kernel.tar.gz
```

Verified target groups after the ICNSS correction:

```text
qcacld_hdd_main
qcacld_hdd_driver_ops
qcacld_pld_snoc
icnss_core
icnss_qmi
```

Resolved paths inside `Kernel.tar.gz`:

```text
./drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/hdd/src/wlan_hdd_main.c
./drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/hdd/src/wlan_hdd_driver_ops.c
./drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/pld/src/pld_snoc.c
./drivers/soc/qcom/icnss.c
./drivers/soc/qcom/icnss_qmi.c
```

## Fixes Made

- Updated `.gitignore` so `kernel_build/` keeps only tracked README/.gitkeep
  while ignoring the staged source tree.
- Updated V760 verifier to:
  - scan one-level nested archives under staged source roots;
  - accept Samsung's actual `drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0`
    QCACLD path;
  - require the live ICNSS/QCACLD target groups before reporting instrumentation
    readiness.

## Safety Result

This verification was host-only. It executed no source patch, no source
extraction, no kernel build, no boot image or partition write, no device command,
no Wi-Fi trigger, no service-manager or Wi-Fi HAL start, no scan/connect, no
credential use, no DHCP/routes, and no external ping.

## Next Gate

V763 should rebase the architecture target to ICNSS/QCACLD before V764 plans
minimal kernel log instrumentation. Patching, building, flashing, and live boot
handoff remain separate gates.

## Evidence

- `tmp/wifi/v760-source-staging/manifest.json`
- `tmp/wifi/v760-source-staging/summary.md`
- `kernel_build/README.md`
