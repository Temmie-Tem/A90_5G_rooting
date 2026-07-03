# Server-Distro D4D Userdata Appliance Handoff

- Date: `2026-07-03`
- Decision: `server-distro-d4d-userdata-appliance-handoff-live-pass`
- Handoff command: `switch-root-to-userdata SERVER-DISTRO-D4-USERDATA-APPLIANCE userdata=appliance-root`
- Candidate used: `A90 Linux init 0.11.138 (v3381-server-distro-journaled-formatter)`
- Appliance root: `/dev/block/a90-userdata`
- Final boot resident: v2321 clean

## Result

D4D passed. The V3381 native-init handoff command switched PID1 into the populated userdata Debian
rootfs, and the host observed the appliance over USB/NCM SSH:

- Debian version `12.14`;
- `/proc/1/comm=init`;
- `/proc/1/exe=/usr/sbin/init`;
- root filesystem `/dev/block/a90-userdata` mounted as ext4 on `/`;
- SSH/dropbear reachable on the USB-local NCM path;
- appliance marker `userdata=appliance-root`;
- mandatory 120-second auto-reboot returned the device to the V3381 native-init candidate;
- final checked-helper rollback restored v2321 with `selftest fail=0`.

The D4-capable V3381 boot image was not promoted as a new resident in this unit. Promotion is a
separate decision; the device ended on the v2321 rollback baseline, while userdata remains formatted
and populated with the appliance rootfs.

## Pre-Handoff State

D4C left V3381 live with userdata mounted and populated:

```text
marker_readback=userdata=appliance-root
/mnt/a90-userdata-root/sbin/init mode=0755 size=68448
/dev/block/a90-userdata on /mnt/a90-userdata-root type ext4
candidate_status_selftest=pass=12 warn=1 fail=0
```

The mounted userdata rootfs already contained the D3 firstboot script and sysvinit handoff wiring:

```text
/etc/inittab contains si::sysinit:/etc/a90-d3-firstboot
/etc/a90-d3-firstboot reasserts ncm0=192.168.7.2/24
/etc/a90-d3-firstboot schedules autoreboot_sec=120
/etc/a90-d3-firstboot starts dropbear on 192.168.7.2:2222 when authorized_keys exists
```

A per-run SSH key was generated under `workspace/private/run/` and only the public key was installed
into the mounted userdata root:

```text
key_fingerprint=SHA256:vurftgeO2zEgnQ1a1gpsz537uu+LABRYM6FR9uSIyIA
authorized_keys=/mnt/a90-userdata-root/root/.ssh/authorized_keys
authorized_keys_mode=0600
```

Host USB/NCM reachability before handoff:

```text
host_interface=enxbe676d692161
host_ip=192.168.7.1/24
device_ip=192.168.7.2
ping_loss=0%
```

## Switch Root

The native-init command intentionally has no normal completion marker on success because PID1 is
replaced. The captured output reached `exec_switch_root_now`:

```text
A90D4 switch-ready-check target.source=partname-scan target.devname=sda33 target.dev=259:17 target.sectors=231577432 target.mounted=1
A90D4 node=exists-ok path=/dev/block/a90-userdata dev=259:17
A90D4 rootfs=already-mounted root=/mnt/a90-userdata-root
A90D4 marker=ok value=userdata=appliance-root
A90D4 appliance_init=ok path=/mnt/a90-userdata-root/sbin/init mode=755
A90D4 mount_move=/proc->/mnt/a90-userdata-root/proc ok=1
A90D4 mount_move=/sys->/mnt/a90-userdata-root/sys ok=1
A90D4 devpts=mounted path=/mnt/a90-userdata-root/dev/pts
A90D4 dev_mountpoint=0 dev_nodes=prepared root=/mnt/a90-userdata-root/dev
A90D4 exec_switch_root_now busybox=/bin/busybox root=/mnt/a90-userdata-root init=/sbin/init marker=userdata=appliance-root
SELinux: Could not open policy file <= /etc/selinux/targeted/policy/policy.33: No such file or directory
```

The SELinux policy warning did not block the handoff proof.

## SSH Appliance Proof

SSH to `root@192.168.7.2:2222` succeeded on the first attempt with the per-run key:

```text
A90D3_MARKER
stage=D3-sysvinit-switch-root
debian_version=12.14
pid1_comm=init
proc1_exe=/usr/sbin/init
ncm_ip=192.168.7.2
autoreboot_sec=120
stage=D3 sysvinit switch_root prepared
init=sysvinit-core
ssh=dropbear early by inittab sysinit, key-only, NO keys installed in artifact
ncm_ip=192.168.7.2
autoreboot_sec=120
userdata=untouched
dropbear_started=1
proc1_comm=init
proc1_exe=/usr/sbin/init
debian_version=12.14
appliance_marker=userdata=appliance-root
root_findmnt=/dev/block/a90-userdata ext4 /
root_mount_line=/dev/block/a90-userdata on / type ext4 (rw,relatime,seclabel,i_version,stripe=128,data=ordered)
ncm_addr=192.168.7.2/24
```

The `userdata=untouched` line is from the older D3 stage file copied into the rootfs; the D4 appliance
marker is the separate `appliance_marker=userdata=appliance-root` line and is the D4D acceptance marker.

## Timed Auto-Reboot Proof

The firstboot script's mandatory auto-reboot was observed:

```text
native_return_attempts=9
handoff_state=a90ctl version END timeout while Debian PID1 owned the system
reboot_signal=serial-missing and connection reset
returned_version=A90 Linux init 0.11.138 (v3381-server-distro-journaled-formatter)
post_autoreboot_status_selftest=pass=12 warn=1 fail=0
post_autoreboot_explicit_selftest=pass=12 warn=1 fail=0
```

## Rollback

After the D4D proof, the boot image was rolled back through `native_init_flash.py` to v2321:

```text
rollback_local_sha256=ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb
rollback_remote_sha256=ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb
rollback_boot_readback_sha256=ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb
rollback_total_sec=64.782
final_version=A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)
final_status_selftest=pass=11 warn=1 fail=0
final_explicit_selftest=pass=11 warn=1 fail=0
```

## Safety Boundary

- No forbidden partition was written.
- `userdata` remained the only destructive D4 storage target.
- The SSH private key stayed under `workspace/private/run/` and was not committed.
- No public tunnel or external exposure was opened; SSH was USB/NCM-local only.
- V3381 was not promoted as a resident boot image.

## Next

D4A through D4D are now live-proven. Any future step should be a separate decision: either promote a
D4-capable boot image as the appliance resident, or build the next appliance-management surface on top
of the proven userdata rootfs.
