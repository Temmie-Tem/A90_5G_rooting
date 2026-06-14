# Native Init V629 Sibling-SSCTL Trigger Classifier Report

- date: `2026-05-23 KST`
- status: `classified`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_sibling_ssctl_trigger_classifier_v629.py`
- evidence: `tmp/wifi/v629-sibling-ssctl-trigger-classifier/`
- decision: `v629-boot-time-sibling-ssctl-candidate-classified`

## Scope

V629 is host-only. It reads V614 vendor init evidence, native v319 source, V622
Android timing, V627 safe native observer evidence, V619 unsafe native evidence,
and V628's service `74` classifier result.

No device command, sysfs write, boot image build/flash, DSP live retry,
`esoc0` open, daemon start, service-manager start, Wi-Fi HAL start,
scan/connect/link-up, credential, DHCP, route change, or external ping was
executed.

## Result

```text
decision: v629-boot-time-sibling-ssctl-candidate-classified
pass: True
reason: Android's visible sibling-SSCTL trigger is early-boot ADSP/CDSP/SLPI boot-node writes; native v319 lacks an equivalent boot-time path, V627 proves the safe modem-only path stops at service 180, and V619 proves late direct writes are unsafe and still do not publish service 74.
next: V630 should be a rollback-ready, opt-in boot-time one-shot sibling-SSCTL proof; keep HAL/qcwlanstate/connect blocked
```

## Evidence Matrix

| subject | classification | evidence | next |
| --- | --- | --- | --- |
| Android trigger contract | early-boot DSP writes | V614 vendor init writes ADSP/CDSP/SLPI boot nodes; V622 has sibling sysmon and service `74` | treat this as a boot-time candidate, not a late live retry |
| Native v319 source | missing equivalent | no ADSP/CDSP/SLPI boot-node reference found under `stage3/linux_init/` | native boot image currently lacks the Android-equivalent early path |
| V627 safe path | modem-only partial positive | service-locator and `180` present; sibling sysmon and `74` absent; warning count `0` | lower sibling trigger is still missing before HAL/connect |
| V619 late direct write | unsafe negative | ADSP/CDSP/SLPI writes reached sibling sysmon but warning count was `21` and service `74` stayed absent | do not repeat late direct boot-node live tests |
| Next gate | boot-time opt-in proof | requires rollback image, rescue path, marker-only success, and no Wi-Fi bring-up | design V630 as a minimal one-shot boot-time experiment |

## Interpretation

The best current candidate is not another userspace daemon retry and not a
late sysfs live write. Android performs visible ADSP/CDSP/SLPI boot-node writes
during early boot, while native v319 does not. The safe modem-only path reaches
`service-notifier 180`, so the remaining blocker is below Wi-Fi HAL and above
or at the sibling SSCTL publication layer.

V619 proves the safety boundary: writing the same boot nodes late in a live
session is not equivalent to Android early boot. It produced kernel warnings
and still failed to publish service `74`, so V630 must be a boot-time one-shot
proof with rollback, not a manual live retry.

`boot_wlan`, `qcwlanstate`, and Wi-Fi HAL remain blocked. They are later WLAN
controls and should not be touched until service `74`, WLAN-PD, or WLFW/BDF
markers advance under native init.

## Validation

```text
python3 -m py_compile scripts/revalidation/native_wifi_sibling_ssctl_trigger_classifier_v629.py
python3 scripts/revalidation/native_wifi_sibling_ssctl_trigger_classifier_v629.py --out-dir tmp/wifi/v629-sibling-ssctl-trigger-classifier run
```

Both commands passed.

## Next Gate

Proceed to V630 planning:

1. create a rollback-ready opt-in boot image experiment;
2. perform ADSP/CDSP/SLPI boot-node writes once during native early boot;
3. collect only marker evidence for sibling sysmon, service `74`, WLAN-PD, and
   kernel warnings;
4. boot back to the known-good image and verify cleanup;
5. keep service-manager, HAL, scan/connect, credentials, DHCP, routes, and
   external ping blocked.

