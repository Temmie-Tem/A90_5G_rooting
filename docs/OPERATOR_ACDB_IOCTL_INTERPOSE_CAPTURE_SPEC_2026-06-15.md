# OPERATOR SPEC — ACDB `acdb_ioctl` interposition capture of the custom-topology payload (2026-06-15)

**Author:** operator (host-side RE), not the autonomous loop. This is a build spec for the
loop to implement. It supersedes the cross-process dmabuf / file-read source-buffer capture
line (V2463–V2473), which is a dead end for the reasons below.

## Goal

Capture the **4916-byte `CORE_CUSTOM_TOPOLOGIES_CAL_TYPE` (cal_type 39) payload** that V2461
saw delivered via `AUDIO_SET_CALIBRATION` (`mem_handle=37`, `cal_size=4916`) but never read,
because the bytes live behind a dma-buf that is opaque to cross-process inspection
(procfs fd reopen → `ENXIO`, owner-VA read → `EIO`, early-dup → `ENXIO`; see V2466–V2472).

This payload is the missing input for native ACDB replay (V2462 boundary). Once it is pinned
(bytes + length + SHA-256), the native replay scaffolding can send it through
`/dev/msm_audio_cal`.

## Why interposition, not more snooping

Host RE of the stock 32-bit `libacdbloader.so` (+ `libaudcal.so`) from the V2324 vendor dump
shows the topology blob is produced **inside the audio HAL process** by the ACDB engine and
copied into the dma-buf only afterward. The clean capture point is the ACDB database query
call itself, **before** the dma-buf copy. That call is `acdb_ioctl`, which `libacdbloader.so`
imports (`U acdb_ioctl`) from `libaudcal.so` — so it is **interposable via `LD_PRELOAD`**.

Capturing in the HAL's own process avoids: (a) dma-buf cross-process opacity, (b) reversing
the `.acdb` binary format, (c) reversing `acdb_loader_init_v4`'s init struct, (d) injecting
into `audioserver` by ptrace. The HAL inits ACDB and fetches the topology naturally; our
wrapper just observes the output buffer.

## RE facts (evidence)

Tool: `workspace/private/inputs/toolchains/llvm-arm-toolchain-ship-10.0/bin/llvm-objdump`
(LLVM 10, run with `LD_LIBRARY_PATH=tmp/relibs` where `tmp/relibs/libtinfo.so.5` →
host `libtinfo.so.5`). Analyzed files (host-only, proprietary, never commit):

- `workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump/lib/libacdbloader.so`
- `workspace/private/runs/audio/v2324-aud0-inventory/vendor_dump/lib/libaudcal.so`

Confirmed `acdb_ioctl` signature (from prologue at `libaudcal.so` `0xd884`, Thumb):
`push {r4-r9,lr}` (28B) + `sub sp,#4` then `ldr.w r9,[sp,#32]` reads the 5th arg off the
stack; `r0..r3` are args 1–4. Classic Qualcomm ACDB ABI:

```c
int32_t acdb_ioctl(uint32_t command_id,    // r0
                   const uint8_t *in_buf,   // r1
                   uint32_t       in_len,   // r2
                   uint8_t       *out_buf,  // r3
                   uint32_t       out_len); // [sp,#32] -> r9
```

- Command IDs are in the `~0x12xxx–0x13xxx` range (switch/`tbh` jump table on `r0`). The exact
  `ACDB_CMD_GET_AVCS_CUSTOM_TOPO_INFO` constant is **not needed**: filter empirically by
  `out_len == 4916`. Record the observed `command_id` for documentation.
- `acdb_loader_send_common_custom_topology` (`libacdbloader.so` `0x8cf0`) first queries size
  (`ACDB_CMD_GET_AVCS_CUSTOM_TOPO_INFO_SIZE`, `out_len==4` returning 4916), then fetches the
  payload (`out_len==4916`), then `allocate_cal_block` (ION/dma-buf) + `AUDIO_SET_CALIBRATION`.
  The first two are the `acdb_ioctl` calls we interpose.
- `acdb_loader_init_v4` (`libacdbloader.so` `0x808c`) takes `arg0`=init-info struct ptr,
  `arg1`==4; allocates ~5824B of stack. **SUPERSEDED by the RE UPDATE 2026-06-16 below:** the
  arg0 struct is now fully pinned (16 bytes), `acdb_loader_init_v3` is a clean 3-arg entry that
  builds it, and the `.acdb` files are discovered by directory scan — so an own-process
  `dlopen` helper is no longer expensive and is now a co-primary path, not just a fallback.

## Helper to build

A **32-bit `armeabi-v7a`** shared object (the stock audio HAL is 32-bit; must match), e.g.
`libacdbtap.so`:

```c
// real = dlsym(RTLD_NEXT, "acdb_ioctl") resolved lazily on first call
int32_t acdb_ioctl(uint32_t cmd, const uint8_t *in, uint32_t in_len,
                   uint8_t *out, uint32_t out_len) {
    int32_t r = real_acdb_ioctl(cmd, in, in_len, out, out_len);
    if (out && out_len > 0) {
        // append one record to a private capture file:
        //   {pid, tid, cmd(hex), in_len, out_len, ret=r, sha256(out[0:out_len])}
        // and write raw out bytes to <dir>/acdbtap-<cmd>-<seq>-<out_len>.bin
        // (only out_len bytes). Especially flag out_len == 4916.
    }
    return r;
}
```

Requirements:
- Resolve the real symbol with `dlsym(RTLD_NEXT, "acdb_ioctl")`; never recurse.
- Be allocation-light and reentrancy-safe (the HAL calls this many times); guard the dump
  with a simple in-process append, bounded.
- Write raw payloads only under a private capture dir (e.g. `/data/local/tmp/a90-acdb-tap/`),
  then `adb pull` to `workspace/private/runs/audio/<run>/`. **Never commit raw bytes.**
- Public/report output: per-call `command_id`, `in_len`, `out_len`, `ret`, SHA-256 only.

## Injection (the genuinely tricky part — capsule engineering)

`LD_PRELOAD` `libacdbtap.so` into the process that loads `libacdbloader.so` — the audio HAL
(`android.hardware.audio.service`; the worker TID seen as the `/dev/msm_audio_cal` owner in
V2416/V2458). Constraints/contract:

1. The preload must be active **before the HAL initializes ACDB**. If the topology fetch is a
   one-time init-cached call, set the preload, then **restart the audio HAL** (so it re-execs
   with the preload), then trigger playback. If unsure, restart-then-play is the safe order.
2. Mechanism is the transient Magisk measurement capsule's job (you built M0/M1). Candidate
   approaches in order of preference: an init `.rc` `setenv LD_PRELOAD` override for the HAL
   service via a Magisk service overlay; or a wrapper-exec shim for the service binary; or a
   root-set environment on a manual service relaunch. The `wrap.<name>` zygote property likely
   does **not** apply (the HAL is init-started, not zygote-spawned) — verify before relying on it.
3. **SELinux is the main risk:** loading an unconfined preload into a system HAL domain under
   enforcing may be denied. If blocked, capture the denial (`dmesg`/`logcat avc:`) and report
   it; do not silently disable enforcing as a "fix". A bounded permissive-for-the-capture or a
   minimal `magiskpolicy` allow, fully reverted on cleanup, is acceptable only inside the
   recoverable envelope and must be documented.

## Trigger & acceptance

