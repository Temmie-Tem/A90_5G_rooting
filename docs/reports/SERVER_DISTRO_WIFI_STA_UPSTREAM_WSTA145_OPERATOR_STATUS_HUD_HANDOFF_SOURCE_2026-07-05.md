# WSTA145 Operator Status HUD Handoff Source Pass

Date: 2026-07-05 10:25 KST

## Verdict

WSTA145 folds the WSTA144 durable D-public HUD handoff proof into the operator
server-status bundle.  This was a host-only source/status unit.  It did not
touch the device, flash, reboot, switch root, connect Wi-Fi, start DHCP, open a
public tunnel, mutate packet filters, or write userdata.

Result: PASS.  WSTA108 now treats the WSTA144 shared-run bind proof as a
first-class fail-closed input and reports the HUD presenter state as
`DPUBLIC_HUD_DURABLE_PRESENTER_HANDOFF_LIVE_PROVEN`.

## Source Changes

- Added
  `workspace/public/src/scripts/server-distro/run_wsta144_dpublic_hud_shared_run_bind_summary.py`.
  It re-reads the private WSTA144 live transcripts and emits
  `wsta144_dpublic_hud_shared_run_bind_live.json` with no device action.
- Extended
  `workspace/public/src/scripts/server-distro/run_wsta108_operator_server_status.py`
  with `--wsta144-hud-presenter-handoff-proof-json`.
- Added WSTA108 tests for a valid WSTA144 handoff proof and an incomplete proof
  that must block even when the supplied decision says pass.

## Proof Folded

The generated WSTA144 summary decision was
`wsta144-dpublic-hud-shared-run-bind-live-pass`.

The proof includes:

- V3401 candidate:
  `A90 Linux init 0.11.157 (v3401-dpublic-hud-shared-run-bind)`.
- Boot SHA256:
  `d9496d565af554f4fb30a9064c1998356b27396163b7cc67fd693db8a3a8e418`.
- Checked-helper flash health clean.
- Native shared `/run/a90-dpublic` tmpfs mounted as `root:a90hud 1770`.
- Shared run bind proven through Debian handoff with same device and inode.
- Debian PID1 on userdata root.
- Preserved presenter remained the sole DRM fd owner.
- Debian `a90hud` intent writer had UID/GID 3904, `CapEff=0`, no DRM fd, and
  no network intent.
- Fresh Debian intent `sequence=14401` was consumed by the preserved presenter
  with `present_rc=0`.
- Final V3401 native health stayed clean.

## Operator Status Result

Private WSTA108 status regeneration decision:
`wsta108-operator-server-status-source-pass`.

Key resulting state:

- Server state: `SERVER_PROFILE_READY_DEFAULT_OFF`.
- HUD presenter state:
  `DPUBLIC_HUD_DURABLE_PRESENTER_HANDOFF_LIVE_PROVEN`.
- `handoff_live_proven=true`.
- `hud_presenter_handoff_shared_run_bind_proven=true`.
- `hud_presenter_handoff_fresh_debian_intent_consumed=true`.
- `hud_presenter_handoff_sole_drm_owner=true`.
- Public exposure remains default-off.
- No public URL value or secret value is present in the public summary or
  generated markdown.

The operator next action now moves past handoff design to:
`continue-dpublic-service-integration-or-containment-hardening`.

## Validation

- `py_compile`:
  - `run_wsta108_operator_server_status.py`
  - `run_wsta144_dpublic_hud_shared_run_bind_summary.py`
  - `test_server_distro_wsta108_operator_server_status.py`
- Focused WSTA108 unit tests: `39 tests OK`.
- Full server-distro WSTA regression: `460 tests OK`.
- WSTA144 summary generation from the live WSTA144 private transcripts: pass.
- WSTA108 operator status regeneration with the generated WSTA144 proof: pass.

## Safety

This unit was source/status-only.  The live device remained on the previously
proven V3401 resident image from WSTA144; no new device operation was performed
for WSTA145.

## Next

Continue D-public service integration or containment hardening.  The next
highest-signal units are presenter cleanup/restart policy for long-running
appliance mode and optional HUD syscall trace profiling before seccomp
enforcement.
