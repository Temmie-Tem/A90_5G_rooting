# V2288 Kernel Security Recon: FastRPC ioctl-surface inventory

Date: 2026-06-12
Scope: recon-phase source inventory plus a live preflight check. No flash, no reboot, no exploit payload, no FastRPC payload, no `mmap(2)`, no DSP invoke, and no map/session ioctl was issued.
Baseline context: resident rollback checkpoint is `A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)`. V2284 confirmed the public CVE-2024-43047 `dma_handle_refs` fix invariant is absent in this 4.14 source tree. V2286/V2287 confirmed `adsprpc-smd` is registered as major `480`, materializable as `/dev/adsprpc-smd`, and openable `O_RDONLY`/`O_RDWR`.

## Plan review

No objection to the proposed Stage A plan with one guard:

> Stage-B is documented here only as a semantic command-family boundary. This report intentionally omits argument values, payload layout, fd values, timing, and runnable trigger construction.

The optional live invalid-ioctl dispatch check was considered, but not run. The resident image has no `toybox` or `busybox` `ioctl` applet, and deploying a new helper binary only for an optional invalid ioctl would widen the live scope beyond "existing-tool, single-shot" dispatch confirmation. Therefore no temporary devnode was created in V2288 and no ioctl reached the driver in this unit.

## Inputs

- Primary source root: `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source`
- FastRPC source files:
  - `drivers/char/adsprpc.c`
  - `drivers/char/adsprpc_shared.h`
  - `drivers/char/adsprpc_compat.c`
  - `drivers/char/adsprpc_compat.h`
- Live preflight only:
  - `version`: `A90 Linux init 0.9.268 (v2237-supplicant-terminate-poll)`
  - `status`: `selftest: pass=11 warn=1 fail=0`
  - `selftest verbose`: `fail=0`

## Native 64-bit ioctl inventory

The command values below are computed from `adsprpc_shared.h` on an LP64 host, matching the AArch64 userspace ABI sizes used by this driver.

| Command | nr | cmd | Arg struct | Handler | Class | Reason |
| --- | ---: | --- | --- | --- | --- | --- |
| `FASTRPC_IOCTL_INVOKE` | 1 | `0xc0105201` | `struct fastrpc_ioctl_invoke` | `fastrpc_internal_invoke` | (b) map-lifecycle | Enters `context_alloc`, `get_args`, DSP send/wait, `put_args`, and `context_free`; fd-backed args can create maps and the DSP-returned fdlist path can free maps. |
| `FASTRPC_IOCTL_MMAP` | 2 | `0xc0205202` | `struct fastrpc_ioctl_mmap` | `fastrpc_internal_mmap` | (b) map-lifecycle | Direct user map entry: requires initialized DSP process, calls `fastrpc_mmap_create`, maps on DSP, and frees map on error. |
| `FASTRPC_IOCTL_MUNMAP` | 3 | `0xc0105203` | `struct fastrpc_ioctl_munmap` | `fastrpc_internal_munmap` | (b) map-lifecycle | Removes a map with `fastrpc_mmap_remove`, unmaps on DSP, and frees the map. |
| `FASTRPC_IOCTL_INVOKE_FD` | 4 | `0xc0185204` | `struct fastrpc_ioctl_invoke_fd` | `fastrpc_internal_invoke` | (b) map-lifecycle | Same invoke pipeline, with fd list exposed directly to `get_args`. |
| `FASTRPC_IOCTL_SETMODE` | 5 | `0xc0045205` | `uint32_t` encoded in ioctl param | inline switch in `fastrpc_device_ioctl` | (a) local file-state control | Changes only `fl->mode`, `fl->profile`, or `fl->sessionid`; no map creation/free, no DSP invoke, no session allocation. Not needed for live recon. |
| `FASTRPC_IOCTL_INIT` | 6 | `0xc0285206` | `struct fastrpc_ioctl_init` | `fastrpc_init_process` | (c) session/init | Opens channel, attaches or creates DSP process state, can call `fastrpc_internal_invoke`, and CREATE/CREATE_STATIC paths can create/free maps. |
| `FASTRPC_IOCTL_INVOKE_ATTRS` | 7 | `0xc0205207` | `struct fastrpc_ioctl_invoke_attrs` | `fastrpc_internal_invoke` | (b) map-lifecycle | Same invoke pipeline, with fd attributes that affect map creation. |
| `FASTRPC_IOCTL_GETINFO` | 8 | `0xc0045208` | `uint32_t *` | `fastrpc_get_info` | (c) session/init | On first use, selects `fl->cid`, checks secure channel policy, and allocates a session context via `fastrpc_session_alloc_locked`; not a pure query. |
| `FASTRPC_IOCTL_GETPERF` | 9 | `0xc0185209` | `struct fastrpc_ioctl_perf` | inline perf copy path | (a) query | Copies perf key names/counts or current-thread perf data; no map lifecycle, no session creation, no DSP invoke. |
| `FASTRPC_IOCTL_INIT_ATTRS` | 10 | `0xc030520a` | `struct fastrpc_ioctl_init_attrs` | `fastrpc_init_process` | (c) session/init | Attribute-bearing variant of `INIT`; same channel/session/process creation and map-adjacent behavior. |
| `FASTRPC_IOCTL_INVOKE_CRC` | 11 | `0xc028520b` | `struct fastrpc_ioctl_invoke_crc` | `fastrpc_internal_invoke` | (b) map-lifecycle | Superset invoke form; reaches the same `get_args`/`put_args` map paths plus CRC output copy. |
| `FASTRPC_IOCTL_CONTROL` | 12 | `0xc00c520c` | `struct fastrpc_ioctl_control` | `fastrpc_internal_control` | (a) non-map control | `KALLOC` is query-like; `LATENCY` and `WAKELOCK` mutate PM/QoS or file wake state. No map lifecycle or session creation, but avoid live use unless a later unit explicitly needs it. |
| `FASTRPC_IOCTL_MUNMAP_FD` | 13 | `0xc018520d` | `struct fastrpc_ioctl_munmap_fd` | `fastrpc_internal_munmap_fd` | (b) map-lifecycle | Finds a persistent map by fd/va/len and clears `FASTRPC_ATTR_KEEP_MAP` before `fastrpc_mmap_free`. |
| `FASTRPC_IOCTL_MMAP_64` | 14 | `0xc020520e` | `struct fastrpc_ioctl_mmap_64` | converts to `fastrpc_internal_mmap` | (b) map-lifecycle | 64-bit address variant of `MMAP`; direct map creation/on-DSP map/free-on-error path. |
| `FASTRPC_IOCTL_MUNMAP_64` | 15 | `0xc010520f` | `struct fastrpc_ioctl_munmap_64` | converts to `fastrpc_internal_munmap` | (b) map-lifecycle | 64-bit address variant of `MUNMAP`; direct map remove/unmap/free path. |

