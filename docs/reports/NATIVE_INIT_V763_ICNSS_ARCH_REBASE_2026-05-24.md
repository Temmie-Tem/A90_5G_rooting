# Native Init V763 ICNSS Architecture Rebase Report

- date: `2026-05-24 KST`
- status: `pass`
- decision: `v763-icnss-architecture-rebased`
- scope: host-only correction before instrumentation planning

## Summary

The user-supplied architecture correction is consistent with the staged Samsung
OSRC source and prior live evidence. The live SM-A908N path is ICNSS/QCACLD
SNOC, not the CNSS2 PCIe/MHI model.

Confirmed facts:

```text
live platform node: 18800000.qcom,icnss
live driver: /sys/bus/platform/drivers/icnss
cnss2 platform driver dir: absent in native evidence
source ICNSS QMI: drivers/soc/qcom/icnss_qmi.c
source ICNSS core: drivers/soc/qcom/icnss.c
source QCACLD PLD SNOC: drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/pld/src/pld_snoc.c
source QCACLD HDD: drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/hdd/src/
```

V760 was corrected so source target verification now requires:

```text
qcacld_hdd_main
qcacld_hdd_driver_ops
qcacld_pld_snoc
icnss_core
icnss_qmi
```

The verifier reports `v760-source-targets-verified` with no missing target
groups.

## Interpretation

The next useful kernel instrumentation is not around `drivers/net/wireless/cnss2`
or MHI. It should instrument the ICNSS QMI/WLFW service-arrival edge and the
QCACLD PLD-SNOC/HDD probe handoff.

The core question is whether native ever reaches:

```text
WLFW service 69 on QRTR
  -> wlfw_new_server()
  -> icnss_call_driver_probe()
  -> pld_snoc_probe()
  -> wlan_hdd_probe() / hdd_wlan_startup()
```

Current evidence says native reaches HDD module entry and `qcwlanstate`
creation, but not driver-loaded, ICNSS-QMI, BDF, FW-ready, wiphy, or `wlan0`.

## Safety Result

V763 was host-only. It executed no source patch, no source extraction, no kernel
build, no boot image or partition write, no device command, no ICNSS bind/unbind,
no `boot_wlan`, no `qcwlanstate`, no service-manager or Wi-Fi HAL start, no
scan/connect, no credential use, no DHCP/routes, and no external ping.

## Next Gate

V764 should plan minimal source log instrumentation at ICNSS/QMI/WLFW,
PLD-SNOC, and HDD handoff points. Patching, building, flashing, and live boot
handoff remain separate approval gates.

## Evidence

- `tmp/wifi/v760-source-staging/manifest.json`
- `tmp/wifi/v711-icnss-edge-readonly-live/native/dmesg-focus-tail.txt`
- `tmp/wifi/v711-icnss-edge-readonly-live/native/focus-sysfs.txt`
- `tmp/wifi/v744-v122-cnss-only-comparison/native/cnss2-driver-ls-before.txt`
