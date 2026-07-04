# WSTA73 Persistent Arming Packet Source

- Date: 2026-07-04
- Scope: host-only operator arming packet for WSTA72 prepare-to-arm output
- Device action: none
- Flash: none
- Public exposure: none
- Decision: `wsta73-persistent-arming-packet-pass`

## Summary

WSTA73 consumes a private WSTA72 prepare-to-arm result and renders a compact
operator arming packet.  Before rendering the packet, it reruns WSTA71 over the
WSTA70 launch manifest so stale WSTA72 artifacts cannot be treated as fresh.

The output is:

```text
wsta73_arming_packet.json
wsta73_arming_packet.md
```

The packet includes:

```text
WSTA58 command template with placeholders
required placeholder replacements
required explicit acknowledgements
abort conditions
cleanup expectations
fresh WSTA71 recheck path
```

This is still not live execution.  WSTA73 does not replace token placeholders,
start a tunnel, touch the device, connect Wi-Fi, or run public smoke.

## Source Change

Added:

- `workspace/public/src/scripts/server-distro/run_wsta73_persistent_arming_packet.py`
- `tests/test_server_distro_wsta73_persistent_arming_packet.py`

The runner is fail-closed until a private WSTA72 prepare-to-arm result is
supplied:

```text
python3 workspace/public/src/scripts/server-distro/run_wsta73_persistent_arming_packet.py \
  --wsta72-prepare-to-arm-json workspace/private/runs/server-distro/<wsta72-run>/wsta72_prepare_to_arm.json
```

WSTA73 returns pass only if:

```text
wsta72-persistent-prepare-to-arm-pass
pipeline.state=READY_TO_ARM_DEFAULT_OFF
fresh WSTA71 recheck pass
WSTA71 state=READY_TO_ARM_DEFAULT_OFF
ready_for_live=true
command template still contains placeholders only
```

If the selected session has aged into STALE/EXPIRED/NOT_READY, WSTA73 blocks on
the WSTA71 recheck and records the recheck result path.

## Private Smoke

Private smoke directory:

```text
workspace/private/runs/server-distro/wsta73-arming-packet-smoke-20260704T105056Z
```

Observed WSTA73 result:

```text
decision=wsta73-persistent-arming-packet-pass
state=ARMING_PACKET_READY_DEFAULT_OFF
wsta65_session_state=READY
ready_for_live=true
initial_seconds_remaining=298
abort_condition_count=5
ack_count=7
live_command_template contains <native-confirm-token>
live_execution_requested=false
```

Generated packet:

```text
workspace/private/runs/server-distro/wsta73-arming-packet-smoke-20260704T105056Z/arming/wsta73_arming_packet.json
workspace/private/runs/server-distro/wsta73-arming-packet-smoke-20260704T105056Z/arming/wsta73_arming_packet.md
```

## Safety

- No boot image was built or flashed.
- No forbidden partition was touched.
- No device command, native reboot, Wi-Fi association, DHCP, public tunnel,
  public smoke, userdata action, switch-root, or external service action ran.
- The runner has no `native_init_flash.py` or `a90ctl.py` call path.
- The WSTA58 command remains a placeholder template; raw confirm-token values
  are not embedded.
- READY sessions remain default-off.  WSTA73 only creates an operator packet for
  a later explicit operator-selected WSTA58 live gate.
- Redaction checks are applied to the public summary and generated Markdown.
- The committed report/source/test changes contain no raw public URL, public
  tunnel domain, confirm-token value, Wi-Fi credential, SSID, BSSID, MAC, IP,
  gateway, DNS, lease id value, or device serial.
- Raw private lease artifacts, prepare-to-arm outputs, WSTA71 rechecks, and
  arming packets remain under `workspace/private/`.

## Validation

Compile check:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta73_persistent_arming_packet.py
```

Result: pass

WSTA73 focused tests:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta73_persistent_arming_packet
```

Result: `Ran 7 tests ... OK`

Focused WSTA52-WSTA73 regression:

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
  tests.test_server_distro_wsta69_persistent_session_snapshot \
  tests.test_server_distro_wsta70_persistent_session_launch_manifest \
  tests.test_server_distro_wsta71_persistent_launch_readiness_audit \
  tests.test_server_distro_wsta72_persistent_prepare_to_arm \
  tests.test_server_distro_wsta73_persistent_arming_packet
```

Result: `Ran 121 tests ... OK`

Fresh WSTA72 + WSTA73 private smoke: pass.

## Next

The default-off persistent exposure workflow now has a one-command
prepare-to-arm path and a fresh arming-packet renderer.  Continue only with
explicit operator-selected WSTA58 live proof, or further default-off operator
UX/reporting that does not start public exposure.
