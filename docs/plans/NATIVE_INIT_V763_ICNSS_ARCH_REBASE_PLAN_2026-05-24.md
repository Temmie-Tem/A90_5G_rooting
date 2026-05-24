# Native Init V763 ICNSS Architecture Rebase Plan

- date: `2026-05-24 KST`
- scope: host-only architecture correction before kernel log instrumentation
- input: staged Samsung OSRC `Kernel.tar.gz` plus prior native/Android ICNSS evidence

## Goal

Before planning instrumentation, correct the target model from CNSS2/MHI to the
live SM-A908N ICNSS/QCACLD SNOC path. The next instrumentation plan must target
WLFW service `69` arrival and ICNSS driver-probe handoff, not CNSS2 MHI power-up.

## Basis Evidence

- source archive: `kernel_build/SM-A908N_KOR_12_Opensource/Kernel.tar.gz`
- source verifier evidence: `tmp/wifi/v760-source-staging/manifest.json`
- live ICNSS evidence:
  - `tmp/wifi/v711-icnss-edge-readonly-live/native/dmesg-focus-tail.txt`
  - `tmp/wifi/v711-icnss-edge-readonly-live/native/focus-sysfs.txt`
  - `tmp/wifi/v744-v122-cnss-only-comparison/native/cnss2-driver-ls-before.txt`
- source paths:
  - `drivers/soc/qcom/icnss.c`
  - `drivers/soc/qcom/icnss_qmi.c`
  - `drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/pld/src/pld_snoc.c`
  - `drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/hdd/src/wlan_hdd_main.c`
  - `drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/hdd/src/wlan_hdd_driver_ops.c`

## Corrected Chain

```text
mdm3 OFFLINING
  -> wlan_pd not booted inside modem MPSS
  -> WLFW service 69 absent on QRTR
  -> icnss_qmi wlfw_new_server() not called
  -> icnss_call_driver_probe() not called
  -> pld_snoc_probe() / wlan_hdd_probe() / hdd_wlan_startup() not reached
  -> wlan: driver loaded / BDF / FW-ready / wlan0 absent
```

## Instrumentation Targets

V764 should plan source patch points around:

- `drivers/soc/qcom/icnss_qmi.c`
  - `icnss_register_fw_service()`
  - `wlfw_new_server()`
- `drivers/soc/qcom/icnss.c`
  - `icnss_call_driver_probe()`
  - `__icnss_register_driver()`
- `drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/pld/src/pld_snoc.c`
  - `pld_snoc_register_driver()`
  - `pld_snoc_probe()`
- `drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/hdd/src/wlan_hdd_main.c`
  - `__hdd_module_init()`
  - `hdd_wlan_startup()`
- `drivers/net/wireless/qualcomm/wcn39xx/qcacld-3.0/core/hdd/src/wlan_hdd_driver_ops.c`
  - `wlan_hdd_register_driver()`

## Forbidden

- no source patch in V763
- no kernel build
- no boot image or partition write
- no device command
- no ICNSS bind/unbind, `driver_override`, module load/unload, `boot_wlan`, or
  `qcwlanstate`
- no service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or
  external ping

## Success Criteria

- Record the ICNSS architecture correction.
- Correct V760 target verification groups to ICNSS/QCACLD.
- Select V764 kernel log instrumentation planning against ICNSS/QMI/WLFW and
  PLD-SNOC callbacks.
