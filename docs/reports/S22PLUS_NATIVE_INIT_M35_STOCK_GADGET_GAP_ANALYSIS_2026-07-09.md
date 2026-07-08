# S22+ M35 Stock Gadget Gap Analysis

Date: 2026-07-09 KST / 2026-07-08 UTC

Status: HOST/READ-ONLY COMPLETE. No live flash is authorized by this report.

## Scope

This unit explains the post-M34 S3 state:

- M34 S1/S2/S3 all survived the 90 second native-init observation window.
- S3 performed the final `UDC=a600000.dwc3` bind/pullup and still survived.
- S3 did not expose a host `/dev/ttyACM*` endpoint.

Inputs:

- S3 live result:
  `docs/reports/S22PLUS_NATIVE_INIT_M34_S3_LIVE_RESULT_2026-07-09.md`
- S3 source:
  `workspace/public/src/native-init/s22plus_init_m34_runtime_gadget_split.c`
- Stock configfs inventory:
  `workspace/private/runs/s22plus_m35_stock_gadget_inventory_20260708T201524Z/stock_gadget_inventory_redacted.txt`
- Stock host USB inventory:
  `workspace/private/runs/s22plus_m35_stock_host_usb_20260708T201842Z/host_usb_stock_android_redacted.txt`
- Earlier stock recipe report:
  `docs/reports/S22PLUS_STOCK_USB_GADGET_ACM_RECIPE_2026-07-09.md`

All live reads were redacted before use here. Device serials are intentionally
not recorded in this report.

## Stock Android Baseline

Current rooted Android exposes the stock Samsung gadget as:

```text
sys.usb.config = mtp,conn_gadget,adb
sys.usb.state  = mtp,conn_gadget,adb
controller     = a600000.dwc3
UDC            = a600000.dwc3
max_speed      = super-speed-plus
idVendor       = 0x04e8
idProduct      = 0x6860
bcdUSB         = 0x0320
bcdDevice      = 0x0504
bDeviceClass   = 0x00
bDeviceSubClass= 0x00
bDeviceProtocol= 0x00
bMaxPacketSize0= 0x09
```

The active stock config links five functions:

```text
configs/b.1/f1 -> functions/ffs.mtp
configs/b.1/f2 -> functions/ss_acm.0
configs/b.1/f3 -> functions/conn_gadget.0
configs/b.1/f4 -> functions/ffs.adb
configs/b.1/f5 -> functions/ss_mon.mtp
```

Host `lsusb -d 04e8:6860 -v` confirms this enumerates as a 5-interface
composite device. The ACM interface is an IAD pair:

- interface association: first interface 1, count 2, CDC ACM
- interface 1: CDC ACM control
- interface 2: CDC data
- host driver: `cdc_acm`
- host node: `/dev/ttyACM0`

So the controller, cable, host driver, and Samsung `ss_acm.0` function are known
good on this exact device. The problem is not that ACM is impossible on
`a600000.dwc3`; it is that the native-init composition is not yet sufficient to
make the host bind an ACM tty.

## S3 Native-Init Composition

M34 S3 creates only one function:

```text
functions/ss_acm.0
configs/b.1/f1 -> ../../functions/ss_acm.0
```

It writes:

```text
bcdUSB          = 0x0200
idVendor        = 0x04E8
idProduct       = 0x6860
bcdDevice       = 0x0034
bDeviceClass    = 0xef
bDeviceSubClass = 0x02
bDeviceProtocol = 0x01
configuration   = acm
max_speed       = high-speed
usb_role        = device
UDC             = a600000.dwc3
```

The S3 module list contains the P30/M32 ACM closure, including
`usb_f_ss_mon_gadget.ko` and `usb_f_ss_acm.ko`, but the S3 program does not
create the stock companion functions `ffs.mtp`, `conn_gadget.0`, `ffs.adb`, or
`ss_mon.mtp`.

## Key Correction

The S3 live helper observed ADB, Odin, and `/dev/ttyACM*` state. It did not
capture `lsusb`, `usb-devices`, udev properties for all `04e8:6860` nodes, or a
host dmesg delta during the 90 second native-init window.

Therefore the strict S3 conclusion is:

- proven: no host ACM tty endpoint appeared
- proven: no ADB/Odin endpoint appeared
- proven: final UDC pullup did not cause the reset boundary
- not proven: no USB device enumerated at all

Future live helpers must capture USB-device-level evidence, not just ttyACM.
Otherwise a descriptor-level enumeration failure, a non-ACM composite
enumeration, and complete no-enumeration all collapse into the same symptom.

## Current Best Explanation

The highest-confidence gap is descriptor/composition mismatch, not power/DT:

1. S3 survived final UDC pullup, so pullup itself is no longer the reset wall.
2. Stock Android proves `ss_acm.0` can enumerate on the same controller.
3. S3 uses ACM-only `f1` plus non-stock device-class and `bcdDevice` values.
4. Stock uses a Samsung composite config where `ss_acm.0` is `f2` after MTP,
   with `conn_gadget.0`, ADB, and `ss_mon.mtp` companions.

The next candidate should first tighten stock parity and improve observation
before introducing DTBO, QMP, EUD, kernel rebuild, or new power writes.

## Recommended Next Unit

M35A should be host-build only first:

- keep boot-only MagiskBoot construction and no live auth by default
- keep the S2/S3 survival-safe `max_speed=high-speed` and `usb_role=device`
  unless the candidate explicitly isolates one of those knobs
- set stock-like device descriptor values:
  `bDeviceClass=0x00`, `bDeviceSubClass=0x00`, `bDeviceProtocol=0x00`,
  `bcdDevice=0x0504`
- set stock-like strings where low risk:
  manufacturer `SAMSUNG`, product `SAMSUNG_Android`, config `mtp_conn_adb`
- preserve `idVendor=0x04E8`, `idProduct=0x6860`, `UDC=none` before relink, and
  final `UDC=a600000.dwc3`
- decide separately whether to add companion functions:
  `conn_gadget.0`/`ss_mon.mtp` are plausible next deltas, while `ffs.mtp` and
  `ffs.adb` require extra caution because FunctionFS usually needs userspace
  descriptors/daemons before bind
- update the live helper observation loop to collect:
  `lsusb -d 04e8:6860 -v`, `lsusb -t`, `usb-devices`, `/dev/ttyACM*`,
  `/dev/serial/by-*`, udev properties, and host dmesg/journal deltas

M35A should not be flashed until it has a fresh SHA-pinned `AGENTS.md`
exception and explicit operator approval.

## Authorization State

No active live authorization exists. This report does not authorize S3 repeat,
M35A live flash, DTBO, vendor_boot, recovery, vbmeta, non-boot flash, raw host
`dd`, fastboot, EUD writes, RDX PC dump retrieval, Magisk modules, format data,
or any A90 action.
