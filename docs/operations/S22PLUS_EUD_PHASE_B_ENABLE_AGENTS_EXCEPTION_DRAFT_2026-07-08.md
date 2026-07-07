# S22+ EUD Phase-B Enable AGENTS Exception Draft (2026-07-08)

This is an inert draft. It does not authorize live work while it remains in this
document. Copy it into `AGENTS.md` only after explicit operator authorization
for a reversible EUD module-parameter write.

## Copy Block

```text
   **Narrow operator-authorized exception (2026-07-08, S22+ EUD Phase-B reversible enable only):**
   after EUD Phase-A proved `eud.ko` is loaded, `88e0000.qcom,msm-eud` is
   bound, `/dev/ttyEUD0` exists, and source analysis identified
   `/sys/module/eud/parameters/enable` as the actual runtime control, Codex may
   perform one bounded attended EUD Phase-B reversible enable run on the Samsung
   S22+ `SM-S906N`/`g0q` `S906NKSS7FYG8` using only the checked helper
   `workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py`
   and live ack token `S22PLUS-EUD-PHASE-B-ENABLE-LIVE-GATE`.
   The helper must first verify Android/root, the known Magisk boot hash, the
   EUD module parameter, and `/dev/ttyEUD0`. It may then write 1 exactly once to
   `/sys/module/eud/parameters/enable`, collect host `lsusb`, dmesg, and host
   serial/TTY evidence for a Qualcomm/EUD USB-C debug hub/interface or a new
   host serial/TTY path, and must write 0 back to
   `/sys/module/eud/parameters/enable` before exit (`restore enable=0`). This
   exception authorizes no flash, no reboot, no partition write, no native-init
   boot candidate, no module insertion, no boot/vendor_boot/dtbo/vbmeta/recovery
   write, no BL, no CP, no CSC, no super, no userdata, no EFS, no sec_efs, no
   RPMB, no keymaster, no modem, no bootloader, no raw host `dd`, no fastboot,
   no Magisk module, no format data, no additional sysfs writes, and no A90
   action.
```

## Gate Marker Coverage

The draft intentionally includes every authorization marker required by
`s22plus_eud_phase_b_enable_live_gate.py`:

```text
S22+ EUD Phase-B reversible enable only
workspace/public/src/scripts/revalidation/s22plus_eud_phase_b_enable_live_gate.py
SM-S906N/g0q/S906NKSS7FYG8
S22PLUS-EUD-PHASE-B-ENABLE-LIVE-GATE
/sys/module/eud/parameters/enable
/dev/ttyEUD0
write 1
write 0
restore enable=0
no flash
no reboot
no partition write
no native-init boot candidate
no module insertion
host lsusb
host serial/TTY
new host serial/TTY path
```
