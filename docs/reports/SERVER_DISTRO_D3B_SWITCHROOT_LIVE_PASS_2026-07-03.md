# Server-Distro D3B Switchroot Live Pass

- Date: `2026-07-03`
- Unit: `D3B live checked switch_root handoff`
- Decision: `server-distro-d3b-switchroot-live-pass`
- Candidate: `A90 Linux init 0.11.133 (v3372-server-distro-switchroot-stdio)`
- Candidate image SHA256: `09db071ae6bebe538d0f9c6c62f6e86b28a4b1a2a6954f1910f8d189675cc653`
- D3 source image SHA256: `6f1960eb4332e1a22d5da1c98e990352c58d80157fbe6286b53ec9fe8ebe59f7`
- Private run: `workspace/private/runs/server-distro/d3-switchroot-v3372-usrmerge-20260703T101905Z/`
- Final device state: rolled back to `v2321-usb-clean-identity-rodata`, `selftest fail=0`

## Result

D3B passed the PID1 handoff proof. The runner prepared a per-run keyed D3 image, staged it to the SD
runtime path before flashing the candidate, flashed the V3372 D3-capable native-init candidate through
`native_init_flash.py`, then invoked the gated PID1 command:

```text
switch-root-to-distro SERVER-DISTRO-D3B-SWITCHROOT /mnt/sdext/a90/runtime/debian-bookworm-arm64-d3-sysvinit-keyed.img <sha256>
```

The native-init handoff command reported both the expected SHA match and the exec marker:

```text
A90D3B exec_switch_root_now busybox=/bin/busybox root=/mnt/sdext/a90/runtime/distro-root init=/sbin/init console=reuse-stdio
```

The Debian side was observed over the NCM SSH path:

```text
A90D3_MARKER
stage=D3-sysvinit-switch-root
debian_version=12.14
pid1_comm=init
proc1_exe=/usr/sbin/init
ncm_ip=192.168.7.2
autoreboot_sec=120
userdata=untouched
dropbear_started=1
proc1_comm=init
```

That proves `switch_root` reached the SD-backed Debian rootfs and `sysvinit` became PID1. The mandatory
D3 auto-reboot then returned the device to the V3372 candidate, where `version=0.11.133` and
`selftest fail=0` were observed.

## SD Prestage

The D3 keyed image was staged on SD before the candidate flash. The host keyed image and the remote SD
image both matched:

```text
3251fcea80bffc0d35e25143786e13b023a7dd25c72d662088d268ef57aa996e
```

After the handoff, a later read from v2321 reported the SD image as
`648d7a6bc4b47106b81595c016ebad896067cd0dd3558e75adea24bc3cced8c1`. That is expected for this
proof: the image was mounted read-write by Debian firstboot and wrote runtime state. It is not a
prestage mismatch. Future clean D3B/D4 runs should continue generating a fresh per-run keyed image and
staging it before any candidate flash.

## Rollback Note

The first automated rollback attempt hit a TWRP/native recovery transition race: the candidate requested
recovery, the host saw recovery ADB, but the serial bridge disappeared before the helper completed its
`--from-native` transaction. The checked helper was then run directly from TWRP recovery against the
pinned v2321 rollback image:

```text
boot block prefix sha256: ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb
cmdv1 verify passed: selftest rc=0 status=ok fail=0
version: 0.9.285 build=v2321-usb-clean-identity-rodata
```

Post-recovery standalone checks also reported `status` with SD mounted read-write and
`selftest: pass=11 warn=1 fail=0`.

The D3B runner has been updated so rollback uses the normal `--from-native` checked-helper path first,
then falls back to the same checked helper without `--from-native` if TWRP recovery ADB is already
available. This keeps the rollback boot-only and pinned to the same v2321 SHA/version.

## Verification

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/run_d3_switchroot_handoff.py tests/test_server_distro_d3_switchroot_handoff.py`
- `PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_server_distro_d3_switchroot_handoff`
- `PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_server_distro_d3_sysvinit_rootfs`
- Final live health: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`, `selftest fail=0`

## Next

D3B is complete. D4 preflight is now unblocked, but D-public remains a separate external-exposure gate.
