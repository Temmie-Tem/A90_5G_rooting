# Native Init V3341 SoftAP S3 IfType Probe Live

- Cycle: `V3341`
- Decision: `v3341-softap-s3-iftype-probe-live-wlan0-timeout`
- Init: `A90 Linux init 0.11.105 (v3341-softap-s3-iftype-probe)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3341_softap_s3_iftype_probe.img`
- Boot SHA256: `a0fe07b1f347a2212d375067c442b163b7e6cd68cb7a605ab5dce4c87082c7af`
- Source/build report: `docs/reports/NATIVE_INIT_V3341_SOFTAP_S3_IFTYPE_PROBE_SOURCE_BUILD_2026-06-28.md`

## Flash And Health

- Reconfirmed rollback images before flashing:
  - V2321: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - V2237: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - V48: `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
- Flashed only through `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Flash helper verified the local V3341 marker/SHA, wrote only the boot partition, read back the boot image, and matched the V3341 SHA256 above.
- Post-flash `version` reported `0.11.105 build=v3341-softap-s3-iftype-probe`.
- Post-flash and follow-up `selftest` stayed clean: `pass=12 warn=1 fail=0`.
- Current resident after this iteration remained V3341 with `selftest fail=0`; this was a functional-gate miss, not a boot/health regression.

## Functional Probe

Command:

```text
wifi softap iftype-probe 220000
```

Observed result:

```text
version=a90-native-wifi-softap-v2
scope=s3-ap-iftype-add-delete-probe-no-ap-start
credentials=0
ssid_psk_logged=0
config_write_attempted=0
wpa_supplicant_mode2_start_attempted=0
dhcp_server_start_attempted=0
listener_start_attempted=0
address_assign_attempted=0
server_exposure_attempted=0
wlan0_wait_timeout_ms=220000
wlan0_wait_rc=-110
wlan0_wait_elapsed_ms=220000
wlan0_present=0
ap_iftype_add_attempted=0
ap_iftype_cleanup_attempted=0
decision=softap-iftype-probe-wlan0-timeout
```

The V3341 no-start contract held: no SSID/PSK config, no `wpa_supplicant mode=2`,
no DHCP server, no listener, no AP address, and no WAN/NAT exposure. The AP-iftype
add/delete proof did not run because `wlan0` never surfaced.

## Root-Cause Evidence

V3341 did carry the V2237-style post-FW_READY trigger route far enough to reach
the WLAN firmware_class request path:

```text
post_fw_ready_boot_wlan_trigger.pre.fw_ready_processed=0
post_fw_ready_boot_wlan_trigger.final.fw_ready_processed=1
post_fw_ready_boot_wlan_trigger.write_rc=0
post_fw_ready_boot_wlan_trigger.reason=boot-wlan-write-ok
firmware_class_fallback_sampler.after_boot_wlan_trigger.preview=FIRMWARE=wlan/qca_cld/WCNSS_qcom_cfg.ini
```

The helper then repeatedly saw the QCACLD firmware request but could not source
the payload:

```text
qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.label=WCNSS_qcom_cfg_ini
qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.firmware=wlan/qca_cld/WCNSS_qcom_cfg.ini
qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.seen=1
qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.source_errno=2
qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.request_0.fed=0
qcacld_firmware_class_fallback_feeder.after_boot_wlan_trigger.timed_out=1
```

The supervisor summary ended with:

```text
wlan0_present=0
supervisor_result=helper-complete-no-wlan0
```

Current visible native paths did not expose the expected Android vendor
`wlan/qca_cld` firmware tree. Historical Android-side evidence from the Wi-Fi
lineage showed the required payloads under `/vendor/firmware/wlan/qca_cld/`
including `WCNSS_qcom_cfg.ini`, `bdwlan.bin`, and `regdb.bin`. Therefore V3341
does not yet prove AP-iftype capability; it proves the remaining blocker is the
firmware source visibility/feed path before `wlan0`.

## Next Unit

V3342 should restore a safe read-only Android vendor firmware source route for
the QCACLD firmware_class feeder, then rerun `wifi softap iftype-probe`. The
next PASS remains unchanged:

```text
wlan0_present=1
sta_supplicant.stoppable=1
decision=softap-iftype-probe-pass
ap_iftype_add_rc=0
ap_iftype_iface_created=1
ap_iftype_cleanup_ok=1
selftest fail=0
```
