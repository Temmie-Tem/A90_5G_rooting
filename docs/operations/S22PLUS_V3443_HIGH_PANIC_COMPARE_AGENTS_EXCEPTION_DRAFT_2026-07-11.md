# S22+ V3443 HIGH Panic Comparison Exception Draft

`DRAFT_INACTIVE` - this proposal authorizes no device contact, debug-level
change, panic, USB command, reboot, flash, or recovery action.

## Proposed AGENTS.md Clause

**Narrow operator-authorized exception (2026-07-11, S22+ V3443 HIGH panic
MID-control comparison live gate):** after V3442 proved that S-Boot accepts
HIGH and Android exposes exact `18760` / `0x4948`, Codex may perform one
bounded attended zero-candidate-flash comparison on the Samsung S22+
`SM-S906N`/`g0q` `S906NKSS7FYG8` using only the checked helper
`workspace/public/src/scripts/revalidation/s22plus_v3443_high_panic_compare_live_gate.py`
SHA256 `9e5e561bc39019b7ec5ebe1a79c3a24fa89803bca568c7aec6d5308a1a35f6a9`.
The active clause must contain sentinel
`S22PLUS_V3443_HIGH_PANIC_COMPARE_POLICY_STATE=ACTIVE`. Before any live action,
the operator must provide all three acknowledgements
`S22PLUS-V3443-HIGH-ONE-SYSRQ-PANIC`,
`S22PLUS-V3443-RDX-PREAMBLE-ONLY`, and
`S22PLUS-V3443-MID-RESTORE-RECOVERY`.

The helper must pin and verify the existing V3440 MID control before device
contact:

- `result.json` SHA256
  `62a6d12adb5ab33f39d9d44078de09f6180a39980b417dadf1fe9a598acd7dbe`;
- retained `/proc/last_kmsg` SHA256
  `a397d9688e740bc03bead8c4fd2fcc667910cfe98d2f92252a36b474e66a5b04`;
- S-Boot preamble response SHA256
  `3a4a3980e7835ebb77c927b99863e01847086171bdb81773e81e06f2192ab60c`.

The control must prove MID SysRq panic, current-run marker, `RDX is locked`,
kernel-panic upload cause, exact `NegativeAck`, `probe_sent=false`, and
`data_transfer_requested=false`. The live baseline must then prove exact
Android identity, boot completion, Magisk root, MID `18765` / `0x494d`, known
Magisk boot, stock DTBO, and stock recovery. The helper may stage only the
exact V3442 setter SHA256
`5bc230b87d090dcb694cd5eb68eb7e24a0ba5d8d9062cfada817953e5cc6f346`,
dispatch HIGH once, and require exact HIGH `18760` / `0x4948` before panic.

At exact HIGH, the helper may write one run-bound marker to `/dev/kmsg`, write
`1` once to `/proc/sys/kernel/sysrq`, and write `c` once to
`/proc/sysrq-trigger`. It may observe USB for at most 120 seconds. Only when
exactly one Samsung RDX endpoint `04e8:685d` exists may it send exactly
`PrEaMbLe\0` once and read one bounded endpoint packet. `PrObE forbidden` and
`DaTaXfEr forbidden`: positive, negative, malformed, timeout, or transport
error all stop without another S-Boot command. It must not invoke qdl, Sahara,
Firehose, request a range, read memory, or transfer dump data.

The operator must physically use RDX EXIT after the helper reports observation
complete. When HIGH Android returns, the helper may read `/proc/last_kmsg`,
durably store it, compute the same bounded metrics as the pinned MID control,
then re-stage the exact setter and dispatch MID exactly once. PASS requires
final Android/Magisk root, MID `18765` / `0x494d`, and exact boot/DTBO/recovery
identities. HIGH dispatch and panic each consume the exception regardless of
result and may not be retried.

If HIGH Android fails to return either after HIGH dispatch or after physical
RDX EXIT, the operator may physically enter Download mode. Recovery may flash
only exact V3441 MID-rescue boot AP SHA256
`25a8a5b5cfdeeebd47525c236d975561da8492bb08df5716cfa9da15e00ecfd6`,
then after its endpoint disconnects require a second physical Download entry
and flash only exact Magisk boot rollback AP SHA256
`d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`.
If that transfer fails while one Odin endpoint remains, exact FYG8 stock
boot-only fallback AP SHA256
`2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94`
may be used for cleanup only. Emergency continuation must not dispatch HIGH or
panic again.

This exception authorizes no candidate flash, RAM dump, memory range, device
memory write, partition-table operation, recovery/vendor_boot/DTBO/vbmeta/BL/
CP/CSC/super/userdata/persist/EFS/sec_efs/RPMB/keymaster/modem/bootloader
flash, raw host `dd`, fastboot, Magisk module, EUD/UART write, LCS/fuse/QFPROM
change, raw parameter action, format data, native-init candidate, or A90
action. Timeline output must use only the single
`events:[{name,timestamp_utc}]` schema with all eight mandatory phases.
`S22+ V3443 HIGH panic MID-control comparison live gate` is the policy marker.