1. Boot stock Android via the checked handoff; stage the transient capsule + `libacdbtap.so`.
2. Establish the preload into the audio HAL; restart the HAL.
3. Run the existing AudioTrack speaker stimulus (reuse the V2377/V2407 path).
4. The wrapper records **every** `acdb_ioctl` call with `out_len > 0`.
   **Full success = at least one call with `out_len == 4916` captured**, its raw
   bytes saved privately and SHA-256 recorded; ideally also the paired
   `out_len==4` size query returning 4916.
   **Partial success = a complete ordered out-buffer set with no 4916-byte
   record** (`captured-acdbtap-full-outbuf-set-no-4916`): preserve the run and
   hand it to the operator because the per-device AFE/ASM/ADM/VOL payloads are
   still valuable for size/order mapping. Do **not** count this outcome as a
   fails-twice dead run.
5. Pull artifacts privately, clean up the capsule + any sepolicy change, reboot to recovery,
   checked rollback to **v2321**, final `selftest fail=0`.

This finally pins the V2462-blocked payload (bytes + length 4916 + SHA-256). Combined with the
V2461/V2462 ioctl-sequence + kernel mem-handle/cleanup facts, native N3 replay is then
unblocked: allocate an ION/dma-buf of 4916, fill with these bytes, run the
`ALLOC`/`SET`/`DEALLOC` sequence on `/dev/msm_audio_cal`, keep fds open across the bounded PCM
probe.

## RE UPDATE 2026-06-16 — own-process path is now UNBLOCKED (gate removed)

Host RE of `acdb_loader_init_v4`/`init_v3`/`init_v2`/`send_common_custom_topology`
(libacdbloader.so, V2324 dump, llvm-objdump thumbv7) pinned everything the former
fallback was missing. **The "ping the operator for init_v4 RE" gate is removed.**

- **`init_v4(arg0, version)` validates** `arg0 != NULL` (else returns `-22`) and
  `version == 4` (else returns `-22`). `arg0+12` is read as a status-byte out-pointer
  guarded by `cmp #0; strbne`, so NULL is allowed.
- **`arg0` is a 16-byte struct** (proved by the thin wrappers `init_v3`/`init_v2`, which
  build it on-stack inside a `sub sp,#24`/`#48` frame and tail-call `init_v4` with `r1=4`,
  touching only `+0..+12`):

  ```c
  struct acdb_init_v4 {          // 16 bytes
      char    *delta_file_path;  // +0   writable delta dir (a temp dir is fine)
      char    *acdb_files_path;  // +4   "/vendor/etc/acdbdata"
      uint32_t meta_info_type;   // +8   0
      uint8_t *status_out;       // +12  NULL ok
  };
  ```

- **No struct construction needed:** call the clean 3-arg wrapper instead —
  `acdb_loader_init_v3(acdb_files_path /*r0->+4*/, delta_file_path /*r1->+0*/,
  meta_info_type /*r2->+8*/)`, i.e.
  `acdb_loader_init_v3("/vendor/etc/acdbdata", "<writable_dir>", 0)`.
- **No file list needed:** `init_v4` discovers `.acdb` files by `opendir()`-scanning the
  `acdb_files_path` directory (≤20 files; rodata: `Maximum number of ACDB files hit, %d!`,
  `No .acdb files found in %s!`). The `.acdb` files already exist on the live device.
- **Topology fetch command IDs** (passed in `r0` to `acdb_ioctl`, arg layout
  `r0=cmd, r1=in_buf(sp+56), r2=in_len, r3=out_buf(sp+88), out_len=[sp]`):
  `0x11394`, `0x12E01`, `0x130DA`, `0x130DC` (=`0x130DA+2`). The 4916-byte one is
  identified empirically by `out_len==4916`. **`0xC00461CB` is the direct
  `/dev/msm_audio_cal` SET ioctl** — a pure-read capture must NOT issue it.

## Fallback → now a CO-PRIMARY path: own-process ARM32 helper

Own-process ARM32 helper that `dlopen`s `libacdbloader.so` (+ on-device deps
`libaudcal.so`, `libacdb-fts.so`, `libacdbrtac.so`, `libadiertac.so`), then:

1. `acdb_loader_init_v3("/vendor/etc/acdbdata", "<writable_dir>", 0)`;
2. pure-read capture of the 4916-byte topology, either by
   (a) `dlsym(acdb_ioctl)` and calling the GET command(s) above directly (size cmd →
   alloc → data cmd → dump; **no SET, no `0xC00461CB`**), or
   (b) interposing `acdb_ioctl` in *our* process and calling
   `acdb_loader_send_common_custom_topology` but capturing only the `out_len==4916` GET
   (note this variant also triggers the `0xC00461CB` SET, so prefer (a) for pure read).

This sidesteps the live-HAL blockers entirely: AudioFlinger only talks to the
init-managed HAL PID (so a second/manual HAL copy is useless — V2483), the in-HAL
SELinux domain risk, and the linker-namespace/wrapper-exec injection problem
(V2479–V2487). Remaining risk is only VNDK namespace loadability of `/vendor/lib`
deps from a standalone binary — far more tractable than HAL injection (run from a
vendor path, use the linker namespace API, or run as `su`).

Tradeoff vs in-HAL interpose: the own-process direct-GET reliably captures the
**topology** (the V2462 blocker) but not the full per-device set. In-HAL interpose
during real playback captures topology **+** AFE/ASM/ADM/VOL naturally. They are
complementary; capturing the topology unblocks the V2462 boundary regardless.

## Boundaries (unchanged)

Measurement only. Transient capsule, no persistent module install. No native
`/dev/msm_audio_cal` calibration ioctls in this unit. No native speaker write. Recoverable
envelope + checked rollback to v2321 + anti-churn/fails-twice all stay in force. Do not commit
raw payload bytes, the vendor `.so` files, or unredacted captures.

## RE UPDATE 2026-06-16 (b) — per-device cal path (`send_audio_cal_v5`) for the FULL manifest

The 4916-byte custom topology (cal_type 39) is necessary but NOT what blocks
`pcm_prepare` (V2393: the EINVAL is AFE/ASM/ADM **per-device** cal_block NULL, cal_types
8/9/11/15/16). The own-process helper must capture the full set, which means also driving
the per-device cal fetch. RE of `acdb_loader_send_audio_cal_v5` (libacdbloader.so `0x9d30`)
and its thin wrappers `v4`/`v3`/`v2` (`0xb550`/`0xb574`/`0xb590`):

- **`send_audio_cal_v5` is a 7-arg function** (4 regs + 3 stack):
  `r0..r3` = args 1–4; `arg5=[sp+160]`, `arg6=[sp+164]`, `arg7=[sp+168]` after the
  `push {r4-r11,lr}` + `sub sp,#124` prologue. The `v4` wrapper hardcodes `arg7=1`
  (instance/use-case flag); `v2`/`v3` default the newer trailing args, confirming the arg
  order grows v2→v5.
- **Semantic mapping** from the log format string
  `ACDB -> send_audio_cal, acdb_id = %d, path = %d, app id = 0x%x, sample rate = %d, afe_sample_rate = %d`
  plus V2407 live values:

  ```c
  acdb_loader_send_audio_cal_v5(
      int acdb_id,           // arg1 = 15        (speaker RX device)
      int path_or_caps,      // arg2 = 0 (RX)    (v5 bit-tests low bits of this arg)
      int app_id,            // arg3 = 0x11135   (app_type 69941)
      int sample_rate,       // arg4 = 48000
      int afe_sample_rate,   // arg5 = 48000
      int session_type,      // arg6
      int instance_flag);    // arg7 = 1         (v4 hardcodes 1)
  ```

  (arg6/arg7 exact names are best-effort; the loop can confirm empirically — the first
  five are pinned by the format string.)
