# V1030 PM Runtime Domain Guard Support

- date: `2026-05-26`
- scope: source/build-only
- helper: `a90_android_execns_probe v175`
- decision: `v1030-pm-runtime-domain-guard-support-pass`
- pass: `True`
- evidence: `tmp/wifi/v1030-pm-runtime-domain-guard-support/manifest.json`
- artifact: `tmp/wifi/v1030-execns-helper-v175-build/a90_android_execns_probe`
- artifact sha256: `9036bb15ced9fb1098c4375c15c2c729502c841574ae14798fb331fc29c89e42`

## Summary

V1030 adds a fail-closed SELinux exec-match guard to helper `v175`.

New flag:

```text
--require-android-selinux-exec-match
```

When enabled, each child that requests an Android service context now re-reads
`/proc/self/attr/exec` after writing the target context. If the observed value
does not exactly match the requested context, the child exits before `execv`.

## Why This Matters

V1029 proved the current blocker:

```text
Android PM actor domain = vendor domain
Native requested target context = accepted
Native captured attr/current = kernel
```

V1030 does not claim to fix the SELinux transition itself. It adds the missing
safety and observability layer so the next live proof can fail closed before
executing `pm_proxy_helper` in a known-bad context.

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_runtime_domain_guard_support_v1030.py
python3 scripts/revalidation/native_wifi_pm_runtime_domain_guard_support_v1030.py
```

Result:

```text
decision: v1030-pm-runtime-domain-guard-support-pass
pass: True
```

Source/build checks passed:

| Check | Result |
| --- | --- |
| version marker `v175` | PASS |
| CLI flag present | PASS |
| config field and parser present | PASS |
| match-required logging present | PASS |
| observed/expected exec context logging present | PASS |
| mismatch fails before `execv` | PASS |
| helper static build | PASS |
| artifact strings include marker/flag/match key | PASS |

## Guardrails

- Source/build-only verifier.
- No helper deploy, device command, actor start, daemon start, Wi-Fi HAL,
  scan/connect, credential use, DHCP/route, external ping, eSoC ioctl,
  `/dev/subsys_esoc0` open, GPIO/sysfs/debugfs write, boot image write, or
  partition write occurred in V1030.

## Next

V1031 should deploy helper `v175` only and verify remote sha/usage parity. A
later bounded live proof should pass `--require-android-selinux-exec-match` and
stop before unsafe PM actor execution if `attr/exec` is still `kernel`.
