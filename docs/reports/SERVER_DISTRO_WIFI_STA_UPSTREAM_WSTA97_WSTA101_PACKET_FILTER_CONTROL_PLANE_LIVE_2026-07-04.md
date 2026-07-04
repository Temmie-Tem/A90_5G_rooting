# WSTA97-WSTA101 Packet Filter Control-Plane Live Check

Date: 2026-07-05 01:05 KST host clock  
Scope: server-distro D-public packet-filter lifecycle live follow-up  
Device mutation: SD/chroot/userspace only, no boot flash  
Secret hygiene: no SSID, PSK, confirm token, or public URL value recorded here

## Summary

WSTA97 correctly fail-closed before live exposure because the then-selected rootfs
did not contain the IPv6 legacy restore tool:

- decision: `wsta88-blocked-wsta80-live`
- nested decision: `wsta42-blocked-packet-filter-preflight`
- missing tool: `/usr/sbin/ip6tables-legacy-restore`
- secret/public URL leakage flags: `secret_values_logged=0`,
  `public_url_value_logged=false`

WSTA98 prepared a packet-filter-ready private rootfs image:

- image SHA256: `2dae0d4dcfde1854f0d91b0fe94948720b175638261d156572e82ca7d18e928b`
- legacy tools present: `iptables-legacy`, `ip6tables-legacy`,
  `iptables-legacy-restore`, `ip6tables-legacy-restore`,
  `iptables-legacy-save`, `ip6tables-legacy-save`

Two live blockers were then identified and fixed in source:

- D2 dropbear daemon mode could return without a usable listener/pidfile.  The
  D2 start path now runs dropbear foreground/backgrounded with `-E -F`, writes
  the observed PID, checks `kill -0`, and captures a failure log.
- The generated ext4 rootfs had `/root` owned by host uid/gid `1000:1000`,
  causing Dropbear public-key auth rejection.  The D2 start path now normalizes
  `/root`, `/root/.ssh`, and `authorized_keys` to root-owned strict modes before
  starting Dropbear.

D2 foreground proof passed:

- run: `workspace/private/runs/server-distro/d2-foreground-dropbear-live-20260704T154122Z`
- result: foreground Dropbear started, host SSH marker returned, Debian version
  `12.14`, stage marker present
- postcheck: mount absent, loop absent, dropbear absent

WSTA99 then proved the next packet-filter design flaw:

- WSTA42 reached Wi-Fi autoconnect, resolver sync, SSH stage, D-public binary
  stage, packet-filter preflight, local loopback smoke, and packet-filter apply.
- packet-filter apply set `INPUT DROP` but did not preserve the USB-local SSH
  control plane.
- after apply, new host SSH sessions to `192.168.7.2:2222` timed out, so
  cloudflared start and cleanup could not run.

The packet-filter helper is now version `3` and keeps the public-facing default
drop posture while explicitly preserving the USB-local control plane:

- `INPUT DROP` remains.
- loopback accept remains.
- established/related accept remains.
- new IPv4 allow rule: `192.168.7.1/32 -> tcp/2222`.
- apply emits:
  - `packet_filter_control_ssh_accept=1`
  - `packet_filter_control_cidr=192.168.7.1/32`
  - `packet_filter_control_ssh_port=2222`

Focused live control-plane proof passed:

- run: `workspace/private/runs/server-distro/packet-filter-control-ssh-live-20260704T160025Z`
- `packet_filter_decision=packet-filter-loopback-default-drop-applied`
- `packet_filter_helper_version=3`
- `packet_filter_control_ssh_accept=1`
- new SSH session after apply returned the D2 marker:
  `ssh_after_apply_marker=true`
- restore succeeded: `packet_filter_restore_ok=true`
- postcheck: mount absent, loop absent, dropbear absent

Full WSTA42 public-live retries WSTA100 and WSTA101 did not reach the
packet-filter/public-tunnel section.  Both failed earlier at native uplink
confirmed autoconnect:

- decision: `wsta42-blocked-native-uplink-confirmed`
- nested decision: `wifi-uplink-service-autoconnect-failed`
- native rc: `-22`
- scan recovery: `wifi-autoconnect-scan-recovery-probe-failed`

Because that failure repeated twice, live retry stopped.  It is tracked as a
separate STA/uplink transient or state issue, not a packet-filter control-plane
failure.

Final device health after the live attempts:

- resident: `A90 Linux init 0.11.153 (v3397-wsta-execute-gate-screen)`
- selftest: `pass=12 warn=1 fail=0`
- no leftover chroot mount, loop0 attachment, dropbear, or TCP/2222 listener

## Validation

Host-side:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_d2_ssh_in_chroot.py \
  workspace/public/src/scripts/server-distro/run_wsta42_native_uplink_dpublic_tunnel.py \
  workspace/public/src/scripts/server-distro/run_wsta43_orchestrated_native_uplink_dpublic.py \
  workspace/public/src/scripts/server-distro/run_wsta55_short_lived_public_proof.py \
  workspace/public/src/scripts/server-distro/run_wsta58_renewal_manual_stop_proof.py \
  workspace/public/src/scripts/server-distro/run_wsta80_persistent_operator_execute_gate.py \
  workspace/public/src/scripts/server-distro/run_wsta88_persistent_operator_workflow.py \
  workspace/public/src/scripts/server-distro/run_wsta94_packet_filter_live_gate.py \
  workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_d2_ssh_in_chroot \
  tests.test_server_distro_wsta42_native_uplink_dpublic_tunnel \
  tests.test_server_distro_wsta43_orchestrated_native_uplink_dpublic \
  tests.test_server_distro_wsta55_short_lived_public_proof \
  tests.test_server_distro_wsta58_renewal_manual_stop_proof \
  tests.test_server_distro_wsta80_persistent_operator_execute_gate \
  tests.test_server_distro_wsta88_persistent_operator_workflow \
  tests.test_server_distro_wsta94_packet_filter_live_gate \
  tests.test_server_distro_debian_rootfs_builder \
  tests.test_prepare_wsta3_sta_rootfs
```

Result: `Ran 106 tests ... OK`.

Device-side:

- D2 foreground SSH proof passed.
- packet-filter apply/new-SSH/restore proof passed.
- final `a90ctl status` returned v3397, transport ready, SD rw.
- final `a90ctl selftest` returned `pass=12 warn=1 fail=0`.

## Next

Do not repeat the packet-filter control-plane proof unless changing the helper.
The packet-filter source path is now ready for the WSTA42 public path.  The next
bounded live unit should focus on the repeated native uplink autoconnect
failure before rerunning WSTA42/WSTA88 public exposure.
