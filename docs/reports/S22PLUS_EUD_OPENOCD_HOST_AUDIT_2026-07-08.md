# S22+ EUD OpenOCD Host Audit (2026-07-08)

## Verdict

HOST-ONLY PASS / SWD PATH NOT STAGED / NO DEVICE ACTION.

The EUD Phase-B live gate already proved that the no-jig runtime enable did not
produce a host EUD USB device or a new serial/TTY path. This unit checks the
remaining EUD-SWD/JTAG branch from the host side: whether OpenOCD and the needed
EUD/Qualcomm/SM8450 config are present locally.

Result:

```text
blocked_no_openocd
```

## Command

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_openocd_host_audit.py
```

Output:

```text
S22+ EUD OpenOCD host audit: blocked_no_openocd; openocd=0 eud_cfg=0 qcom_cfg=0 sm8450_cfg=0 host_eud_usb=0
```

Private summary:

```text
workspace/private/runs/s22plus_eud_openocd_host_audit_20260707T222229Z/summary.json
```

## Evidence

| Check | Result |
| --- | --- |
| `openocd` binary | absent |
| OpenOCD script dirs | none found |
| `interface/eud.cfg` | absent |
| Qualcomm target cfg | absent |
| SM8450 target cfg | absent |
| Current host EUD USB hint | false |
| Current host TTY paths | existing Android CDC ACM only |
| Consumed Phase-B summary | `restored_enable_0=true` |
| Phase-B host EUD/new TTY | false |
| Phase-B secure path hint | true |

Classification reasons:

```text
openocd-not-installed
missing-interface-eud-cfg
missing-qualcomm-target-cfg
missing-sm8450-target-cfg
phase-b-no-host-eud-or-new-tty
no-current-host-eud-usb
```

## Safety

The helper is host-only. It performs no ADB access, flash, reboot, partition
write, sysfs write, module insertion, EUD enable, Magisk action, or A90 action.
It only runs host commands such as `lsusb`, `lsusb -t`, and TTY path listing,
then reads the private Phase-B summary if present.

## Interpretation

The current host cannot run the proposed EUD-SWD probe:

- B2/no-jig EUD COM is already negative from the live Phase-B run.
- B1/EUD-SWD is not executable locally because OpenOCD and the relevant EUD /
  Qualcomm / SM8450 configs are not staged.
- The currently visible host serial path is the normal Android CDC ACM path, not
  evidence of an EUD debug interface.

Do not spend another native-init flash expecting EUD observability from the
current host state. The next useful unit is host-only OpenOCD-EUD staging under
`workspace/private/` or attaching the physical EUD/SWD hardware path, then
rerunning this audit.

## Validation

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_eud_openocd_host_audit.py \
  tests/test_s22plus_eud_openocd_host_audit.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests/test_s22plus_eud_openocd_host_audit.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_eud_openocd_host_audit.py
```

Results:

```text
py_compile: pass
unittest: Ran 5 tests, OK
audit: blocked_no_openocd
```
