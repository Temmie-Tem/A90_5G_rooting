# S22+ — We Read the Wrong Surface: Samsung reset_summary Captures the Watchdog Bite (Operator Steer, 2026-07-08)

Operator (Claude) host-only steer. No device action here. Reframes the M18
"no-hit": M18's fault is a **watchdog bite**, and Samsung captures that on a
**different channel than the one we read** — cheap, no EUD/JTAG, MID already set.

## Why M18 was a "no-hit" (wrong file, not no evidence)

We only read `/proc/last_kmsg`. That is the **console ring**, snapshotted at
**panic** time. M18's fault is a **CPU hang → msm watchdog bite → warm reset**,
which is **not a panic** → last_kmsg is empty of it. That is the entire "no-hit."

The reset-reason probe capture proves two things:
1. **The reset mechanism is the msm watchdog.** dmesg shows
   `msm_watchdog_data - pet: … (delta: 9.47s)` — the watchdog runs and is petted
   ~every 9.5 s on normal Android; a bare init that pets nothing → bite → reset.
2. **Samsung has a dedicated reset-context subsystem we never read** —
   `sec_qc_user_reset`, exposed as `/proc/reset_summary`, `/proc/reset_klog`,
   `/proc/reset_history`, `/proc/reset_tzlog`, `/proc/reset_rwc`,
   `/proc/enhanced_boot_stat`, `/proc/store_lastkmsg`. On a clean boot these are
   empty (`sec_qc_user_reset: … failed to load reset_header (-2)` = no prior
   crash). **After a crash/watchdog reset they populate.**

On a Samsung watchdog bite at debug_level=MID, the sec_debug watchdog handler
(bark pre-timeout) typically dumps **per-core last-PC / registers + a klog
snapshot + reset reason** into these surfaces — exactly the hung-CPU context we
need, on a channel that captures **bites** (unlike last_kmsg which captures only
panics).

## The cheap next unit (no EUD, no JTAG, no risk)

Re-run the native QMP-PHY candidate (M18, or the M23 DTS-exact substrate) at
**debug_level=MID**, roll back, then read — in addition to last_kmsg — the
**sec_qc_user_reset surfaces**:
- `/proc/reset_summary` (reset reason + likely per-core last PC)
- `/proc/reset_klog` (kernel log at reset time)
- `/proc/reset_history`, `/proc/reset_tzlog`, `/proc/enhanced_boot_stat`
- `/sys/kernel/wakeup_reasons/last_resume_reason`

Classify: does `reset_summary`/`reset_klog` contain a faulting/last PC or the
module/driver active at bite time? If yes, that localizes the hang **without any
hardware debug** — the observability we thought EUD/JTAG was needed for.

Caveats (honest): the bite may be a hard reset that outruns the bark handler, or
the sec_debug summary may need the watchdog **module** loaded to register its
handler (M18 excludes watchdogs) — so also try a variant that loads
`qcom_wdt_core` (its bark handler is what dumps) while still not petting, and see
if the bite then produces a summary. If the surfaces stay empty even so, fall
back to the pmsg-marker path below.

## Parallel cheap path — pmsg progress markers (init-side, module granularity)

Have the native init write an explicit marker to **`/dev/pmsg0`** (backed by
`samsung,pstore_pmsg`, active at MID, survives warm reset) **before each risky
insmod / bring-up step**: `A90_STEP: about to insmod phy-msm-ssusb-qmp`, etc.
After the hang+reset, read `/sys/fs/pstore/pmsg-ramoops` (or the retained pmsg)
from Android — the **last marker = the step that hung**. Coarser than a PC
(module granularity) but pure software, zero risk, and directly answers "which
bring-up step triggers the bite," which with the DTS is likely enough to fix the
power substrate.

## Sequencing (this comes before/with Track B, not after)
1. **Read reset_summary/reset_klog after an M18/M23 run** (cheapest; may hand us
   the PC/module directly). Add the watchdog-module variant if empty.
2. **pmsg step-markers** in the native init (module-granularity localization).
3. Feed whatever these localize into **Track B (M23 DTS-exact substrate)** to fix
   the exact missing supply/clock — observation + fix combined.

## Relationship to EUD/UART
This is a **third no-jig observability avenue** that opened after EUD closed
(TZ-gated) and MID/last_kmsg missed the hang: Samsung's own watchdog-reset
capture, which we simply had not read. It does not need EUD, JTAG, UART, or a TZ
bypass. Pursue it before spending on a UART clip.

## Discipline
Read-only /proc reads + one attended candidate flash (existing boot-only gate);
pmsg markers are init-source only; no forbidden partitions, no power writes,
redacted logs (strip serials). Device stays recoverable to the Magisk baseline.
