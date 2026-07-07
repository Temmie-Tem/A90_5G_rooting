# S22+ EUD Phase-A Read-Only Probe (2026-07-08)

## Verdict

PASS / READ-ONLY / EUD PRESENT.

Codex added and ran a narrow EUD Phase-A inventory helper:

```text
workspace/public/src/scripts/revalidation/s22plus_eud_phase_a_readonly_probe.py
```

The helper performed no flash, reboot, partition write, sysfs write, module
insertion, EUD enable, or Odin transfer. It only verified the current rooted
Android baseline, checked the Magisk boot hash, and read EUD-related state.

Private run, not committed:

```text
workspace/private/runs/s22plus_eud_phase_a_readonly_20260707T205129Z
```

## Result

Public metadata:

```text
mode                         eud_phase_a_readonly_probe
writes_performed             false
reboots_performed            false
flashes_performed            false
sysfs_writes_performed       false
modules_inserted             false
eud_enable_attempted         false

eud_module_file_found        true   (/vendor_dlkm/lib/modules/eud.ko)
eud_module_loaded            true
eud_platform_bound           true   (88e0000.qcom,msm-eud, DRIVER=msm-eud)
eud_sysfs_path_count          11
eud_dt_compatible_hit         true
eud_dt_path_count             14
eud_enable_attr_count         0
eud_tty_present              true   (/dev/ttyEUD0, major 502 minor 0)
console_route_candidate       true
phase_b_enable_candidate      false
host_eud_usb_hint             false
```

Key raw facts:

```text
lsmod/proc_modules: eud 32768 0
module file:        /vendor_dlkm/lib/modules/eud.ko
platform node:      /sys/devices/platform/soc/88e0000.qcom,msm-eud
DT node:            /sys/firmware/devicetree/base/soc/qcom,msm-eud@88e0000
DT compatible:      qcom,msm-eud
DT status:          ok
DT interrupt-name:  eud_irq
tty driver:         msm-eud /dev/ttyEUD major 502
device tty:         /dev/ttyEUD0
tty console flag:   N
extcon state:       USB=0, SDP=0, JIG=0
host USB baseline:  Samsung MTP/ADB only, no EUD hub/interface hint
```

`qcom,secure-eud-en` is present in the live device-tree node path, so the next
unit should treat EUD as security-gated/driver-specific rather than absent.

## Interpretation

This changes the EUD picture materially:

- EUD is not merely a vendor ramdisk module. On the current rooted Android
  baseline it is already loaded, bound to the live DT node, and exposes
  `/dev/ttyEUD0`.
- The original generic Phase-B plan, `echo 1 > /sys/.../eud/enable`, does not
  directly apply to this build because no `enable`/`enabled` sysfs attribute was
  present under the observed EUD paths.
- The host did not enumerate a Qualcomm EUD hub during the read-only baseline.
  Therefore `/dev/ttyEUD0` being present is a console-route opportunity, not yet
  proof that the USB-C debug hub is externally attached.

The next useful unit is host/source analysis of Samsung's `msm-eud` driver and
FYG8 kernel source to find the actual runtime control or boot parameter for the
EUD hub/COM path. If the driver shows that `ttyEUD0` is the expected console
endpoint, a later boot-only experiment can route `console=ttyEUD0` under the
normal S22+ flash gates. If it shows a runtime attach knob, make that a separate
attended ack-gated helper.

Do not run a blind EUD-enable write: Phase A found no enable attr to write.

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_a_readonly_probe.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_a_readonly_probe.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_a_readonly_probe.py
```

Results:

- `py_compile`: pass.
- `--offline-check`: pass, no device action.
- live Phase-A read-only probe: pass, no writes/reboots/flashes/sysfs writes.
