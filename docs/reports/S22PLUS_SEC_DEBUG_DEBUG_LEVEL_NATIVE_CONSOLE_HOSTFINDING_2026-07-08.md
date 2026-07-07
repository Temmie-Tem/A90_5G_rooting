# S22+ — The Real Persistence Stack is Samsung sec_debug (debug_level), Not Mainline ramoops (Host Finding, 2026-07-08)

Operator (Claude) host-only analysis of the DTBO blobs we already hold + one
websearch. No device action. This reinforces and **redirects** the no-UART
console card before more DTBO flashes are spent.

## What the DTBO actually contains (decoded from the blob, no dtc needed)

I wrote a minimal FDT walker and dumped the patched vs stock `dtbo.img`
(`workspace/private/outputs/s22plus_ramoops_dtbo_enable_v0_1/build/`). Two facts:

1. **The whole enable-target overlay (fragment@116) is Samsung's `sec_debug`
   framework**, not a mainline ramoops region. Nodes present, all with
   `compatible = samsung,*`:
   - `samsung,kernel_log_buf` — reg `0x8_00200000` size `0x200000` (2 MiB),
     `sec,strategy=3`, `sec,use-last_kmsg_compression`,
     `sec,last_kmsg_compressor="zstd"`. **This is the source of `/proc/last_kmsg`**
     (the retained captures were exactly 2,097,136 B ≈ 0x200000).
   - `samsung,pstore_pmsg` — reg `0x8_00900000` size `0x200000` (the `/dev/pmsg0`
     backing), gated `sec,debug_level`.
   - `samsung,sec_debug`, `samsung,upload_cause`, `samsung,crashkey`
     (forced "Crash Key" upload), `samsung,qcom-user_reset`,
     `samsung,qcom-rst_exinfo` (exception/reset context),
     `samsung,qcom-summary`, `samsung,qcom-debug` with `sec,use-store_last_kmsg`
     / `sec,use-store_lpm_kmsg`.
   - Several carry `sec,debug_level` gates (2-char codes; the developer nodes use
     MID/HIGH-class codes, the user crashkey uses the LOW-class code).

2. **The loop's "enable" patch is a single `status` string `disabled`→`okay`**
   (16 identical bytes, one property, same length with null padding). It flips a
   mainline-style `ramoops_region` node — which is **not** the node that drives
   the Samsung capture path above.

## Why every capture was empty / bootloader-only (root cause)

The S22+ does not persist the Linux kernel console through mainline
ramoops/pstore-console here. It persists through **Samsung sec_debug**, and
sec_debug's real capture (full kernel log to `kernel_log_buf`, `/dev/pmsg0`,
panic **Upload Mode** / ramdump) is **gated by `debug_level`**, which on a retail
unit ships at **LOW**. At LOW, sec_debug stores only minimal LPM/bootloader logs
— exactly the ABL/download-only `last_kmsg` we kept seeing. Flipping the mainline
`ramoops_region status` to `okay` does not activate the Samsung path, so M13's
pstore stayed empty and `last_kmsg` stayed bootloader-only. **The mainline ramoops
route is likely vestigial on this device.**

## The real lever (websearch-confirmed): raise Samsung debug_level to MID

Samsung exposes debug level in the SysDump menu via the dialer code **`*#9900#`**
→ set **DEBUG LEVEL: MID** (or HIGH). At MID/HIGH, a kernel panic enters
**"Kernel Panic Upload Mode"** and sec_debug captures the full kernel log /
ramdump, retained for the next boot; `echo c > /proc/sysrq-trigger` on a rooted
device is the standard trigger. This is Samsung's **native "UART without a jig."**
(Sources below.)

Key properties that make this better than the DTBO route:
- **No flash to enable.** debug_level is a runtime/param setting on the already-
  rooted Android, reversible back to LOW. It is not a forbidden partition.
- **Kernel-level capture.** sec_debug hooks the kernel console independent of our
  `/init`, so even a bare native-init boot's kernel messages + the QMP PHY abort
  are captured — the fault reason lands in `kernel_log_buf`/upload, readable next
  boot.
- **Catches more than panics.** `samsung,qcom-rst_exinfo` + `user_reset` log
  exception/reset context, so even a watchdog/async-SError reset (our leading M15
  hypothesis) should leave a reason, not just a clean-panic-only trace.

## Cheapest possible positive control (zero flash)

Before any native boot: on normal rooted Android, set debug_level=MID via
`*#9900#`, run `echo c > /proc/sysrq-trigger`, recover, and confirm the panic is
retained (Upload Mode screen and/or next-boot `/proc/last_kmsg` now holds the
real kernel panic log, not ABL-only). That validates the Samsung channel with **no
boot flash at all**. Only after it is proven do we point it at a native
QMP-PHY-loading candidate (M15/M18).

## Relationship to the in-flight M22

The loop's M22 (`sysrq_panic` retained-console control) is a valid positive
control **for the mainline ramoops path**. This finding says: if M22 retains
nothing even for a real sysrq panic, do **not** keep permuting DTBO — that
confirms mainline ramoops is not the live mechanism, and the switch is to
**debug_level=MID (no-flash, native sec_debug)**, which is both cheaper and more
likely to work. Ideally set debug_level=MID *before* the M22 panic so the one
attended run also tests the Samsung path.

## Feasibility verdict (answer to "can we reinforce the card host-only?")

Yes — and it moved. The no-UART odds are **better than before but via a different
mechanism**: the enable-target is Samsung sec_debug + debug_level, not the
mainline `ramoops_region status` flip. Next step is a no-flash Android positive
control at debug_level=MID; if that retains a sysrq panic, the S22+ has a native
kernel-console channel and UART is likely unnecessary. Fallback order stays: this
(sec_debug/MID) → EUD → UART.

## Caveats to verify on-device (host-only cannot settle these)
- Whether debug_level on this unlocked/rooted retail unit is settable purely via
  `*#9900#` or needs a `param`-area write, and that it is cleanly reversible to LOW.
- Whether MID capture survives the specific recovery path we use (manual download
  entry) without wiping — sec_debug is designed to persist across warm reset, but
  confirm with the zero-flash positive control first.
- Whether a silent async-SError (vs a real panic) is captured by rst_exinfo at MID.

## Sources
- Samsung SysDump `*#9900#` DEBUG LEVEL MID/HIGH + `echo c > /proc/sysrq-trigger`
  triggering Kernel Panic Upload Mode:
  https://www.tiktok.com/@savagepotato404/video/7251330575141801243
- Samsung Kernel Panic Upload Mode overview:
  https://itechify.com/2024/02/18/fix-kernel-panic-upload-mode-error-samsung/
- Qualcomm ramdump/minidump for kernel panic analysis:
  https://medium.com/@pitchaimuthu321/android-kernel-panic-debugging-explained-from-crash-log-to-root-cause-analysis-344bcea5e39d
