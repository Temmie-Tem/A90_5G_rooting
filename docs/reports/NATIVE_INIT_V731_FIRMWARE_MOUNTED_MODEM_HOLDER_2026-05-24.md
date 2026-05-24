# Native Init V731 Firmware-mounted Modem Holder Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_firmware_mounted_modem_holder_v731.py`
- evidence: `tmp/wifi/v731-firmware-mounted-modem-holder/`
- latest pointer: `tmp/wifi/latest-v731-firmware-mounted-modem-holder.txt`
- decision: `v731-firmware-mounted-modem-holder-qrtr-rx-pass`
- status: `pass`

## Scope Result

V731 mounted the Android firmware partitions read-only, opened and held only
`subsys_modem`, observed modem readiness markers, and rebooted as cleanup.

It did not create/open `esoc0`, write subsystem state, load/unload modules,
start daemon/service-manager/Wi-Fi HAL, run `qcwlanstate`, scan/connect, use
credentials, run DHCP, change routes, external ping, write a boot image, or
write a partition.

## Key Results

| check | result |
| --- | --- |
| native baseline | V724 healthy |
| V730 routing | pass; `v730-global-firmware-mounted-modem-holder-required` |
| firmware mounts | pass; `/vendor/firmware_mnt` and `/vendor/firmware-modem` mounted read-only |
| modem blob visibility | pass; `/vendor/firmware-modem/image/modem.b00` visible |
| `subsys_modem` holder | pass; holder opened |
| `mss` state | `OFFLINING -> ONLINE -> ONLINE` |
| `mdm3` state | `OFFLINING -> OFFLINING -> OFFLINING` |
| crash counts | stable; `mss 0 -> 0`, `mdm3 0 -> 0` |
| QRTR RX | pass; `qrtr: Modem QMI Readiness RX` observed |
| QRTR TX / `sysmon-qmi` | not yet; no lower companion in V731 |
| kernel warning markers | pass; `0` |
| reboot cleanup | pass; V724 native returned healthy in `32.342s` |

## Evidence Summary

Firmware and holder:

```text
mounted_hits={"/vendor/firmware_mnt": true, "/vendor/firmware-modem": true}
modem_blob_visible={"/vendor/firmware-modem/image/modem.b00": true}
holder_opened=true
```

State movement:

```text
mss:  OFFLINING -> ONLINE -> ONLINE
mdm3: OFFLINING -> OFFLINING -> OFFLINING
```

Dmesg marker:

```text
[ 5013.890597] ... qrtr: Modem QMI Readiness RX cmd:0x2 node[0x0]
```

Guardrails:

```text
firmware_mounts_executed=True
subsys_modem_open_attempted=True
subsys_modem_opened=True
esoc0_open_executed=False
daemon_or_hal_start_executed=False
wifi_bringup_executed=False
external_ping_executed=False
```

Post-run cleanup:

```text
version_seen=True
status_healthy=True
init: A90 Linux init 0.9.68 (v724)
selftest: pass=11 warn=1 fail=0
```

Post-run `/proc/mounts` check returned no `/vendor/firmware_mnt`,
`/vendor/firmware-modem`, or `/firmware` mount entries.

## Interpretation

V731 confirms the V730 routing: the current V724 build can still reproduce the
safe lower modem prerequisite when Android-style firmware mount parity is
present. The no-firmware V729 open-pending result was not a new `mdm_helper`
blocker; it was the expected behavior without visible modem firmware.

The remaining lower gap is now the same as the earlier V596 boundary:

```text
firmware-mounted subsys_modem holder
  -> mss ONLINE
  -> QRTR RX
  -> missing QRTR TX / sysmon-qmi / service-notifier / WLFW / BDF / wlan0
```

Therefore the next useful live gate is lower companion start-only inside the
firmware-mounted holder window. Wi-Fi scan/connect and the supplied credential
must remain blocked until the lower companion restores QRTR TX/`sysmon-qmi` and
later WLAN markers.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_firmware_mounted_modem_holder_v731.py

python3 scripts/revalidation/native_wifi_firmware_mounted_modem_holder_v731.py \
  --out-dir tmp/wifi/v731-firmware-mounted-modem-holder-plan plan

python3 scripts/revalidation/native_wifi_firmware_mounted_modem_holder_v731.py \
  --out-dir tmp/wifi/v731-firmware-mounted-modem-holder run

python3 scripts/revalidation/a90ctl.py --timeout 20 status

python3 scripts/revalidation/a90ctl.py --timeout 20 cat /proc/mounts \
  | rg '/vendor/firmware_mnt|/vendor/firmware-modem| /firmware ' || true
```

Result: pass.

## Next Gate

V732 should add the lower companion stack under the same constraints:

1. mount firmware partitions read-only;
2. hold only `subsys_modem`;
3. start only lower companion services needed to reach QRTR TX/`sysmon-qmi`;
4. avoid `esoc0`, service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP,
   routes, and external ping;
5. reboot cleanup and classify whether the next blocker moves to
   service-notifier/WLFW/BDF/`wlan0`.
