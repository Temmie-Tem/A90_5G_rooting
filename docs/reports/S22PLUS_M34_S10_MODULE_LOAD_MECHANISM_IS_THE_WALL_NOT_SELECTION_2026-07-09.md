# S22+ S10 Reframe: the Wall Is the Module-LOAD MECHANISM (cmd-db not in /proc/modules), Not Module SELECTION — and a Correction to S9.2 (2026-07-09)

Operator (Claude) host-only analysis of the S10A/S10B0 results. Device was
mid-loop (root unavailable, transitional shell) so this is git + firmware +
prior-capture analysis, no new device reads. Includes an honest correction to my
own S9.2 steer.

## Correction to S9.2 (my steer was wrong; the loop caught it)

S9.2 claimed S9 missed because it loaded the devlink providers but not their
`modules.dep` symbol-deps (cmd-db/smem/qcom-scm/...). **That was wrong.** The loop
verified the actual S9 artifact already contained all of them (same 89-module
list, SHA `c07425f4...`). I computed the theoretical `modules.dep` closure but did
not diff it against the built artifact. Credit S10A for disproving the premise.
Lesson: verify a "missing X" claim against the actual artifact, not just the
theoretical closure.

## What S10A/S10B0 actually found

S10A (does any core module appear in `/proc/modules` after native-init load?) and
S10B0 (narrowed to: is `cmd_db` in `/proc/modules`?) both returned **MISS**.

Host-side check settles whether that MISS is real or a false negative:
`cmd-db`, `smem`, `socinfo`, `qcom-scm`, `secure_buffer`, `qcom_ipc_logging`,
`minidump`, `arm_smmu`, `gcc-waipio`, `pinctrl-waipio`, `pinctrl-msm`, `clk-rpmh`,
`rpmh-regulator`, `gdsc-regulator` are **all present in stock `modules.load`** =
they are real loadable modules, **not GKI-built-in**. So `cmd_db` genuinely
should appear in `/proc/modules` if loaded, and the S10 predicate is valid.
**Therefore the MISS is real: `cmd-db` is not loading under native-init.**

## The decisive cross-check: the load mechanism PARTIALLY works

Do not conclude "no modules load." The device **survives the full 90 s** under
S9/S10, whereas **M21A (0 modules) reset at ~30 s** on the PMIC/PON watchdog. The
only thing that tames that watchdog is loading `qcom_wdt_core`/`gh_virt_wdt`
(M31B). So **the watchdog modules ARE loading** (else reset) — the module-load
mechanism runs and succeeds for at least some modules.

So the precise wall is narrower and new: **the load mechanism runs (watchdog
loads → survive), yet `cmd-db` specifically is absent from `/proc/modules`.**
After ~10 iterations spent on *which modules to select*, the frontier has moved
to *why a listed foundational module does not end up loaded*. Candidates:

1. **Per-module insmod failure.** `cmd-db` insmod fails (e.g. its DT
   `reserved-memory qcom,cmd-db` region, or an ordering/dep error) and native
   init continues without it. We are blind to insmod return codes.
2. **Ordering.** In stock `modules.load` the first entries are `sec_boot_stat`,
   `sec_log_buf`, `sec_arm64_ap_context`, `abc`, `gh_virt_wdt`(#5),
   `qcom_wdt_core`(#6), `qcom_cpu_vendor_hooks`, `clk-rpmh`(#8),
   `gcc-waipio`(#9), `icc-rpmh`, `qcom_ipcc`, `qcom_ipc_logging`... `clk-rpmh`
   depends on `cmd-db`, so `cmd-db` must load before #8. If our native-init load
   order or list omits/misplaces `cmd-db`, or an earlier module errors and aborts
   the loop, `cmd-db` never loads.
3. **Read artifact.** Our native-init's `/proc/modules` read could be
   empty/blocked, making the beacon a false negative — but the watchdog-survival
   proves modules load, so this is less likely; still worth ruling out.

## Next unit: instrument the insmod mechanism (one level finer than S10B0)

The S10 module-load beacon direction is correct; go one finer:
- Have native-init record **per-module insmod result** (attempted / rc / errno)
  for the substrate prefix, and beacon/encode the **first module that fails or is
  never attempted** (cmd-db first).
- Confirm the `.ko` files are actually staged and reachable by native-init, and
  that the load loop reaches cmd-db (not aborting on an earlier error).
- Confirm the native-init `/proc/modules` read itself returns non-empty for a
  known-loaded module (e.g. the watchdog) as a positive control for the beacon.

This distinguishes attempted-but-failed (fix the specific insmod error, e.g.
reserved-memory/order) from never-attempted (fix the load list/loop) from
read-artifact (fix the beacon) — instead of guessing.

## Secondary notes

- **`i2c-msm-geni` is ABSENT from stock `modules.load`** (while the rest of the
  substrate is present). It may be built-in, dep-loaded, or named differently;
  the loop should confirm how the GENI i2c controller is instantiated on stock
  before assuming it must be insmod-ed.
- **Device is mid-loop / root currently unavailable.** The loop's `664e5a43`
  ("fix root fallback") shows it hit the same state and is handling it. Operator
  backed off device reads to avoid collision. Worth watching that the rollback
  baseline restores Magisk root for the loop's own pre/post adb-root checks.

## Safety

Host-only analysis (git + firmware `modules.load`/`modules.dep` + prior
captures). No device writes. S10 batch Gate-2: serial-clean, boot-only reads
(`dd if=…/boot | sha256sum` readback), S10A/S10B0 exceptions consumed. Any next
live probe stays boot-only, watchdog-managed, no rail/partition writes.
