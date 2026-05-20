# Native Init V414 Static Runtime Target Classifier

Date: 2026-05-20

## Scope

V414 classifies the V413 static VINTF Wi-Fi declaration inventory into ranked
runtime target candidates.  It is host-only and reads existing V413 evidence.

This pass executed no bridge/device command, helper deploy, daemon start, Wi-Fi
HAL start, scan/connect/link-up, or Wi-Fi bring-up.

## Implementation

```text
scripts/revalidation/wifi_v414_static_runtime_target_classifier.py
```

Input:

```text
tmp/wifi/v413-vintf-live-20260520-120842/manifest.json
```

Evidence:

```text
tmp/wifi/v414-static-runtime-target-classifier-20260520-121416/
```

## Result

```text
decision: v414-static-runtime-targets-ready
pass: True
reason: ranked 33 static Wi-Fi declaration records; primary=vendor.samsung.hardware.wifi@2.0-2::ISehWifi/default
next: compare ranked static targets against V411 binderized runtime registrations after helper v27 deploy
record_count: 33
device_commands_executed: False
device_mutations: False
wifi_bringup_executed: False
```

Evidence permissions:

```text
700 tmp/wifi/v414-static-runtime-target-classifier-20260520-121416
600 tmp/wifi/v414-static-runtime-target-classifier-20260520-121416/manifest.json
600 tmp/wifi/v414-static-runtime-target-classifier-20260520-121416/summary.md
```

## Primary Target

```text
fqinstance: vendor.samsung.hardware.wifi@2.0-2::ISehWifi/default
source: /mnt/system/system/etc/vintf/compatibility_matrix.device.xml
source_kind: device-compatibility-matrix
role: declared-requirement
score: 185
reason: device-matrix, samsung-primary-wifi-package, primary-wifi-interface, default-instance
```

Runtime match set derived from the VINTF version range:

```text
vendor.samsung.hardware.wifi@2.0::ISehWifi/default
vendor.samsung.hardware.wifi@2.1::ISehWifi/default
vendor.samsung.hardware.wifi@2.2::ISehWifi/default
```

## Top Records

```text
185 vendor.samsung.hardware.wifi@2.0-2::ISehWifi/default
120 android.hardware.wifi@1.0-2::IWifi/default
120 android.hardware.wifi@1.0-3::IWifi/default
120 android.hardware.wifi@1.0-4::IWifi/default
120 android.hardware.wifi@1.3-5::IWifi/default
15  vendor.qti.hardware.wifi.hostapd@1.0-3::IHostapdVendor/default
15  vendor.qti.hardware.wifi.supplicant@2.0-3::ISupplicantVendor/default
15  vendor.qti.hardware.wifi.wifimyftm@1.0::IWifiMyFtm/default
15  vendor.samsung.hardware.wifi.hostapd@4.0::ISehHostapd/default
15  vendor.samsung.hardware.wifi.supplicant@3.0-1::ISehSupplicant/default
```

Non-primary `hostapd`, `supplicant`, `wifidisplay`, `keystore`, `offload`,
`wifilearner`, and `wifimyftm` domains are intentionally penalized because the
next question is Wi-Fi HAL runtime registration, not supplicant/hostapd bring-up.

## Interpretation

V414 gives the static comparison target for V411 runtime output.  It does not
prove runtime registration.  The required runtime evidence is still the bounded
V411 binderized `lshal` query after helper v27 deploy.

Current next live gate remains:

```text
approve v411 deploy execns helper v27 only; no daemon start and no Wi-Fi bring-up
```

After V411 runtime output exists:

1. compare V411 binderized registrations with the V414 runtime match set;
2. if the Samsung Wi-Fi HAL target is registered, plan a no-scan/no-link HIDL
   client proof;
3. if V411 still times out or does not list the target, use the V414 target set
   to design a smaller micro `hwservicemanager` query.

## References

- AOSP HIDL interfaces: <https://source.android.com/docs/core/architecture/hidl-cpp/interfaces>
- AOSP `IServiceManager.hal`: <https://android.googlesource.com/platform/system/libhidl/+/refs/heads/android12L-tests-dev/transport/manager/1.0/IServiceManager.hal>
- AOSP `hwservicemanager` implementation: <https://android.googlesource.com/platform/system/hwservicemanager/+/refs/heads/master/ServiceManager.cpp>
