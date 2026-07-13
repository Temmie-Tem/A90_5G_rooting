# S22+ FYG8 R4W1-B Direct-PID1 Exec-Acceptance Design

Date: 2026-07-13 KST

Target: `SM-S906N/g0q/S906NKSS7FYG8`

Scope: host-only target selection and design. No kernel build, candidate image,
device contact, USB enumeration, ADB, Odin invocation, reboot, Download
transition, flash, or partition write is authorized by this document.

## Decision

R4W1-B will combine two already proved boundaries without widening userspace:

1. the R4W1-A kernel-side `kernel_execve("/init") == 0` retained-ring witness;
2. the exact live-proven M4T2 raw-park boot ramdisk and 544-byte `/init`.

A newly Full-LTO-built R4W1-B Image will carry a new marker ID. A dedicated
candidate builder will insert only that Image into the exact M4T2 raw boot's
fixed kernel interval. The Image must remain exactly `41,490,944` bytes at
`[4096,41495040)`. Every byte outside that interval, including the distinct
1,536-byte alignment gap `[41495040,41496576)`, must remain equal to the
live-proven M4T2 carrier.

The load-bearing positive claim is deliberately narrow:

`the exact transferred direct-PID1 candidate had /init accepted by the rebuilt kernel as PID 1`

It does not claim that the first EL0 instruction, first syscall, watchdog
ownership, USB, display, module loading, Android, Debian, or long-duration park
succeeded. Those remain later rungs.

## Why M4T2 Is The Carrier

The exact M4T2 `/init` is the smallest available candidate:

```text
source SHA256  d5ec47527dae3d94e88ca8555e7efd96048de3ea87a3a136b50ad5a8be301551
ELF SHA256     b8371e3ac671ff71e9be752b8ff1087a4f20811c871a43ca8e698eee47783d12
ELF size       544
mode           0750
PT_INTERP      absent
syscalls       none
instructions   wfe; b <wfe>
```

Its exact live-proven carrier identities are:

```text
raw boot SHA256     8103bce76fb3e41d71b64735a64d2f2f29431a44ea1c9a85dc0bc151d71afd15
boot-only AP SHA256 66d7f24b348702f58efbe1945b0d2751052ed27f6ce1f6fc4e5da63f3a585b24
```

M4T2 was transferred once, stopped the prior fast-loop shape, parked without
ADB/Odin during its observation window, and rolled back to exact Magisk Android.
That behavioral result is not reused as the R4W1-B proof; it only establishes
that this exact ramdisk is the least novel direct-PID1 carrier.

V3432 is rejected as the R4W1-B carrier because it adds `getpid`, volatile
mounts, `finit_module`, `sec_log_buf.ko`, proc-node checks, `/dev/kmsg`, frame
generation, and several failure branches. Those operations were necessary when
the observer had to be created from userspace. R4W1-B's kernel writes the ring
before candidate userspace runs, so every V3432 operation is unnecessary noise.

## Host Probe Result

The M4T2 source was rebuilt on the current host with its original compiler and
link flags. The resulting ELF was byte-identical to the live-pinned hash and
disassembled to exactly the two expected instructions. The original M4T2
builder then reproduced the exact live raw boot and AP identities above.
Tool identities, commands, outputs, and hashes are durably recorded in
`docs/reports/S22PLUS_FYG8_R4W1B_M4T2_CARRIER_HOST_REPRO_2026-07-14.md`.

A separate no-change MagiskBoot probe against the R4W1-A stock-Android
candidate was rejected as a construction base. Merely unpacking/repacking that
boot changed the ramdisk size from `1,978,967` to `1,653,775`, changed header
bytes, and produced raw boot SHA256
`f8bbf64e2ac89bf1954291626f6486ecdc1e99daa088f1b0ff10c2e57f2d06b1`
instead of the input
`a2bba0ef907af14e57508ca55d247d571c3f89936dd7020293e51ebfa8f8d133`.
R4W1-B therefore must not reopen or repack that stock ramdisk.