- **Per-device GET commands** the per-device cal pulls go through (visible as named
  constants in rodata; each has a paired `_SIZE` query, same `acdb_ioctl` ABI as topology):
  `ACDB_CMD_GET_AFE_INSTANCE_COMMON_TABLE` (→ `AUDIO_SET_AFE_CAL` cal_type 16),
  `ACDB_CMD_GET_AUDPROC_INSTANCE_COMMON_TABLE` / `..._STREAM_TABLE`
  (→ `AUDIO_SET_AUDPROC_CAL` cal_type 11), `ACDB_CMD_GET_AUDPROC_INSTANCE_GAIN_DEP_STEP_TABLE`
  (→ `AUDIO_SET_VOL_CAL` cal_type 12), plus the LSM instance tables (listen, out of scope).

### Pure-read caveat (important)

`send_audio_cal_v5` internally does the `acdb_ioctl` GETs **and then** the direct
`/dev/msm_audio_cal` SET ioctl `0xC00461CB`. To stay pure-read, the helper must either
(a) call the per-device GET commands directly (size → alloc → data → dump), like the
topology path, issuing **no** `0xC00461CB`; or (b) interpose `acdb_ioctl` AND interpose/no-op
`ioctl()` on the `msm_audio_cal` fd so the captured GETs run but the SET is suppressed.
Prefer (a). The full manifest = topology (cal_type 39, 4916) + AFE (16) + AUDPROC common &
stream (11) + gain-dep/VOL (12), captured in fetch order with sizes + SHA-256.

## RE UPDATE 2026-06-16 (c) — diagnosing `acdb_loader_init_v3` return `-19` (V2510)

V2510 cleared the loader walls (vendor libs load via exec-link DT_NEEDED) and reached
`acdb_loader_init_v3`, which returned `-19`. RE of `init_v4` pins exactly two `-19`
(`mvn r6,#18`) return sites, each preceded by an `ACDB-LOADER`-tagged error log:

- `0x82ba` ← log `"Error initializing ACPH returned = %d"` (ACDB Packet Handler init failed).
- `0x83e8` ← log `"ACDB -> Could not load .acdb files!"` (the `.acdb` DB load/scan failed).

**To disambiguate:** capture the helper's stderr + `logcat -s ACDB-LOADER` during the run;
the printed line tells you which path fired. Likely root causes for a standalone su-domain
binary (vs the in-namespace HAL):

1. `.acdb` load (`0x83e8`): our process cannot read `/vendor/etc/acdbdata/*.acdb` (SELinux
   label on vendor configs not granted to our exec domain), or the `acdb_files_path` arg is
   wrong (check trailing slash / exact `"/vendor/etc/acdbdata"`). Verify with
   `ls -lZ /vendor/etc/acdbdata` and `dmesg | grep avc` after the run.
2. ACPH init (`0x82ba`): the packet handler needs a dependency the HAL normally has — check
   `persist.vendor.audio.calfile%d` properties, any extra dep lib in the closure, or a device
   node the handler opens. ACPH lives in the closure (`acph_init`); ensure its deps loaded.

This stays measurement/pure-read; no `0xC00461CB` SET. If a bounded SELinux allow is needed
to let our domain read `acdbdata`, it must be reverted on cleanup and documented (same policy
as the in-HAL path).

## RE UPDATE 2026-06-16 (d) — `-19` root cause CONFIRMED + magiskpolicy contingency (V2517/V2519)

V2517/V2519 pinned the `init_v3 -19` definitively. The `.acdb` load **and** ACPH init both
**pass** (logs: `ACPH init success`); the abort is downstream:

- `Cannot open /dev/msm_audio_cal errno: 13` (EACCES). Node label `u:object_r:audio_device:s0`,
  `crw-rw---- system:audio`.
- `Access denied finding property "persist.vendor.audio.calfile0"` — property type
  `u:object_r:vendor_audio_prop:s0` denied.
- **Plus** the helper was running as `uid=2000 u:r:shell:s0`, not root — the runner's
  multi-line `adb shell su -c <script>` was dropping out of the `su`/`u:r:magisk:s0` context
  (fixed by the V2520 quoting commit).

### Step 1 — run as root (done)
After the quoting fix the helper must execute as `uid=0 u:r:magisk:s0` (verify by logging
`id` + `cat /proc/self/attr/current` immediately before exec, as V2518/V2519 do).

### Step 2 — if root context STILL hits `errno 13`: bounded `magiskpolicy --live` allow
Magisk's `u:r:magisk:s0` may not natively reach `audio_device`/`vendor_audio_prop`. Apply a
**runtime, non-persistent** allow as root before the helper, capture the exact avc lines
first, and let it revert (these `--live` rules do not survive the rollback reboot):

```sh
# capture denials first (evidence, do not skip)
dmesg | grep -i avc | grep -iE 'audio_device|vendor_audio_prop' || true
# minimal allows for the own-process ACDB init transport
magiskpolicy --live "allow magisk audio_device chr_file { open read write ioctl getattr map }"
magiskpolicy --live "allow magisk vendor_audio_prop file { open read getattr map }"
```

This is the spec-sanctioned bounded path (NOT `setenforce 0`): explicit, minimal, evidence-
logged, auto-reverted on the rollback reboot, and documented in the run report. If a further
denial appears (e.g. an adsprpc/DSP device the cal transport touches), add the same shape of
minimal `--live` allow for that exact label only — never a blanket permissive.

### Note: this is a capture-side artifact only
The SELinux domain wall exists only because we measure on Android-good (enforcing). Native
replay (Gate 3) runs as PID 1 in native-init with no Android sepolicy domain transition, so
this `audio_device`/`vendor_audio_prop` access fight does **not** carry into the native path.

## RE UPDATE 2026-06-16 (e) — V2522 hang root cause + fix: stub the staged `libdiag`

After the root-context fix the helper no longer instant-denies (`-19`); it now **hangs**
(V2522, 60s timeout) past the `/dev/msm_audio_cal` open. Static RE pins the cause with high
confidence — it is the ACDB **RTAC / ACPH-online tuning transport**, which is irrelevant to a
pure-read GET:

- `libacdbloader` imports `pthread_create`/`pthread_join` and runs `acdb_rtac_init` /
  `adie_rtac_init` (deps `libacdbrtac.so` / `libadiertac.so`). Init log order is
  `MCS, FTS INIT` → **`RTAC INIT`** → `ADIE RTAC INIT` → `init done!`.
- The online/RTAC path is **DIAG-based**: `libaudcal` calls `acph_online_init` /
  `Diag_LSM_Init` / `atp_receive_diag_pkt` (QACT real-time-tuning over `/dev/diag`).
- In a standalone process the diag-router handshake/receive does not complete the way it does
  for the real audioserver, so init blocks (a `Diag_LSM_Init` wait or a `pthread_join` on the
  diag receive thread) **before `init done!`** — exactly the V2522 hang.
- RTAC is **not** cleanly property-gated (only `persist.vendor.audio.calfile%d` props exist),
  so disabling via property is unreliable.

### Fix (preferred) — no-op stub `libdiag.so` in OUR staged closure

