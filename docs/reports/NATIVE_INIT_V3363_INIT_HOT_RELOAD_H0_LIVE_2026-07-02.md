# Native Init V3363 Init Hot-Reload H0 Live (mechanism proven)

- Cycle: `V3363` (H0 live)
- Decision: `v3363-init-hot-reload-h0-mechanism-proven`
- Scope: first live proof that native-init can replace PID1 in place via `execve()` without a reboot.
- Device action: TWRP flash V3363, stage its own init ELF, `reload`, then rollback to v2321.
- Final device state: resident on v2321 `0.9.285`, `selftest fail=0` (clean checkpoint).

## Motivation

A research flash cycle is `flash + rollback` (~2 flashes). A reboot decomposition (measured on
v2321) showed `~17s` bootloader+kernel (immovable, stock kernel) and `~14s` native-init startup,
with the serial device re-enumerating on the host. Most research iterations change only the
native-init binary (audio/wifi/gpu/self-dd commands). If PID1 can be replaced in place without a
reboot, those iterations skip the entire reboot + USB re-enumeration.

## Feasibility (confirmed from source before the live test)

The USB gadget / configfs state lives in the kernel and native-init's setup is idempotent and never
unbinds the UDC, so a re-exec'd init does not tear down the host serial link:

- `setup_base_mounts` ignores repeated `mount()` EBUSY; `ensure_dir` is EEXIST-safe.
- `a90_usb_gadget_setup_acm`: `create_symlink_checked` returns 0 on EEXIST; `bind_default_udc`
  treats EBUSY as "already bound; continuing"; it never calls unbind.
- `a90_netservice` already logs "ncm already present; skip usb gadget reconfigure".

## Command

`reload INIT-RELOAD-EXECVE <staged-init-path> <expected-sha256>` (a90_init_reload.c), registered
`CMD_DANGEROUS | CMD_NO_DONE`. It validates an approved-staging path + ELF magic + caller-pinned
SHA-256, then `execve()`s PID1 in place. A failed execve leaves the old init running. Codex pre-live
safety review: GO, 0 MUST-FIX.

## Live sequence

1. TWRP-flashed V3363 (`0.11.124`, `394ab12f…`); resident `selftest pass=12 fail=0`.
2. On device, copied the running `/init` to `/mnt/sdext/a90/flash-staging/init_reload_test`
   (1,723,792 bytes, SHA `5a11c9ba…`) — a self-staged copy of the exact binary already running as
   PID1 (lowest-risk first re-exec).
3. `hide` (the DANGEROUS reload requires the auto-menu hidden), then
   `reload INIT-RELOAD-EXECVE /mnt/sdext/a90/flash-staging/init_reload_test 5a11c9ba…`.

## Result — hot-reload works

Reload transcript (bridge capture):

```text
A90RELOAD begin path=/mnt/sdext/a90/flash-staging/init_reload_test
A90RELOAD candidate=ok size=1723792 elf=1
A90RELOAD sha=5a11c9ba… expected_sha_match=1
A90RELOAD execve_now path=… host_note=serial-persists-no-reboot
```

There is no `execve=fail` line, so the `execve()` succeeded and did not return. Immediately after,
the NEW init re-ran `main()` on the same PID:

```text
# A90 Linux init 0.11.124 (v3363-init-hot-reload)
# USB ACM serial console ready.
# Boot display: splash 2s -> autohud 2s.
autohud: running
```

- The host serial device (`/dev/serial/by-id/usb-A90-LNX_…`) NEVER disappeared during the reload —
  no USB re-enumeration, i.e. no reboot.
- `version` returns `0.11.124`, `selftest fail=0` after the reload.
- Kernel `/proc/uptime` kept climbing across the reload (no kernel reboot). Note: native-init
  "uptime" is the kernel uptime; it does NOT reset on a re-exec (only a real reboot resets it — and
  the reboot-test value of 13.75s is consistent with kernel timekeeping starting ~18.75s into a
  cold boot, not with an init-local clock).

Conclusion: **PID1 replaced itself in place via execve, re-ran main(), and returned to a working
serial shell without a reboot or USB re-enumeration.** The hot-reload mechanism is proven.

## Non-fatal degradations (motivate the H1 fast-path)

The re-exec'd init re-ran the FULL boot path, which re-initializes subsystems that were already live:

- `autohud: SETCRTC failed: Permission denied` (repeated) — the HUD re-acquiring DRM/KMS master
  while the prior master state is still live.
- `# Netservice: start failed rc=-5 errno=5 (Input/output error)` — NCM re-setup failing because the
  NCM function was already configured.

The serial control path (ACM) is unaffected — `version`/`selftest`/`reload`/`recovery` all work,
which is what the research flash cycle needs. Both degradations come from re-initializing
already-running services and are the target of H1: an `A90_RELOADED`-gated fast path in `main()` that
skips the splash sleep, inventory scans, and re-init of already-live services (HUD, netservice), so a
reload is both clean and near-instant. The reload command already sets `A90_RELOADED=1` in the new
environment for that fast path.

## Boundaries

- H0 reloaded a self-staged copy of the exact running init (proves the mechanism at lowest risk). A
  reload of a genuinely-changed init build (to prove new code takes effect) is H1/H2.
- Inherent risk retained: a broken new init that crashes early makes PID1 exit and panics the kernel;
  recover via reboot/TWRP. Mitigation used: SHA-verified own-build input + the always-present TWRP
  recovery envelope. The device was rolled back to clean v2321 (`selftest fail=0`).
- Hot-reload is a research-cycle accelerator for init-only changes; it does not replace the checked
  flash helper for kernel/ramdisk/boot-image changes.
