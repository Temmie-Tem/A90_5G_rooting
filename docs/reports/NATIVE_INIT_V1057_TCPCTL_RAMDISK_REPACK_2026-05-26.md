# Native Init V1057 TCPCTL Ramdisk Repack Report

Date: `2026-05-26`

## Summary

V724 native init was bootable, but its ramdisk did not contain `/bin/a90_tcpctl` even though `a90_netservice` hardcodes that path for the NCM TCP control listener.  This cycle made the v724 boot image reproducibly include the static `a90_tcpctl` helper, flashed the rebuilt image, and verified NCM/TCP control on hardware.

## Change

- Updated `scripts/revalidation/build_native_init_boot_v724.py` so `RAMDISK_HELPERS` includes `bin/a90_tcpctl` from `external_tools/userland/bin/a90_tcpctl-aarch64-static`.
- Rebuilt `a90_tcpctl` with `scripts/revalidation/build_tcpctl_helper.sh`.
- Rebuilt `stage3/ramdisk_v724.cpio` and `stage3/boot_linux_v724.img` with the v724 builder.

## Build Evidence

```text
a90_tcpctl_sha256=271e35e04fcc6fd996015b2081d9b699f27dd277bfb09ebe74e61c010003f232
a90_tcpctl_size=597920
init_sha256=c33ba75518f36fe2da426a0dd99542cd0c619aa6d5e30e9a8c3e1063b248f22e
ramdisk_sha256=205aa7106a91991bd91dec3212bf75432e763773734ab46ed7a90b810e45a2c6
boot_sha256=ae01fa106391756dae12fc9a6c9f57d4111b2180c82cdcfe3691ee31f7542adc
```

Local verification:

```text
stage3/ramdisk_v724/bin/a90_tcpctl: ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped
cpio_entry=bin/a90_tcpctl
boot_strings=/bin/a90_tcpctl, a90_tcpctl v1 ready, A90 Linux init 0.9.68 (v724)
```

## Flash Evidence

Command:

```bash
python3 ./scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v724.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.68 (v724)" \
  --verify-protocol cmdv1 \
  --bridge-timeout 240 \
  --recovery-timeout 240
```

Result:

```text
local image sha256: ae01fa106391756dae12fc9a6c9f57d4111b2180c82cdcfe3691ee31f7542adc
remote image sha256: ae01fa106391756dae12fc9a6c9f57d4111b2180c82cdcfe3691ee31f7542adc
boot block prefix sha256: ae01fa106391756dae12fc9a6c9f57d4111b2180c82cdcfe3691ee31f7542adc
cmdv1 verify passed: version/status rc=0 status=ok
```

Post-boot health:

```text
version=A90 Linux init 0.9.68 (v724)
selftest=pass=11 warn=1 fail=0
netservice_helpers=usbnet=yes tcpctl=yes toybox=yes
```

## Live NCM/TCP Evidence

After current-boot `netservice start`, the device reported:

```text
netservice: ncm0=present tcpctl=running
netservice: if=ncm0 ip=192.168.7.2/255.255.255.0 tcp=2325 bind=192.168.7.2 idle=3600s max_clients=0 auth=required
```

Host-side NetworkManager initially left the new NCM interface in DHCP mode.  The active profile was set to static `192.168.7.1/24`, then validation passed:

```text
host_if=enx56e600ee453b
host_ip=192.168.7.1/24
ping 192.168.7.2: 3 transmitted, 3 received, 0% packet loss
nc 192.168.7.2 2325: succeeded
tcpctl ping: pong / OK
tcpctl version: a90_tcpctl v1 / OK
tcpctl status: listen bind=192.168.7.2 port=2325 auth=required / OK
```

## Outcome

- PASS: v724 ramdisk now contains `/bin/a90_tcpctl` through the reproducible builder.
- PASS: rebuilt boot image flashed with readback hash parity.
- PASS: native init rebooted and `cmdv1 version/status` passed.
- PASS: current-boot NCM and authenticated TCP control path worked over `192.168.7.2:2325`.

## Remaining Work

This patch restores the missing TCP helper. It does not add PID1 auto-restart for `a90_usbnet` or `a90_tcpctl`, and it does not solve generic NCM disconnect causes. The next network hardening loop should add bounded PID1 supervision or a netservice watchdog with clear restart counters and logs.
