# Native Init V929 Current-v153 CNSS / Service-Manager Matrix Plan

## Goal

Design the next source/build-only unit after V927/V928 without repeating an
already-failed service-manager timing experiment.

V929 should add a current helper `v154` matrix mode that can compare CNSS Binder
behavior and lower publication behavior in the same repaired runtime namespace
used by helper `v153`.

## Why V929 Is Not A Simple V604 Repeat

Historical evidence already tested the simple ordering variants:

- V603: QRTR-first service-manager cleared CNSS Binder transaction failures, but
  service-notifier `180` disappeared.
- V604: CNSS-first delayed service-manager still missed service-notifier `180`
  and retained CNSS Binder failures.
- V605: host-only timing analysis showed simple short ordering changes were not
  sufficient.
- V606: no-service-manager baseline replay with helper `v102` still lost
  service-notifier `180`, narrowing the older gap to helper/runtime or lower
  publication state.

V927 is a newer, different surface:

- helper `v153`;
- compact CNSS output;
- repaired linkerconfig/APEX/property runtime namespace;
- `mdm_helper` reaches `/dev/esoc-0`;
- CNSS reaches `cld80211`;
- CNSS Binder failure still appears;
- WLFW/BDF/`wlan0` remain absent.

Therefore V929 should not simply rerun V603/V604 ordering. It should make the
current `v153` runtime able to answer the narrower question: whether Binder
failure can be removed without losing the lower publication/CNSS surface in the
same helper-owned namespace.

## Source/Build Scope

Add helper `v154` support only. Do not deploy or run live in V929.

Proposed mode:

```text
wifi-companion-mdm-helper-cnss-service-manager-matrix
```

Proposed allow flag:

```text
--allow-mdm-helper-cnss-service-manager-matrix
```

The mode should support explicit order variants, selected by a bounded enum:

```text
--service-manager-order none|before-cnss|after-cnss|after-mdm-helper-esoc-fd
```

Default should be `none` in plan/static mode and require explicit runner choice
for live use.

## Required Observability

The helper should report compact, final contract keys for each variant:

- runtime namespace:
  - linkerconfig mode;
  - APEX/VNDK alias mode;
  - Android SELinux context mode;
  - property root presence;
- actors attempted/started:
  - `pm-service`;
  - `mdm_helper`;
  - service-manager trio;
  - `cnss_diag`;
  - `cnss-daemon`;
- lower/CNSS signals:
  - `/dev/esoc-0` fd in `mdm_helper`;
  - `cld80211` reachability;
  - CNSS Binder failure count;
  - service-notifier `180`/`74` markers;
  - WLFW precondition;
  - BDF;
  - `wlan0`;
- safety:
  - service-manager lifecycle and postflight cleanup;
  - CNSS lifecycle and postflight cleanup;
  - no `/dev/subsys_esoc0` open unless a later, separate gate explicitly
    permits it.

## Hard Guardrails

- V929 itself is source/build-only.
- No helper deploy.
- No device command.
- No daemon start.
- No service-manager live start.
- No Wi-Fi HAL start.
- No scan/connect/link-up.
- No credential use.
- No DHCP, route change, or external ping.
- No eSoC ioctl, subsystem open, GPIO/sysfs/debugfs write, boot image write, or
  partition write.

## Success Criteria

- Helper version bumps to `a90_android_execns_probe v154`.
- Usage text exposes the new mode and allow flag.
- Static ARM64 helper build succeeds.
- Strings check confirms:
  - helper marker;
  - new mode;
  - new allow flag;
  - order enum strings;
  - existing compact CNSS-before-eSoC mode remains present.
- No live action, deploy, Wi-Fi HAL, scan/connect, credential, DHCP, route, or
  external ping is executed.

## Next

If V929 source/build passes, V930 should be deploy-only helper `v154`.

The first live matrix run should remain below Wi-Fi HAL and below scan/connect.
It should test only one order variant at a time, with compact output and
postflight cleanup, and should stop as soon as it can classify:

- Binder-clean but lower-publication-regressed;
- lower-publication-present but Binder-failed;
- both present;
- neither present;
- WLFW/BDF/`wlan0` advanced.
