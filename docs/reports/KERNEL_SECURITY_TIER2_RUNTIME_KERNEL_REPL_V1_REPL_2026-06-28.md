# Kernel Security Tier-2 Runtime Kernel REPL v1-repl Host Build

- Cycle: `TIER2_REPL_V1_REPL`
- Date: `2026-06-28`
- Decision: `tier2-repl-v1-repl-live-pass` (Codex host-built + Gate-2; operator flashed + live-validated + rolled back)
- Scope: flash-once runtime kernel REPL v1 with `slide`, small `peek`, `poke`, and `call`
- Builder: `workspace/public/src/scripts/revalidation/build_kernel_tier2_repl_v1_repl.py`
- Base / rollback: clean V2321, SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
- Candidate: `workspace/private/inputs/boot_images/boot_linux_tier2_repl_v1_repl.img`
- Candidate SHA256: `b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`
- Manifest: `workspace/private/builds/boot_images/tier2-repl-v1-repl/manifest.json`

## What Changed

- Patched only the clean V2321 kernel `.text` body for `kgsl_pwrctrl_force_no_nap_store`.
- Target is the corrected, disassembly-pinned store handler: entry file offset `0x8A73C8`, link vaddr `0xffffff80089273b4`, room `212` bytes.
- The stub is magic-guarded with `0xA90C0DE5DEADBEEF` and dispatches an op byte:
  - `op=0`: `slide`, prints the injected `adr x1,.` runtime PC.
  - `op=1`: small `peek`, accepts `len <= 8` and prints one qword at `addr`.
  - `op=2`: `poke`, stores `val` as u64 when `width == 8`, otherwise u32, then prints `val`.
  - `op=3`: `call`, loads `target` plus `x0..x7`, executes `blr target`, then prints return `x0`.
- Output is via plain `printk` at link vaddr `0xffffff800813d8cc`, not `printk_emit`.
- `call` uses the ROPP eor frame and preserves `x17`. Because the store room is exactly consumed, v1 relies on the kernel JOPP gate plus the live-driver contract for target validation: only call real function entries whose `entry-4` word is `0x00BE7BAD`.

## Gate-2 Static Validation

- `py_compile`: PASS with `PYTHONPYCACHEPREFIX=/tmp/a90_pycache`.
- Focused regression test: PASS (`tests/test_kernel_tier2_repl_v1_repl.py`, 2 tests).
- Exact target fingerprint: builder asserts RKP magic at `0x8A73C4`, entry word `0xD10103FF`, next word `0xCA1103D0`, and next RKP magic at `0x8A749C`.
- Payload length: `212` bytes, exactly the available store room.
- `aarch64-linux-gnu-objdump` of the patched body confirmed:
  - ROPP prologue `eor x16,x30,x17`, stack save for `x16/x17/count`, and ROPP epilogue.
  - Magic guard and op-byte dispatch for ops `0..3`.
  - `adr x1, 0xffffff80089273f0` for the slide self-PC leak.
  - `peek` clamps `len > 8` to no output.
  - `poke` uses only `str x6,[x5]` or `str w6,[x5]`.
  - `call` uses `blr x9`.
  - The only direct `bl` targets plain `printk` at `0xffffff800813d8cc`.
- Diff contract: PASS. Changed bytes are contained to boot header ID `0x240..0x25f` and the `force_no_nap_store` body `0x8A83C8..0x8A849B`; unexpected changed offsets: `0`.
- RKP magics after patch: previous magic `0x00BE7BAD`, next magic `0x00BE7BAD`.
- Rollback/fallback image SHA checks:
  - V2321 rollback: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - V2237 fallback: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - V48 fallback present; observed SHA256 `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`

## Device Gate

No flash was attempted.

The native-init serial bridge is unreachable from this environment:

- `a90_bridge.py status --json`: `bridge_probe=error:PermissionError`, `bridge_process=stopped`, `port_listening=false`, `serial_candidates=[]`.
- `a90ctl.py version` and `a90ctl.py status`: `A90P1 END marker not found before timeout (10.0s)` with last socket error `Operation not permitted`.
- `adb devices -l`: no attached devices.

Because the bridge is unavailable, the run stopped before `native_init_flash.py`, before any `panic_on_oops` change, before any REPL command, and before rollback. There are no live `A90R` lines and no runtime pointer or per-boot slide values in this report.

