# Native Init V1943 QCRIL Owner Classifier

## Summary

- Cycle: `V1943`
- Type: host-only classifier over Android PerMgrSrv QCRIL lines and V1942 vendor export
- Decision: `v1943-peripheral-manager-qcril-client-name-samsung-radio-source-lead-host-pass`
- Label: `peripheral-manager-qcril-client-name-samsung-radio-source-lead`
- Pass: `True`
- Reason: Android's QCRIL evidence is emitted by PerMgrSrv as a client-name vote before wlanmdsp; the read-only vendor export has Samsung radio HAL/rild plus pm-service/libperipheral_client, but no QTI qcrild/libqcril artifacts and no explicit wlan_pd/wlanmdsp strings in exported voter artifacts
- Evidence: `tmp/wifi/v1943-qcril-owner-classifier`

## Matrix

| area | value | detail |
| --- | --- | --- |
| Android QCRIL edge | True | PerMgrSrv-only QCRIL register/vote before wlanmdsp |
| QTI QCRIL absent | True | direct qcrild/libqcril paths stat-failed in V1942 |
| Samsung radio present | True | vendor.samsung.hardware.radio artifacts copied |
| Peripheral client present | True | pm-service plus libperipheral_client copied |
| No explicit WLAN strings | True | no wlan_pd/wlanmdsp strings in exported voter artifacts |
| No QCRIL strings | True | QCRIL appears as PerMgrSrv client name in logcat, not in copied artifacts |

## Android QCRIL Lines

| line | time | tag | message |
| --- | --- | --- | --- |
| 168 | 06-04 02:03:50.849 | PerMgrSrv | modem state: is on-line, add client QCRIL |
| 169 | 06-04 02:03:50.849 | PerMgrSrv | QCRIL registered |
| 170 | 06-04 02:03:50.849 | PerMgrSrv | SDX50M state: is off-line, add client QCRIL |
| 171 | 06-04 02:03:50.849 | PerMgrSrv | QCRIL registered |
| 172 | 06-04 02:03:50.850 | PerMgrSrv | QCRIL voting for modem |
| 174 | 06-04 02:03:50.850 | PerMgrSrv | QCRIL voting for SDX50M |

## Vendor Source Ownership

| area | value | detail |
| --- | --- | --- |
| QTI QCRIL present | none | direct qcrild/libqcril artifacts copied |
| QTI QCRIL missing | 10 | bin/qcrild, lib/libqcrilFramework.so, lib/libqcrilNr.so, lib/libril-qc-hal-qmi.so, lib/libril-qcril-hook-oem.so, lib64/libqcrilDataModule.so |
| Samsung radio HAL | 6 | lib64/vendor.samsung.hardware.radio.bridge@2.0.so, lib64/vendor.samsung.hardware.radio.bridge@2.1.so, lib64/vendor.samsung.hardware.radio.channel@2.0.so, lib64/vendor.samsung.hardware.radio@2.0.so, lib64/vendor.samsung.hardware.radio@2.1.so |
| Peripheral manager | 3 | bin/pm-service, lib/libperipheral_client.so, lib64/libperipheral_client.so |
| rild | 1 | bin/hw/rild |
| QCRIL strings | 0 | none |
| WLAN-PD strings | 0 | none |

## String Evidence

