# Native Init v248 CNSS Runtime Primitive Preflight Plan

## Summary

- target: v248 no-start CNSS runtime primitive preflight
- baseline: v247 `v247-safe-body-ready-live-approval-required`
- new host tool: `scripts/revalidation/wifi_cnss_runtime_primitives_preflight.py`
- boot image change: none
- daemon start: not executed

v248 runs before any first live `cnss-daemon` start-only attempt. Its goal is to
turn the remaining runtime uncertainties into a compact, current, read-only
checklist: property service visibility, Android property area, SELinux state,
`/dev/diag`, QRTR/IPC surfaces, global-vs-private path aliases, and v247 helper
no-allow namespace health.

## Why v248 Is Needed

v247 created a real guarded start/observe/stop body, but it deliberately stopped
at `LIVE APPROVAL REQUIRED`. Before asking for or using that approval, we want a
fresh no-start evidence bundle that answers:

1. Are the expected native-control paths still stable?
2. Is the v247 helper deployed with the expected hash?
3. Does the v247 no-allow helper path still reach `namespace-ready`?
4. Which Android runtime primitives are definitely missing in native root?
5. Which missing primitives are acceptable expected gaps for a bounded
   start-only test, and which should block live execution?

This does not try to emulate Android framework or property service. It only
classifies the current state so the next live approval discussion is concrete.

## Scope

Collect only read-only evidence:

- `version`, `status`, `bootstatus`, `selftest verbose`
- `netservice status`, `mountsystem ro`, `wifiinv full`, `kernelinv summary`
- `/proc/net/dev`, `/proc/net/netlink`, `/proc/mounts`
- `/dev/socket`, `/dev/socket/property_service`, `/dev/__properties__`
- `/sys/fs/selinux`, `/sys/fs/selinux/null`, `/sys/fs/selinux/enforce`
- `/dev/diag`, `/dev/qrtr`, `/dev/ipa`, `/dev/wlan`, matching `find /dev`
- `/sys/class/net`, `/sys/class/rfkill`, `/sys/class/ieee80211`
- v247 helper `sha256sum`
- v247 helper no-allow `--mode cnss-start-only` run

## Explicit Non-Goals

v248 must not do any of the following:

- start `/vendor/bin/cnss-daemon`
- pass `--allow-cnss-start-only`
- run `cnss_diag`
- unblock rfkill
- link up `wlan*`
- scan/connect Wi-Fi
- start supplicant/HAL/wificond/hostapd
- mutate firmware path
- bind/unbind ICNSS
- write to Android partitions
- reboot automatically

## Output

Recommended output directory:

```text
tmp/wifi/v248-cnss-runtime-primitives-preflight/
├── manifest.json
├── runtime-primitives.json
├── live-captures.json
├── helper-noallow.txt
├── summary.md
└── captures/*.txt
```

Decision labels:

- `cnss-runtime-primitives-ready-for-live-approval`: no-start evidence is
  current and known gaps are compatible with a bounded start-only attempt.
- `cnss-runtime-primitives-blocked`: required control/helper/preflight evidence
  failed.
- `cnss-runtime-primitives-manual-review`: unexpected state or ambiguous gaps.

## Expected Gap Classification

Expected gaps that do not automatically block a bounded start-only test:

- global `/vendor/bin/cnss-daemon` absent outside the private helper namespace
- `/dev/socket/property_service` absent
- `/dev/__properties__` absent
- `/dev/diag` absent for `cnss_diag` phase2
- `/dev/qrtr` absent if only classified as runtime risk
- SELinux Android domain transition not reproduced by native init

Hard blockers:

- bridge/control path failure
- v247 helper hash mismatch
- v247 no-allow helper does not reach `namespace-ready`
- v247 no-allow helper does not report `start-only-blocked`
- active unexpected `wlan*` interface before start-only
- `cnss-daemon` already running
- required system/vendor assets missing inside the helper private namespace

## Validation Plan

Static:

```bash
python3 -m py_compile scripts/revalidation/wifi_cnss_runtime_primitives_preflight.py
git diff --check
```

Live read-only validation:

```bash
python3 scripts/revalidation/wifi_cnss_runtime_primitives_preflight.py \
  --out-dir tmp/wifi/v248-cnss-runtime-primitives-preflight
```

Acceptance:

- `daemon_start_executed=false`
- helper no-allow result is `start-only-blocked`
- required live captures pass
- decision is one of the documented labels
- no `cnss-daemon` process remains after validation

## Next Step

If v248 returns `cnss-runtime-primitives-ready-for-live-approval`, the next step
is still an explicit operator approval decision for the first bounded v247 live
start-only run. If approval is not given, continue with no-start analysis or
runtime primitive documentation. If v248 blocks, fix the blocker before any live
start discussion.
