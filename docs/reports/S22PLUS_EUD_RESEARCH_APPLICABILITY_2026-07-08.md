# S22+ EUD — Research & Applicability (Host Survey, 2026-07-08)

Operator (Claude) host-only research: A90-tree `drivers/soc/qcom/eud.c` source
(same driver family as the S22+ stock `eud.ko`) + Phase-A on-device facts +
Linaro/LWN/postmarketOS precedent. Purpose: pin what is *confirmed applicable*
vs what must be *checked on-device* before/during EUD Phase B, now that EUD is
the priority (M18 fault is a silent reset that post-mortem sec_debug/last_kmsg
does not capture).

## Confirmed applicable — device side

From `eud.c` (SM8150 A90 tree; S22+ FYG8 ships eud as binary-only module, same
family) + Phase-A probe:
- **Enable = `eud.enable=1`.** The driver comment is explicit: *"On the kernel
  command line specify `eud.enable=1` to enable EUD. EUD is disabled by
  default."* It is a `module_param_cb(enable, …, 0644)` → writable at runtime via
  **`/sys/module/eud/parameters/enable`** (echo 1 to attach, 0 to detach —
  reversible). Writing 1 calls `enable_eud()` → `writel EUD_REG_CSR_EUD_EN` +
  `EUD_REG_EUD_EN2=EUD_ENABLE_CMD` + arms INT mask + `SW_ATTACH_DET` (software
  USB attach). This is exactly what the loop's Phase-B gate does.
- **COM console = a real Linux `uart_port`.** `eud.c` registers a full
  `struct uart_port` with uart_ops (`eud_tx_empty/stop_tx/start_tx/startup/…`)
  bridged to the `EUD_REG_COM_TX_*`/`RX_*` registers → this is what creates
  **`/dev/ttyEUD0`** (Phase A: present, major 502). So the device side of a serial
  console is complete: route the kernel console with **`console=ttyEUD0`** (boot
  cmdline/bootconfig; currently `console=null`), or read/write `/dev/ttyEUD0` as a
  data tty on a running system.
- **Phase-A already proved device readiness:** `eud.ko` loaded, driver bound
  (`88e0000.qcom,msm-eud`, DRIVER=msm-eud), DT `qcom,msm-eud@88e0000`
  `status=ok` (not fused off), `/dev/ttyEUD0` exists. The one action left is the
  attended `enable=1` write + host observation.

## Confirmed — host side (from Linaro/LWN precedent)

- Enabling makes the PC enumerate **a 7-port USB hub with one port = "EUD control
  interface"**; "with the right USB commands a second device appears exposing an
  **SWD** interface."
- **SWD/JTAG is a solved host path:** OpenOCD with `interface/eud.cfg` +
  `target/qualcomm/qcom.cfg` → real `SWD DPIDR` + a **GDB server on :3333**
  (Linaro demonstrated). JTAG = halt the CPU and read PC/registers directly.
- Device-side EUD enable "has been somewhat supported in upstream Linux for a
  while"; an SM8450-specific EUD enablement series exists (LWN 984085).

## The gap to check on-device (the uncertain part)

**The COM (UART) console peripheral is NOT integrated into OpenOCD / not explored
by the open tooling** (Linaro: *"there is also a COM (UART) peripheral, and a
trace peripheral. These haven't yet been explored (and aren't integrated into
OpenOCD)."*). So reading the EUD **serial console on the host** is not a proven
off-the-shelf path. Open questions, all resolved by Phase B:
1. When Samsung's stock EUD is enabled, what does `lsusb` show — VID/PID and
   interface descriptors? Does a **serial/CDC endpoint (COM)** appear that the
   host can open as `/dev/ttyUSB*`/`ttyACM*`, or does the COM need a **Qualcomm
   proprietary host driver** (QUD-style)? (Note: stock Samsung host tooling reads
   EUD COM in factory; open-host readability is the unknown.)
2. If a serial appears → does it carry the kernel console? (may require
   `console=ttyEUD0` on the boot candidate's cmdline, since live `console=null`).
3. Does the attach survive our USB-C usage (enabling reroutes the port → adb
   drops; that is expected, not failure).

## Two host sub-paths, ranked for our silent-reset need

- **B1 — EUD-SWD/JTAG via OpenOCD (recommended primary).** Proven host path.
  For a **silent reset** (M18's fault class) JTAG is arguably ideal: set a
  breakpoint / catch the exception and read the **exact PC + faulting register**,
  which beats any console line. Cost: build OpenOCD with EUD support + obtain/adapt
  an **SM8450 `eud.cfg` + `qcom.cfg`** target (the Linaro configs target specific
  SoCs; SM8450 may need the enablement-series config). Host setup task, but the
  payoff is full halt-debug of the exact fault.
- **B2 — EUD-COM live console.** Simpler *if* the host enumerates a readable
  serial; gives the live boot console (last line before the silent reset). Blocked
  on gap #1 (open-host COM readability) + `console=ttyEUD0` routing.

Run Phase B to resolve #1 first (cheap: enable + `lsusb`), then pick B2 (if COM is
host-readable) or commit to B1 (OpenOCD/JTAG, always available via SWD).

## Applicability caveats
- "Newer SoCs need additional changes" (mainline) — but our **stock vendor
  `eud.ko` already binds on SM8450** (Phase A), so the device-side enable should
  work; the proof is the host enumerating the hub on `enable=1`.
- Samsung could still gate the USB-attach behind a secure/fuse state even with the
  module bound; DT `status=ok` + bound driver are encouraging, but the
  host-enumeration-on-enable is the real test.
- Host needs a Linux box with **OpenOCD (EUD build)** for the JTAG path — a
  setup/build task to stage before the attended Phase-B session.

## Concrete Phase-B checklist (attended, reversible, no flash)
1. `echo 1 > /sys/module/eud/parameters/enable` (device, rooted Android).
2. Host: `lsusb` + `lsusb -v` for the new Qualcomm hub/interfaces; `dmesg` for a
   new tty/serial or hub; note VID/PID.
3. If a serial appears → `screen`/`cat` it; check for console text.
4. In parallel stage OpenOCD-EUD + an SM8450 target config; try
   `openocd -f interface/eud.cfg -f target/qualcomm/qcom.cfg` → SWD DPIDR + GDB
   :3333.
5. `echo 0 > /sys/module/eud/parameters/enable`; confirm adb/USB returns.
Record only redacted metadata (no serial in committed logs).

## Sources
- Linaro "hidden JTAG" (7-port hub, SWD/OpenOCD, COM not yet explored):
  https://www.linaro.org/blog/hidden-jtag-qualcomm-snapdragon-usb/
- LWN "Enable EUD on Qualcomm sm8450": https://lwn.net/Articles/984085/
- Hackaday EUD overview: https://hackaday.com/2025/07/10/embedded-usb-debug-for-snapdragon/
- postmarketOS serial debugging: https://wiki.postmarketos.org/wiki/Serial_debugging
- Device-side mechanism: A90-tree `drivers/soc/qcom/eud.c` (eud.enable module param,
  uart_port/ttyEUD0, CSR_EUD_EN + SW_ATTACH_DET).
