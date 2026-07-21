# S22+ FYG8 snapshot and independent-witness H0 audit

Date: 2026-07-22 KST
Scope: H0 host-only FYG8 source, model, existing live evidence, and primary
documentation review
Status: investigation complete; no build, image generation, device access,
flash, or live authority

## Verdict

Two questions are now separated.

1. The exact Samsung snapshot algorithm does **not** require a fully saturated
   retained ring for the current contiguous no-index-mutation carrier. For a
   record of `L` bytes, valid magic plus current `idx >= L` is sufficient for
   the next stock `/proc/last_kmsg` snapshot to expose the complete record.
   The E/E0 requirement `idx >= payload_size` is therefore source-proven to be
   stronger than the visibility contract requires.
2. No reusable candidate-selection witness independent of this Samsung ring
   was found within the current FYG8 evidence and permanent safety envelope.
   This is not a universal impossibility claim. It means every identified
   existing alternative is inaccessible, destructive, reset-class-only,
   downstream and unproved, or already live-retired.

The next design may relax the saturation gate only after changing and reviewing
the candidate/checker closure. It must not call a same-ring all-zero result an
independent execution proof. F1 remains inactive.

## Source identity

The modeled source is the source-matched FYG8 Samsung implementation already
pinned by the marker oracle:

```text
sec_log_buf_main.c
296f4fc175d958feb35b92c8736faf6361ade2e7c447d9a9af5a93f59bdb97b8

sec_log_buf_last_kmsg.c
ba9e0f9f0832cbf666e55b51804515fc8298203fd37958ccdfb6bfbbe3524443

include/linux/samsung/debug/sec_log_buf.h
5ed73be105e4984f3b4767229094af3f1a2e0f7258df9f648f7d32abc545d46e
```

The two implementation hashes exactly match their members in the official
base OSRC archive. The FYG8 delta archive contains no `log_buf` replacement,
so the base members remain the applicable FYG8 implementation.

The wider Samsung-driver review used the locally retained official source
archives:

```text
SM-S906N_15_base_osrc/Kernel.tar.gz
86e2f73412c65fadff0b15bbf0eac9140610f70250514ac0bddbf3b53fb5f7bf

S906NKSS7FYG8_osrc/S906NKSS7FYG8_kernel.tar.gz
23ef2b27de8843e271d41405b3c0b1a71bfa668615c8f0f12a1e5c4395ec851a
```

The exact header is four little-endian `u32` fields followed by payload:

```c
struct sec_log_buf_head {
    uint32_t boot_cnt;
    uint32_t magic;
    uint32_t idx;
    uint32_t prev_idx;
    char buf[];
};
```

For the FYG8 DT range, total size is `0x200000`, header size is 16, and
payload size `N` is `0x1ffff0` (2,097,136 bytes). Magic is `0x4d474f4c`.

## Exact stock snapshot

The stock probe order is load-bearing:

1. map the reserved range;
2. validate or initialize the header;
3. allocate the private last-kmsg buffer;
4. copy the retained payload into that private buffer;
5. publish `/proc/last_kmsg`;
6. import the current boot's early kmsg; and
7. install the current live writer.

The exported snapshot is therefore frozen before current-boot Samsung logging
starts. `/proc/last_kmsg` reads only the private copy.

The FYG8 DT enables `sec,use-last_kmsg_compression` with compressor `zstd`.
This does not change the exported byte geometry. The driver records the raw
snapshot size first, may compress and release its private raw buffer later,
then decompresses back to that recorded size on `/proc/last_kmsg` open before
`copy_to_user()`. If compression setup fails, it disables compression and
retains the original raw buffer. Thus the formulas below describe the actual
decompressed proc output, not merely an intermediate RAM copy.

Header preparation and copy reduce to:

```text
if magic != LOG_MAGIC:
    magic = LOG_MAGIC
    idx = 0
    prev_idx = 0
    # boot_cnt and payload bytes are not changed

if idx > N:
    head = idx % N
    output = payload[head:N] + payload[0:head]
else:
    output = payload[0:idx]
```

The comparison is strictly `idx > N`, not `idx >= N`. At `idx == N`, stock
takes the prefix branch and exports all `N` bytes.

Neither `boot_cnt` nor `prev_idx` is read by the copy function. `boot_cnt` is
useful to E0 as a same-boot overwrite-integrity check, but it cannot change
ENTRY visibility in the next stock snapshot. A boot-count mismatch could block
the later USERSPACE overwrite; it cannot explain a missing ENTRY that was
already stored.

The complete Samsung log-buffer driver also contains no Linux-side increment
or comparison of `boot_cnt`; only invalid-magic initialization writes
`prev_idx`. Any bootloader ownership of those fields is outside this snapshot
algorithm, so neither field may be used to infer proc visibility.

Invalid magic is different. Stock resets `idx` to zero before taking the
snapshot, so the exported file is empty for that prior generation. Candidate
code must continue refusing a physical payload write when magic is invalid.

## Contiguous pre-cursor proof

The D/E/E0 placement for an `L`-byte record is:

```text
cursor = idx % N
position = cursor - L       if cursor >= L
position = N - L            otherwise
write payload[position:position + L]
do not change idx
```