Default unknown native ioctl behavior is `-ENOTTY` with `pr_info("bad ioctl: %d\n", ioctl_num)`, but V2288 did not issue that live because doing so required a new helper binary.

## Compat ioctl inventory

`adsprpc_compat.c` exposes the 32-bit ABI by converting compat structs and forwarding to the same native handlers:

| Compat command | nr | Native target | Class |
| --- | ---: | --- | --- |
| `COMPAT_FASTRPC_IOCTL_INVOKE` | 1 | `FASTRPC_IOCTL_INVOKE_CRC` | (b) map-lifecycle |
| `COMPAT_FASTRPC_IOCTL_MMAP` | 2 | `FASTRPC_IOCTL_MMAP` | (b) map-lifecycle |
| `COMPAT_FASTRPC_IOCTL_MUNMAP` | 3 | `FASTRPC_IOCTL_MUNMAP` | (b) map-lifecycle |
| `COMPAT_FASTRPC_IOCTL_INVOKE_FD` | 4 | `FASTRPC_IOCTL_INVOKE_CRC` | (b) map-lifecycle |
| `FASTRPC_IOCTL_SETMODE` | 5 | `FASTRPC_IOCTL_SETMODE` | (a) local file-state control |
| `COMPAT_FASTRPC_IOCTL_INIT` | 6 | `FASTRPC_IOCTL_INIT_ATTRS` | (c) session/init |
| `COMPAT_FASTRPC_IOCTL_INVOKE_ATTRS` | 7 | `FASTRPC_IOCTL_INVOKE_CRC` | (b) map-lifecycle |
| `FASTRPC_IOCTL_GETINFO` | 8 | `FASTRPC_IOCTL_GETINFO` | (c) session/init |
| `COMPAT_FASTRPC_IOCTL_GETPERF` | 9 | `FASTRPC_IOCTL_GETPERF` | (a) query |
| `COMPAT_FASTRPC_IOCTL_INIT_ATTRS` | 10 | `FASTRPC_IOCTL_INIT_ATTRS` | (c) session/init |
| `COMPAT_FASTRPC_IOCTL_INVOKE_CRC` | 11 | `FASTRPC_IOCTL_INVOKE_CRC` | (b) map-lifecycle |
| `COMPAT_FASTRPC_IOCTL_CONTROL` | 12 | `FASTRPC_IOCTL_CONTROL` | (a) non-map control |
| `COMPAT_FASTRPC_IOCTL_MMAP_64` | 14 | `FASTRPC_IOCTL_MMAP_64` | (b) map-lifecycle |
| `COMPAT_FASTRPC_IOCTL_MUNMAP_64` | 15 | `FASTRPC_IOCTL_MUNMAP_64` | (b) map-lifecycle |

