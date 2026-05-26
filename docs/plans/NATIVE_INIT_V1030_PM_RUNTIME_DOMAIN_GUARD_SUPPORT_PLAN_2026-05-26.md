# V1030 PM Runtime Domain Guard Support Plan

- date: `2026-05-26`
- type: source/build-only
- input: `docs/reports/NATIVE_INIT_V1029_PM_RUNTIME_INPUT_DELTA_2026-05-26.md`

## Objective

Add fail-closed helper support so PM actor startup can require the requested
Android SELinux exec context to be visible before `execv`. This prevents another
blind PM full-contract live retry from entering the same `pm_proxy_helper`
D-state when `/proc/self/attr/exec` remains `kernel`.

## Change

Add helper `v175` support for:

```text
--require-android-selinux-exec-match
```

When enabled, after writing the target Android context to
`/proc/self/attr/exec`, the child re-reads `attr/exec` and fails before `execv`
if it does not exactly match the requested context.

## Guardrails

- source/build-only
- no helper deploy
- no device command
- no actor start
- no daemon start
- no Wi-Fi HAL, scan/connect, credentials, DHCP, route, or external ping
- no eSoC ioctl, subsystem open, GPIO/sysfs/debugfs write
- no boot image or partition write

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_runtime_domain_guard_support_v1030.py
python3 scripts/revalidation/native_wifi_pm_runtime_domain_guard_support_v1030.py
```

## Next

If V1030 passes, V1031 should deploy helper `v175` only. The following live gate
should use the new flag and remain bounded; it should prove runtime-domain
parity or fail before unsafe PM actor exec.