Combining that placement with the stock copy gives this complete visibility
rule:

| Current header | Stock output | Complete proof visibility |
|---|---|---|
| invalid magic | empty after header reset | no; physical write remains forbidden |
| `0 <= idx < L` | `payload[0:idx]` | no; an `L`-byte record cannot fit in the exposed prefix |
| `L <= idx < N` | `payload[0:idx]` | yes, at output offset `idx - L` |
| `idx == N` | complete payload, prefix branch | yes, at `N - L` |
| `idx > N`, `cursor >= L` | rotated complete payload | yes, in the final `L` output bytes |
| `idx > N`, `cursor < L` | rotated complete payload | yes, in the first physical segment |

The ring index is `u32`. After counter wrap, stock reasons only about the
current wrapped value. A wrapped current value below `L` again exposes too
short a prefix; a current value at least `L` follows the same rule above.
`boot_cnt` does not repair or alter that ambiguity.

The executable model is:

`workspace/public/src/scripts/revalidation/s22plus_fyg8_retained_snapshot_model.py`

It source-pins the two effective FYG8 files, verifies the strict branch and
probe order, and exercises both the exact 45-byte E0 record and arbitrary
record lengths. Focused tests cover invalid magic, `L-1`, `L`, `N-1`, `N`,
`N+1`, both rotation placements, `UINT32_MAX`, and header-field independence.

For `L=45`, the important model boundary is:

| `idx` | Branch | Snapshot size | Proof visible |
|---:|---|---:|---|
| 44 | prefix | 44 | no |
| 45 | prefix | 45 | yes |
| 2,097,135 | prefix | 2,097,135 | yes |
| 2,097,136 | prefix | 2,097,136 | yes |
| 2,097,137 | rotated full | 2,097,136 | yes |

The same threshold is 173 for the former E carrier. Full saturation is not
required for either shape.

## Impact on the E/E0 result

The current E0 code rejects every candidate-time index below `N`. The source
model proves that the much larger interval `45 <= idx < N` would have exposed
the complete E0 record had the code stored it. Therefore a candidate-time
index in that interval is a concrete explanation for silent refusal followed
by an all-zero observer result.

This remains an explanation, not a reconstruction of the completed run. The
candidate-time header was not captured, and offsets in the later rotated stock
snapshot do not recover its physical `idx`. Candidate nonselection, invalid
magic, `idx < 45`, and later corruption remain unresolved zero-result branches.

## Independent candidate-selection witness inventory

An acceptable independent witness would carry a candidate-derived identity,
survive until an established observer can read it, and remain inside the
boot-only/no-extra-partition/no-panic recovery envelope.

| Candidate channel | Source/evidence result | Disposition |
|---|---|---|
| Samsung kernel log | Proven positive for D, but it is the channel under test | not independent |
| Samsung pmsg carveout | Separate 2 MiB DT subrange, but `sec_pmsg_read()` always returns 0 and stock probe resets only its volatile writer index to 0 | no established post-reset reader |
| Mainline ramoops/pstore | Correct backend and binding were live-proven; the attended reset retained zero current-run records | retired for this reset path |
| `pstore/blk` | Upstream design persists by writing a block device | violates the no-non-boot-partition-write boundary |
| Samsung debug partition | Source uses block-device reads and `generic_perform_write()`; reset history and auto-comment are consumers of that partition | persistent but forbidden as a candidate writer |
| Samsung debug-region pool | Probe constructs a new root; new client memory is zeroed | current-boot workspace, not a prior-generation snapshot |
| Qualcomm summary/SMEM | Probe zeroes and rebuilds the summary; debug-kinfo setup also initializes its region | current-boot crash metadata, not a retained exact-Image witness |
| `rst_exinfo` | Probe zeroes the 4 KiB structure; useful paths are die/panic and later dump handling | destructive/terminal path, no normal observer |
| Upload-cause IMEM | Stock module initializes the word; defined values are reset classes, not an exact candidate identity | consumed/coarse and can alter RDX behavior |
| PON restart reason | One-byte NVMEM value is consumed/cleared by ABL; Download is also reachable through boot failure | coarse, non-unique, and state-changing |
| RDX | Exact FYG8 endpoint returned locked `NegativeAck` before data transfer | inaccessible and panic/RDX is outside the ordinary process |
| EUD | Reversible stock enable reached secure calls but produced no host endpoint or new TTY | controlled negative |
| Physical UART | Upstream guidance prefers UART, but no demonstrated accessible S22+ UART path exists in this setup | potentially independent, presently unavailable |
| USB/ACM, display, audio | Could carry a nonce after bring-up, but direct-PID1 versions are not yet proven | downstream future witnesses, not current selectors |
| Attended park/timing behavior | Prior stable-park observations are useful native-PID1 floor evidence | behavioral differential, not an exact candidate-Image binding |
| Bootconfig/cmdline | Supplied by build/vendor_boot/bootloader before kernel execution | input identity, not proof that the selected kernel ran |
| Bootloader text | Contains no exact candidate hash and is captured through the same Samsung ring | neither exact nor independent |
| Android `uname`/bugreport | Requires Android userspace under the candidate; post-rollback Android describes the rollback boot | unavailable for direct PID1 selection |