We already stage and DT_NEEDED-link the dependency closure ourselves (V2506/V2508) under
`/data/local/tmp`, so this is fully measurement-only and touches no device file. Replace the
staged `libdiag.so` with a stub exporting exactly these symbols (the set `libaudcal` imports):

```
Diag_LSM_Init            -> return 0   // report "diag unavailable" so RTAC/online init skips, no thread
Diag_LSM_DeInit          -> return 0
diagpkt_commit           -> no-op (return)
diagpkt_err_rsp          -> return 0/NULL
diagpkt_subsys_alloc     -> return NULL
diagpkt_subsys_get_cmd_code -> return 0
diagpkt_tbl_reg          -> return 0
```

Returning failure from `Diag_LSM_Init` makes the ACDB online/RTAC init skip cleanly (RTAC is
non-essential for cal loading), so no diag thread is created and nothing is joined. Stubbing
the bottom of the stack neutralizes diag for `libacdbrtac`/`libadiertac` too in one move.

### Expected result

With diag stubbed, init should reach `ACDB -> init done!`, `acdb_loader_init_v3` returns `0`,
and the helper proceeds to the topology + per-device GET commands → first real `out_len>0`
captures. V2523 observability (preserve logcat + artifacts on timeout) should still land first
to confirm the hang site is `Diag_LSM_Init`/RTAC and that `init done!` now prints; the stub is
robust whether init was joining the thread or just lingering on it.

### Fallback if stubbing is insufficient

If init still blocks with diag stubbed, the hang is deeper in `acph_online_init`; then either
(a) also stub the `acph_online_*` entry via an interposer, or (b) skip `init_v3` and call the
lower-level DB-load + GET directly (needs a short additional RE of the load-only entry).

## OPERATOR VERIFICATION 2026-06-16 — V2529 "get-success-4916" is a FALSE POSITIVE

Run `v2490-acdb-ownprocess-get-20260616-051924` was classified
`v2490-acdb-get-success-4916` but captured **no real payload**. Operator verification (Gate 2)
of the captured event set + raw `.bin`:

- **Every** `acdb_ioctl` GET returned **`ret=-2`** (0 records with `ret==0`).
- All `out_len==4` buffers hash to `df3f619804a92fdb...` = `SHA256(4 × 0x00)`.
- All `out_len==4916` buffers hash to `9af4895ee511379e...` = `SHA256(4916 × 0x00)`.
- The pulled `*-out4916.bin` is confirmed **all-zero, len 4916**.

So the helper hashed a zero-filled output buffer that `acdb_ioctl` never wrote (it returned
`-2` = ACDB-not-initialized). The `is_target_4916=true` flag is true only because the helper
*requested* `out_len=4916`, not because real bytes came back.

### Root cause

The GET commands require a fully initialized ACDB engine. `acdb_loader_init_v3` returns `-12`
because `allocate_cal_block` → `AUDIO_ALLOCATE_CALIBRATION` ioctl returns `-1`, so the engine
is **not initialized** and every subsequent GET returns `-2`. **The soft-fail strategy
(V2529) is a dead end: GET needs init success; it cannot read the DB while init is failed.**

### Required corrections

1. **Classifier bug (fix first):** success must require `ret == 0` **and** a non-all-zero
   output buffer (reject `SHA256(N×0x00)`), not merely `out_len == 4916`. Re-classify the
   051924 run as a failure.
2. **Abandon soft-fail; fix the real blocker:** make `AUDIO_ALLOCATE_CALIBRATION` succeed so
   `init_v3` returns `0`. `ion_open`/`ion_alloc_fd` already succeed (no "Cannot allocate ION"
   log); only the `msm_audio_cal` ioctl fails (`-1`). Diagnose with `dmesg | grep avc` around
   the run + the exact ioctl errno. Likely: SELinux **ioctl-level** filtering on `u:r:magisk:s0`
   for `audio_device` (open is allowed but the specific cal ioctl is not), or the kernel
   rejecting our ion buffer's heap, or the cal block already held by the live audioserver.
3. This `AUDIO_ALLOCATE_CALIBRATION` path is **also required for Gate 3 (native replay)**, so
   solving it now is double-value — capture the exact errno + any avc denial verbatim.

## OPERATOR HANDOVER 2026-06-16 — bypass the `AUDIO_ALLOCATE_CALIBRATION` EINVAL by faking it

V2533 pinned the blocker: `AUDIO_ALLOCATE_CALIBRATION` (`0xc00461c8`) returns `ret=-1
errno=22 (EINVAL)` with **no avc** (SELinux ruled out; the ioctl reached the kernel and was
rejected on args/state). Deallocate (`0xc00461c9`) succeeds. The kernel audio techpack source
is not in the partial tree here, so the exact EINVAL line can't be read from source — but it
doesn't need to be.

**Key insight:** the GET commands read the in-memory `.acdb` DB; the cal block allocated by
`AUDIO_ALLOCATE_CALIBRATION` is the shared-memory region for the **SET** path (sending cal to
the DSP), which a pure-read GET does not use. Most-likely EINVAL cause = the live audioserver
already holds that cal_type's allocation and the kernel rejects a second one (a runtime-state
conflict, not a malformed request — the request geometry equals what audioserver sends, same
lib code). So don't fight the kernel; make init think it succeeded.

### Fix: intercept the allocate ioctl in our own process (reuse the V2531 preload)

We already preload an `ioctl()` interposer (V2531 trace). Change it from observe-only to:

- `AUDIO_ALLOCATE_CALIBRATION` (`0xc00461c8`): **do not call the real ioctl** (or call and
  override); **return 0**. Leave the loader's own ion fd/`mem_handle` untouched — `ion_alloc_fd`
  already succeeded and the buffer is mmap-able, so any later `mmap(mem_handle)` by the loader
  still works. Apply to **every** allocate call (init may allocate several cal types).
- `AUDIO_DEALLOCATE_CALIBRATION` (`0xc00461c9`): return 0 (no-op) for symmetry.
- Pass through all other ioctls unchanged. Still issue **no** `AUDIO_SET_CALIBRATION`
  (`0xc00461ca`) and no real `0xC00461c8` to the kernel — this stays measurement/pure-read.

Expected: `allocate_cal_block` "succeeds" → `acdb_loader_init_v3` reaches `init done!` and
returns `0` → `is_initialized=true` → the topology + per-device GET commands return `ret=0`
with real non-zero buffers (verify against the zero-buffer discriminator: `ret==0` AND not
`SHA256(N×0x00)`).

### If init still fails after faking allocate
Then init depends on the cal block beyond registration (unlikely). Fallback: also intercept
the `mmap` of the returned handle, or RE the loader's `is_initialized` gate to find any other
init step. But faking the two allocate/deallocate ioctls should be sufficient.

### Diagnostic value preserved
Record that the EINVAL is a kernel arg/state rejection (no avc). If later confirmation is
wanted, capture whether stopping the live audioserver first lets the real allocate succeed —
but the fake-allocate path is the pragmatic capture route and does not require that.

## OPERATOR HANDOVER 2026-06-16 (b) — gate the acdb_ioctl dump to AFTER init (fixes V2535 SIGSEGV + V2538 hang)

State: fake-allocate (V2534) advances init into the custom-topology path, but (A) single-preload
fake-allocate SIGSEGVs before GET rows (V2535), and (B) adding the `acdb_ioctl` capture preload
hangs init at `ACDB_CMD_INITIALIZE_V2` with zero events (V2536/2537/2538). Two clean structural
facts resolve both:

