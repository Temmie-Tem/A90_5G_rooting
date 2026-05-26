# Native Init V1093 PM Post-Provider Surface Report

## Summary

V1093 passed. The current PM observer path can reproduce
`vendor.qcom.PeripheralManager` registration, but the lower Wi-Fi surface still
does not advance in that provider-positive window.

Decision:

```text
v1093-provider-positive-mdm3-still-not-online
```

This closes the PM provider registration blocker as a cause of the current
native Wi-Fi gap. The remaining blocker is below the provider layer: mdm3/eSoC,
WLAN-PD, and WLFW service publication.

## Evidence

| item | path |
| --- | --- |
| helper source | `stage3/linux_init/helpers/a90_android_execns_probe.c` |
| deploy wrapper | `scripts/revalidation/wifi_execns_helper_v203_deploy_preflight.py` |
| live wrapper | `scripts/revalidation/native_wifi_pm_post_provider_surface_live_v1093.py` |
| helper artifact | `tmp/wifi/v1093-execns-helper-v203-build/a90_android_execns_probe` |
| deploy evidence | `tmp/wifi/v1093-execns-helper-v203-deploy/manifest.json` |
| live evidence | `tmp/wifi/v1093-pm-post-provider-surface-live/manifest.json` |
| V490 evidence | `tmp/wifi/v490-native-selinux-policy-load-proof/manifest.json` |

## Result

```text
helper: a90_android_execns_probe v203
sha256: 3b8d0bd04cf0c4519d907833acdd8aac88c2db61f388872342ee35a91de5b594
vndservicemanager_ready: True
vndservice_provider_seen: True
post_provider_surface_present: True
post_provider_mdm3_state: OFFLINING
post_provider_wlfw_service69_seen: False
wifi_hal_start_executed: False
wifi_bringup_executed: False
external_ping_executed: False
```

The provider query returned:

```text
wifi_vndservice_query.pm_observer_after_per_mgr_probe.result=query-exit-zero
wifi_vndservice_query.pm_observer_after_per_mgr_probe.vendor_qcom_peripheral_manager_seen=1
```

The post-provider lower surface returned:

```text
pm_service_trigger_observer.post_provider_surface.after_provider.mdm3_state=OFFLINING
pm_service_trigger_observer.post_provider_surface.after_provider.mdm3_crash_count=0
pm_service_trigger_observer.post_provider_surface.after_provider.mdm3_firmware_name=esoc0
pm_service_trigger_observer.post_provider_surface.after_provider.qcwlanstate_exists=0
pm_service_trigger_observer.post_provider_surface.after_provider.wlan0_exists=0
```

QRTR readback for services `69`, `74`, and `180` completed but saw no service
events in the provider-positive window.

## Implementation Notes

- `a90_android_execns_probe v203` adds a post-provider lower-surface snapshot to
  the existing PM observer.
- The PM observer mode now permits QRTR nameservice readback while continuing to
  reject daemon, HAL, scan/connect, eSoC, and Wi-Fi bring-up proof flags.
- The V1093 runner writes a device-side shell script and full helper transcript
  under `/cache/a90-runtime/v1093/`, returning only compact key lines to avoid
  the tcpctl output cap that affected V1092.

## Safety

- No Wi-Fi HAL, scan/connect/link-up, DHCP, route, or external ping executed.
- No CNSS daemon or `mdm_helper` executed.
- No eSoC open/ioctl, GPIO write, partition write, flash, or reboot executed.
- QRTR readback used nameservice lookup/readback only and sent no QMI payload.
- Device remained healthy: `selftest` reported `fail=0`; NCM/tcpctl remained up.

## Interpretation

The provider-positive setup is not sufficient to advance mdm3 or publish WLFW.
That means the next useful work is not more `pm-service` startup tracing. The
next gate should classify the lower MDM3/eSoC trigger still missing from native
init.

Candidate next checks:

1. Compare V1093 provider-positive window against Android-good PM/eSoC timing.
2. Revisit safe MDM3/eSoC trigger surfaces that do not raw-open
   `/dev/subsys_esoc0`.
3. Keep PM provider proof as a precondition only; do not expand to Wi-Fi HAL or
   scan/connect until mdm3/WLFW moves.

## Validation

Executed:

```bash
scripts/revalidation/build_android_execns_probe_helper.sh tmp/wifi/v1093-execns-helper-v203-build/a90_android_execns_probe
python3 -m py_compile scripts/revalidation/wifi_execns_helper_v203_deploy_preflight.py scripts/revalidation/native_wifi_pm_post_provider_surface_live_v1093.py
python3 scripts/revalidation/wifi_execns_helper_v203_deploy_preflight.py --approval-phrase "approve v1093 deploy execns helper v203 only; no daemon start and no Wi-Fi bring-up" --apply --assume-yes run
python3 scripts/revalidation/native_selinux_policy_load_proof_v490.py --helper-sha256 3b8d0bd04cf0c4519d907833acdd8aac88c2db61f388872342ee35a91de5b594 --approval-phrase "approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up" --apply --assume-yes run
python3 scripts/revalidation/native_wifi_pm_post_provider_surface_live_v1093.py --helper-sha256 3b8d0bd04cf0c4519d907833acdd8aac88c2db61f388872342ee35a91de5b594 --helper-marker "a90_android_execns_probe v203" --local-helper tmp/wifi/v1093-execns-helper-v203-build/a90_android_execns_probe --helper-timeout-sec 10 --toybox-timeout-sec 36 --allow-mountsystem-ro --allow-selinuxfs-mount --allow-pm-service-trigger-observer --allow-cleanup-reboot --assume-yes run
```

Result:

```text
decision: v1093-provider-positive-mdm3-still-not-online
pass: True
```