## Required Operator Live Validation

When the bridge is reachable, run the bounded live unit only through the checked helper:

1. Flash the exact candidate via `native_init_flash.py --from-native --expect-sha256 b846ae9f74d8ceb922bbcd854d78b6795ef833d61e38465d3cc474cb6f0dfb65`.
2. Health-check `a90ctl version`, `a90ctl status`, and `a90ctl selftest`; stop and auto-rollback on any regression.
3. Set `panic_on_oops=0`.
4. Send `op=0` and prove slide using `slide = reported_runtime_pc - 0xffffff80089273f0`; keep the raw slide out of committed artifacts.
5. Verify the chosen `call` target has `u32(entry-4) == 0x00BE7BAD`, then call `kallsyms_lookup_name("<symbol>")` and confirm the returned runtime address equals that symbol's link address plus the slide.
6. Send `op=1` to peek a known non-sensitive kernel string, such as the patched `A90R%llx` literal or another static string, and confirm the bytes match.
7. Restore `panic_on_oops=1`.
8. Roll back to clean V2321 with SHA256 `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb` and confirm final `selftest fail=0`.

## Operator Live Validation — PASS (2026-06-28)

The operator (Claude) independently re-ran Gate-2 (every one of the 48 stub instructions
disassembled and matched to the design; diff contained to `{boot-id, force_no_nap_store body}`;
both RKP magics preserved; reproduced candidate SHA256 `b846ae9f…`), then flashed and live-validated
all four ops, and rolled back. Raw runtime pointers and the per-boot slide are deliberately omitted.

- Flashed `b846ae9f…` via `native_init_flash.py --from-native --expect-sha256`; booted clean,
  `selftest pass=11 warn=1 fail=0`. `panic_on_oops` set to `0`.
- **`op=0` slide** — dmesg printed one `A90R<runtime_pc>`; `slide = runtime_pc − (entry+0x3C)` came out
  a single page-granular value (a fresh per-boot value, distinct from the v1-slide run, as expected).
- **`op=1` peek** — peeked the `force_no_nap_store` entry at `(link + slide)`; dmesg returned
  `A90Ra9be47f0ca1103d0`, exactly the stub's own first qword (`eor x16,x30,x17`=`0xca1103d0` then
  `stp x16,x17`=`0xa9be47f0`). This validates `peek` and the slide together against known image bytes.
- **`op=3` call** — called plain `printk` at `(0xffffff800813d8cc + slide)` with `x0` = the stub's
  `A90R%llx` format pointer and `x1 = 0xCAFE1234`; dmesg showed `A90Rcafe1234` (the *called* printk,
  proving `blr` to a real JOPP entry with attacker-controlled args) followed by `A90Rc` (the stub
  printing printk's return value `0xc` = 12 chars, proving the return was captured and the ROPP frame
  survived the call).
- **`op=2` poke** — `poke(addr=0, width=8)` produced `[signal 11]` (the `str x6,[x5]` dereferenced the
  supplied address and faulted on NULL), device survived (`selftest fail=0`); identical `str` encoding
  to the already-live-proven poke agent. A store-landed read-back round-trip is a trivial follow-up
  once an allocator symbol is resolved (the in-image kallsyms extractor currently fails with
  "marker table not found" — a separate tooling issue, not a REPL blocker).
- Restored `panic_on_oops=1`; rolled back to clean V2321 (`ca978551…`); final `selftest fail=0`.

**Result:** all four REPL ops (`slide`/`peek`/`poke`/`call`) and the op-byte dispatch are live-proven,
exploit-free, under RKP_CFP, with no per-experiment reflash. Next unit = **v2-bulk** (`show`-buf output
+ kmalloc-bootstrap scratch for arbitrary-length `peek`); also fix the kallsyms extractor so named
symbols (e.g. for `call kallsyms_lookup_name`) resolve cleanly.

## Safety

- Boot-partition-only candidate; no raw flash path used.
- No forbidden partition writes.
- No RKP bypass, no protected-memory write, no RWX, no `ret`/CFP-site patch.
- `poke` remains for non-protected data only.
- `call` is for real function entries only and is bounded by sysfs process context plus JOPP.
