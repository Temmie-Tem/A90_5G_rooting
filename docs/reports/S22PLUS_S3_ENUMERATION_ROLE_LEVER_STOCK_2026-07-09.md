# S22+ Why S3 Bound But Didn't Enumerate: the Role Lever Is `ssusb/mode`, Not `usb_role` (live read-only, 2026-07-09)

Operator (Claude) read-only pull from the live rooted device (Android baseline,
connected as a device to the host right now), applying the read-stock-first rule
before another live flash. No writes, no flash. Serials in scratchpad only.

## The finding: S3 forced the role via a path that does not exist

S3 survived the full runtime-gadget bring-up (configfs + `ss_acm` link +
`max_speed=high-speed` + `usb_role=device` + `UDC=a600000.dwc3`) with **no reset**
— the hang wall is solved — but the host saw **no ACM endpoint**. Reading the
live stock device shows why:

- **`/sys/class/usb_role/` is EMPTY** on this device. So S3's
  `usb_role=device` wrote to a **non-existent path — a silent no-op.** The dwc3
  role was never forced to peripheral.
- **`/sys/class/extcon/` is EMPTY** too — cable/VBUS role is not surfaced via
  extcon sysfs here.
- The **real, live role lever is `/sys/devices/platform/soc/a600000.ssusb/mode`**.
  Right now (stock, enumerated as a device to the host) it reads:

```text
/sys/devices/platform/soc/a600000.ssusb/mode = peripheral
/sys/class/udc/a600000.dwc3/state         = configured
/sys/class/udc/a600000.dwc3/current_speed = super-speed
/sys/class/udc/a600000.dwc3/function      = g1
/sys/class/udc/a600000.dwc3/is_otg        = 0
```

So a fully-enumerated stock gadget has `ssusb/mode = peripheral` and udc
`state = configured`. S3 never set `ssusb/mode`, so dwc3 stayed off the
peripheral path → D+ pull-up not asserted → host sees nothing, but the CPU is
fine (hence "survived, no endpoint").

## Who sets `mode` on stock — and why native init must do it manually

**No init `.rc` writes `a600000.ssusb/mode`** (grep of `init.qcom.usb.rc` and
`/vendor|/system|/odm` init is empty for it). On stock, `mode=peripheral` is set
by **dwc3-msm's own VBUS/PD/role auto-detection** (the driver has
`dwc3_msm_usb_role_switch_set_role`; the role-switch is fed by the TypeC/PD
charger path). Under native init we have the TypeC/PD *modules* loaded but **no
live PD/VBUS negotiation driving the role**, so the auto-switch never fires.
**Therefore native init must write the mode lever manually.**

## The lever is writable and its accepted values (from the `.ko`)

```text
-rw-r--r-- root root  /sys/devices/platform/soc/a600000.ssusb/mode
-rw-r--r-- root root  /sys/devices/platform/soc/a600000.ssusb/speed
```

Root-writable (0644) → our root PID1 can write them. `dwc3-msm.ko` strings show
the accepted values:

- `mode`  ∈ { `peripheral`, `host`, `none` }
- `speed` ∈ { `high-speed`, `full-speed`, `super-speed` }

`ssusb/speed` is a **second, dwc3-msm-level HS cap** distinct from the gadget
`g1/max_speed` — useful to also pin HS-only at the controller.

## S4 recipe (stock-verified) — the one change S3 was missing

From the S3-proven setup, replace the no-op `usb_role=device` with the real
lever, and pin controller speed:

```text
# ... S1/S2-proven: create g1, ss_acm.0 link, g1/max_speed=high-speed ...
write /sys/devices/platform/soc/a600000.ssusb/speed  high-speed   # controller HS cap
write /sys/devices/platform/soc/a600000.ssusb/mode   peripheral   # THE role lever (was missed)
write /config/usb_gadget/g1/UDC  a600000.dwc3                      # pullup
# host-scan for /dev/ttyGS0 (VID:PID 04e8:6860)
```

Order note: setting `mode=peripheral` puts dwc3 on the peripheral path; the
`UDC` write then asserts the gadget. Try `mode=peripheral` before the `UDC`
bind. Keep `soft_connect` in mind — if `mode`+`UDC` still does not pull up,
`/sys/class/udc/a600000.dwc3/soft_connect` (write `connect`) is the explicit
pull-up fallback.

## Sequencing for S4 (single new variable)

S3 already proved everything up to and including the UDC bind survives. S4 adds
exactly the missing `ssusb/mode=peripheral` (and `ssusb/speed=high-speed`). Two
clean outcomes:
- **`/dev/ttyGS0` (04e8:6860) enumerates** ⇒ ACM up over HS-only native init.
  The blind phase ends; build the command surface on ttyGS0.
- **Still no endpoint** ⇒ inspect udc `state`/`current_speed` on-device
  post-write (bound vs pulled-up), try `soft_connect`, and if the controller
  refuses HS pull-up without a real VBUS/role event, that is where a VBUS/charger
  angle or `dr_mode=peripheral` DTBO finally enters — but only then.

## Lesson applied

Per [[feedback_read_stock_before_live]]: S3's `usb_role=device` was a
plausible-sounding guess that targeted a class that does not exist here. One
read-only pull of the live device gave the real lever (`ssusb/mode=peripheral`),
its writability, and its accepted values — before spending another flash. Read
first.

## Discipline

Read-only device pull only; no writes, no flash. Raw dumps (with serial) stay in
scratchpad; this report uses placeholders. Any S4 candidate + live test needs a
fresh SHA-pinned boot-only exception. Device left on the clean Magisk baseline.
