# Native Init V1059 Firmware Mount Refresh Report

Date: `2026-05-27`

## Summary

V1059 acted on the V1058 blocker by reusing the existing bounded V584 firmware/modem mount proof against the current v724 boot.  It verified that the native init environment can mount the Android `apnhlos` and `modem` firmware partitions read-only into the global namespace, expose the expected firmware mount targets, and cleanly unmount them afterward.

Decision from the runner: `v584-firmware-modem-mount-proof-no-readiness-delta`

This is a PASS for the firmware-mount prerequisite refresh.  Mount parity alone does not publish QRTR/modem/WLFW markers, so the next gate should combine mount parity with a bounded companion start-only path while still blocking `qcwlanstate`, `IWifi`, scan/connect, DHCP/routes, credentials, and external ping.

## Evidence

Private evidence directory:

```text
tmp/wifi/v1059-firmware-mount-refresh/
```

Manifest:

```text
tmp/wifi/v1059-firmware-mount-refresh/manifest.json
```

## Preflight

| Check | Result |
| --- | --- |
| native health | `True` |
| vfat support | `True` |
| `apnhlos` partition | `sda20`, major `259`, minor `4` |
| `modem` partition | `sda21`, major `259`, minor `5` |
| pre-existing firmware mounts | none |
| `/vendor` symlink shim | not required |

## Mount Proof

Read-only mount commands succeeded:

```text
mkdir-proof-base:ok:0
mkdir-vendor:ok:0
mkdir-vendor-firmware_mnt:ok:0
mkdir-vendor-firmware-modem:ok:0
mknodb-apnhlos:ok:0
stat-node-apnhlos:ok:0
mount-apnhlos:ok:0
mknodb-modem:ok:0
stat-node-modem:ok:0
mount-modem:ok:0
```

Mounted targets during proof:

```text
/vendor/firmware_mnt: true
/vendor/firmware-modem: true
```

Cleanup succeeded:

```text
cleanup-umount-vendor-firmware-modem:ok:0
cleanup-umount-vendor-firmware_mnt:ok:0
cleanup-rmdir-vendor-firmware-modem:ok:0
cleanup-rmdir-vendor-firmware-mnt:ok:0
cleanup-rmdir-vendor:ok:0
cleanup-rm-proof-nodes:ok:0
cleanup-rmdir-proof-base:ok:0
```

Post-cleanup state:

```text
post_mount_hits={"/vendor": false, "/vendor/firmware_mnt": false, "/vendor/firmware-modem": false}
post_healthy=true
selftest=pass=11 warn=1 fail=0
```

## Marker Result

No lower readiness marker moved from mount-only activity:

```text
qrtr_modem_readiness_rx=0
qrtr_modem_readiness_tx=0
sysmon_qmi=0
service_notifier=0
wlan_pd=0
qmi_server_connected=0
wlfw=0
```

This is expected: read-only mount parity supplies firmware visibility but does not itself start PM actors, companion daemons, CNSS, or WLFW.

## Guardrails

- No Wi-Fi credentials used.
- No scan/connect/link-up, DHCP/routes, or external ping attempted.
- No service-manager, Wi-Fi HAL, actor start, daemon start, `qcwlanstate`, `IWifi`, module load, eSoC ioctl, modem/eSoC device-node open, sysfs/debugfs write, firmware mutation, boot image write, partition write, or reboot.
- The only device mutation was bounded read-only mount/unmount of firmware partitions plus temporary proof nodes under `/tmp`.

## Next

V1060 should combine the now-validated firmware mount prerequisite with a bounded companion start-only observer.  The gate should verify firmware mounts and blob visibility, then start only the lower companion set needed to observe QRTR/modem/WLFW readiness.  It should still block service-manager widening, Wi-Fi HAL start, scan/connect, credentials, DHCP/routes, and external ping until WLFW/BDF/wlan surface evidence exists.
