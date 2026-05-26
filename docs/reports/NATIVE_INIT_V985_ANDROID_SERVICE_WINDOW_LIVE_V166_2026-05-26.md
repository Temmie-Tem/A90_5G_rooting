# V985 Android Service-Window Live v166

- generated: `2026-05-26`
- scope: bounded start-only live proof
- decision: `v970-android-service-window-runtime-gap`
- pass: `True`
- evidence: `tmp/wifi/v985-android-service-window-live-v166/manifest.json`
- helper: `a90_android_execns_probe v166`

## Summary

V985 reran the Android service-window proof after V983/V984 enabled and deployed
the private property service shim for helper `v166`.

The property-service gap is now closed: the helper started the private property
shim and accepted three bounded Android service-window property writes. The
remaining runtime gap is `wificond` aborting with `SIGABRT` before the observe
window, while WLFW/BDF/`wlan0` preconditions remain absent.

## Findings

- `child_started=14`: all planned service-window actors were spawned.
- `property_service_shim.mode=auto`, `started=1`, `request_count=3`.
- Accepted property writes were limited to service-manager readiness and
  peripheral state markers.
- `wificond` exited by signal `6` before timeout.
- `per_mgr` exited early with code `0`.
- `cnss-daemon` was observable but required cleanup escalation after `TERM`.
- `wlfw_precondition_observed=0`; `wlan0` was not present.

## Guardrails

- no `qcwlanstate`
- no `IWifi.start`
- no `/dev/subsys_esoc0` open
- no eSoC ioctl
- no scan/connect/link-up
- no credential use
- no DHCP/route/external ping

## Validation

Command:

```bash
python3 scripts/revalidation/native_wifi_android_service_window_live_v970.py \
  --out-dir tmp/wifi/v985-android-service-window-live-v166 \
  --local-helper tmp/wifi/v983-execns-helper-v166-build/a90_android_execns_probe \
  --helper-sha256 f184d79c1e6a72b12a8db5f51310cc82599fa1fed9a7cdde3c9814732a7621a8 \
  --helper-marker "a90_android_execns_probe v166" \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-android-wifi-service-window \
  --allow-cleanup-reboot \
  --assume-yes \
  run
```

Result:

```text
decision: v970-android-service-window-runtime-gap
pass: True
wifi_bringup_executed: False
```

## Next

Build helper `v167` with service-window-only `wificond` ptrace crash capture,
then redeploy and rerun the same bounded live proof.