| path | keyword counts | sample |
| --- | --- | --- |
| bin/pm-service | PerMgr=1, peripheral=27, SDX50M=2, modem=2 | _ZN7android11BnInterfaceINS_18IPeripheralManagerEE10onAsBinderEv \| _ZN7android18IPeripheralManager10descriptorE \| _ZN7android18IPeripheralManagerC2Ev |
| lib64/libperipheral_client.so | PerMgr=1, peripheral=50 | _ZN7android16pm_client_unlockEPNS_23PeripheralManagerClientE \| _ZN7android18IPeripheralManager11asInterfaceERKNS_2spINS_7IBinderEEE \| _ZN7android18ServerDiedNotifierC1EPNS_23PeripheralManagerClientE |
| lib/libperipheral_client.so | PerMgr=1, peripheral=58 | _ZN7android16pm_client_unlockEPNS_23PeripheralManagerClientE \| _ZN7android18IPeripheralManager11asInterfaceERKNS_2spINS_7IBinderEEE \| _ZN7android18ServerDiedNotifierC1EPNS_23PeripheralManagerClientE |
| lib64/libril_sem.so | modem=47 | _ZN5radio13modemResetIndEiii9RIL_ErrnoPvm \| _ZN5radio28getModemActivityInfoResponseEiii9RIL_ErrnoPvm \| _ZN8sehradio11modemCapIndEiii9RIL_ErrnoPvm |
| lib64/vendor.samsung.hardware.radio@2.0.so | modem=14 | _ZN6vendor7samsung8hardware5radio4V2_022BnHwSehRadioIndication31_hidl_modemCapabilityIndicationEPN7android4hidl4base4V1_08BnHwBaseERKNS5_8hardware6ParcelEPSC_NSt3__18functionIFvRSC_EEE \| _ZN6vendor7samsung8hardware5radio4V2_022BnHwSehRadioIndication37_hidl_configModemCapabilityChangeNotiEPN7android4hidl4base4V1_08BnHwBaseERKNS5_8hardware6ParcelEPSC_NSt3__18functionIFvRSC_EEE \| _ZN6vendor7samsung8hardware5radio4V2_022BpHwSehRadioIndication25modemCapabilityIndicationEN7android8hardware5radio4V1_019RadioIndicationTypeERKNS6_8hidl_vecIhEE |
| lib64/vendor.samsung.hardware.radio@2.1.so | modem=10 | _ZN6vendor7samsung8hardware5radio4V2_022BnHwSehRadioIndication31_hidl_modemCapabilityIndicationEPN7android4hidl4base4V1_08BnHwBaseERKNS5_8hardware6ParcelEPSC_NSt3__18functionIFvRSC_EEE \| _ZN6vendor7samsung8hardware5radio4V2_022BnHwSehRadioIndication37_hidl_configModemCapabilityChangeNotiEPN7android4hidl4base4V1_08BnHwBaseERKNS5_8hardware6ParcelEPSC_NSt3__18functionIFvRSC_EEE \| _ZN6vendor7samsung8hardware5radio4V2_022BpHwSehRadioIndication31_hidl_modemCapabilityIndicationEPN7android8hardware10IInterfaceEPNS6_7details16HidlInstrumentorENS6_5radio4V1_019RadioIndicationTypeERKNS6_8hidl_vecIhEE |
| lib64/vendor.samsung.hardware.radio@2.2.so | modem=10 | _ZN6vendor7samsung8hardware5radio4V2_022BnHwSehRadioIndication31_hidl_modemCapabilityIndicationEPN7android4hidl4base4V1_08BnHwBaseERKNS5_8hardware6ParcelEPSC_NSt3__18functionIFvRSC_EEE \| _ZN6vendor7samsung8hardware5radio4V2_022BnHwSehRadioIndication37_hidl_configModemCapabilityChangeNotiEPN7android4hidl4base4V1_08BnHwBaseERKNS5_8hardware6ParcelEPSC_NSt3__18functionIFvRSC_EEE \| _ZN6vendor7samsung8hardware5radio4V2_022BpHwSehRadioIndication31_hidl_modemCapabilityIndicationEPN7android8hardware10IInterfaceEPNS6_7details16HidlInstrumentorENS6_5radio4V1_019RadioIndicationTypeERKNS6_8hidl_vecIhEE |

## Symbol Samples

