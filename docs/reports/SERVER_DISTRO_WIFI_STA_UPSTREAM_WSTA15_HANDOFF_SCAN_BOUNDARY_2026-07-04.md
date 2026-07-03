# Server-Distro WSTA15 Handoff / Scan Boundary

Date: 2026-07-04
Scope: native WLAN scan boundary below association
Result: native scan engine survives AP-iftype probe; STA-only scan can materialize `wlan0`

## Goal

WSTA14 proved the Debian side can see a managed `wlan0`/phy, but direct `iw` scan and
`wpa_cli` scan windows still returned zero visible BSS.  WSTA15 narrows the boundary before
returning to association, gateway, API, or tunnel work:

- test a STA-only native materialization path that avoids AP-iftype add/delete;
- test whether the WSTA2 AP-iftype add/delete probe poisons scan state;
- keep the run below association, DHCP, ping, DNS, API, and public tunnel exposure.

## Source Changes

Added a no-flash WSTA15 live runner:

- `workspace/public/src/scripts/server-distro/run_wsta15_handoff_scan_boundary.py`

The runner requires resident V3384 and records a private JSON result under
`workspace/private/runs/server-distro/`.  It performs:

1. native `version`, `status`, `selftest`, and `server-distro hardware-contract`;
2. a repeated STA-only `wifi scan <delay_ms>` window;
3. the bounded `wifi softap iftype-probe <timeout_ms>` AP-iftype add/delete proof;
4. a second `wifi scan <delay_ms>` window after the AP-iftype probe;
5. process-table screening for forbidden native Wi-Fi/tunnel workers.

Safety markers stay below association: no credentials, no native connect, no DHCP, no ping,
no public tunnel, and no flash.

Added focused host tests:

- `tests/test_server_distro_wsta15_handoff_scan_boundary.py`

The tests pin parsing/classification behavior and assert the runner does not expose flash,
association, DHCP, ping, or tunnel command paths.

## Static Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta15_handoff_scan_boundary.py \
  tests/test_server_distro_wsta15_handoff_scan_boundary.py

PYTHONPATH=tests python3 -m unittest \
  tests/test_server_distro_wsta15_handoff_scan_boundary.py \
  tests/test_server_distro_wsta2_native_materialization.py

Ran 10 tests in 0.000s
OK
```

## Live Validation

Precondition:

- resident native-init: `0.11.140` / `v3384-server-distro-hardware-contract`
- fresh native reboot before the WSTA15 run
- post-run selftest: `fail=0`

Private result:

```text
workspace/private/runs/server-distro/wsta15-handoff-scan-boundary-20260703T231130Z/wsta15_result.json
```

Redacted live summary:

```text
decision=wsta15-native-scan-engine-survives-iftype
selftest_fail_zero=true
hardware_contract_ok=true
forbidden_native_workers=[]

wifi_status_pre: decision=wifi-status-wlan0-missing

pre_sta_only_scan_window:
  attempts_completed=4
  attempt 1: decision=wifi-scan-link-up-failed link_up_errno=19
  attempt 2: decision=wifi-scan-link-up-failed link_up_errno=19
  attempt 3: decision=wifi-scan-link-up-failed link_up_errno=19
  attempt 4: decision=wifi-scan-pass scan_result_count=11

iftype_probe:
  decision=softap-iftype-probe-pass
  wlan0_present=1
  ap_iftype_add_rc=0
  ap_iftype_cleanup_ok=1

post_iftype_scan_window:
  attempts_completed=1
  decision=wifi-scan-pass scan_result_count=12
```

## Interpretation

WSTA15 rules out the narrow AP-iftype-poisons-native-scan hypothesis.  From a fresh V3384
native boot, `wlan0` is initially missing, but a bounded STA-only `wifi scan` loop eventually
materializes it and gets visible BSS results.  After the AP-iftype add/delete probe, the native
scan engine still works and sees visible BSS immediately.

That means WSTA14's Debian failure is not explained by native AP-iftype poisoning alone.  The
next useful boundary is handoff-specific: use the STA-only native scan materialization path,
then switch to Debian and capture immediate post-handoff link/scan state before supplicant
association.  If Debian still cannot scan, the next design target is a bounded Debian
post-handoff WLAN reset/materialization step rather than more gateway/API/tunnel probing.

## Next

WSTA16 should reuse the fresh-boot STA-only native scan gate:

```text
fresh native boot
  -> repeated native wifi scan until scan engine pass / visible BSS
  -> switch_root
  -> immediate Debian sysfs/ip-link/iw scan snapshot before wpa_supplicant
```

Keep association, DHCP, API, and cloudflared parked until that immediate Debian scan boundary
is understood.
