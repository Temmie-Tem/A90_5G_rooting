# S22+ FYG8 R4W1-C Connected Read-Only Exception Draft

Status: `DRAFT_INACTIVE`

Policy marker: `S22+ FYG8 R4W1-C connected read-only qualification gate`

The following are parser boundary identifiers, not a sufficient activation
clause by themselves:

`BEGIN_S22PLUS_FYG8_R4W1C_CONNECTED_POLICY_V1`

`S22PLUS_FYG8_R4W1C_CONNECTED_POLICY_STATE=ACTIVE`

`END_S22PLUS_FYG8_R4W1C_CONNECTED_POLICY_V1`

The only copyable activation text is the complete fenced block in
`S22PLUS_FYG8_R4W1C_CONNECTED_BINDING_CLAUSE_2026-07-20.md`. That separate
binding document must be generated after this draft and the helper/test bytes
are final, independently reviewed, and copied byte-for-byte into `AGENTS.md` by
a separate commit.

This draft authorizes no action by itself. Once activated, it permits one
successful connected read-only qualification record against Samsung S22+
`SM-S906N` / `g0q` / `S906NKSS7FYG8`, after a fresh operator acknowledgement:

`S22PLUS-FYG8-R4W1C-CONNECTED-READ-ONLY-DRY-RUN`

The only executable helper is
`workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1c_connected_gate.py`,
size `54734`, SHA256
`fa4e9b0a77032fbb8b17affb2ae985b80c990b6e4b07c0ee095328cfd80516b9`.
Its focused test is `tests/test_s22plus_fyg8_r4w1c_connected_gate.py`, size
`32764`, SHA256
`98938da61fc6a3f95389a31f019950fa00b3e6575687aab8d1edf5d070240251`.

Before any device contact, the helper must rerun the complete offline gate and
prove:

- candidate raw boot size `100663296`, SHA256
  `1d394028714c48cfc0fd220acade9ead9a49ea21a81c59b2b87f88e61de704b0`;
- candidate LZ4 size `27057849`, SHA256
  `abe6b9069b1bfd04c0aeac4b022e367d5d8450101302d623ea2c9efe3b0c0d66`;
- candidate boot-only AP size `27064361`, SHA256
  `85514e79e3400de30b7146606a9e86c3655fc7a8766daba5f054ae1bd54fd42f`,
  containing exactly one regular `boot.img.lz4` member;
- manifest size `15635`, SHA256
  `bfb932fd840104b54d41a957b13d56459c635d8939899c6f50d773aa7474ab76`;
- static result size `8306`, SHA256
  `14786803582b62b88db9a3791ac49364a580fe9c5c8459d0e11b66e0f8215c94`,
  schema `s22plus_fyg8_r4w1c_watchdog_carrier_static_checker_v1`, verdict
  `PASS_R4W1C_WATCHDOG_CARRIER_TWO_REPRO_STATIC_CONTRACT`;
- exact Magisk boot-only rollback AP SHA256
  `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`;
- exact cleanup-only stock boot AP SHA256
  `2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94`;
- full FYG8 firmware evidence SHA256
  `f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8`;
- hardened Odin transition core SHA256
  `ab418aac5ce4c854f433e2132bd9536a610991384ec82c50dc0ba063f1888a9b`;
- pinned Odin4 SHA256
  `6754aa54f2abe6e99ece32414cd34c8b23b28dbddde537a33203036813637c3b`;
- all other source and test pins embedded in the helper; and
- a fresh static-check result byte-identical to the pinned result.

The run must start with exactly one authorized normal Android target. It must
prove exact model, device, bootloader, FYG8 incremental, completed boot,
stopped boot animation, orange verified-boot state, Magisk `uid=0(root)`, exact
known Magisk boot, stock vendor_boot, stock DTBO, and stock recovery.

The hardened Odin transition core must hold its whole-transaction lease across
initial Odin inspection, all Android/observer collection, final Android
identity and boot-ID continuity checks, final Odin inspection, and receipt
closure, durable preflight/timeline/result/PASS creation, and complete PASS
reopening. Both the initial and final bounded `odin4 -l` snapshots must have
no raw, live, stale, or identity entries. Enumeration failure, stale output,
a previously live endpoint, replacement, ambiguity, or race fails closed.

The helper may then perform only read-only ADB operations. It must prove live
`sec_log_buf`, exact platform bind
`/sys/bus/platform/drivers/samsung,kernel_log_buf/8.samsung,kernel_log_buf`,
both pstore console paths absent, one EOF-complete bounded read of
`/proc/ap_klog`, and two EOF-complete bounded byte-identical reads of
`/proc/last_kmsg`. Every capture must have rc=0, empty stderr, nonzero content,
and no R4W1-B marker-family contamination.

PASS is only `PASS_R4W1C_CONNECTED_BASELINE_READ_ONLY`. A failed or interrupted
attempt creates no PASS and a new invocation requires a new fresh operator
acknowledgement; an existing PASS permanently blocks another successful run.
The helper may exclusively create
`workspace/private/state/s22plus_fyg8_r4w1c_connected_read_only_pass.json`,
path, size, and SHA256. The result must in turn bind and reopen every raw
observer and empty stderr file, marker semantics, the preflight record, the
canonical timeline, both sealed clean-empty Odin snapshots, the prepared phase
receipt with exact target-specific serial/boot-ID/sequence semantics, and every
complete transaction-index segment. Timeline output must
contain only `events:[{name,timestamp_utc}]` with the canonical eight ordered
phases; result semantics must state that all candidate and rollback transfer
phases are zero-action.

This connected exception authorizes no candidate execution and no device
write. It authorizes no reboot, Download transition, Odin transfer, flash, raw
host `dd`, fastboot, Magisk module, panic, SysRq, RDX/S-Boot command, RAM dump,
qdl/Sahara/Firehose, EUD/UART write, format, cleanup, or A90 action. It
authorizes no write to boot, recovery, vendor_boot, DTBO, vbmeta, BL, CP, CSC,
super, userdata, persist, EFS, sec_efs, RPMB, keymaster, modem, bootloader, or
any other partition.

Connected PASS does not activate a live exception. Candidate transfer remains
forbidden until a separate live helper, tests, exact connected-evidence
binding, independent review, committed one-shot `AGENTS.md` exception, and
fresh exact live acknowledgement all exist.