| path | readelf | sample |
| --- | --- | --- |
| bin/pm-service | ok | 9: 0000000000000000     0 OBJECT  GLOBAL DEFAULT  UND _ZN7android18IPeripheralManager10descriptorE \| 10: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND _ZN7android18IPeripheralManagerC2Ev \| 11: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND _ZN7android18IPeripheralManagerD0Ev |
| lib/libperipheral_client.so | ok | 100: 00005e29     6 FUNC    GLOBAL DEFAULT   14 _ZN7android16pm_client_unlockEPNS_23PeripheralManagerClientE \| 103: 00006919   336 FUNC    GLOBAL DEFAULT   14 pm_client_unregister \| 104: 0000bb8c     4 OBJECT  GLOBAL DEFAULT   22 _ZN7android18IPeripheralManager10descriptorE |
| lib64/libperipheral_client.so | ok | 100: 0000000000006d98   304 FUNC    GLOBAL DEFAULT   14 pm_show_peripherals \| 103: 000000000000b998   256 OBJECT  GLOBAL DEFAULT   16 _ZTCN7android19BnPeripheralManagerE8_NS_7IBinderE \| 106: 000000000000b540   112 OBJECT  GLOBAL DEFAULT   16 _ZTTN7android19BnPeripheralManagerE |
| lib64/vendor.samsung.hardware.radio.bridge@2.0.so | ok | 95: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND _ZN7android8hardware7details25registerAsServiceInternalERKNS_2spINS_4hidl4base4V1_05IBaseEEERKNSt3__112basic_stringIcNSA_11char_traitsIcEENSA_9allocatorIcEEEE \| 164: 0000000000013818    16 FUNC    GLOBAL DEFAULT   14 _ZN6vendor7samsung8hardware5radio6bridge4V2_010ISehBridge5debugERKN7android8hardware11hidl_handleERKNS7_8hidl_vecINS7_11hidl_stringEEE \| 165: 0000000000025008   408 OBJECT  GLOBAL DEFAULT   16 _ZTVN6vendor7samsung8hardware5radio6bridge4V2_013BpHwSehBridgeE |
| lib64/vendor.samsung.hardware.radio.bridge@2.1.so | ok | 2: 0000000000000000     0 OBJECT  GLOBAL DEFAULT  UND _ZN6vendor7samsung8hardware5radio6bridge4V2_020ISehBridgeIndication10descriptorE \| 3: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND _ZN6vendor7samsung8hardware5radio6bridge4V2_020ISehBridgeIndication11linkToDeathERKN7android2spINS6_8hardware20hidl_death_recipientEEEm \| 4: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND _ZN6vendor7samsung8hardware5radio6bridge4V2_020ISehBridgeIndication12getDebugInfoENSt3__18functionIFvRKN7android4hidl4base4V1_09DebugInfoEEEE |
| lib64/vendor.samsung.hardware.radio.channel@2.0.so | ok | 94: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND _ZN7android8hardware7details25registerAsServiceInternalERKNS_2spINS_4hidl4base4V1_05IBaseEEERKNSt3__112basic_stringIcNSA_11char_traitsIcEENSA_9allocatorIcEEEE \| 152: 0000000000015048   164 FUNC    GLOBAL DEFAULT   14 _ZN6vendor7samsung8hardware5radio7channel4V2_019ISehChannelCallback8castFromERKN7android2spINS6_4hidl4base4V1_05IBaseEEEb \| 153: 000000000001b550    32 OBJECT  GLOBAL DEFAULT   16 _ZTTN6vendor7samsung8hardware5radio7channel4V2_019ISehChannelCallbackE |
| bin/hw/rild | ok | 5: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND RIL_register \| 6: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND RIL_register_socket \| 37: 0000000000001634    58 OBJECT  GLOBAL DEFAULT   11 RIL_SIM_SAP_DISCONNECT_IND_fields |

## Interpretation

- The V1941 `QCRIL voting for modem` evidence is not a native permission to start QCRIL; it is a `PerMgrSrv` log for a client named `QCRIL`.
- V1942 shows this vendor image does not expose the expected QTI `qcrild`/`libqcril*` artifacts on `sda29`; the available source lead is Samsung radio HAL/rild using the same peripheral-manager client interface.
- Keep the next step host-only: callgraph/disassembly of Samsung radio HAL/rild to identify which `libperipheral_client` call sequence produces the modem vote, while excluding SDX50M/eSoC/PCIe side effects.

## Inputs

- Android logcat: `tmp/wifi/v1934-android-libqmi-service69-positive-control-live-20260603-170139/android-postfs-evidence/a90-v1934-libqmi69/logcat-filtered.txt`
- V1941 report: `docs/reports/NATIVE_INIT_V1941_ANDROID_PM_VOTER_DELTA_2026-06-04.md`
- V1942 manifest: `tmp/wifi/v1942-qcril-radio-vendor-artifact-export/manifest.json`
- V1942 report: `docs/reports/NATIVE_INIT_V1942_QCRIL_RADIO_VENDOR_ARTIFACT_EXPORT_2026-06-04.md`
- V1942 vendor source: `tmp/wifi/v1942-qcril-radio-vendor-artifact-export/vendor-source`

## Safety Scope

Host-only parser. No live device command, flash, reboot, QCRIL/radio start, firmware/partition write, remount-write, `/dev/subsys_esoc0`, eSoC/PCIe/GDSC/PMIC/GPIO/regulator action, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, or restart-PD request was used.
