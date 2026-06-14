# Native Init V619 Android-Order Post-Sysmon Observer Live Report

- date: `2026-05-23 KST`
- helper: `a90_android_execns_probe v104`
- runner: `scripts/revalidation/native_wifi_android_order_post_sysmon_observer_v619.py`
- deploy evidence: `tmp/wifi/v619-execns-helper-v104-deploy-run-serial-safe/`
- V401 evidence: `tmp/wifi/v619-v401-selinuxfs-mount-run/`
- V490 evidence: `tmp/wifi/v619-v490-current-run/`
- live evidence: `tmp/wifi/v619-android-order-post-sysmon-observer-run/`
- decision: `v619-unsafe-kernel-warning`
- status: failed safe; no Wi-Fi bring-up attempted; do not repeat direct
  DSP boot-node observer from this state

## Scope

V619 tested the V618 ordering hypothesis only:

```text
qrtr_ns -> pd_mapper -> rmt_storage -> tftp_server
```

The live run did not start CNSS, service-manager, Wi-Fi HAL, `wificond`,
supplicant, hostapd, scan/connect/link-up, credentials, DHCP, route changes, or
external ping. It reused the V615 lower-surface model: firmware mounts,
ADSP/CDSP/SLPI boot-node writes, `subsys_modem` holder, and reboot cleanup.

## Preconditions

| item | result |
| --- | --- |
| helper v104 deploy | serial deploy succeeded; remote SHA `f811c18d1a9af92f5ca9fadcfd4dbd94593318240744a0c86d0419280bbea019` verified |
| V401 SELinuxfs mount | `toybox-selinuxfs-mount-live-executor-run-pass` |
| V490 policy load | `v490-selinux-policy-load-proof-pass` |
| V619 preflight | `v619-android-order-post-sysmon-observer-preflight-ready` |
| native cleanup after run | rebooted back to `A90 Linux init 0.9.61 (v319)`, `selftest fail=0` |

## Result

The helper contract was honored:

```text
observed_order: qrtr_ns,pd_mapper,rmt_storage,tftp_server
child_started: 4
all_observable: 1
all_postflight_safe: 1
service_manager: 0
wifi_hal: 0
scan_connect_linkup: 0
external_ping: 0
qmi_payload: 0
```

Lower modem/DSP progress was reproduced:

| marker | count |
| --- | ---: |
| `qrtr_rx` | `1` |
| `qrtr_tx` | `1` |
| `sysmon_qmi` | `4` |
| `adsp_sysmon` | `1` |
| `cdsp_sysmon` | `1` |
| `slpi_sysmon` | `1` |

But the blocker did not move:

| marker | count |
| --- | ---: |
| `service_notifier` | `0` |
| `wlan_pd` | `0` |
| `qmi_server_connected` | `0` |
| `wlfw` | `0` |
| `bdf` | `0` |
| `wlan_fw_ready` | `0` |
| `wlan0` | `0` |

Subsystem state remained split:

```text
mss_after_companion: ONLINE
mdm3_after_companion: OFFLINING
```

## Safety Finding

The run emitted `21` kernel warnings on the same class as V615:

```text
pm_qos_add_request() called for already added request
WARNING: CPU ... at kernel/power/qos.c:616 pm_qos_add_request+0x34/0x288
Call trace includes msm_asoc_machine_probe
```

This means Android-order lower companion startup is not the missing trigger, and
the direct ADSP/CDSP/SLPI boot-node path remains unsafe to repeat. The warning
appears tied to deferred audio/DSP probe side effects rather than the lower
companion process order itself.

## Interpretation

V619 falsifies the narrow V618 hypothesis:

```text
pd_mapper-before-rmt/tftp alone does not publish service-notifier 180/74
```

The current native gap is still:

```text
sibling sysmon-qmi present
service-locator path present in previous native evidence
service-notifier 180/74 absent
mdm3 remains OFFLINING
```

The next useful work is not a CNSS/HAL retry and not another direct DSP
boot-node live attempt. The next gate should be host-only: compare Android and
native evidence around DSP boot, `mdm3`, audio deferred probe, and vendor init
triggers to identify a safer pre-service-notifier trigger path.

## Next Gate

Proceed to V620 as a host-only classifier:

1. compare Android/V619/V615 dmesg around ADSP/CDSP/SLPI boot and
   `pm_qos_add_request`;
2. compare Android `mdm3` transition timing with native `mdm3=OFFLINING`;
3. inspect `vendor.mdm_launcher`, `vendor.mdm_helper`, `wcnss-service`, and
   `boot_wlan` timing without executing them;
4. select a next bounded live gate only if it avoids repeating the direct
   boot-node warning path.