## Proof Composition

R4W1-B is motivated by three independently proved facts:

1. R4W1-A proved that the rebuilt kernel's direct `sec_log_buf` append executes
   after PID 1 accepts `/init`, and that the exact marker is recoverable from a
   canonical stock-Android bugreport in the same boot.
2. V3428R proved that an exact run-bound ring frame can survive its specific
   attended RDX-to-Download plus boot-only Magisk transition and appear
   unchanged in the first rollback boot's `/proc/last_kmsg`.
3. M4T2 proved that the selected raw-park ramdisk is accepted as a boot carrier
   and produces the intended no-transport park behavior.

V3428R is a feasibility prior, not a substitute for R4W1-B evidence. A future
R4W1-B result is positive only when its own exact marker is recovered. Marker
absence remains `NO_PROOF` even if the transition resembles V3428R. The result
may attribute the marker to the exact M4T2 ELF only when it pins the exact new
kernel, exact M4T2 outside-kernel bytes, exact AP transfer, stock `vendor_boot`,
stock DTBO/recovery, final rootfs ownership of `/init`, the retained-memory
contract, and exact Magisk rollback.

No prior run proves that `sec_log_buf` survives the specific forced transition
from a no-transport `wfe` park. That retention leg is an explicit hypothesis of
R4W1-B, not an inherited fact. A marker-bearing park-origin positive control
would reduce the risk of spending the one-shot on structural `NO_PROOF`, but it
would itself require a separately reviewed boot candidate. Until such a control
exists, marker absence is the expected null and cannot disprove exec acceptance
separately from transition retention.

## New Marker Contract

The marker ID is the first 128 bits of SHA256 over this exact ASCII preimage:

```text
S22PLUS_FYG8_R4W1B_DIRECT_PID1_EXEC_ACCEPTED|SM-S906N|g0q|S906NKSS7FYG8|init=b8371e3ac671ff71e9be752b8ff1087a4f20811c871a43ca8e698eee47783d12|base=8103bce76fb3e41d71b64735a64d2f2f29431a44ea1c9a85dc0bc151d71afd15|r4w1a=35d015d04bdde36469bbb9ebcd2f355158a2cc475444d426f49a9d83d112ad3e
```

Full preimage SHA256:

`36dc5462adedcf136176f2ddcfee08a80ae871167935f7353f51062e4691a2dc`

The exact 99-byte marker, including leading and trailing newlines, is:

```text

[[S22R4W1B|id=36dc5462adedcf136176f2ddcfee08a8|phase=DIRECT_INIT_EXEC_ACCEPTED|pid=1|path=/init]]
```

The runtime does not claim to hash `/init`. The exact transferred boot and its
outside-kernel equality, stock `vendor_boot`, and final-rootfs composition audit
bind the marker to the M4T2 `/init`; the static checker and live helper carry
that evidentiary responsibility.

The marker family namespace is the exact delimiter-anchored ASCII prefix
`[[S22R4W1B|`; it must never be searched as loose substring `S22R4W1B` or
`S22R4W1`. In particular, `[[S22R4W1B|` and the historical
`[[S22R4W1|` are distinct anchored families. The classifier must count complete
exact records separately from family records.
Any family-prefix occurrence that is not one complete exact marker, any foreign
ID or field value, or any proper prefix/suffix of the exact marker at an
observer boundary is integrity failure. One or more complete exact records are
positive exec-acceptance evidence; the count and any intervening reset are
reported as a separate stability observation. Repeated exact records cannot
negate the narrower acceptance proof.

## Kernel Build Contract

R4W1-B starts from a newly reconstructed clean FYD9+FYG8 source tree. It must
not binary-patch the existing Image because the linked FIPS and provenance
outputs must be regenerated.

The new patch may change only the same three files as R4W1:

1. `kernel_platform/common/init/main.c`;
2. `kernel_platform/common/init/Kconfig`;
3. `kernel_platform/common/arch/arm64/configs/gki_defconfig`.

The control flow and ring-write implementation remain equal to R4W1. Only the
build-bound marker and source identifiers change. The build retains Full LTO,
RKP, KDP, UH, DEFEX, PROCA, FIVE, module/KMI, and all FYG8 security settings.

Required host gates:

- exact source overlay and toolchain provenance;
- exact FYG8 release/banner;
- new marker exactly once in `Image` and `vmlinux`;
- old R4W1/R4W1B foreign marker absence as appropriate;
- only the witness config delta;
- `CONFIG_CRYPTO_FIPS=y` and a successful regenerated FIPS post-link HMAC whose
  source inputs, symbol placement, and final Image insertion pass the R4W1
  checker contract;
- complete KMI CRC and ABI equality against the pinned R4W1 baseline
  `vmlinux.symvers` SHA256
  `fd75413401617a427ddf6c264d0ae4f5452b46cde02b4575b9af09f19601ca19`
  and `abi.xml` SHA256
  `3660c592e1884ab323816c09a3abd197744c8b2f78aed890b02c3e69dbc1c55c`;
- raw Image size exactly `41,490,944` bytes; aligned kernel allocation length
  exactly `41,492,480` bytes; absolute ramdisk start `41,496,576`; and the
  intervening 1,536-byte gap preserved;
- source-level path/PID/return-value contract plus final `vmlinux`
  disassembly, symbol, xref, and control-flow proof that the ring append is
  reachable only for PID 1, path `/init`, and `kernel_execve()` return zero;
- two independent clean Full-LTO builds with byte-identical Image, config,
  regenerated FIPS HMAC, `vmlinux.symvers`, `abi.xml`, `vmlinux`, and
  `System.map`;
- all temporary source/build controls restored byte-exactly.

Historical R4W1 scripts, tests, results, and pins remain unchanged. R4W1-B uses
new source names and schemas rather than mutating the retired evidence chain.

## Candidate Construction Contract

The future R4W1-B builder must consume:

- exact live-proven M4T2 raw boot SHA256
  `8103bce76fb3e41d71b64735a64d2f2f29431a44ea1c9a85dc0bc151d71afd15`;
- exact M4T2 `/init` SHA256
  `b8371e3ac671ff71e9be752b8ff1087a4f20811c871a43ca8e698eee47783d12`;
- exact stock FYG8 `vendor_boot` SHA256
  `096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7`;
- exact separately reproduced R4W1-B Image;
- pinned LZ4 and Odin binaries;
- full FYG8 stock evidence and both rollback chains.

Construction is a fixed-slice replacement only:

```text
Android header    exact M4T2 bytes [0,4096), header v4
kernel_size       41490944 (unchanged)
kernel format     raw (unchanged)
kernel interval  [4096, 41495040)
alignment gap    [41495040, 41496576), preserve exact M4T2 bytes
outside interval byte-for-byte equal to exact M4T2 raw boot
raw boot size    100663296
AP members       exactly [boot.img.lz4]
```

After construction, an independent checker must unpack the final boot, verify
the exact `/init` bytes and mode, disassemble its entrypoint, prove no syscall
instruction, verify the new kernel marker exactly once, compare every
outside-kernel byte against M4T2, require the complete kernel interval to equal
the separately reproduced R4W1-B Image SHA256 byte-for-byte, validate Android
header v4, exact unchanged `kernel_size`, raw kernel format, ARM64 header
equality, and fixed layout, and round-trip the LZ4/AP containers. Here ARM64
header equality means
the extracted final kernel header equals the separately built R4W1-B Image
header; it does not mean equality to M4T2's old kernel header.

