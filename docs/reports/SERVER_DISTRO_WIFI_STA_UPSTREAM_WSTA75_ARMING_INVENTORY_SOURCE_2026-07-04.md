# WSTA75 Persistent Arming Inventory Source

- Date: 2026-07-04
- Scope: host-only inventory of WSTA73 arming packets
- Device action: none
- Flash: none
- Public exposure: none
- Decision: `wsta75-persistent-arming-inventory-pass`

## Summary

WSTA75 scans a private WSTA run tree for WSTA73 arming packets, reruns WSTA74
for each candidate, and emits a redacted inventory of currently ready, stale, or
drifted arming packets.

The useful operator question is now answered at inventory level:

```text
Is there any currently usable default-off arming packet, and which one should be selected?
```

This is still a status/reporting layer.  WSTA75 does not replace token
placeholders, start a tunnel, touch the device, connect Wi-Fi, or run public
smoke.

## Source Change

Added:

- `workspace/public/src/scripts/server-distro/run_wsta75_persistent_arming_inventory.py`
- `tests/test_server_distro_wsta75_persistent_arming_inventory.py`

The runner scans only private paths:

```text
python3 workspace/public/src/scripts/server-distro/run_wsta75_persistent_arming_inventory.py \
  --scan-root workspace/private/runs/server-distro \
  --max-packets 50
```

WSTA75 ignores WSTA74-generated nested `wsta73-recheck` packets so repeated
inventory runs do not count their own recheck artifacts as independent operator
arming packets.

## Private Smoke

Private smoke directory:

```text
workspace/private/runs/server-distro/wsta75-arming-inventory-smoke-20260704T110331Z
```

Observed flow:

```text
WSTA72 prepare-to-arm
WSTA73 arming packet
WSTA75 inventory over the private run tree
```

Observed WSTA75 result:

```text
decision=wsta75-persistent-arming-inventory-pass
overall_state=READY_PACKET_PRESENT_DEFAULT_OFF
packet_count=1
ready_count=1
selected_ready_packet=workspace/private/runs/server-distro/wsta75-arming-inventory-smoke-20260704T110331Z/packet/wsta73_arming_packet.json
live_execution_requested=false
public_url_value_logged=false
secret_values_logged=0
```

Generated inventory:

```text
workspace/private/runs/server-distro/wsta75-arming-inventory-smoke-20260704T110331Z/inventory/wsta75_arming_inventory.json
workspace/private/runs/server-distro/wsta75-arming-inventory-smoke-20260704T110331Z/inventory/wsta75_arming_inventory.md
```

## Safety

- No boot image was built or flashed.
- No forbidden partition was touched.
- No device command, native reboot, Wi-Fi association, DHCP, public tunnel,
  public smoke, userdata action, switch-root, or external service action ran.
- The runner has no `native_init_flash.py` or `a90ctl.py` call path.
- WSTA75 invokes WSTA74 status checks only; WSTA58 live execution remains a
  separate explicit operator-selected gate.
- Redaction checks are applied to the public summary and generated Markdown.
- The committed report/source/test changes contain no raw public URL, public
  tunnel domain, confirm-token value, Wi-Fi credential, SSID, BSSID, MAC, IP,
  gateway, DNS, lease id value, or device serial.
- Raw private prepare-to-arm outputs, WSTA73 packets, WSTA74 rechecks, and
  WSTA75 inventory artifacts remain under `workspace/private/`.

## Validation

Compile check:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta75_persistent_arming_inventory.py
```

Result: pass

WSTA75 focused tests:

```text
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta75_persistent_arming_inventory
```

Result: `Ran 7 tests ... OK`

Focused WSTA52-WSTA75 regression:

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
  tests.test_server_distro_wsta73_persistent_arming_packet \
  tests.test_server_distro_wsta74_persistent_arming_status \
  tests.test_server_distro_wsta75_persistent_arming_inventory
```

Result: `Ran 135 tests ... OK`

Fresh WSTA72 + WSTA73 + WSTA75 private smoke: pass.

## Next

The default-off persistent exposure workflow now has a one-command
prepare-to-arm path, an arming packet, per-packet status, and multi-packet
inventory.  Continue only with explicit operator-selected WSTA58 live proof, or
further default-off operator UX/reporting that does not start public exposure.
