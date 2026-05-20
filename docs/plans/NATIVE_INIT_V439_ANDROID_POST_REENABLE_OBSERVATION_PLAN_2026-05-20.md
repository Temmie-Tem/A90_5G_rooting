# Native Init V439 Android Post-reenable Observation Plan

Date: 2026-05-20

## Goal

V439 follows V438.  V438 re-enabled Android framework Wi-Fi and did not see
route/DNS/connectivity exposure during the short bounded window.  V439 extends
that observation and then restores containment with a final framework disable
cleanup.

The gate answers two questions:

```text
Does the V438 re-enabled Android Wi-Fi state persist into a fresh Android boot?
If it persists, does Android auto-connect and expose wlan0 route/DNS/connectivity?
```

## Scope

Allowed:

- boot Android to `sys.boot_completed=1` through the existing handoff wrapper;
- sample Wi-Fi status, `wlan0` address, routes, route-get, Android
  connectivity, filtered Wi-Fi dumpsys, and listening sockets over a bounded
  window;
- optionally run one cleanup mutation at the end:

  ```text
  cmd wifi set-wifi-enabled disabled
  ```

- restore native v319 and verify rollback.

Not allowed:

- Wi-Fi enable commands;
- explicit scan/connect or credential operations;
- DHCP, route, interface, sysfs/rfkill, module, property, or daemon-start
  mutation;
- external packet probes such as `ping`, `curl`, `nc`, `dig`, or `nslookup`;
- server exposure or new Wi-Fi-facing listeners.

## Implementation

- Collector: `scripts/revalidation/wifi_android_post_reenable_observation_v439.py`
  - reuses V438 redacted status/route/connectivity/listener captures;
  - samples for a configurable duration and interval;
  - allows only the optional final cleanup disable mutation;
  - classifies exposure and cleanup containment separately.
- Handoff: `scripts/revalidation/android_wifi_post_reenable_handoff_v439.py`
  - boots Android through the known baseline boot image;
  - waits for boot-complete;
  - runs the V439 collector;
  - restores native v319.

## Validation Plan

```text
python3 -m py_compile \
  scripts/revalidation/wifi_android_post_reenable_observation_v439.py \
  scripts/revalidation/android_wifi_post_reenable_handoff_v439.py

python3 scripts/revalidation/wifi_android_post_reenable_observation_v439.py \
  --out-dir tmp/wifi/v439-android-wifi-post-reenable-plan-<ts> \
  --sample-duration 60 --sample-interval 20 \
  --cleanup-disable --allow-wifi-disable-cleanup \
  --i-understand-android-wifi-cleanup-mutation \
  plan

python3 scripts/revalidation/android_wifi_post_reenable_handoff_v439.py \
  --out-dir tmp/wifi/v439-android-wifi-post-reenable-handoff-dryrun-<ts> \
  --allow-android-boot-flash --assume-yes --i-understand-native-rollback \
  --sample-duration 60 --sample-interval 20 \
  --cleanup-disable --allow-wifi-disable-cleanup \
  --i-understand-android-wifi-cleanup-mutation \
  dry-run

python3 scripts/revalidation/android_wifi_post_reenable_handoff_v439.py \
  --out-dir tmp/wifi/v439-android-wifi-post-reenable-handoff-live-<ts> \
  --allow-android-boot-flash --assume-yes --i-understand-native-rollback \
  --sample-duration 180 --sample-interval 30 \
  --cleanup-disable --allow-wifi-disable-cleanup \
  --i-understand-android-wifi-cleanup-mutation \
  run

python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py --json selftest
python3 scripts/revalidation/a90ctl.py --json status

git diff --check
```

## Expected Decisions

- `v439-android-wifi-post-reenable-plan-ready`
- `v439-android-wifi-post-reenable-preflight-ready`
- `v439-android-wifi-post-reenable-exposure-observed-cleanup-pass`
- `v439-android-wifi-post-reenable-enabled-contained-cleanup-pass`
- `v439-android-wifi-post-reenable-not-enabled-cleanup-pass`
- `v439-android-wifi-cleanup-disable-failed`
- `v439-android-wifi-cleanup-not-contained`
- `v439-handoff-dryrun-ready`

## Pass Criteria

A PASS decision must show:

- Android boot-complete passed before sampling;
- no Wi-Fi enable, scan/connect, credential, route/DHCP, sysfs/rfkill, module,
  property, daemon-start, server, or external probe operation ran;
- if cleanup is requested, the cleanup disable command succeeds;
- final cleanup removes active `wlan0` IP, route, route-get, DNS, validated
  Wi-Fi connectivity, and global listener exposure;
- native v319 rollback completes.

Wi-Fi exposure during the sample window is acceptable as observation evidence.
It does not approve server exposure or explicit scan/connect.

## Next Gate Rule

If V439 sees immediate Android auto-connect exposure, the next gate should treat
Android-managed Wi-Fi as functional but externally routed.  The safe follow-up
is policy-driven:

- either run an exposure-aware stability/read-only map; or
- proceed to an explicit scan/connect design only after credential and network
  target handling are documented.

Server exposure remains blocked until the Wi-Fi control policy is explicit.
