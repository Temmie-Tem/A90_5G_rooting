# V986 Android Service-Window Wificond Trace

- generated: `2026-05-26`
- scope: source/build-only
- decision: `v986-android-service-window-wificond-trace-pass`
- pass: `True`
- evidence: `tmp/wifi/v986-android-service-window-wificond-trace/manifest.json`
- build artifact: `tmp/wifi/v986-execns-helper-v167-build/a90_android_execns_probe`
- build sha256: `fa96337b9103a411d6e229fe9ada744a6ed7df296f3d986e5a9d00a861736626`

## Summary

V986 adds the next diagnostic step for the V985 blocker. Helper `v167` keeps the
same Android service-window start-only mode but enables ptrace crash capture for
`wificond` only inside that dedicated mode.

This does not widen the Wi-Fi gate. It only records `SIGABRT` stop state,
siginfo, registers, maps, and compact memory context when `wificond` crashes in
the next service-window live proof.

## Patch

- bumped helper version to `a90_android_execns_probe v167`
- added `composite_child_should_trace()`
- preserved existing Wi-Fi HAL and CNSS ptrace paths
- added service-window-only `COMPOSITE_ID_WIFICOND` trace gating
- reused the existing compact crash capture path

## Guardrails

- source/build-only
- no device command from verifier
- no actor start
- no `qcwlanstate`
- no `IWifi.start`
- no `/dev/subsys_esoc0` open
- no eSoC ioctl
- no scan/connect/link-up
- no credential use
- no DHCP/route/external ping

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_android_service_window_wificond_trace_v986.py
python3 scripts/revalidation/native_wifi_android_service_window_wificond_trace_v986.py
```

Result:

```text
decision: v986-android-service-window-wificond-trace-pass
pass: True
```

Verified checks:

- helper version string is `v167`
- `wificond` tracing is limited to Android service-window mode and allow flag
- parent/child trace gates both use the shared trace predicate
- property shim and binder materialization coverage remain intact
- no-scan/connect/no-eSoC/no-credential guardrails remain present

## Next

Deploy helper `v167`, then rerun the bounded Android service-window live proof
and inspect the captured `wificond` crash context.