The checker must independently enumerate the generic ramdisk and every stock
`vendor_boot` ramdisk fragment under the exact FYG8 boot-v4 composition order.
The resulting rootfs must contain exactly one effective `init`, a regular file
with UID/GID `0/0`, mode `0750`, size `544`, and the exact M4T2 SHA256. It must
reject duplicate CPIO entries, symlink/hardlink aliases, absolute or `./init`
path aliases, any vendor-fragment override, and any kernel/vendor cmdline or
bootconfig `rdinit=` override.

Kernel replacement intentionally leaves the M4T2 boot signature and AVB
descriptor stale. The checker must require byte-exact preservation of the M4T2
footer/signature/tail, the expected failing/stale `avbtool` verification result,
orange/unlocked boot as a future live precondition, and
`PATCHVBMETAFLAG=false`. No AVB or vbmeta patch is permitted.

Three independent candidate reproductions must be byte-identical before any
live-helper design.

## Future Live Contract

R4W1-B is one-shot, boot-only, attended, and separately authorized. The future
helper must begin from one completed rooted FYG8 Android baseline with exact
known Magisk boot, stock `vendor_boot` SHA256
`096e433e049fb088cd956e083d5a1039b33cdf0ca907e713bba7feaaf1b080b7`,
stock DTBO SHA256
`97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c`,
stock recovery SHA256
`93fac06ca79bf4b365b25a8d49902bc41aba112ea253c30880c90e314d7895d4`,
orange state, live `sec_log_buf`, both proc observers readable to EOF, complete
exact-family and boundary-partial marker absence, and no Odin endpoint. The
same stock `vendor_boot`, DTBO, and recovery hashes are mandatory after rollback.

Immediately before candidate transfer, the helper must exclusively and durably
create a consumed-state record that binds the exact helper, candidate AP,
static result, target, and run directory. Creation is the
`candidate_flash_start` event and consumes the exception regardless of transfer
result. A preexisting or malformed state stops the run. After consumption,
mandatory rollback applies to every outcome. A separate recovery-only mode may
restore the exact Magisk AP from one unambiguous normal Odin endpoint, but may
never retransfer the candidate.

The helper may transfer the exact candidate AP once. After Odin disconnect it
observes raw park for at most 90 seconds. Candidate ADB is not expected and is
not a proof requirement. The attending operator then physically enters the
same RDX-to-normal-Download path used by V3428R when the hardware presents it;
the host sends no RDX command. A direct unambiguous normal Download endpoint is
recorded as a transition difference but may still be used for mandatory
rollback. The helper transfers the exact Magisk boot-only rollback AP and waits
for the first rooted Android boot.

No RDX command is allowed. If RDX appears, host observation stops; the operator
physically exits it and enters normal Download. RDX dwell and the complete
candidate-disconnect-to-Odin transition are separately bounded by 120 seconds.
An ambiguous or multiple endpoint stops transfer and requires attended recovery.
A failed Magisk transfer with one unambiguous normal Odin endpoint may use only
the pinned stock boot cleanup AP; stock cleanup is never PASS.

The first rollback boot must read `/proc/last_kmsg` twice to EOF. The reads must
be byte-identical. Marker classification is:

| Evidence | Final rollback | Verdict |
| --- | --- | --- |
| one or more exact R4W1-B markers, no family issue | exact Magisk health | `PASS_R4W1B_DIRECT_PID1_EXEC_ACCEPTED_AND_ROLLED_BACK` |
| no exact/family marker | exact Magisk health | `NO_PROOF_R4W1B_EXEC_OR_TRANSITION_UNRESOLVED` |
| partial, malformed, foreign, or duplicate family marker | any | `FAIL_R4W1B_MARKER_INTEGRITY` |
| any evidence shape | rollback unverified | `FAIL_R4W1B_ROLLBACK_NOT_VERIFIED_RECOVERY_REQUIRED` |

Marker presence proves exec acceptance even if later park behavior is abnormal;
exact marker count, transport timing, and spontaneous reset observations are
recorded separately and cannot synthesize or negate the marker proof.

The timeline schema remains exactly:

```text
events:[{name,timestamp_utc}]
```