1. In `send_common_custom_topology` the **GET (size then 4916 data) happens BEFORE** the
   allocate → memcpy → SET steps. So the topology bytes are available *before* whatever crashes
   downstream. Capture the GET and you have the payload regardless of the later crash.
2. V2538 hanging at `INITIALIZE_V2` (the very first `acdb_ioctl` call) with zero events means the
   `acdb_ioctl` wrapper destabilizes init on its first invocation — it must not do its dump work
   during the hundreds of init-time `acdb_ioctl` calls.

### Fix: arm the dump only after `init_v3` returns

Combined single preload (keep V2538's one-`.so` design exporting `acdb_ioctl` + `ioctl`):

- `ioctl`: keep `A90_ACDB_FAKE_ALLOCATE=1` (fake-success ALLOC/DEALLOC/SET, pass through the rest).
- `acdb_ioctl`: add a process-global flag, e.g. `static volatile int a90_armed = 0;`
  - while `a90_armed == 0`: just `return real(...)` — **no dump, no file I/O, no hashing**. This
    lets `init_v3` (incl. `INITIALIZE_V2` and all init-time GETs) run clean.
  - the **helper** sets `a90_armed = 1` immediately after `acdb_loader_init_v3` returns and right
    before it calls `acdb_loader_send_common_custom_topology()` (export the flag, or expose a tiny
    `a90_arm_capture()` setter from the preload that the helper `dlsym`s/calls).
  - while armed: dump every `out_len>0` buffer; on the first record with `ret==0` AND a non-all-zero
    buffer AND `out_len==4916`, flush it (and the paired size query) to the private file and
    `_exit(0)` immediately — this banks the payload and dodges the downstream allocate/SET SIGSEGV
    entirely.

This needs **no in_buf RE** (the real `send_common_custom_topology` builds the correct query) and
no in-HAL injection. If the per-device cal (AFE/AUDPROC/VOL) is also wanted in the same run, don't
`_exit` on the first 4916 — keep dumping armed records through `acdb_loader_send_audio_cal_v5(15,
0, 0x11135, 48000, 48000, ...)` and exit after the matrix, accepting the crash risk only after the
needed records are banked.

### Fallback
If arming-after-init still misses the topology GET, RE the exact size/data `in_buf` that
`send_common_custom_topology` passes (libacdbloader `0x9154`/`0x958c`: `in_len=8`, in_buf at
`sp+56` = `{...}`) and have the helper call the GET directly post-init. Ping the operator to finish
that in_buf decode if needed.

## OPERATOR VERIFICATION 2026-06-16 (b) — V2547 topology capture is REAL (Gate 2 pass, partial)

Run `v2490-acdb-ownprocess-get-20260616-080716`, file
`acdbtap-00000003-cmd-00013296-len-00001334.bin`:

- **size 4916, 2420 non-zero bytes, structured to the tail** (not a zero buffer; not the
  V2530-class false positive). The V2530 discriminator correctly separated it from the prior
  `no-4916` run.
- Decoded as a valid **AVCS custom-topology** blob: header `{count=0x45, ...}`, 116 words in the
  topology/module-ID range (`0x1002a000`, `0x10028000`, `0x10030fff`, ...).
- ABI confirmed (loop RE): topology cmd = `ACDB_CMD_GET_AVCS_CUSTOM_TOPO_INFO_V3` `0x13296`,
  **indirect** output — `in_buf = {len=0x1334=4916, ptr=payload_VA}`; the payload is behind the
  pointer, not in `out_buf` (which is 4 bytes). This is why earlier `out_buf`-only attempts
  captured zeros.
- **Canonical topology SHA-256: `7c5d45efa40944bc23dcc83af9f0046249499bb13d1a03c3470c287127992b89`**
  (one successful capture; confirm determinism with a second capture → same SHA before
  hard-coding into replay).

### Completeness caveat (important for Gate 3)

This is the topology (cal_type 39) ONLY. V2393's `pcm_prepare` EINVAL was driven by missing
**per-device** cal: AFE (`afe_get_cal_topology_id` types 8/9, `send_afe_cal_type` 16), ASM
(`q6asm_send_cal` NULL), plus `adm_open ADSP_EFAILED`. Topology registration likely fixes the
`adm_open`/custom-topology part but **not** the AFE/ASM cal blocks. The V2550 topology-only replay
is a valid experiment — run it and read dmesg:

- if `pcm_prepare` passes → topology was the key (great);
- if it still fails naming AFE/ASM `cal_block not found`/NULL → that is the expected signal, not a
  regression. Capture the per-device set next by extending the armed capture through
  `acdb_loader_send_audio_cal_v5(15, 0, 0x11135, 48000, 48000, ...)` (don't `_exit` on first 4916),
  banking AFE(16)/AUDPROC(11)/VOL(12), and add them to the replay manifest.

## OPERATOR RE 2026-06-16 — `send_audio_cal_v5` arg2 is a capability MASK that must be nonzero (V2574 fix)

V2574 reached `send_audio_cal_v5` but produced no per-device GET records (only a spurious
`cmd=0x0` call, then hang/timeout). Re-RE of the `send_audio_cal_v5` prologue
(libacdbloader `0x9d30`) finds an early bail keyed on **arg2 (the 2nd argument, `r1`)**:

```
9d68 lsls r0, r7, #30   ; r7 = arg2 ; test bit1
9d70 movpl r5, #-1      ; bit1 == 0 -> r5 = -1
9d74 lsls r0, r7, #31   ; test bit0
9d7c movne r5, #0       ; bit0 == 1 -> r5 = 0
9d7e adds r0, r5, #1
9d80 beq.w +0x18e       ; bail if r5 == -1  (i.e. (arg2 & 0x3) == 0)
```

**Conclusion: arg2 is a capability/path bitmask; v5 returns early (no cal fetch, no
`acdb_ioctl` GET) when `(arg2 & 0x3) == 0`.** Passing `path=0` there → immediate bail, which
matches the V2574 "send_audio_cal_v5 reached but zero per-device records" + spurious `cmd=0`.

### Fix
Pass **arg2 = 1** (RX, bit0 set), not 0. Refined prototype:

```c
acdb_loader_send_audio_cal_v5(
    int acdb_id,        // arg1 = 15
    int cap_mask,       // arg2 = 1  (RX; MUST be nonzero / (x&3)!=0, else v5 bails)
    int app_id,         // arg3 = 0x11135
    int sample_rate,    // arg4 = 48000
    int afe_sample_rate,// arg5 = 48000
    int session_type,   // arg6
    int instance_flag); // arg7 = 1
```

`send_audio_cal_v5` is a **dispatcher** (only one direct `acdb_ioctl`, cmd `0x1122E`; it
delegates AFE/AUDPROC/VOL fetches to sub-functions via ~12 `blx` calls), so with arg2 fixed the
internal per-device GETs should fire and the armed `acdb_ioctl` interpose should capture them
(cal_type 8/9/11/12/15/16 buffers). Verify each with the V2530 zero-buffer discriminator
(`ret==0` AND non-all-zero).

### If a hang persists after the arg2 fix
A sub-function may enter the ACPH-online/RTAC/diag path (the V2510-class `Diag_LSM_Init` hang)
or block on the faked-allocate cal block. Mitigations: keep the libdiag-stub / thread-group
`exit_group` already in place; and as with topology, capture each per-device GET as it returns
and bank it, then `_exit(0)` after the needed cal_types are collected rather than letting v5 run
to a downstream crash.

## OPERATOR GATE-2 VERIFICATION 2026-06-16 — per-device cal manifest (V2614/V2618)

Verified the captured per-device candidates against each other across two independent
runs/methods (V2614 meta-list-indirect, V2618 direct-matrix).

### Determinism: PASS (data is real)
For every per-device payload, the two runs are **byte-identical except the first 4-byte word**:

| cal_type | size | bytes 4..end | first word (V2614 / V2618) |
| ---: | ---: | --- | --- |
| 11 AUDPROC common | 18084 | identical | `0x0001031f` / `0x000046a4` (=18084=size) |
| 15 AUDPROC/ASM stream | 28 | identical | `0x00010bfe` / `0x0000001c` (=28=size) |
| 16 AFE common | 1560 | identical | `0x0001025f` / `0x00000618` (=1560=size) |

So the cal **data is deterministic / real**, not garbage. Only the leading word differs by
capture method: V2618 wrote the buffer **size** there; V2614 left an ACDB id-like value. For
replay, treat the first word as a header/length field — prefer the V2618 size form (or confirm
empirically), the trailing data is what matters and it is stable.

### Completeness: FAIL — missing the FIRST dmesg blocker
Captured: cal_type 11, 15, 16 (+ topology 39 from V2547). **Missing:**
- **cal_type 8/9 (AFE topology)** — this is the **first** error in the V2393/V2552 dmesg
  (`afe_get_cal_topology_id: cal_type 8 and 9 not initialized for port 16384`), gating the whole
  AFE chain. AFE common (16) alone is NOT enough; `afe_get_cal_topology_id` runs before it.
- **cal_type 12 (VOL)** — V2614 gain/VOL GET returned `-19`, not captured (likely secondary; VOL
  may not block `pcm_prepare`).

### Verdict for the V2624 multi-cal replay gate
- The 3 verified payloads + topology can go into replay, BUT **replay will most likely STILL fail
  at AFE** because cal_type 8/9 are absent. Capture 8/9 first (a distinct AFE-topology GET command,
  not the AFE-common 16 path) before expecting `pcm_prepare` to pass.
- **Replay order (DSP chain): topology 39 → AFE topology 8/9 → AFE cal 16 → AUDPROC 11 → ASM/stream
  15 → (VOL 12).** AFE topology must precede AFE cal; topology 39 registers first.
- mem_handle/cleanup: reuse the V2552-proven ALLOCATE(fake/real)/SET/DEALLOCATE-per-cal pattern;
  keep each cal's fd/handle until its SET returns, deallocate after.

**Gate-2 result: 3 payloads verified real + deterministic; manifest INCOMPLETE (need 8/9, ideally 12);
replay not yet expected to clear `pcm_prepare` until AFE topology 8/9 is added.**

### GATE-2 CORRECTION 2026-06-17 (supersedes the "capture 8/9 via a distinct GET" line above)
The loop tested the "8/9 via AFE-topology GET" steer (V2626 probe → V2627 live → V2628 mapping) and it is a **dead end**: the AFE-topology GET (`0x130d8`/`0x13262`) only returns small **scalars** — topology ID `0x1001025d`, a count word `0x4`, an indirect word `0x1` — **not a replay-able cal block**. V2628 correctly rejected the 4-byte indirect record as "evidence, not payload."
- **Root cause (V2629):** cal_type 8/9 is **header-only** at the SET layer. The V2614 `AUDIO_SET_CALIBRATION` trace shows cal_type 9 as `data_size=52, cal_size=0, mem_handle=-1` — i.e. it is programmed purely by the **ioctl argument struct**, with **no dma-buf payload**. That is why GET exposes only scalars and why every dma-buf-only capture (Phase H) missed it.
- **Correct mechanism (V2630, own-process):** intercept `AUDIO_SET_CALIBRATION` as fake-success in our own process and dump **(1) the full ioctl arg bytes** (captures header-only 8/9) **+ (2) the same-process `mmap` of `mem_handle`** when `cal_size>0` (captures 11/15/16 payloads). Same-process fd ⇒ no `ENXIO`/`EIO` — this **also resolves the Phase H dma-buf dead end**. One live run yields the **full ordered SET manifest** (8 records: types 13, 9, 11, 12, 15, 23, 16, 21) instead of per-cal GET grinding.
- **Replay order unchanged** (topology 39 → AFE topology 8/9 → AFE cal 16 → AUDPROC 11 → ASM/stream 15 → VOL 12). Next: run V2630 live (Android-good handoff, V2321 rollback), then Gate-2 the captured SET manifest.

### OPERATOR RE 2026-06-18 — Gate-4 DSP-rejection ROOT CAUSE = missing per-subsystem custom topology defs (cal_type 10 / 14 / 24)
V2632 captured the full `send_audio_cal_v5` SET manifest and V2648 replayed it natively: the blocker MOVED from "kernel has no cal" to "kernel sends cal, DSP rejects it" (V2650). Operator host-RE of the QC q6 DSP sources (CAF msm-4.14 = same code as the Samsung audio techpack; kernel tree ships no `techpack/audio`, so this is from public `kernel/msm-extra` + coral-kernel headers) pins the cause.

**Exact global cal_type enum (`msm_audio_calibration.h`)** — the project's "AFE topology" labels were off by the enum:
`9=ADM_TOPOLOGY`, **`10=ADM_CUST_TOPOLOGY`**, `11=ADM_AUDPROC`, `12=ADM_AUDVOL`, `13=ASM_TOPOLOGY`, **`14=ASM_CUST_TOPOLOGY`**, `15=ASM_AUDSTRM`, `16=AFE_COMMON_RX`, `17=AFE_COMMON_TX`, `20=AFE_FB_SPKR_PROT`, `21=AFE_HW_DELAY`, `23=AFE_TOPOLOGY`, **`24=AFE_CUST_TOPOLOGY`**, `39=CORE_CUSTOM_TOPOLOGIES`.

**Captured manifest = `{9,11,12,13,15,16,21,23}` (+ GET-blob `39` prepended in V2636). MISSING = cal_type `10`, `14`, `24` — the per-subsystem CUSTOM TOPOLOGY DEFINITIONS.** Verified host-side: no `setcal-events.jsonl` ever contained 10/14/24.

**Kernel mechanism (q6adm.c / q6afe.c / q6core.c):**
- `send_adm_custom_topology()` reads **ADM_CUST_TOPOLOGY (10)** → `ADM_CMD_ADD_TOPOLOGIES`, once, **before COPP open**.
- `afe_send_custom_topology()` reads **AFE_CUST_TOPOLOGY (24)** → `AFE_CMD_ADD_TOPOLOGIES`, **before the AFE port cal**.
- the ASM path reads **ASM_CUST_TOPOLOGY (14)** → `ASM_CMD_ADD_TOPOLOGIES`.
- These register the custom topology graphs (e.g. ADM topo `0x10004000`) with the DSP. `q6core_send_custom_topologies()` (CORE_CUSTOM_TOPOLOGIES `39` → `AVCS_CMD_REGISTER_TOPOLOGIES`) is a **separate global path** — q6core source: "each subsystem manages its own topology registration separately." So replaying `39` does NOT feed ADM/ASM/AFE.

**This maps 1:1 onto the three V2648 DSP rejections:**
- `adm_open topo_id 0x10004000 → ADSP_EFAILED` ⇐ ADM_CUST_TOPOLOGY (10) never set → topology `0x10004000` not registered.
- `afe AFE_PORT_CMD_SET_PARAM_V2 (0x100ef) → ADSP_EBADPARAM` ⇐ AFE_CUST_TOPOLOGY (24) never set → AFE port cal references modules not present in the (unregistered) topology.
- `q6asm set_pp_params (0x10da1) → ADSP_ENEEDMORE` ⇐ ASM_CUST_TOPOLOGY (14) never set → ASM postproc topology modules absent.

**Why the prepended cal_type 39 didn't help:** (a) the subsystems read 10/14/24, not 39; (b) the replayed 39 was the **ACDB-internal GET blob** (`ACDB_CMD_GET_AVCS_CUSTOM_TOPO_INFO_V3` `0x13296`, 4916 B), not the byte-exact SET payload that `acdb_loader_send_common_custom_topology()` actually writes to `/dev/msm_audio_cal`.

**NEXT (capture EXTENSION, not a new mechanism — supersedes V2651's broad order-only plan):** the own-process fake-SET helper currently drives only `acdb_loader_send_audio_cal_v5()` (per-device cal). **Extend it to ALSO drive the custom-topology send path** — `acdb_loader_send_common_custom_topology()` and whatever the HAL calls that populates cal_type 10/14/24 — and intercept those `AUDIO_SET_CALIBRATION` ioctls byte-exact (cal_type + arg struct + same-process dma-buf), identical V2630 method. Add the captured **cal_type 10/14/24** records to the replay manifest (set before stream open; the kernel sends them lazily before `adm_open`/`afe_port_start`). Then re-run V2639 native replay; expect `adm_open`/`afe`/`asm` to clear, or to surface the next dependency. Alternative source: the V2461/V2466 real-HAL `/dev/msm_audio_cal` ptrace traces (116 ioctls) may already contain the 10/14/24 SETs — re-parse them for cal_type before designing a fresh Android-good capture.

Sources: `msm_audio_calibration.h` (coral-kernel sm8150 headers), `dsp/q6adm.c`, `dsp/q6afe.c`, `dsp/q6core.c` (`kernel/msm-extra`, android-10).

### CORRECTION 2026-06-18 (supersedes the per-subsystem 10/14/24 conclusion just above)
The "missing per-subsystem 10/14/24" framing was the right START but is now corrected by device evidence. **V2716 reparse of the real-HAL `/dev/msm_audio_cal` ptrace traces (V2461/V2466) proves the stock HAL SETs ONLY cal_type `20` (AFE_FB_SPKR_PROT) and `39` (CORE_CUSTOM_TOPOLOGIES) — it NEVER issues per-subsystem cal_type 10/14/24 SETs.** Therefore ADM `0x10004000` / ASM `0x10005000` / AFE `0x1001025d` register via the **CORE path** (cal_type 39 → `q6core_send_custom_topologies` → `AVCS_CMD_REGISTER_TOPOLOGIES`), NOT per-subsystem `*_CMD_ADD_TOPOLOGIES`.
- The `send_asm_custom_topology ADSP_EBADPARAM` seen in V2648/V2708 is **SELF-INFLICTED**: the replay SET stale cal 10/14 (which the real HAL never sets), making the kernel's per-subsystem senders push a malformed `*_CMD_ADD_TOPOLOGIES`. The cal 10/14 GET `-12`/stale results are expected dead data, not a payload to recover.
- The cal_39 CORE payload is **already correct and already replayed**: operator byte-check shows the V2669 byte-exact SET dump == the V2547 GET blob (both 4916 B, SHA `7c5d45ef…`) and both contain `0x10004000`+`0x10005000`+`0x1001025d`. So GET-vs-SET is a no-op; the CORE payload is not the problem.
- **Native-replay dmesg (V2639) confirms the gating error:** `q6asm cmd 0x10dbe (ASM_CMD_ADD_CUSTOM_TOPOLOGIES) error 0x2` → `send_asm_custom_topology ADSP_EBADPARAM` → `msm_pcm_open: Could not allocate memory` → `failed to start FE -12`. This is SELF-INFLICTED by the stale cal 14 SET.
- **Correct replay manifest:** per-device `{9,11,12,13,15,16,21,23}` + cal_39 (existing correct CORE payload) + cal_20, with **NO** 10/14/24 (so the per-subsystem `*_custom_topology` senders skip → the `0x10dbe`/pcm_open `-12` cascade clears). Then read dmesg: pcm_open proceeds (CORE covered topologies → go to PCM write) | a "topology not found" error (CORE registration trigger not firing under native init — RE q6core) | the `afe_get_sp_rx_tmax_xmax … -110` / `wsa881x_get_temp out of range` SP-feedback lines surface (WSA881x speaker-protection is a later gate; these are currently downstream of the failed open).

### CORRECTION 2026-06-18 (b) — redirect CONFIRMED; new frontier = CORE cal_39 registration not taking
V2722 ran the corrected replay (dropped 10/14/24): the self-inflicted `send_asm_custom_topology 0x10dbe ADSP_EBADPARAM` is **GONE**, the replay reached the real prepare path, and the new blocker is `adm_open port 0x4000 topo_id 0x10004000 → ADSP_EFAILED` = **ADM custom topology 0x10004000 not registered in the DSP**. So the CORE cal_39 registration is not making the topologies available, even though cal_39 is SET with the correct payload.

**q6core RE (`dsp/q6core.c`, CAF msm-extra) — `q6core_send_custom_topologies()` is a set-cal callback fired when CUST_TOP_CAL (cal_39) is SET.** It (1) maps the cal block's **physical address** to the ADSP via `q6core_map_memory_regions(&cal_block->cal_data.paddr, ADSP_MEMORY_MAP_SHMEM8_4K_POOL, …)` = `AVCS_CMD_SHARED_MEM_MAP_REGIONS`, then (2) sends `AVCS_CMD_REGISTER_TOPOLOGIES` with `payload_addr_lsw/msw = cal_block->cal_data.paddr` + `mem_map_handle`. **It therefore requires cal_39 to be backed by a real, ADSP-mappable physical address (real ION `AUDIO_ALLOCATE_CALIBRATION`, NOT a fake/short alloc).**

**Diagnostic for the V2724 `post_set_dmesg` (immediately after the cal_39 SET, before PCM prepare) — grep for these exact q6core pr_err strings to classify why 0x10004000 isn't registered:**
- `q6core_map_memory_regions failed` → cal_39 block has no valid ADSP-mappable paddr (replay alloc issue — prime suspect; ensure cal_39 uses real ION allocate, not the capture-side fake-allocate).
- `wait_event timeout for Register topologies` / `ADSP is not ready!` → q6core APR/SHARED_MEM channel not up under native init (ADSP bring-up gap).
- `Register topologies failed <n>` → DSP rejected the topology blob (payload/format).
- `cal block is NULL!` / `cal size … not sending` → the cal_39 SET didn't land in q6core's cal block (cal-framework routing / size 0).
- **(nothing q6core at all)** → the cal_39 SET never reached q6core's set-cal callback; check that the replay SETs cal_type 39 through the same `/dev/msm_audio_cal` path the kernel routes to `CUST_TOP_CAL`.

Prime hypothesis (REVISED 2026-06-18 — the "no paddr" guess is FALSIFIED): operator read the corrected-replay helper stderr (`v2639-acdb-setcal-replay-20260618-214430`) and **cal_39 already gets a real ION ALLOCATE** — `AUDIO_ALLOCATE_CALIBRATION ok cal_type=39 mem_handle=4` + `ALLOCATE_OK size=4916` + `SET ok cal_size=4916 mem_handle=4 has_payload=1`. So `cal_block->cal_data.paddr` IS valid; do NOT "fix" the allocation, it's already correct. The full corrected sequence is `{39,20,20,13,9,11,12,15,23,16,21}` (no 10/14/24), every SET `rc=0`, `REPLAY_DONE rc=0`. Therefore the unresolved gate is purely **whether q6core_send_custom_topologies registered the topology with the DSP**, and the only remaining candidates are: `ADSP is not ready!` (q6core AVCS handshake not complete under native init), `Register topologies failed <n>` (DSP rejected the blob), or the callback never fired. **This is unobservable until the dmesg capture is switched from `tail` to the keyword grep (see next section) — that is the blocking next step, not another allocation change.**

### INSTRUMENTATION BLOCKER 2026-06-18 — the dmesg capture is truncating the q6core evidence (fix before the next replay)
Operator inspected the V2724 `post_set_dmesg` from the corrected replay run `v2639-acdb-setcal-replay-20260618-214430`: it contains **zero** `q6core` / `REGISTER_TOPOLOGIES` / `map_memory_regions` lines — only unrelated `core_get_license_status` + EXT4/tsens/`wsa881x_get_temp` noise. Reason: the runner captures `dmesg | tail -n 260` (V2639 `DMESG_TAIL_LINE_COUNT=260`, both the post-set and playback-failure steps), and the q6core registration fires at the **cal_39 SET time** (mid-sequence), so by the time the post-set step runs the q6core lines have scrolled **out of the 260-line tail window**. The kernel ring buffer holds far more than 260 lines, so the data is there — the capture is just looking at the wrong slice.
- **Fix (do this before the next live replay):** change the post-set and playback-failure dmesg steps from `dmesg | tail -n 260` to a **keyword grep over the full ring buffer**, e.g. `dmesg | grep -iE 'q6core|register_topolog|map_memory|avcs|adsp.*ready|cust_top|topolog|cal_block|adm_open|q6asm|q6afe|send_.*cal|EBADPARAM|EFAILED|ENEEDMORE|pcm_open' | tail -n 200`. Run it through serial `cmdv1x` (bounded), same as the V2392 tail step.
- This will definitively classify the CORE-registration outcome (the `q6core_*` pr_err checklist above) instead of leaving it ambiguous. Until the capture is fixed, "no q6core line in post_set_dmesg" is an artifact of the tail window, **not** evidence that registration didn't fire.

### OPERATOR RE 2026-06-18 (c) — `app_type_cfg[]` is empty → `adm_open: bit_width:0`; the replay writes the WRONG app-type control (cheap fix, no new capture)
The loop's V2727 re-read of the V2726 post-failure dmesg surfaced a line the V2726 report omitted, and it changes the priority order ahead of the q6core CORE-registration RE:
```
msm_pcm_routing_get_app_type_idx: App type not available, fallback to default
adm_open: … bit_width:0 app_type:0x11135 acdb_id:15
adm_open: DSP returned error[ADSP_EFAILED]
```
- **Two different kernel app-type tables, two different controls.** Operator read `msm-pcm-routing-v2.c`: `msm_pcm_routing_get_app_type_idx(app_type)` iterates the **global** `app_type_cfg[MAX_APP_TYPES]` array and matches `.app_type`; on miss it prints `App type not available, fallback to default` and **returns idx 0**. That array is populated by the global **`App Type Config`** mixer control (numid **3122**), via `msm_routing_put_app_type_cfg_control`. This is a **different array** from `fe_dai_app_type_cfg[]`, which is what the per-stream **`Audio Stream 0 App Type Cfg`** control (numid **3345**) populates. `adm_open` then consumes `app_type_cfg[idx].bit_width` and `.sample_rate` (confirmed: the SM8150 routing source uses `app_type_cfg[app_type_idx].bit_width` inside the `adm_open()` call site).
- **The V2638/V2639 replay sets only numid 3345** (`set_observed_app_type=True` → `Audio Stream 0 App Type Cfg 69941 15 48000 2`), which fills `fe_dai_app_type_cfg[]`. It **never writes numid 3122**, so the global `app_type_cfg[]` stays empty → lookup of `0x11135` fails → fallback to idx 0 → `app_type_cfg[0].bit_width = 0`, `.sample_rate = 0`. **That is exactly the `bit_width:0` in the dmesg**, and feeding bit_width=0 / wrong sample-rate into adm_open + the AFE/ASM cal sends is a clean explanation for `EFAILED` / `EBADPARAM` / `ENEEDMORE` together.
- **Why we never saw Android's value:** `App Type Config` (3122) is **write-only/transient** — it reads back all-zero even in the Android-good ACTIVE snapshot (operator-verified: `v2397-android-acdb-measurement-…/device-artifacts/{baseline,active,post}-tinymix-all-values.txt` all show `3122 … 0 0 0 …`). The HAL writes it at `start_output_stream` and the kernel consumes it immediately into `app_type_cfg[]`; the get callback returns 0. So a tinymix snapshot can never reveal it — it has to be reconstructed from the put format + the logcat app-type tuple.
- **NEXT UNIT (cheapest discriminator, BEFORE the V2728/V2729 vi-feedback byte capture — needs no new capture, just one mixer write):** in the replay runner, before route apply / SET replay / pcm_prepare, write numid 3122 `App Type Config` via serial `cmdv1x`. QC techpack put layout = `[num_app_types, (app_type, sample_rate, bit_width) × num_app_types]`; speaker entry → **`1 69941 48000 16`**. Re-probe and read dmesg:
  - **(a)** `adm_open: bit_width:` flips `0→16` AND `App type not available` is gone AND adm_open proceeds → app_type table was the gate; advance to PCM write.
  - **(b)** bit_width now 16 but adm_open still `EFAILED` on topo `0x10004000` → the remaining gate is the q6core CORE registration (use the grep-dmesg fix in the section above to read it).
  - **(c)** AFE/ASM clear but ADM alone remains → narrow to the ADM COPP custom topology.
- **Reframes the vi-feedback direction (V2727–V2729):** the HAL feeds app-type cfg for BOTH speaker (`acdb 15 / app 69941`) and vi-feedback (`acdb 102 / app 69938`) through this SAME `App Type Config` control plus `/dev/msm_audio_cal` SET. So the loop's vi-feedback instinct is partly right, but the FIRST, FREE fix is the `app_type_cfg[]` table write — not capturing vi-feedback bytes. If AFE still `EBADPARAM` after the speaker entry, extend to `num=2 … 69938 8000 16` before pursuing a vi-feedback `cal_type 17` capture.
- **Confidence/caveat:** the put field order (`app_type, sample_rate, bit_width`, num-prefixed, 3 ints/entry) is from QC techpack source memory — `msm-pcm-routing-v2.c` is too large for the operator's web fetcher to return the put callback this session, and the file is not in the Samsung opensource drop locally. The **`bit_width 0→16` dmesg flip is the unambiguous on-device proof** the layout is right; if the flip does not happen, try alternate orderings (`app_type, bit_width, sample_rate`) before abandoning the lead.
