# Native Init V586 QRTR Companion Blocker Plan

- date: `2026-05-22 KST`
- objective: classify the post-V585 QRTR/control-plane blocker before any qcwlanstate, Wi-Fi HAL, scan/connect, or boot-time probe retry
- status: `planned`

## Context

V585 proved that helper-private `apnhlos` and `modem` mounts can be created in the same private namespace as the Android companion processes. The companion window was observable and cleanup-safe, but it still produced no QRTR modem readiness, WLFW, QMI server, BDF, firmware-ready, or `wlan0` marker.

The prior V572 boot-time probe caused a boot loop before USB/ADB evidence returned, so V586 must not add PID1 boot-time execution or flash a new boot image.

## Guardrails

- No boot image flash.
- No reboot or recovery handoff.
- No PID1/native-init boot hook.
- No daemon start from V586.
- No qcwlanstate/sysfs driver-state write.
- No Wi-Fi HAL or `IWifi.start()`.
- No supplicant/hostapd/wificond.
- No scan/connect/link-up/DHCP/routing.
- No external ping.

## Implementation

Add `scripts/revalidation/native_wifi_qrtr_companion_blocker_v586.py`:

1. `plan`: host-only, no device command.
2. `run`: read-only live captures only:
   - `version`, `status`, `selftest`
   - `/proc/net/protocols`, `/proc/net/qrtr`, `/proc/net/dev`
   - `/dev/qrtr` stat
   - targeted `/sys` surface listing for QRTR/RPMSG/subsys/service-notifier/sysmon/WLAN hints
   - `ps` and `dmesg`
3. Parse existing V585 evidence:
   - helper private firmware mount readiness
   - child preexec/SELinux/capability success keys
   - companion process socket counts
   - helper `/proc/<pid>/net/qrtr` capture result
   - `QIPCRTR` socket count
   - dmesg readiness marker counts
4. Compare against Android reference markers from V206/V521/V571.
5. Emit a private evidence bundle under `tmp/wifi/v586-qrtr-companion-blocker/`.

## Success Criteria

V586 passes if it produces a defensible classification that either:

- finds a new lower-layer readiness marker and routes the next gate toward bounded qcwlanstate/HAL retry; or
- confirms the V585 blocker remains below qcwlanstate/HAL and routes the next gate toward QRTR/modem readiness inputs, not another same-window Wi-Fi retry.

## Expected Decision

Likely decision: `v586-qrtr-control-plane-not-entered`.

That means: Android has QRTR/QMI/WLAN-PD/WLFW/BDF evidence, but native V585 only proves process launch, private firmware mounts, CNSS netlink, and cleanup. QRTR modem readiness and WLFW service discovery are still missing.

## References

- Linux QRTR AF_QIPCRTR implementation: `https://codebrowser.dev/linux/linux/net/qrtr/af_qrtr.c.html`
- Android common QRTR implementation reference: `https://android.googlesource.com/kernel/common/+/d4d74449367e/net/qrtr/qrtr.c`
- Android service-notifier reference: `https://android.googlesource.com/kernel/msm/+/refs/heads/android-msm-crosshatch-4.9-s-preview-1/drivers/soc/qcom/service-notifier.c`
- Android sysmon-qmi reference: `https://android.googlesource.com/kernel/msm/+/refs/heads/android-msm-crosshatch-4.9-s-preview-1/drivers/soc/qcom/sysmon-qmi.c`

## Next Gate After V586

If no marker appears, do not retry qcwlanstate or HAL yet. The next useful gate is a bounded QRTR/modem readiness input proof that stays after boot and host-controlled, such as:

1. compare Android/native QRTR endpoint and `/proc/net/protocols` details with improved socket-domain evidence;
2. inspect modem/rpmsg/subsys readiness surfaces immediately before and during companion windows;
3. only after a lower marker changes, allow a bounded qcwlanstate/HAL retry.
