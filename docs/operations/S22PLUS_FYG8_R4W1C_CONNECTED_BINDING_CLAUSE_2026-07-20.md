# S22+ FYG8 R4W1-C Connected Read-Only Binding Clause

Status: `INERT_HOST_ONLY_BINDING_DRAFT`

This file authorizes no device contact. After an independent exact-text review,
copy the complete fenced block below byte-for-byte into `AGENTS.md` in a
separate policy-binding commit. Do not copy only the sentinel lines.

```text
BEGIN_S22PLUS_FYG8_R4W1C_CONNECTED_POLICY_V1

**Pending exception (2026-07-20, S22+ FYG8 R4W1-C connected read-only
qualification):** Codex may perform one successful bounded connected read-only
qualification on Samsung S22+ `SM-S906N` / `g0q` / `S906NKSS7FYG8` only after
the exact helper, tests, artifacts, this complete clause, and the inactive
exception draft have passed independent host-only review and the attending
operator supplies the exact fresh acknowledgement below. Policy marker:
`S22+ FYG8 R4W1-C connected read-only qualification gate`.

`S22PLUS_FYG8_R4W1C_CONNECTED_POLICY_STATE=ACTIVE`

The only executable helper is
`workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1c_connected_gate.py`,
size `54734`, SHA256
`fa4e9b0a77032fbb8b17affb2ae985b80c990b6e4b07c0ee095328cfd80516b9`.
Its focused test is
`tests/test_s22plus_fyg8_r4w1c_connected_gate.py`, size `32764`, SHA256
`98938da61fc6a3f95389a31f019950fa00b3e6575687aab8d1edf5d070240251`.
The reviewed inactive exception draft is
`docs/operations/S22PLUS_FYG8_R4W1C_CONNECTED_EXCEPTION_DRAFT_2026-07-20.md`,
size `5774`, SHA256
`e1ff33327385b22e25e27ebd541b4103a2ce6b39408148d9e3318052c3eb2af2`.

Fresh acknowledgement:
`S22PLUS-FYG8-R4W1C-CONNECTED-READ-ONLY-DRY-RUN`.

Before device contact, the helper must rerun its complete offline artifact gate
and fresh deterministic static checker. It must require candidate raw boot
size `100663296`, SHA256
`1d394028714c48cfc0fd220acade9ead9a49ea21a81c59b2b87f88e61de704b0`;
candidate LZ4 size `27057849`, SHA256
`abe6b9069b1bfd04c0aeac4b022e367d5d8450101302d623ea2c9efe3b0c0d66`;
candidate boot-only AP size `27064361`, SHA256
`85514e79e3400de30b7146606a9e86c3655fc7a8766daba5f054ae1bd54fd42f`,
containing exactly one regular `boot.img.lz4` member; manifest size `15635`,
SHA256
`bfb932fd840104b54d41a957b13d56459c635d8939899c6f50d773aa7474ab76`;
and static result size `8306`, SHA256
`14786803582b62b88db9a3791ac49364a580fe9c5c8459d0e11b66e0f8215c94`,
schema `s22plus_fyg8_r4w1c_watchdog_carrier_static_checker_v1`, verdict
`PASS_R4W1C_WATCHDOG_CARRIER_TWO_REPRO_STATIC_CONTRACT`.

It must require exact Magisk boot-only rollback AP SHA256
`d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`;
exact cleanup-only stock boot AP SHA256
`2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94`;
full FYG8 stock firmware evidence SHA256
`f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8`;
hardened Odin transition core SHA256
`ab418aac5ce4c854f433e2132bd9536a610991384ec82c50dc0ba063f1888a9b`;
and Odin4 size `3746744`, SHA256
`6754aa54f2abe6e99ece32414cd34c8b23b28dbddde537a33203036813637c3b`.
All other source, test, builder, checker, reproduction, firmware, and transport
pins embedded in the helper must pass. These candidate and rollback artifacts
are qualification inputs only; this exception authorizes no transfer.

The run must start with exactly one authorized normal Android target and no
Odin endpoint. It must prove exact model, device, bootloader, FYG8 incremental,
completed boot, stopped boot animation, orange verified-boot state, Magisk
`uid=0(root)`, exact known Magisk boot SHA256
`2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`,
stock `vendor_boot` SHA256
`096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7`,
stock DTBO SHA256
`97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c`,
and stock recovery SHA256
`93fac06ca79bf4b365b25a8d49902bc41aba112ea253c30880c90e314d7895d4`.

The hardened Odin transition core must hold its PID/thread-bound
whole-transaction lease from initial Odin inspection through all Android and
observer collection, final Android identity and boot-ID continuity checks,
final Odin inspection, sealed receipt closure, durable preflight/timeline/result
and PASS creation, and complete PASS reopening. Initial and final bounded
`odin4 -l` must each complete successfully and produce exactly one clean-empty
snapshot with no raw, live, stale, or endpoint-identity entries. Enumeration
failure, stale output, a previously live endpoint, replacement, ambiguity, or
race fails closed. Every sealed snapshot and phase receipt and every complete
transaction-index segment must be reopened by path, size, SHA256, and final
stable bytes. The single prepared phase receipt must semantically match the
exact mode, Android serial, boot ID, and initial/final snapshot sequences.

The helper may perform only read-only ADB operations. It must prove live
`sec_log_buf`, exact platform bind
`/sys/bus/platform/drivers/samsung,kernel_log_buf/8.samsung,kernel_log_buf`,
absence of both `/sys/fs/pstore/console-ramoops` and
`/sys/fs/pstore/console-ramoops-0`, one EOF-complete bounded nonempty read of
`/proc/ap_klog`, and two EOF-complete bounded nonempty byte-identical reads of
`/proc/last_kmsg`. Every capture must have rc=0 and empty stderr. Every raw and
stderr file must be direct, contained in the run directory, identity-bound,
reopened, and free of R4W1-B marker-family contamination.

The helper must bind the exact active clause SHA256 before device contact and
recheck the same clause, inactive-draft, helper, and test identities before
PASS. A policy or source change fails closed. The result must bind and reopen
the exact preflight, canonical timeline, all raw observers, all empty stderr
files, all Odin receipts, and all transaction-index segments. A result path
must be a direct regular file under the private run root; symlinks are rejected.

PASS is only `PASS_R4W1C_CONNECTED_BASELINE_READ_ONLY`. A failed or interrupted
attempt creates no valid PASS and a new invocation requires a new exact fresh
acknowledgement. An existing valid PASS permanently blocks another successful
run. The helper may exclusively create only host-side run evidence and
`workspace/private/state/s22plus_fyg8_r4w1c_connected_read_only_pass.json`.
Timeline output must contain only `events:[{name,timestamp_utc}]` with the exact
canonical eight ordered phases. Candidate and rollback phases are explicit
zero-action semantics.

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

END_S22PLUS_FYG8_R4W1C_CONNECTED_POLICY_V1
```
