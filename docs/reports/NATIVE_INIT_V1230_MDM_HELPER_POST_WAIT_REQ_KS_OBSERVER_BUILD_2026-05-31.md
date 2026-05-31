# V1230 mdm_helper Post-WAIT_FOR_REQ ks Observer Build

- date: 2026-05-31
- scope: source/build-only helper support
- helper: `a90_android_execns_probe v256`
- helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- helper binary: `stage3/linux_init/helpers/a90_android_execns_probe_v256`
- verifier: `scripts/revalidation/native_wifi_mdm_helper_post_wait_req_ks_observer_support_v1230.py`
- evidence: `tmp/wifi/v1230-execns-helper-v256-build/manifest.json`
- result: `v1230-post-wait-req-ks-observer-build-pass`
- pass: `true`
- sha256: `56ab12b7c7951f2fd5ff9132d6d9662b77560fc2cd55da712115b99b2ec029e9`
- size: `1253872`

## Purpose

V1228 showed that the non-ptrace native PM/CNSS path reaches `mdm_helper`
inside `ESOC_WAIT_FOR_REQ` while `pm-service` attempts `/dev/subsys_esoc0`.
V1229 then reconciled that with V891/V1199/V896 and classified the active
blocker as the request/image-link handoff around Android's `ks` + MHI contract.

V1230 adds helper support to observe that exact boundary: after the
subsystem-trigger child starts, sample `mdm_helper` until the
`ESOC_WAIT_FOR_REQ` wait disappears, then continue a bounded post-transition
window to catch `/vendor/bin/ks` or `/dev/mhi_0305_01.01.00_pipe_10`.

## Added Helper Surface

New opt-in flag:

```text
--pm-observer-mdm-helper-post-wait-req-ks-observer
```

The flag is fail-closed behind the existing post-PM lower trace gate:

```text
--allow-post-pm-mdm-helper-esoc-observer
--allow-post-pm-mdm-helper-lower-trace
```

New output prefix:

```text
post_wait_req.*
```

Key summary fields:

| field | meaning |
|---|---|
| `post_wait_req.transition_detected` | `mdm_helper` left the observed `ESOC_WAIT_FOR_REQ` wait |
| `post_wait_req.transition_sample` | sample index where the wait disappeared |
| `post_wait_req.ks_process_count` | max observed `/vendor/bin/ks` / `ks` process count |
| `post_wait_req.mhi_pipe_exists` | max observed `/dev/mhi_0305_01.01.00_pipe_10` path existence |
| `post_wait_req.mhi_pipe_fd_count` | max observed global fd count for the MHI pipe |
| `post_wait_req.mdm_helper_mhi_pipe_fd_count` | max observed `mdm_helper` fd count for the MHI pipe |

The sample cadence is bounded:

- pre-transition window: `80` samples
- post-transition window: `80` samples
- sample interval: `50 ms`

## Safety Audit

- source/build-only: `true`
- device command executed: `false`
- deploy executed: `false`
- live eSoC ioctl executed: `false`
- PM actor / `mdm_helper` / CNSS actor executed: `false`
- `ESOC_NOTIFY`: not added
- `ESOC_BOOT_DONE`: not added
- Wi-Fi HAL start: `false`
- scan/connect/link-up: `false`
- credential use: `false`
- DHCP/route: `false`
- external ping: `false`
- boot image write / flash / partition write: `false`

## Verification

| check | result |
|---|---|
| V1229 input manifest | pass |
| source marker/string checks | pass |
| static aarch64 build | pass |
| built helper strings | pass |
| stage3 helper exists | pass |
| stage3 helper sha matches build output | pass |
| no dynamic section / no interpreter | pass |

Build command:

```bash
python3 scripts/revalidation/native_wifi_mdm_helper_post_wait_req_ks_observer_support_v1230.py run
```

## Next

V1231 should deploy helper `v256` only. V1232 should run the bounded
post-WAIT_FOR_REQ observer live, still without Wi-Fi HAL, scan/connect,
credentials, DHCP/routes, external ping, `ESOC_NOTIFY`, or `ESOC_BOOT_DONE`.