Notable compat gap: no compat wrapper is defined for native `FASTRPC_IOCTL_MUNMAP_FD` nr `13` in this tree.

## CVE-adjacent map-lifecycle path

Source anchors:

- `fastrpc_mmap_find` increments map refs only when its `refs` argument is nonzero and returns `-ENOTTY` when no matching map exists.
- `fastrpc_mmap_create` first tries `fastrpc_mmap_find(... refs=1 ...)`, otherwise allocates a new `struct fastrpc_mmap`, initializes `refs=1`, sets fd/attr/va/len state, and adds it to the file/global map list.
- `fastrpc_mmap_free` decrements `map->refs`, unlinks on zero, unmaps or releases DMA-buf state, and frees the map object.
- `get_args` creates maps for fd-backed buffer args and handle args through `fastrpc_mmap_create`.
- `put_args` reads the DSP-returned `fdlist`; for each entry it calls `fastrpc_mmap_find(... refs=0 ...)` and then `fastrpc_mmap_free(mmap, 0)`.

This matches the V2284 public-fix-marker analysis: the local tree has the vulnerable-area shape around `get_args`, `put_args`, `fastrpc_mmap_find`, and `fastrpc_mmap_free`, while the public `dma_handle_refs` invariant is absent.

## Proposed-but-not-executed Stage-B boundary

This is not a runnable recipe. It records only the command families that would need explicit human approval before any future Stage-B attempt.

Semantic Stage-B family:

1. A session/process setup command family is required before normal map/invoke operations:
   - `FASTRPC_IOCTL_INIT`
   - `FASTRPC_IOCTL_INIT_ATTRS`
   - possibly `FASTRPC_IOCTL_GETINFO` first if a channel/session context is not already selected.
2. The public-fix-adjacent UAF class is closest to the invoke family, because the relevant fd-backed maps are created in `get_args` and the DSP-returned fdlist is consumed in `put_args`:
   - `FASTRPC_IOCTL_INVOKE`
   - `FASTRPC_IOCTL_INVOKE_FD`
   - `FASTRPC_IOCTL_INVOKE_ATTRS`
   - `FASTRPC_IOCTL_INVOKE_CRC`
3. Direct map lifecycle commands are adjacent and remain unsafe for Stage A:
   - `FASTRPC_IOCTL_MMAP`
   - `FASTRPC_IOCTL_MMAP_64`
   - `FASTRPC_IOCTL_MUNMAP`
   - `FASTRPC_IOCTL_MUNMAP_64`
   - `FASTRPC_IOCTL_MUNMAP_FD`

Stage-B avoid-list for all recon/autonomous units:

- All `INVOKE*` commands.
- All `MMAP*` and `MUNMAP*` commands.
- `INIT` and `INIT_ATTRS`.
- `GETINFO`, because it can allocate session state on first use.
- `CONTROL`, unless a later plan explicitly scopes a single non-map subrequest; it is not required for UAF reachability and has control side effects.
- Any `mmap(2)`, payload buffer, fd-backed DMA-buf setup, DSP invoke, loop, retry, or timing sequence.

Only an invalid unknown ioctl default-path check remains acceptable for Stage-A-like dispatch liveness, and even that should use an already-present tool or a separately approved helper. V2288 did not run it.

## Optional live dispatch check result

Live preflight was successful:

- Bridge reachable.
- Resident version matched v2237.
- `status` and `selftest verbose` reported `fail=0`.

Dispatch check was not run:

- `toybox` and `/cache/bin/toybox` did not expose an `ioctl` applet.
- `/cache/bin/busybox --list` did not expose an `ioctl` applet.
- Creating and transferring a new helper binary solely to issue one invalid ioctl would add a new live artifact and widen this Stage-A scope.

No temporary `/dev/adsprpc-smd` node was created in V2288, and no FastRPC ioctl was issued.

## Decision

V2288 classifies the FastRPC ioctl surface as follows:

- Safe for source inventory only: all commands.
- Safe for possible future dispatch-only liveness: unknown invalid ioctl only, with separate helper/tool approval if no existing ioctl applet is present.
- Unsafe / Stage-B-only: every `INVOKE*`, `MMAP*`, `MUNMAP*`, `INIT*`, and first-use `GETINFO` path.

FastRPC remains the top candidate, but this report stops at inventory and boundary definition. The next step is not autonomous triggering. Any Stage-B action must be a separate, explicitly approved, babysat single-shot session with rollback/recovery handling decided before the call.
