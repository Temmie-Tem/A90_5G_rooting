# V983 Android Service-Window Property Shim

- generated: `2026-05-26`
- scope: source/build-only
- decision: `v983-android-service-window-property-shim-pass`
- helper: `a90_android_execns_probe v166`
- evidence: `tmp/wifi/v983-android-service-window-property-shim/manifest.json`
- build artifact: `tmp/wifi/v983-execns-helper-v166-build/a90_android_execns_probe`
- build sha256: `f184d79c1e6a72b12a8db5f51310cc82599fa1fed9a7cdde3c9814732a7621a8`

## Summary

V982 showed that `wificond` still aborted after binder materialization, while the helper reported the private property service shim was disabled.

Helper `v166` enables the existing property service shim for the dedicated Android service-window mode when:

```text
wifi-companion-android-wifi-service-window-start-only
--allow-android-wifi-service-window
```

This keeps the dedicated one-flag service-window model but gives Android userspace actors the same private property service socket support already used by related composite modes.

## Patch

- bumped helper version to `a90_android_execns_probe v166`
- added Android service-window coverage to `property_service_shim_needed()`
- preserved V980 binder device materialization coverage
- preserved no-scan/connect/no-eSoC/no-credential guardrails

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
python3 -m py_compile scripts/revalidation/native_wifi_android_service_window_property_shim_v983.py
python3 scripts/revalidation/native_wifi_android_service_window_property_shim_v983.py
```

Result:

```text
decision: v983-android-service-window-property-shim-pass
pass: True
```

Verified checks:

- helper version string is `v166`
- property service shim gate includes Android service-window mode and allow flag
- binder materialization coverage remains intact
- static helper artifact was produced and version/mode strings are present

## Next

Deploy helper `v166`, then rerun the bounded Android service-window live proof.
