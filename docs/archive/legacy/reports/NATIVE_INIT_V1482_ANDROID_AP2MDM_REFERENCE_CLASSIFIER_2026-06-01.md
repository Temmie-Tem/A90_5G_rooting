# Native Init V1482 Android AP2MDM Reference Classifier

## Summary

- Cycle: `V1482`
- Type: host-only classifier over existing Android-positive and native-negative evidence
- Decision: `v1482-android-gpio135-low-not-primary-gate-next-auto-boot-supervisor`
- Result: PASS
- Reason: Existing Android-positive evidence already shows that post-boot GPIO135/GPIO142 readback can be low while Android still reaches WLFW, BDF, FW-ready, and `wlan0`. Therefore a new native Wi-Fi test boot should not spend another cycle trying to hold GPIO135 from userspace. The next test boot should automatically run the Android-order provider/CNSS lower stack at boot and classify primary progress by WLFW/BDF/FW-ready/`wlan0`, while keeping GPIO135/GPIO142/pcie1/MHI as diagnostics.

## Inputs

- V914 Android timeline reclassifier: `docs/reports/NATIVE_INIT_V914_V913_ANDROID_TIMELINE_RECLASSIFIER_2026-05-26.md`
- V1291 static GPIO parity classifier: `docs/reports/NATIVE_INIT_V1291_STATIC_GPIO_PARITY_CLASSIFIER_2026-05-31.md`
- V1331 Android SDX50M timing handoff: `docs/reports/NATIVE_INIT_V1331_ANDROID_SDX50M_TIMING_HANDOFF_2026-05-31.md`
- V1348 Android WLFW request path classifier: `docs/reports/NATIVE_INIT_V1348_ANDROID_WLFW_REQUEST_PATH_CLASSIFIER_2026-06-01.md`
- V1480 AP2MDM hold live classifier: `docs/reports/NATIVE_INIT_V1480_AP2MDM_HOLD_LIVE_CLASSIFIER_2026-06-01.md`
- V1481 provider feasibility classifier: `docs/reports/NATIVE_INIT_V1481_AP2MDM_PROVIDER_FEASIBILITY_2026-06-01.md`

## Android Reference Facts

V914 reclassified the Android-positive V913 evidence and separated upper Wi-Fi
success from lower post-boot diagnostics:

- Android upper path positive:
  - service-notifier 180 connected;
  - service-notifier 74 connected;
  - `cnss-daemon wlfw_start`;
  - WLAN-PD indication;
  - BDF `regdb.bin` and `bdwlan.bin`;
  - `wlan0`.
- Android post-boot lower diagnostics not positive:
  - `subsys9/state = OFFLINING`;
  - GPIO142 IRQ total `0`;
  - current `ks = false`;
  - current MHI pipe fd `false`;
  - `pm-service` does not currently hold `/dev/subsys_esoc0`;
  - `mdm_helper` still holds `/dev/esoc-0`.

V1291 additionally shows static GPIO parity:

- native GPIO135: `out 0 16mA no pull`
- Android GPIO135: `out 0 16mA no pull`
- native GPIO142: `in 0 8mA no pull`
- Android GPIO142: `in 0 8mA no pull`

This means post-boot GPIO135/GPIO142 low readback is not, by itself, a proof
that Android did not trigger SDX50M/Wi-Fi. Android can show low readback after
the successful path has already produced `wlan0`.

## Native Negative Facts

V1470-V1481 remain important, but their interpretation changes:

- Native has provider/AP2MDM set-high trace evidence.
- Native readback still samples GPIO135 low and GPIO142 low.
- Native pcie1, MHI, WLFW, BDF, FW-ready, and `wlan0` remain absent.
- V1480 proves userspace cannot hold GPIO135 through sysfs because the line is kernel-owned.
- V1481 proves the kernel-provider patch route is not currently live-feasible because custom OSRC kernels remain boot-incompatible.

Therefore the current blocker should not be phrased as "GPIO135 is low" alone.
The stronger blocker is:

```text
native boot reaches provider/AP2MDM trace
  -> no WLFW/BDF/FW-ready/wlan0 primary progress
  -> lower diagnostics also stay negative
```

## Decision

The next test boot should be an automated Wi-Fi readiness boot, but not a
credentialed Wi-Fi connect boot yet.

Primary success criteria:

1. `cnss-daemon` emits WLFW start/request markers.
2. ICNSS/QMI or WLFW service progress appears.
3. BDF transfer markers appear.
4. FW-ready appears.
5. `/sys/class/net/wlan0` exists.

Diagnostic secondary markers:

- GPIO135/AP2MDM trace and readback;
- GPIO142/MDM2AP IRQ/readback;
- pcie1 GDSC/clock/LTSSM;
- MHI bus and pipe;
- `ks`;
- service-manager/PM provider liveness.

Blocked until `wlan0` exists:

- Wi-Fi HAL scan/connect;
- credential materialization;
- DHCP/routes;
- external ping.

## Next Gate

V1483 should be source/build-only:

`v1483-wifi-auto-readiness-test-boot-design`

Scope:

- add a rollbackable PID1 test-boot mode that automatically starts the
  Android-order provider/CNSS readiness chain during boot;
- keep it credential-free and below scan/connect;
- summarize progress by the primary WLFW/BDF/FW-ready/`wlan0` checkpoints;
- keep GPIO135/GPIO142/pcie1/MHI as diagnostic state, not as sole pass/fail
  blockers;
- preserve rollback to `stage3/boot_linux_v724.img`.

The user's "Wi-Fi boot test image" direction is correct, but this classifier
sets the first boot-test objective precisely: prove automatic boot-time
progress to `wlan0` before introducing SSID/password or external ping.

## Safety Scope

V1482 is host-only. It performs no device command, no helper deployment, no
flash, no reboot, no Wi-Fi HAL, no scan/connect, no credential use, no
DHCP/routes, no external ping, no PMIC/GPIO/GDSC/eSoC write, no PCI rescan, and
no platform bind/unbind.

