# WSTA126 Operator Status Cloudflared Runtime Proof Source Pass

Date: 2026-07-05 06:38 KST

## Scope

WSTA126 folds the private WSTA125 native-upstream cloudflared runtime proof into
the existing WSTA108/WSTA90 operator server status bundle. This is a host-only
source/status unit. It reads existing private proof JSON files and emits a
redacted private operator status artifact.

This unit did not run a device action, build or flash a boot image, reboot
native init, associate Wi-Fi, run DHCP, open a new public tunnel, run public
smoke, mutate packet filters, touch userdata, or switch root.

## Changes

- Updated `run_wsta108_operator_server_status.py` to accept
  `--wsta125-cloudflared-runtime-proof-json`.
- Added compact status field `hardening.cloudflared_runtime`.
- The proof consumer requires the WSTA125 pass decision and fail-closes unless
  the proof includes all required runtime evidence:
  - WSTA28 precondition and native uplink confirmed;
  - default route on native STA, resolver ready, and egress route ready;
  - packet-filter preflight/apply/restore;
  - cloudflared UID/GID, no-new-privs, CapEff-zero, command-shape, outbound-only,
    and outbound-observed checks;
  - private URL artifact saved with URL value redacted from public JSON/markdown;
  - private syscall trace artifacts saved;
  - core `execve/socket/connect` syscalls observed;
  - runtime cleanup, uplink-service stop, helper/profile cleanup, chroot cleanup,
    and final selftest fail-zero.
- When WSTA125 is complete, WSTA108 marks
  `hardening.cloudflared_runtime.state=CLOUDFLARED_RUNTIME_LIVE_PROVEN`, sets
  `cloudflared_live_proven=true`, clears WSTA122 model `remaining_live_proofs`,
  removes `cloudflared-quick-tunnel` from remaining launcher/syscall proof
  profiles, and removes the cloudflared runtime next action.

## Source Proof

Private regenerated status:

```text
workspace/private/runs/server-distro/wsta126-operator-status-cloudflared-runtime-20260705T0638KST/wsta108_operator_server_status.json
```

Input proofs:

- WSTA88 workflow:
  `workspace/private/runs/server-distro/wsta107-status-hud-preflight-20260705T0200KST/wsta88_operator_workflow.json`
- WSTA90 manifest:
  `workspace/private/runs/server-distro/wsta108-server-status-hardening-input-20260705T0205KST/wsta90_service_hardening_manifest.json`
- WSTA94 packet filter:
  `workspace/private/runs/server-distro/wsta94-packet-filter-live-20260704T143227Z/wsta94_result.json`
- Packet-filter control summary:
  `workspace/private/runs/server-distro/packet-filter-control-ssh-live-20260704T160025Z/packet_filter_control_summary.json`
- WSTA110 service launcher:
  `workspace/private/runs/server-distro/wsta110-service-launcher-live-20260704T173234Z/wsta110_result.json`
- WSTA117/WSTA114 syscall trace:
  `workspace/private/runs/server-distro/wsta117-server-only-wsta114-live-v2-20260705T0407KST/wsta114_result.json`
- WSTA120 Dropbear admin:
  `workspace/private/runs/server-distro/wsta120-dropbear-admin-live-v6-20260705T044147KST/wsta120_result.json`
- WSTA122 cloudflared model:
  `workspace/private/runs/server-distro/wsta122-cloudflared-service-model-20260705T045720KST/wsta122_cloudflared_service_model.json`
- WSTA125 native-upstream cloudflared runtime:
  `workspace/private/runs/server-distro/wsta125-native-upstream-cloudflared-runtime-live-v4-20260705T062106KST/wsta125_result.json`

Result:

- Decision: `wsta108-operator-server-status-source-pass`
- Server state: `SERVER_PROFILE_READY_DEFAULT_OFF`
- Public state: `PUBLIC_OFF`
- Cloudflared model state: `CLOUDFLARED_SERVICE_MODEL_SOURCE_DEFINED`
- Cloudflared runtime proof state: `CLOUDFLARED_RUNTIME_LIVE_PROVEN`
- Cloudflared runtime user: `a90tunnel`, UID/GID `3902/3902`
- Native upstream confirmed: true
- Egress route ready: true
- Packet-filter apply/restore: true/true
- no-new-privs and CapEff zero: true/true
- Outbound-only and outbound-observed: true/true
- Private URL artifact present and redacted: true/true
- Syscall trace artifacts saved: true
- Cloudflared syscall count: `52`
- Core cloudflared syscalls observed: `execve/socket/connect`
- Runtime cleanup and final selftest fail-zero: true/true
- WSTA122 model `remaining_live_proofs`: empty
- Remaining launcher profiles no longer include `cloudflared-quick-tunnel`
- Remaining syscall profiles no longer include `cloudflared-quick-tunnel`
- Operator next actions no longer include the cloudflared runtime proof action
- Public URL value logged: false
- Secret values logged: `0`

Remaining blockers:

- `remaining service users/groups not live-proven beyond dpublic-smoke-httpd/dropbear-admin-usb/cloudflared-quick-tunnel`
- `remaining syscall traces not captured beyond dpublic-smoke-httpd/cloudflared-quick-tunnel`

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta108_operator_server_status.py \
  tests/test_server_distro_wsta108_operator_server_status.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  tests/test_server_distro_wsta108_operator_server_status.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest discover \
  -s tests -p 'test_server_distro_wsta*.py'
```

Result:

- WSTA108 focused tests: `28 tests OK`
- Full server-distro WSTA regression: `412 tests OK`
- The WSTA94 runner-error JSON printed during the full run is the expected
  exception-path fixture from that unit test; unittest completed OK.
- `git diff --check`: OK

## Next

WSTA126 retires the cloudflared runtime gap in operator status. The remaining
server-hardening work is no longer cloudflared runtime; it is the still-broad
launcher/user/syscall coverage for the remaining service profiles, especially
`dpublic-hud` and the native uplink helper boundary before any always-on or
seccomp-enforcement claim.
