# WSTA139 D-public HUD Presenter Service Model Source Pass

Date: 2026-07-05 09:05 KST

## Verdict

WSTA139 defines the durable native HUD presenter service model for the Debian
handoff.  WSTA130 established the split architecture, and WSTA137 proved the
native/root presenter can validate, present, and reject bad intents.  WSTA139
turns that into the next implementation contract:

- native/root starts a durable presenter before `switch_root`;
- that presenter is the sole `/dev/dri/card0` owner and survives the Debian
  handoff as a forked native child;
- Debian `a90hud` writes bounded intent files only;
- handoff cleanup preserves the armed durable presenter instead of killing it as
  a stale native DRM holder;
- stop/cleanup releases DRM and removes presenter runtime files.

This is a host-only source/model unit.  It did not perform device action, boot
flash, native reboot, Wi-Fi association, DHCP, public tunnel, public smoke,
packet-filter mutation, userdata mutation, `switch_root`, DRM open, or KMS
`SETCRTC`.

## Added

- `workspace/public/src/scripts/server-distro/run_wsta139_dpublic_hud_presenter_service_model.py`
  - inert by default and requires `--emit-service-model`;
  - requires private WSTA130 presenter model and WSTA137 live proof JSON inputs;
  - recomputes both precondition proof sets;
  - emits `wsta139_dpublic_hud_presenter_service_model.json`;
  - defines `native-dpublic-hud-presenter` as the durable native/root service;
  - defines start/stop/status command shapes;
  - defines handoff cleanup, DRM ownership, intent watch, lifecycle, and live
    proof plan.

- `tests/test_server_distro_wsta139_dpublic_hud_presenter_service_model.py`
  - covers inert default behavior;
  - covers durable native service shape;
  - covers Debian intent-writer-only handoff contract;
  - covers fail-closed intent watch and handoff proof plan;
  - covers private source artifact generation;
  - covers missing/non-pass precondition blockers;
  - covers non-private run-dir fail-closed behavior;
  - covers host-only/redaction source assertions.

## Source Proof

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/server-distro/run_wsta139_dpublic_hud_presenter_service_model.py \
  --run-id wsta139-dpublic-hud-presenter-service-model-20260705T0905KST \
  --run-dir workspace/private/runs/server-distro/wsta139-dpublic-hud-presenter-service-model-20260705T0905KST \
  --emit-service-model \
  --wsta130-hud-presenter-model-json workspace/private/runs/server-distro/wsta130-dpublic-hud-presenter-model-20260705T0735KST/wsta130_dpublic_hud_presenter_model.json \
  --wsta137-hud-presenter-live-proof-json workspace/private/runs/server-distro/wsta137-dpublic-native-presenter-live-summary-20260705T0900KST/wsta137_dpublic_native_presenter_live.json
```

Result:

- decision: `wsta139-dpublic-hud-presenter-service-model-source-pass`
- state: `DPUBLIC_HUD_DURABLE_NATIVE_PRESENTER_SERVICE_SOURCE_DEFINED`
- WSTA130 model precondition: pass
- WSTA137 live proof precondition: pass
- service: `native-dpublic-hud-presenter`
- process model: `forked-native-child-survives-switch-root`
- start phase: `native-pre-switch-root`
- start command:
  `dpublic-hud-presenter-service start --intent /run/a90-dpublic/hud-intent.json --pid-file /run/a90-dpublic/hud-presenter.pid --status-file /run/a90-dpublic/hud-presenter.status --stale-after-ms 2000`
- stop command:
  `dpublic-hud-presenter-service stop --pid-file /run/a90-dpublic/hud-presenter.pid --release-drm`
- sole DRM owner: `native-dpublic-hud-presenter`
- Debian direct DRM/KMS: `false`
- runtime dir: `/run/a90-dpublic`, `root:a90hud`, mode `1770`
- intent file: `/run/a90-dpublic/hud-intent.json`, mode `0640`
- intent watch: bounded atomic JSON, max `4096` bytes, stale after `2000ms`,
  latest sequence wins, unknown/forbidden fields rejected
- public URL value logged: `false`
- secret values logged: `0`

All model checks were true:

- `native_root_service_survives_handoff`
- `sole_drm_owner_policy`
- `handoff_cleanup_preserves_presenter`
- `debian_intent_only_contract`
- `intent_watch_fail_closed`
- `proof_plan_covers_handoff_drm_intent_cleanup`
- `bounded_shutdown_releases_drm`
- `no_power_writes`

## Live Proof Plan For Next Unit

The next live unit should implement the service control surface and prove:

- native pre-handoff status shows a presenter PID and `/dev/dri/card0` fd;
- after Debian PID1 comes up, the same presenter PID still owns `/dev/dri/card0`;
- Debian `a90hud` and other Debian services have no DRM fd;
- Debian writes a fresh intent sequence and the presenter reports that sequence
  presented;
- forbidden `command` and stale monotonic intent still reject;
- stop/cleanup removes the presenter PID and no process holds `/dev/dri/card0`.

## Validation

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta139_dpublic_hud_presenter_service_model.py \
  tests/test_server_distro_wsta139_dpublic_hud_presenter_service_model.py
```

Pass.

```sh
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta139_dpublic_hud_presenter_service_model
```

`8 tests OK`.

```sh
PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest discover \
  -s tests -p 'test_server_distro_wsta*.py'
```

`458 tests OK`.

The WSTA94 runner-error JSON printed during the full run is the expected
exception-path fixture from that unit test; unittest completed OK.

## Next

WSTA140 should implement the native service control surface in source: add
`dpublic-hud-presenter-service start|status|stop`, preserve an armed durable
presenter through the Debian handoff cleanup path, and keep Debian as the intent
producer only.  The unit can remain source/build-only first, then live-gate as a
separate bounded step.
