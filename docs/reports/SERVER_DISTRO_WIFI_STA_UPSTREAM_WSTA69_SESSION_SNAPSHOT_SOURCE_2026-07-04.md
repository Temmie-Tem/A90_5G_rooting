# WSTA69 Persistent Session Snapshot Source

- Date: 2026-07-04
- Scope: host-only operator snapshot for persistent session inventory
- Device action: none
- Flash: none
- Public exposure: none
- Decision: `wsta69-persistent-session-snapshot-pass`

## Summary

WSTA69 adds a host-only reporting layer on top of WSTA67 inventory output.  It
consumes a private `wsta67_inventory.json` and writes:

```text
wsta69_snapshot.json
wsta69_snapshot.md
```

The snapshot is intended for operator use: it summarizes current session counts,
renders a compact session table, and gives default-off next actions.  READY
sessions are reported as selectable for an explicit WSTA58 live gate, but WSTA69
does not start a tunnel, touch the device, connect Wi-Fi, or run public smoke.

## Source Change

Added:

- `workspace/public/src/scripts/server-distro/run_wsta69_persistent_session_snapshot.py`
- `tests/test_server_distro_wsta69_persistent_session_snapshot.py`

The runner is fail-closed until a private WSTA67 inventory is supplied:

```text
python3 workspace/public/src/scripts/server-distro/run_wsta69_persistent_session_snapshot.py \
  --wsta67-inventory-json workspace/private/runs/server-distro/<wsta67-run>/wsta67_inventory.json
```

The reported `overall_state` is:

```text
INSPECT_REQUIRED          invalid inventory entries exist
CLEANUP_RECOMMENDED      STALE, EXPIRED, or NOT_READY sessions exist
READY_PRESENT_DEFAULT_OFF READY sessions exist and no cleanup is needed
NO_LIVE_READY            no live-ready session exists
```

## Private Smoke

Private smoke directory:

```text
workspace/private/runs/server-distro/wsta69-snapshot-smoke-20260704T102713Z
```

Observed flow:

```text
READY session: WSTA63 -> WSTA64
STALE session: WSTA63 -> WSTA64 -> WSTA67 inventory at near-expiry
WSTA69 snapshot over the WSTA67 inventory
```

WSTA69 result:

```text
decision=wsta69-persistent-session-snapshot-pass
overall_state=CLEANUP_RECOMMENDED
ready_count=1
stale_count=1
next_actions=[bulk-retire-nonliveable, operator-may-select-explicit-live]
live_execution_requested=false
```

Generated Markdown:

```text
workspace/private/runs/server-distro/wsta69-snapshot-smoke-20260704T102713Z/snapshot/wsta69_snapshot.md
```

## Safety

- No boot image was built or flashed.
- No forbidden partition was touched.
- No device command, native reboot, Wi-Fi association, DHCP, public tunnel,
  public smoke, userdata action, switch-root, or external service action ran.
- The runner has no `native_init_flash.py` or `a90ctl.py` call path.
- READY sessions remain default-off; the live action is only an operator-facing
  instruction to rerun status and then choose WSTA58 explicitly.
- Redaction checks are applied to the public summary and generated Markdown
  before Markdown is written.
- The committed report/source/test changes contain no raw public URL, public
  tunnel domain, confirm-token value, Wi-Fi credential, SSID, BSSID, MAC, IP,
  gateway, DNS, lease id value, or device serial.
- Raw private lease artifacts, inventories, and snapshots remain under
  `workspace/private/`.

## Validation

Compile check:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta69_persistent_session_snapshot.py
```

Result: pass

WSTA69 focused tests:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta69_persistent_session_snapshot
```

Result: `Ran 7 tests ... OK`

Focused WSTA52-WSTA69 regression:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta52_persistent_exposure_design \
  tests.test_server_distro_wsta53_persistent_exposure_plan \
  tests.test_server_distro_wsta54_private_lease_artifact \
  tests.test_server_distro_wsta55_short_lived_public_proof \
  tests.test_server_distro_wsta58_renewal_manual_stop_proof \
  tests.test_server_distro_wsta63_persistent_session_controller \
  tests.test_server_distro_wsta64_persistent_session_readiness_audit \
  tests.test_server_distro_wsta65_persistent_session_status \
  tests.test_server_distro_wsta66_persistent_session_retire \
  tests.test_server_distro_wsta67_persistent_session_inventory \
  tests.test_server_distro_wsta68_persistent_session_bulk_retire \
  tests.test_server_distro_wsta69_persistent_session_snapshot
```

Result: `Ran 91 tests ... OK`

Fresh WSTA63 + WSTA64 + WSTA67 + WSTA69 private smoke: pass.

## Next

The default-off persistent exposure workflow now has prepare, readiness, status,
retire, inventory, bulk-retire cleanup, and operator snapshot layers.  Continue
only with explicit operator-selected WSTA58 live proof, or further default-off
operator UX/reporting that does not start public exposure.
