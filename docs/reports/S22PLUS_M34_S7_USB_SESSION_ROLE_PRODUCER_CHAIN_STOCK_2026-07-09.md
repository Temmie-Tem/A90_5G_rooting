# S22+ Why the Gadget Binds But Never Pulls Up: the Missing TypeC/PD Session-Producer Chain (live read-only, 2026-07-09)

Operator (Claude) read-only pull from the live rooted device (Android baseline,
Magisk root, no active S22+ live authorization = loop is host-only = safe to
read). No writes, no flash. Applying the read-stock-first rule before another
live gate. Serials stay in scratchpad; this report uses placeholders.

## The question S4/S5/S6 left open

S4 (`ssusb/mode=peripheral`) and S6 (stock QMP/EUD/ucsi softdep parity, HS
forcing removed) both **bound the gadget and survived** the full window but
produced **no `04e8:6860` endpoint**. S5 (`soft_connect=connect`) **crashed**
into Samsung `04e8:685d` MSM_UPLOAD and returned to Odin at ~74 s. Three levers,
zero enumeration. So "bind + survive" is solved; "assert D+ pullup as `6860`" is
not. This unit reads the live stock device to find what drives the pullup.

## What actually drives the pullup on stock: the peripheral SESSION, via TypeC/PD

The USB HAL rc (`/vendor/etc/init/android.hardware.usb@1.3-service.coral.rc`)
`chown`s three controller knobs at `on post-fs`:

```text
/sys/devices/platform/soc/a600000.ssusb/b_sess
/sys/devices/platform/soc/a600000.ssusb/id
/sys/devices/platform/soc/a600000.ssusb/usb_data_enabled
```

**But those three nodes do NOT exist on this kernel** — `ls a600000.ssusb/`
shows only `mode` and `speed`; `dwc3-msm.ko` strings expose only
`bus_vote/mode/orientation/speed` (no `b_sess`/`id`/`vbus`). So the peripheral
**session** is not forced through dwc3 sysfs here. It comes from the TypeC/PD
framework:

```text
/sys/class/typec/port0        exists   (+ port0-partner when a cable is present)
  data_role   = host [device]   perm 664   ← active selection: device (peripheral)
  power_role  = source [sink]   perm 664   ← active selection: sink
  port_type   = [dual] source sink perm 664
```

On stock, cable insertion → the PD/MUIC chip detects CC/VBUS → the role driver
sets `data_role=device`, `power_role=sink` → dwc3-msm gets a valid **peripheral
session** → the `write UDC` pullup enumerates as `6860`. `mode=peripheral` only
selects the controller role; it does **not** by itself create the session.

## Who produces `/sys/class/typec/port0` and the session — live `lsmod`

The live stock modules that detect the cable and drive the role/session:

```text
altmode_glink            # glink altmode -> TypeC role driver (sets data_role)
pdic_max77705            # Samsung PD-IC on the max77705
pdic_notifier_module     # PD-IC notifier fanout
common_muic              # MUIC cable/CC detection
mfd_max77705             # max77705 MFD (the PD/charger chip)
max77705_charger         # + max77705_fuelgauge
qcom_i2c_pmic            # I2C transport to reach the PMIC/PD chip
redriver                 # USB SS redriver (also a dwc3-msm depends:)
if_cb_manager            # interface callback manager (dwc3-msm depends:)
```

plus the glink transport (`pmic_glink`, `qcom_glink*`, `charger_ulog_glink`).

## Root cause: our native-init set is missing that entire producer chain

Checked against the S6 candidate builder
(`build_s22plus_m34_runtime_gadget_split.py`, commit `ecadff80`):

```text
PRESENT : ucsi_glink
MISSING : altmode_glink
MISSING : pdic_max77705
MISSING : pdic_notifier_module
MISSING : common_muic
MISSING : mfd_max77705
MISSING : max77705_charger
MISSING : qcom_i2c_pmic
MISSING : redriver
MISSING : if_cb_manager
```

We load the generic UCSI-over-glink half but **not** the Samsung max77705
PD-IC/MUIC + `altmode_glink` chain that actually detects the connected cable and
sets `data_role=device`. Consequence, consistent with all three live results:

- **S4/S6:** gadget binds (`state=configured`), CPU survives, but no session is
  ever asserted for the connected cable → **no D+ pullup → no `6860`**.
- **S5:** `soft_connect=connect` forced a pullup with no valid session/PHY state
  → fault → MSM_UPLOAD `685d` → Odin.

This is the same read-stock-first pattern as `modules.dep`, `init.qcom.usb.rc`,
and the live `/config/usb_gadget` tree: the answer was already on the live
device.

## S7 recipe (stock-derived)

1. **Add the session-producer chain to the native-init module set**, in
   dep-correct order, around the existing dwc3-msm/glink modules:
   `qcom_i2c_pmic` → `mfd_max77705` → `max77705_charger`/`max77705_fuelgauge` →
   `common_muic` → `pdic_max77705` → `pdic_notifier_module` → `altmode_glink`;
   also confirm `redriver` and `if_cb_manager` (dwc3-msm `depends:`) are loaded.
   Take the exact names/order from stock `modules.load` +
   `modules.dep` closure, not from this list.
2. **Reconcile against P28.** P28 ("44-module dep-ordered incl the TypeC/PD
   tree") *survived* 90 s. If P28 already contained these producers and S6
   dropped them, the fix is simply to restore them; if P28 also lacked them,
   this chain is genuinely new. Diff S6's set against P28's before building.
3. **Keep `mode=peripheral`**, keep the stock gadget/`ss_acm` configfs order,
   keep the `UDC` write last. Do **not** use `soft_connect` (S5 proved it
   crashes without a valid session).
4. **Live reads to capture on the next boot** (this is the discriminator):
   `cat /sys/class/typec/port0/{data_role,power_role,port_type}` and `dmesg |
   grep -iE 'altmode|max77705|pdic|muic|typec|dwc3|session|vbus'` — before and
   after the UDC write. `data_role` resolving to `device` with a cable present
   is the signal the session is up; then check for `6860`.

## Safety note on the max77705 chain

`max77705_*`/`pdic_*`/`common_muic` touch the external USB-C **PD/charger PMIC**
over I2C. Loading these stock drivers so they do their normal **cable/PD
detection** (negotiating as a **sink** that draws power *from* the host) is a
stock module load, **not** a rail power-write and **not** the display/SoC
regulator/GDSC/GPIO bright-line. The candidate must only let them detect the
cable/role; it must **not** write charge-current, OTG/VBUS-boost, or rail knobs
on the PMIC. Flag for operator confirmation at the S7 gate.

## Discipline

Read-only device pull only (getprop / lsmod / cat sysfs / adb pull of rc files);
no writes, no flash, no reboot. Raw dumps (which contain the real serial) remain
uncommitted in scratchpad; this report uses placeholders. Any S7 candidate +
live test needs a fresh SHA-pinned boot-only `AGENTS.md` exception.