The result is `NO_INDEPENDENT_WITNESS_FOUND_IN_CURRENT_ENVELOPE`. This label
does not exclude future hardware UART, a newly proven USB banner, or a future
separately reviewed observer. It prevents the current design from pretending
that one of those channels already exists.

The local evidence anchors for this inventory are:

- official OSRC member
  `drivers/samsung/debug/pmsg/sec_pmsg.c`: `sec_pmsg_read()` returns zero and
  probe initializes the volatile `pmsg_idx` to zero;
- official OSRC members under `drivers/samsung/debug/debug_region/`:
  each client allocation is zeroed and a new in-memory client list is built;
- official OSRC
  `drivers/samsung/debug/qcom/summary/sec_qc_summary_main.c` and
  `qcom/rst_exinfo/sec_qc_rst_exinfo_main.c`: both clear their structures while
  probing;
- official OSRC
  `drivers/samsung/debug/qcom/dbg_partition/sec_qc_dbg_partition.c`: the
  persistent path opens a block device and uses `generic_perform_write()` plus
  synchronous writeback;
- `NATIVE_INIT_V3439_S22PLUS_CORRECTED_RAMOOPS_LIVE_NO_PROOF_2026-07-11.md`:
  backend and binding positive, current-run records absent after the attended
  reset;
- `NATIVE_INIT_V3440_S22PLUS_RDX_USB_VIABILITY_LIVE_CONTROLLED_NEGATIVE_2026-07-11.md`:
  locked negative acknowledgement before transfer;
- `S22PLUS_EUD_OPENOCD_HOST_AUDIT_2026-07-08.md`: no usable host endpoint after
  the reversible stock EUD probe; and
- `S22PLUS_FYG8_BOOTLOADER_REBOOT_REASON_AND_RETAINED_MEMORY_STATIC_RE_2026-07-11.md`:
  exact PON consumer plus non-unique Download/Odin fallback paths.

## Bounded same-ring consequence

Without an independent selector, the next carrier can improve information but
cannot make every zero result unique:

1. Keep exact path/PID, target, physical-layout, and magic validation before
   any retained-memory write.
2. Replace full saturation with the source-backed record-fit condition
   `idx >= record_size` for the exact no-index-mutation placement.
3. Bind every positive record to the candidate identity and read it back before
   returning from the hook.
4. Optionally define a shorter candidate-bound `UNSAT` record for
   `reason_size <= idx < entry_size`; validate that geometry separately.
5. Preserve the unresolved class when magic is invalid, `idx < reason_size`,
   the candidate is not selected, or the later stock observer loses the data.

The bounded outcome contract is therefore:

| Candidate-time state | Candidate action | Later positive meaning |
|---|---|---|
| valid magic and `idx >= entry_size` | write candidate-bound `ENTRY`, read it back, leave `idx` unchanged | exact ENTRY store completed |
| valid magic and `reason_size <= idx < entry_size` | write shorter candidate-bound `UNSAT`, read it back, leave `idx` unchanged | candidate reached the hook with valid magic but insufficient exposed prefix for ENTRY |
| invalid magic or `idx < reason_size` | write nothing | no positive classification is safe |
| candidate not selected or later data lost | no observable record | indistinguishable from the preceding no-write class |

A same-ring reason code cannot safely distinguish invalid magic from candidate
nonselection because writing before the magic guard remains forbidden. With an
unchanged index, `idx == 0` exposes no bytes at all. The next design must state
that residual ambiguity rather than claim a complete three-way discriminator.

No candidate, manifest, approval token, or F1-ready artifact is produced by
this audit.

## Primary documentation cross-check

- [Linux ramoops](https://docs.kernel.org/6.2/admin-guide/ramoops.html): ramoops
  requires a RAM region whose contents actually survive restart; backend
  registration alone does not establish platform retention.
- [Linux shutdown debugging with pstore](https://docs.kernel.org/power/shutdown-debugging.html):
  UART is preferred when available; otherwise pstore needs a working backend
  and retrieval on the next boot.
- [Linux pstore/blk](https://docs.kernel.org/6.2/admin-guide/pstore-blk.html):
  persistence is explicitly backed by a block/non-block storage device.
- [AOSP bootconfig](https://source.android.com/docs/core/architecture/bootloader/implementing-bootconfig):
  bootconfig is assembled from build-time and bootloader inputs before kernel
  execution.
- [AOSP generic boot partition](https://source.android.com/docs/core/architecture/partitions/generic-boot):
  `boot` supplies the GKI kernel while `vendor_boot` supplies device-specific
  cmdline, modules, and DTB; packaging identity is not a post-execution
  witness.

## Validation

```text
py_compile                                      PASS
official OSRC implementation-member SHA parity  PASS
focused snapshot-model tests                    14/14 PASS
related D/E/E0 and active-doc contract tests    54/54 PASS
exact FYG8 model, proof_size=45                 PASS
exact FYG8 model, proof_size=173                PASS
device contact / image build / flash            none
```
