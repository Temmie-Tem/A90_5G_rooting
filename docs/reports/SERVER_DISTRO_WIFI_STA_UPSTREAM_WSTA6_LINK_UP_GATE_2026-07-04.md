# Server-Distro Wi-Fi STA Upstream WSTA6 Link-Up Gate

- Date: `2026-07-04`
- Decision: `wsta6-link-up-gate-live-pass-next-carrier-blocked`
- Native resident: `A90 Linux init 0.11.140 (v3384-server-distro-hardware-contract)`
- Device ending state: native V3384, `selftest fail=0`
- Private runner run dir: `workspace/private/runs/server-distro/wsta6-linkup-runner-live-20260703T193656Z`
- Private handoff run dir: `workspace/private/runs/server-distro/wsta6-linkup-handoff-live-20260703T193740Z`

## Result

WSTA6 closed the WSTA5 link-up blocker.  The WSTA2 materialization runner previously treated
`wlan0_present=1` as sufficient and skipped the native bounded probe even when the interface was
not administratively UP.  The runner now parses the native `flags=` field and requires IFF_UP
before passing the pre-handoff gate.

Live evidence from resident V3384:

```text
initial wifi status: wlan0_present=1 flags=0x1002
needs_iftype_probe=true
wifi softap iftype-probe: link_up_rc=0 link_up_errno=0 decision=softap-iftype-probe-pass
after probe: wlan0_present=1 flags=0x1003
checks.wlan0_admin_up=true
decision=wsta2-native-materialization-pass
```

This used the already-proven bounded `wifi softap iftype-probe` path: no credentials, no DHCP, no
ping, no listener, no AP service start, and no public exposure.  It creates and deletes the AP
probe interface only to force the native Wi-Fi stack through the known-good link-up/materialization
path.

With that native link-up state in place, the existing populated Debian userdata appliance was
switched again.  The previous failure moved forward:

```text
wifi_sta_wpa_supplicant_rc=0
wifi_sta_started=1
```

So Debian can now start `wpa_supplicant` on `wlan0`; the WSTA5 `EINVAL` link-up blocker is gone.
The new blocker is the next layer, carrier/association:

```text
wifi_sta_carrier_up=0
wifi_sta_dhcp_attempted=1
wifi_sta_dhcp_rc=2
wifi_sta_default_route_iface=ncm0
wifi_sta_decision=wifi-sta-dhcp-failed
```

The interface remained `UP` but `NO-CARRIER`, and `dhclient` failed without a Wi-Fi lease.  The
next WSTA unit should target the Debian supplicant association/carrier state, not link-up, DHCP,
L3, or D-public tunnel behavior.

## Source Changes

- `run_wsta2_native_materialization.py` adds `wlan0_admin_up(text)` and records
  `needs_iftype_probe`.
- With `--probe-iftype`, the runner now probes when `wlan0` is missing **or** present but not
  IFF_UP.
- The pass checks now require both `wlan0_present` and `wlan0_admin_up`.
- Tests pin `flags=0x1003` as UP, `flags=0x1002` as not-UP, and the new runner fields.

## Safety Boundary

- No boot image was built or flashed.
- No forbidden partition was written.
- No userdata format/populate was performed in this WSTA6 unit; it reused the already populated
  WSTA5 userdata rootfs.
- No public tunnel was started; manual mode left tunnel startup disabled.
- No SSID, PSK, BSSID, MAC, private IP, gateway, DHCP lease, public URL, or token is committed.
- After diagnostics, the device was rebooted back to native V3384 and final `selftest` returned
  `fail=0`.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py \
  tests/test_server_distro_wsta2_native_materialization.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta2_native_materialization \
  tests.test_server_distro_wifi_sta_upstream_plan

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py \
  --run-dir workspace/private/runs/server-distro/wsta6-linkup-runner-live-20260703T193656Z \
  --probe-iftype
```

Result: host tests passed, the no-flash WSTA2 runner live gate passed with
`wlan0_admin_up=true`, and the follow-up Debian handoff advanced to `wpa_supplicant_rc=0` before
blocking at carrier/DHCP.

## Next

WSTA7 should inspect the Debian association boundary:

1. capture redacted `wpa_cli status`/events and the full non-secret `wpa_supplicant` state after
   start;
2. compare native successful STA behavior against Debian config/driver parameters without logging
   SSID/PSK/BSSID;
3. keep USB/NCM recovery and manual tunnel mode unchanged;
4. retry DHCP/L3 only after `wlan0` reaches carrier.
