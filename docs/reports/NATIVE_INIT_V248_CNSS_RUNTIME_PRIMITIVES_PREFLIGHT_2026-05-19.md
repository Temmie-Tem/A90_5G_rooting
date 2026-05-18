# Native Init v248 CNSS Runtime Primitive Preflight Report

## Summary

- status: PASS
- decision: `cnss-runtime-primitives-ready-for-live-approval`
- boot image change: none
- daemon start: not executed
- output: `tmp/wifi/v248-cnss-runtime-primitives-preflight/`
- host tool: `scripts/revalidation/wifi_cnss_runtime_primitives_preflight.py`

v248 collected current no-start evidence before any first bounded `cnss-daemon`
start-only attempt. It confirms that the v247 helper and private namespace path
are still healthy, while keeping Android runtime gaps explicit.

## Validation

Static checks:

```bash
python3 -m py_compile scripts/revalidation/wifi_cnss_runtime_primitives_preflight.py
git diff --check
```

Live read-only collection:

```bash
python3 scripts/revalidation/wifi_cnss_runtime_primitives_preflight.py \
  --out-dir tmp/wifi/v248-cnss-runtime-primitives-preflight
```

Result:

```text
decision: cnss-runtime-primitives-ready-for-live-approval
pass: True
```

Post-check:

```bash
python3 scripts/revalidation/a90ctl.py run /cache/bin/toybox pidof cnss-daemon || true
```

Result: `pidof` returned rc=1, so `cnss-daemon` was not running after v248.

## Required Checks

| Check | Result | Notes |
| --- | --- | --- |
| v242 prerequisite | PASS | `cnss-runtime-inventory-ready-for-launcher-contract-plan` |
| v243 prerequisite | PASS | `cnss-launcher-contract-ready` |
| v244 prerequisite | PASS | `cnss-identity-probe-pass` |
| v247 report gate | PASS | `v247-safe-body-ready-live-approval-required` present |
| helper SHA | PASS | `77fbdcdcbc6774abe5e34712097496edbac4a4ed763d87c82cf02effb88cd319` |
| helper no-allow namespace | PASS | `helper_status=namespace-ready` |
| helper no-allow guard | PASS | `cnss_start.result=start-only-blocked`, `exec_attempted=0` |
| private CNSS target | PASS | helper private `/vendor/bin/cnss-daemon` exists and is executable |
| linker64 mounted evidence | PASS | `/mnt/system/system/bin/linker64` present |
| active wlan interface | PASS | no `wlan*` in `/proc/net/dev` |

## Runtime Gap Matrix

| Primitive | State | Classification | Meaning |
| --- | --- | --- | --- |
| property service socket | missing | expected runtime gap | daemon may fail if it requires Android property service |
| Android property area | missing | expected runtime gap | property reads may differ from Android boot |
| SELinux null | missing | known gap | Android service domain transition is not recreated |
| `/dev/diag` | missing | phase2 blocker | `cnss_diag` remains blocked |
| `/dev/qrtr` | missing | runtime risk | QMI/PDR expectations may cause early daemon exit |
| global `/vendor` path | missing | expected private namespace only | approved start-only must use helper private namespace |

## Important Correction

The first v248 run incorrectly treated `/mnt/system/vendor/bin/cnss-daemon` as a
required global evidence path. On this native setup, `/mnt/system/system/vendor`
is the Android symlink to `/vendor`, while the helper mounts vendor privately in
its temporary namespace. The required check was corrected to use helper-emitted
`context.target.exists=1` and `context.target.access_x=1` evidence for private
`/vendor/bin/cnss-daemon`.

## Guardrails Preserved

- no `--allow-cnss-start-only`
- no `cnss-daemon` execution
- no `cnss_diag`
- no rfkill unblock, `wlan*` link-up, scan/connect, credentials, DHCP, or routing
- no ICNSS bind/unbind, firmware mutation, Android partition write, or reboot

## Next Step

v248 does not approve live daemon execution by itself. The next decision is one
of:

1. request explicit operator approval for exactly one bounded v247 live
   start-only run, with reboot-only recovery accepted; or
2. continue no-start analysis around missing property/QRTR/SELinux primitives.
