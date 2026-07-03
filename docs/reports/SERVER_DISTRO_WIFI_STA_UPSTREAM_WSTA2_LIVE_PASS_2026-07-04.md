# Server-Distro Wi-Fi STA Upstream WSTA2 Live Pass

- Date: `2026-07-04`
- Decision: `wsta2-native-materialization-pass`
- Candidate: `A90 Linux init 0.11.140 (v3384-server-distro-hardware-contract)`
- Candidate boot image: `workspace/private/inputs/boot_images/boot_linux_v3384_server_distro_hardware_contract.img`
- Candidate SHA256: `47890d04219837af3acb96ad8e281ad4eab0ea3a73ae2641e05633d014979178`
- Final device state: V3384 native-init resident, `selftest fail=0`

## Result

WSTA2 passed live.  Native init materialized `wlan0` below association, proved the Stage0 hardware
contract, and did not start a native STA session, DHCP client, AP server, DNS server, public tunnel,
or credential-bearing path.

The accepted pass run is:

```text
workspace/private/runs/server-distro/wsta2-native-materialization-20260703T174709Z/wsta2_result.json
```

The patched runner was then re-run against the already-materialized resident and passed again:

```text
workspace/private/runs/server-distro/wsta2-native-materialization-20260703T174947Z/wsta2_result.json
```

## Recovery Into Native Control

The device initially remained in the Debian userdata appliance, so native cmdv1 was unavailable.  The
USB/NCM link and local SSH were still reachable on the appliance.  A normal Debian reboot returned
control to native-init without writing any partition.

After reboot:

```text
version: 0.11.139 build=v3383-server-distro-handoff-cleanup
```

This restored the checked native recovery path required by `native_init_flash.py --from-native`.

## V3384 Flash

`run_wsta2_native_materialization.py --flash-v3384 --probe-iftype` flashed the exact V3384 image through
the checked helper:

```text
native_to_recovery=ok
recovery_adb=ready
remote_sha256=47890d04219837af3acb96ad8e281ad4eab0ea3a73ae2641e05633d014979178
boot_readback_sha256=47890d04219837af3acb96ad8e281ad4eab0ea3a73ae2641e05633d014979178
verify_native_init=cmdv1 version/status ok
```

Rollback image preconditions were checked before flash:

```text
v2321 sha256_ok=1
v2237 sha256_ok=1
v48 exists=1
```

The first post-flash runner process recorded `wsta2-runner-error` because serial noise interrupted the
runner's immediate `selftest` command after the helper had already verified V3384.  Direct follow-up
health checks proved the candidate was clean:

```text
version: 0.11.140 build=v3384-server-distro-hardware-contract
selftest: pass=12 warn=1 fail=0
status: selftest fail=0, transport.ncm=ready, storage rw=yes
```

## WSTA2 Gate Evidence

The accepted WSTA2 pass run showed:

```text
selftest_fail_zero=true
hardware_contract_ok=true
wlan0_present=true
forbidden_native_workers=[]
```

`wifi status` before the probe reported `wlan0_present=0`.  The bounded native iftype probe then brought
up the WLAN surface without credentials:

```text
wlan0_wait_timeout_ms=220000
wlan0_wait_elapsed_ms=70444
wlan0_present=1
link_up_attempted=1
link_up_rc=0
sta_supplicant.process_count_before=0
sta_supplicant.process_count_final=0
ap_iftype_add_attempted=1
ap_iftype_add_rc=0
ap_iftype_iface_created=1
ap_iftype_cleanup_ok=1
decision=softap-iftype-probe-pass
```

`wifi status` after the probe reported:

```text
wlan0_present=1
operstate=down
carrier=0
ipv4=none
default_route_present=0
supplicant.process_count=0
secret_values_logged=0
decision=wifi-status-wlan0-present
```

The native process table check found no forbidden WSTA2 workers:

```text
wpa_supplicant=absent
dhclient=absent
udhcpc=absent
udhcpd=absent
hostapd=absent
dnsmasq=absent
cloudflared=absent
```

## Runner Fix

The second no-flash runner attempt hit the native auto-menu busy gate on `server-distro hardware-contract`.
The runner now detects the exact `rc=-16 status=busy auto menu active` shape, sends one raw `hide`, and
retries the same cmdv1 command.  This keeps WSTA2 stable after boot/menu redraw without widening the
allowed command surface.

The patched runner passed live in:

```text
workspace/private/runs/server-distro/wsta2-native-materialization-20260703T174947Z/wsta2_result.json
```

## Safety Boundary

- Boot flash used only `native_init_flash.py`.
- No forbidden partition was written.
- No Wi-Fi association was attempted.
- No DHCP, ping, AP/NAT/DNS server, public tunnel, or credential-bearing command was run.
- No SSID/PSK, public URL, token, raw MAC/BSSID, or raw device identifier is committed.
- V3384 was left resident for the next bounded WSTA3 unit; v2321/v2237/v48 rollback images remain present.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py \
  tests/test_server_distro_wsta2_native_materialization.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta2_native_materialization \
  tests.test_prepare_wsta3_sta_rootfs \
  tests.test_server_distro_wifi_sta_upstream_plan \
  tests.test_dpublic_smoke_helpers \
  tests.test_prepare_d4c_userdata_rootfs_tarball

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/server-distro/run_wsta2_native_materialization.py --probe-iftype

git diff --check
```

Result: tests passed, patched live runner returned `wsta2-native-materialization-pass`.

## Next

WSTA3 can now move from host-only prep to a bounded live unit: stage the WSTA3 private rootfs tarball
under the SD runtime path, refresh/populate userdata with that tarball, switch into Debian, and run the
Debian-owned STA association/DHCP/default-route validation using private credentials only.
