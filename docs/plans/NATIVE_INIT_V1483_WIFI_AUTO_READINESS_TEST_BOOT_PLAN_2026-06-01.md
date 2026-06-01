# Native Init V1483 Wi-Fi Auto-readiness Test Boot Plan

## Summary

- Cycle: `V1483`
- Type: implementation plan for the next rollbackable Wi-Fi test boot
- Decision: `v1483-plan-auto-readiness-test-boot-before-credentials`
- Goal: make the test boot do the useful work automatically at boot time, but stop at `wlan0` readiness before scan/connect, credentials, DHCP/routes, or external ping.

## Rationale

The user direction is correct: a dedicated test boot is faster than repeatedly
driving the same lower sequence from the host after native init has already
settled.

The V1482 correction matters for the exact target:

- GPIO135/GPIO142 low readback is not enough to drive another GPIO-hold cycle.
- Android-positive evidence can reach WLFW/BDF/`wlan0` while lower post-boot
  diagnostics are already quiet.
- The next test image should therefore classify automatic boot-time progress by
  WLFW, ICNSS/QMI or WLFW service progress, BDF, FW-ready, and `wlan0`.

## Non-goals

V1483/V1484 must not introduce:

- Wi-Fi HAL scan/connect;
- SSID/password/PSK materialization;
- DHCP/routes;
- external ping;
- direct PMIC/GPIO/GDSC writes;
- direct MMIO/pinctrl/GPIO register writes;
- blind eSoC notify/`BOOT_DONE`;
- global PCI rescan;
- platform bind/unbind;
- custom OSRC kernel flash.

The final goal still includes connecting to the target AP and pinging
`google.com`, but that remains gated on `wlan0` existence.

## Existing Infrastructure

The current rollbackable Wi-Fi test boot already has the right outer shape:

- `scripts/revalidation/build_native_init_wifi_test_boot_v1393.py` builds a
  static native init and bundles `/bin/a90_android_execns_probe`,
  `/bin/a90_tcpctl`, and `/bin/a90_rshell` into the ramdisk.
- `stage3/linux_init/v724/90_main.inc.c` has compile-time gated test-boot logic
  that spawns `/bin/a90_android_execns_probe`, writes `/cache` logs/summaries,
  supports debugfs setup/cleanup, and can roll back through the existing
  handoff wrappers.
- V1477/V1479 proved the source/build -> artifact sanity -> rollbackable
  handoff pattern works for a dedicated Wi-Fi test image.

## Implementation Shape

### V1484 helper/source build

Add a new helper summary mode or flag, tentatively:

```text
--pm-observer-auto-readiness-summary
```

Scope:

- reuse the existing Android-order provider/CNSS and current-route observer
  surfaces instead of adding a new lower mutation;
- collect a compact summary for:
  - service-manager/provider liveness;
  - `cnss-daemon` WLFW start/request markers;
  - ICNSS/QMI or WLFW service progress;
  - BDF `regdb.bin` / `bdwlan.bin`;
  - FW-ready;
  - `/sys/class/net/wlan0`;
  - GPIO135/GPIO142 diagnostics;
  - pcie1 GDSC/clock/LTSSM diagnostics;
  - MHI bus/pipe and `ks` diagnostics;
  - safety zeros for HAL, scan/connect, credentials, DHCP/routes, external ping.

The output should be single-line-key friendly, following existing
`cnss_wlfw_pre.*` and `mdm2ap_timing.*` conventions:

```text
auto_readiness.begin=1
auto_readiness.mode=boot-android-order-provider-cnss
auto_readiness.wlfw_start_seen=0|1
auto_readiness.icnss_qmi_seen=0|1
auto_readiness.bdf_seen=0|1
auto_readiness.fw_ready_seen=0|1
auto_readiness.wlan0_seen=0|1
auto_readiness.primary_checkpoint=...
auto_readiness.gpio135_last=...
auto_readiness.gpio142_last=...
auto_readiness.pcie1_last=...
auto_readiness.mhi_pipe_seen=0|1
auto_readiness.ks_seen=0|1
auto_readiness.safety_credentials_used=0
auto_readiness.safety_scan_connect=0
auto_readiness.safety_external_ping=0
auto_readiness.end=1
```

### V1485 test boot source/build

Add a compile-time gated PID1 boot mode, tentatively:

```text
A90_WIFI_TEST_BOOT_AUTO_READINESS_SUPERVISOR
```

Contract:

- marker: `auto-v1485-wifi-readiness-test`
- log: `/cache/native-init-wifi-test-boot-v1485.log`
- summary: `/cache/native-init-wifi-test-boot-v1485.summary`
- window result: `/cache/native-init-wifi-test-boot-v1485-readiness.result`
- helper path: `/bin/a90_android_execns_probe`
- timeout: bounded, recommended `45s`
- cleanup: kill helper process group, unmount debugfs if PID1 mounted it,
  leave v724 rollback image untouched.

The PID1 mode should run exactly one automatic readiness route first:

```text
service managers
  -> PM/provider chain
  -> companion/CNSS chain
  -> observe WLFW/BDF/FW-ready/wlan0
```

If the first implementation uses an existing helper mode, prefer the route that
most closely matches V1341/V1351 without adding HAL/scan/connect:

- Android-order provider/CNSS startup from
  `wifi-companion-android-order-pre-cnss-provider-observe-only`, plus
  readiness summary; or
- current-route `wifi-companion-post-pm-mdm-helper-esoc-observer`, plus
  readiness summary.

Do not run both routes in one first boot image unless cleanup and child
ownership are explicitly proven. One route per test boot keeps evidence
attributable.

### V1486 artifact sanity

Local-only checks before any flash:

- boot image uses v724 base header/kernel parity;
- ramdisk includes `/init`, `/bin/a90_android_execns_probe`,
  `/bin/a90_tcpctl`, `/bin/a90_rshell`;
- boot marker `auto-v1485-wifi-readiness-test` present;
- forbidden credential literal scan passes;
- helper is static aarch64 and marker version matches manifest;
- no HAL/scan/connect/ping strings are required for success;
- manifest records the exact helper mode and safety flags.

### V1487 rollbackable live handoff

Only after V1484-V1486 pass:

- flash only the V1485 test image;
- verify the expected `v1485-wifitest` init version;
- collect log, summary, readiness result, focused dmesg, and `wlan0` state;
- roll back to `stage3/boot_linux_v724.img`;
- verify v724 selftest `fail=0`;
- classify result host-only afterward.

## Success Criteria

Source/build success:

- helper and boot image build reproducibly;
- static checks pass;
- no credential literals appear in tracked files or artifacts;
- the summary contract is present in the image.

Live success for the first auto-readiness handoff:

- `wlan0_seen=1` is a major pass and unlocks the next gate: scan/connect design.
- WLFW/BDF/FW-ready without `wlan0` is partial progress and should classify the
  missing netdev edge.
- No WLFW/BDF/FW-ready/`wlan0` means the automatic boot route did not improve
  over V1479; classify by the new readiness summary rather than by GPIO135 alone.

## Next

V1484 should be source/build-only and add the compact helper readiness summary
needed by the test boot. No live action is required for V1484.