with exactly one ordered occurrence of:

`live_session_start`, `candidate_flash_start`, `candidate_flash_done`,
`candidate_boot_ready`, `rollback_flash_start`, `rollback_flash_done`,
`rollback_boot_ready`, `live_session_end`.

For this no-transport candidate, `candidate_boot_ready` means bounded raw-park
observation close, not Android readiness or marker proof.

All eight events remain present on recovery-only or failed-action results. The
result must explicitly label a named phase as no-action/no-proof rather than
changing the timeline shape or pretending that a transfer occurred.

## Safety Boundary

Only boot may ever be transferred under a future reviewed exception. This
design authorizes no current device action and no write to recovery,
vendor_boot, DTBO, vbmeta, BL, CP, CSC, super, userdata, persist, EFS,
sec_efs, RPMB, keymaster, modem, bootloader, or any other partition. It also
authorizes no raw host `dd`, fastboot, Magisk module, panic, SysRq, RDX command,
RAM dump, qdl/Sahara/Firehose, EUD/UART write, format, security-config change,
or A90 action.

## Promotion Rule

Only exact R4W1-B marker PASS promotes the direct-PID1 path. The next rung is
R4W2 first-userspace execution: prove PID 1 reaches EL0 and performs one exact
first syscall. R4W1-B by itself does not promote USB, watchdog-managed runtime,
module loading, or Debian.

## Next Unit

Implement host-only R4W1-B source, patch checker, Full-LTO build wrapper, static
audit, reproducibility checker, and focused tests. No candidate builder is
promoted until two clean Full-LTO Images reproduce byte-identically. No live
helper or policy exception is part of that implementation unit.

## Independent Review Closure

Two independent Codex reviewers and one Claude Opus read-only adversarial
review initially returned `NO_GO` or `GO_WITH_MUST_FIX`. This revision closes
their hard findings by:

- retiring both stale M4T2 authorization clauses in `AGENTS.md`;
- separating the exact 41,490,944-byte kernel from its 1,536-byte alignment gap;
- fixing Android header v4, `kernel_size`, raw format, inside-Image equality,
  outside-byte equality, stale AVB, and stock `vendor_boot` ownership gates;
- binding FIPS, named KMI/ABI baselines, and final Full-LTO control flow;
- treating V3428R as a feasibility prior and forced-from-park retention as an
  unproved, fail-closed hypothesis;
- using delimiter-anchored marker families and accepting exact count `>=1` while
  reporting resets separately; and
- specifying durable one-shot consumption, numeric transition bounds, mandatory
  rollback, recovery-only behavior, exact DTBO/recovery pins, and canonical
  no-action timeline semantics.

No reviewer authorized live work. The remaining uncertainty is empirical and
cannot be closed host-only: whether the retained ring survives the exact
park-origin physical transition. Its only permitted null interpretation remains
`NO_PROOF`.

## Static Validation

- `git diff --check`: PASS;
- all relative links in the changed plan/report/ledger: PASS;
- marker preimage SHA256, 128-bit ID, and exact 99-byte record: PASS;
- kernel interval `41,490,944`, alignment gap `1,536`, and aligned allocation
  `41,492,480`: PASS;
- current source/tool/base/vendor_boot hashes and temporary M4T2 manifest versus
  the durable report: PASS;
- M4T2 live/Odin RETIRED sentinels present exactly once and no R4W1-B ACTIVE
  sentinel: PASS;
- 61 focused historical R4W1/R4W1-A tests: 60 PASS; one pre-live-only real A4
  qualification test correctly stopped because the post-live one-shot consumed
  state now exists. The failure predates and is independent of this docs-only
  R4W1-B unit; the consumed state must not be removed or bypassed to make that
  historical precondition pass.

Verdict:

`PASS_R4W1B_HOST_DESIGN; SOURCE_IMPLEMENTATION_NEXT; NO_LIVE_AUTHORIZATION`
