# Server-Distro Wi-Fi STA Upstream WSTA5 Preparer Gap

- Date: `2026-07-04`
- Decision: `wsta5-live-invalid-preparer-gap-fixed`
- Native resident: `A90 Linux init 0.11.140 (v3384-server-distro-hardware-contract)`
- Device ending state: native V3384, `selftest fail=0`
- Private run dir: `workspace/private/runs/server-distro/wsta5-l3-live-20260703T191601Z`

## Result

The first WSTA5 live attempt is not a valid L3-gate result.  It exposed a deployment gap:
`prepare_wsta3_sta_rootfs.py` staged the latest D-public firstboot script, but it did not overwrite
`/usr/local/bin/a90-dpublic-wifi-sta` with the current repo helper.  The populated userdata rootfs
therefore ran the older helper that has no WSTA5 L3 gate.

The invalid live attempt did prove the surrounding handoff path was still functional:

- prepared a private STA rootfs tarball with `netcat-openbsd` installed;
- staged the tarball to SD runtime and verified its SHA on device;
- ran `userdata-appliance-preflight`;
- hit a fail-closed stale D4C toolroot node (`259:17` from an older boot) before mkfs began;
- removed only that stale SD-runtime toolroot node and re-ran format with the current preflight
  identity (`sda33`, current `dev`, current sectors);
- formatted and populated `userdata`;
- injected the temporary SSH public key into populated userdata;
- switched into Debian and reached key-only SSH over USB/NCM.

The marker from that boot ended at the old helper's DHCP-level failure:

```text
wifi_sta_wpa_supplicant_rc=0
wifi_sta_started=1
wifi_sta_carrier_up=0
wifi_sta_dhcp_attempted=1
wifi_sta_dhcp_rc=2
wifi_sta_default_route_iface=ncm0
wifi_sta_decision=wifi-sta-dhcp-failed
```

Diagnostics confirmed the old-helper problem: the new WSTA5 L3 marker fields were absent, and the
Debian shell had `nc.openbsd` from the package extraction but no `nc` alternative.  Because this was
not the current helper, the boot cannot answer the intended WSTA5 L3 question.

## Source Fix

Two source fixes landed:

- `prepare_wsta3_sta_rootfs.py` now always copies the current repo
  `a90_dpublic_wifi_sta.sh` into `/usr/local/bin/a90-dpublic-wifi-sta` in the private target rootfs.
  The summary records `latest_helper_staged`, `l3_gate_present`, and `tcp_probe_fallback_present`.
- `a90_dpublic_wifi_sta.sh` now accepts either `nc` or `nc.openbsd` for the outbound TCP/443 probe
  and records the selected tool as `wifi_sta_tcp_probe_tool`.

## Safety Boundary

- No boot image was built or flashed.
- No forbidden partition was written.
- The only destructive device action was the already-authorized `userdata` format/populate path.
- The stale node cleanup touched only the SD-runtime D4C toolroot node, not a partition.
- No public tunnel was started; manual mode left `tunnel_started=manual`.
- No SSID, PSK, BSSID, MAC, private IP, gateway, DHCP lease, public URL, or token is committed.
- The device was rebooted back to native V3384 and final `selftest` returned `fail=0`.

## Validation

```text
sh -n workspace/public/src/scripts/server-distro/a90_dpublic_wifi_sta.sh \
  workspace/public/src/scripts/server-distro/a90_dpublic_firstboot.sh

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py \
  tests/test_dpublic_smoke_helpers.py \
  tests/test_prepare_wsta3_sta_rootfs.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_dpublic_smoke_helpers \
  tests.test_prepare_wsta3_sta_rootfs \
  tests.test_server_distro_debian_rootfs_builder \
  tests.test_server_distro_wifi_sta_upstream_plan
```

Result: `27` host-side tests passed.

## Next

Rebuild a fresh private WSTA5 userdata rootfs with the fixed preparer, then rerun:

1. stage tarball to SD runtime;
2. format/populate userdata using fresh preflight identity;
3. inject temporary SSH key;
4. run WSTA2 materialization;
5. switch into Debian and collect the new WSTA5 L3 markers.
