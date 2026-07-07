# S22+ EUD Source Analysis + Phase-B Gate Source (2026-07-08)

## Verdict

HOST-ONLY SOURCE ANALYSIS PASS. PHASE-B GATE SOURCE READY, POLICY INERT.

No EUD enable write, no sysfs write, no flash, no reboot, no partition write, no
module insertion, and no native-init candidate ran in this unit.

## Why This Unit

After M18 no-hit, the native-init path needs a stronger live progress channel.
GOAL's fallback ladder is:

```text
sec_debug/MID -> EUD -> UART
```

sec_debug/MID is proven for a real kernel panic but did not retain M18 native
evidence. EUD Phase-A already proved the S22+ has `eud.ko` loaded, the
`88e0000.qcom,msm-eud` platform node bound, and `/dev/ttyEUD0` present, but it
found no generic platform-node `enable` attribute. This unit inspected the FYG8
Android 15 source package to find the real control path.

## Source Evidence

Source archive inspected read-only from:

```text
/home/temmie/.local/share/Trash/files/SM-S906N_15_Opensource.zip
```

Nested source path:

```text
Kernel.tar.gz:
  kernel_platform/msm-kernel/drivers/soc/qcom/eud.c
  kernel_platform/qcom/proprietary/devicetree/bindings/soc/qcom/qcom,msm-eud.yaml
  kernel_platform/qcom/proprietary/devicetree/qcom/waipio.dtsi
  kernel_platform/qcom/proprietary/devicetree/qcom/waipio-usb.dtsi
```

Key findings:

- `eud.c` exposes a module parameter:
  `module_param_cb(enable, &eud_param_ops, &enable, 0644)`.
- `param_eud_set()` accepts only `0` or `1`. When `eud_ready`, `1` calls
  `enable_eud(eud_private)` and `0` calls `disable_eud(eud_private)`.
- `enable_eud()` performs the hardware transition: extcon spoof disconnect,
  EUD clkref vote, CSR enable, IRQ enable, secure EUD SCM write when
  `qcom,secure-eud-en` is set, then extcon USB/SDP connect.
- `disable_eud()` reverses the same path and drops the clkref vote.
- The UART driver registers as `driver_name="msm-eud"`, `dev_name="ttyEUD"`,
  `nr=1`; the console pointer is `NULL`, so `/dev/ttyEUD0` is a TTY endpoint,
  but not registered as a kernel console by this driver.
- `waipio.dtsi` defines `qcom,msm-eud@88e0000` with `reg-names =
  "eud_base", "eud_mode_mgr2"`, clock `GCC_EUSB3_0_CLKREF_EN`, and
  `qcom,secure-eud-en`.
- `waipio-usb.dtsi` wires the USB controller to `extcon = <&eud>` and the HS PHY
  has an `eud_enable_reg` resource at `0x088e2000`.

## Live Read-Only Correction

A read-only ADB check confirmed the module parameter exists on the live rooted
device:

```text
/sys/module/eud/parameters/enable: rw-r--r--, value 0
/dev/ttyEUD0: present
/sys/devices/platform/soc/88e0000.qcom,msm-eud/tty/ttyEUD0/console: N
runtime_status: unsupported
```

Therefore the Phase-A interpretation is refined:

```text
No platform-node enable attr was found, but the real control is the eud module
parameter at /sys/module/eud/parameters/enable.
```

## Added Helper

`workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py`

Modes:

- `--offline-check`: verify inert policy draft markers; no device action.
- `--print-plan`: print attended operator plan; no device action.
- `--read-only-check`: verify Android/root, Magisk boot hash, EUD module
  parameter, `/dev/ttyEUD0`, and host USB baseline; no write and no policy
  needed.
- default dry-run: once policy is active, verify AGENTS marker, Android/root,
  Magisk boot hash, EUD state, and host baseline.
- `--live`: once policy is active, write `1` to
  `/sys/module/eud/parameters/enable`, collect host `lsusb`/dmesg evidence, and
  write `0` back before exit.

## Phase-B Safety Shape

Phase-B is not a native-init boot flash. It is an Android-side reversible
sysfs/module-param test. It still changes the USB-C debug mux state, so it
requires a fresh attended `AGENTS.md` exception before live.

Authorized live surface in the inert draft:

```text
write 1 -> /sys/module/eud/parameters/enable
collect host lsusb/dmesg
write 0 -> /sys/module/eud/parameters/enable
```

Explicitly not authorized:

```text
flash, reboot, partition write, native-init boot candidate, module insertion,
DTBO/vendor_boot/vbmeta/recovery writes, additional sysfs writes
```

## Validation

Commands:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py \
  --offline-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py \
  --print-plan

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py \
  --read-only-check

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py
```

Results:

```text
py_compile: pass
offline-check: pass; no device action
print-plan: pass; no device action
default execution: rc=1, fail-closed before Android because AGENTS.md lacks EUD Phase-B markers
read-only-check: pass; no write/reboot/flash
```

Read-only check private log, not committed:

```text
workspace/private/runs/s22plus_eud_phase_b_enable_20260707T214930Z
```

Read-only check result:

```text
Android/root stability: OK
current boot hash: 2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
/sys/module/eud/parameters/enable: present, rw-r--r--, value 0
/dev/ttyEUD0: present, crw-------, major 496 minor 0
ttyEUD0 console flag: N
eud module: loaded
platform: DRIVER=msm-eud
host lsusb EUD hint: false
writes_performed: false
```

## Next

Next actionable step, only with explicit attended approval, is to promote the
narrow Phase-B exception and run the reversible `enable=1` -> host
`lsusb`/dmesg -> `enable=0` test. Do not run a native-init boot candidate for
EUD before this cheaper Android-side EUD attach test.
