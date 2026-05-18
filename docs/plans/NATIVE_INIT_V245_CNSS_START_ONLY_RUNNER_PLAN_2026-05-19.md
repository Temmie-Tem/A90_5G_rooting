# Native Init v245 CNSS Start-Only Runner Plan

## Summary

- target: `v245` controlled CNSS start-only runner redesign
- baseline: v244 `cnss-identity-probe-pass`
- boot image change: none planned
- default behavior: no daemon execution
- live daemon start: requires explicit dangerous flags plus operator approval
- output: `tmp/wifi/v245-cnss-start-only-runner/`

v245 replaces the older v229 `runandroid`-style start experiment with a runner
that reuses the v244 private Android execution namespace and verified launcher
identity/capability contract.

## Goal

Build a safe path to answer one narrow question:

> Can native init start `/vendor/bin/cnss-daemon -n -l` briefly inside the
> private Android execution namespace, observe it, and stop it without Wi-Fi
> scan/connect/link-up or persistent Android partition mutation?

v245 itself should first deliver plan/preflight/dry-run behavior. The live
`run` mode must fail closed unless all explicit opt-in conditions are present.

## Required Inputs

| input | required decision | role |
| --- | --- | --- |
| v223 | `reboot-recovery-accepted` | only accepted recovery primitive |
| v225 | `cnss-start-plan-approved` | exposure/security boundary |
| v241 | `android-linker-vndk-apex-alias-cnss-list-pass` | linker dependency closure baseline |
| v242 | `cnss-runtime-inventory-ready-for-launcher-contract-plan` | runtime gap inventory |
| v243 | `cnss-launcher-contract-ready` | launcher contract |
| v244 | `cnss-identity-probe-pass` | harmless identity/capability proof |

The runner must reject stale/missing/mismatched manifests before any live start.

## Implementation Direction

### Helper

Extend `stage3/linux_init/helpers/a90_android_execns_probe.c` or split a small
successor helper with a new mode:

```text
--mode cnss-start-only
```

The mode must reuse v244 primitives:

- private mount namespace
- private `/dev/null`
- real linkerconfig copy
- private bind-backed `/apex` farm plus `com.android.vndk.v30` alias
- private read-only vendor mount
- uid/gid `system=1000`
- groups `inet=3003`, `net_admin=3005`, `wifi=1010`
- ambient/effective/permitted `CAP_NET_ADMIN`
- process group/session tracking
- bounded timeout and cleanup

### Host Wrapper

Add a v245 wrapper instead of overloading old v229 assumptions:

```text
scripts/revalidation/wifi_cnss_start_only_runner.py
```

Recommended subcommands:

```text
plan       validate prerequisite manifests only
preflight  collect live read-only state, no daemon start
dry-run    build exact helper argv and cleanup graph, no daemon start
run        opt-in start-only experiment
```

Required flags for `run`:

```text
--allow-daemon-start
--assume-yes
--max-runtime-sec 10
--i-understand-reboot-only-recovery
```

Hard limits:

- default runtime: `10` seconds
- hard max without source edit: `30` seconds
- no retry loop
- one daemon process group per run
- `cnss_diag` remains out of scope

## Guardrails

Always denied in v245:

- Wi-Fi scan/connect/link-up/credential/DHCP/routing
- `rfkill unblock`
- `ip link set wlan* up`
- `iw scan` / `iw connect`
- supplicant/HAL/wificond/hostapd start
- `cnss_diag`
- ICNSS generic `unbind`/`bind`
- firmware path mutation
- persistent writes under `/system`, `/vendor`, `/data`, `/efs`, modem, RPMB
- public network listener expansion
- automatic reboot without operator acknowledgement

## Preflight Gates

Before live start, collect and require:

- `version`, `status`, `bootstatus`, `selftest verbose`
- `wifiinv full`
- `kernelinv summary`
- `netservice status`
- `mountsystem ro`
- `cat /proc/net/dev`
- ICNSS sysfs present/bound baseline from read-only inventory
- firmware path rollback value unchanged
- no existing `wlan*` interface up unexpectedly
- helper version/hash matches expected v245 build
- v244 identity probe still passes or the equivalent v245 helper dry-run proves
  the same identity/capability contract
- ACM rescue path or NCM control path available before live start

Fail closed before daemon start on any required preflight failure.

## Start-Only Observation

During live `run`, capture:

- helper stdout/stderr
- daemon pid/process group
- `/proc/<pid>/status`
- `/proc/<pid>/fd` summary
- `/proc/<pid>/maps` path summary
- native `logcat`/`logtail` excerpt if available
- pre/post `wifiinv full`
- pre/post `/proc/net/dev`
- pre/post `netservice status`
- stop signal/result and reap status

`start-only-pass` requires:

- daemon became observable or exited cleanly with captured reason
- no scan/connect/link-up/credential path executed
- no unexpected WLAN/rfkill/netdev state change
- daemon stopped/reaped cleanly
- postflight equals allowed delta set

If the daemon immediately exits because a property socket, diag device, QRTR, or
SELinux primitive is missing, classify the run as `start-only-runtime-gap` as
long as cleanup/postflight are safe.

## Stop And Recovery

Normal cleanup:

1. signal process group with SIGTERM
2. wait bounded interval
3. signal process group with SIGKILL if still alive
4. reap child
5. verify no `cnss-daemon`/`cnss_diag` remains
6. remove private namespace/runtime paths
7. capture postflight inventory

Failure cleanup:

- if the process cannot be killed/reaped: `start-only-reboot-required`
- if ICNSS/WLAN state drifts unexpectedly: `start-only-reboot-required`
- if serial/NCM control is lost: stop automation and request operator recovery
- recovery remains reboot-only per v223

## Evidence Output

```text
tmp/wifi/v245-cnss-start-only-runner/
├── manifest.json
├── prerequisite-checks.json
├── preflight.json
├── dry-run-plan.json
├── start-observation.json
├── postflight.json
├── cleanup.json
├── commands/
└── summary.md
```

Decision labels:

- `dry-run-ready`
- `preflight-ready`
- `start-only-pass`
- `start-only-runtime-gap`
- `start-only-reboot-required`
- `start-only-blocked`
- `manual-review-required`

## Test Plan

Static:

```bash
scripts/revalidation/build_android_execns_probe_helper.sh
python3 -m py_compile scripts/revalidation/wifi_cnss_start_only_runner.py
git diff --check
```

Safe live modes:

```bash
python3 scripts/revalidation/wifi_cnss_start_only_runner.py plan \
  --out-dir tmp/wifi/v245-cnss-start-only-runner-plan

python3 scripts/revalidation/wifi_cnss_start_only_runner.py preflight \
  --out-dir tmp/wifi/v245-cnss-start-only-runner-preflight

python3 scripts/revalidation/wifi_cnss_start_only_runner.py dry-run \
  --out-dir tmp/wifi/v245-cnss-start-only-runner-dryrun
```

Live daemon mode is not part of automatic validation. It requires explicit
operator approval after reviewing preflight/dry-run evidence.

## Acceptance For v245 Planning

- v245 plan is documented and linked from task queue and next-work docs.
- Existing v244 evidence is not regressed.
- The plan makes daemon execution impossible by default.
- The plan explains why v229 `runandroid` path is superseded by the v244 private
  execution namespace.
- The next implementation can proceed through `plan/preflight/dry-run` without
  asking for daemon-start approval.
