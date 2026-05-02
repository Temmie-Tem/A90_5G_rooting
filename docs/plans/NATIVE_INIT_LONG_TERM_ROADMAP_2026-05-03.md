# Native Init Long-Term Roadmap: v96-v105

Date: `2026-05-03`

## Summary

- Latest verified: `A90 Linux init 0.8.29 (v98)`.
- Roadmap baseline before this cycle: `A90 Linux init 0.8.26 (v95)`.
- Goal: turn the verified native init foundation into a small, server-like embedded Linux runtime without losing recovery safety.
- Scope: this roadmap defines version-level objectives from v96 through v105.
- Rule: each version should keep one primary responsibility, one rollback path, and one concrete device validation checklist.

The v81-v95 cycle focused on splitting PID 1 into testable modules. The next cycle should focus on:

1. auditing the split modules before adding more layers,
2. promoting the SD card into a managed userland/runtime workspace,
3. adding deployable helper/userland packages,
4. introducing optional server access such as TCP shell or SSH,
5. inventorying Wi-Fi only after USB/NCM control remains stable,
6. proving long-running stability and recovery behavior.

## Operating Rules

- Keep `USB ACM serial` as the rescue/control channel even when NCM, TCP, SSH, or Wi-Fi is active.
- Do not write to critical Android identity/security partitions.
- Do not promote README/latest verified until a boot image is flashed and real-device validation passes.
- Keep boot selftest non-destructive and warn-only unless a later plan explicitly changes the policy.
- Prefer static helpers and SD workspace deployment over modifying Android system/vendor partitions.
- Treat reboot/recovery/poweroff/USB re-enumeration commands as raw-control operations where a framed END may not be returned.

## Version Roadmap

### v96. Structure Audit / Refactor Debt Cleanup

- Target: `A90 Linux init 0.8.27 (v96)` / `0.8.27 v96 STRUCTURE AUDIT`
- Goal: inspect the v95 module boundary before adding new userland layers.
- Primary work:
  - find duplicate helpers, stale globals, and direct path access that should use module APIs;
  - inspect `a90_usb_gadget` vs `a90_netservice` responsibility overlap;
  - inspect `a90_storage` vs SD workspace command/path policy overlap;
  - inspect `a90_run` adoption in command handlers for remaining fork/wait/kill duplication;
  - inspect `a90_shell`/`a90_controller` busy gate and hide/menu policy duplication;
  - produce a cleanup report and apply only low-risk mechanical fixes.
- Non-goals:
  - no SD runtime feature expansion;
  - no BusyBox/dropbear integration;
  - no Wi-Fi enablement.
- Acceptance:
  - v95 behavior preserved;
  - structure audit report documents keep/split/merge candidates;
  - `selftest`, `status`, `storage`, `netservice status`, `screenmenu`, `autohud 2` still pass.

### v97. SD Runtime Root

- Target: `A90 Linux init 0.8.28 (v97)` / `0.8.28 v97 SD RUNTIME ROOT`
- Goal: promote `/mnt/sdext/a90` from storage workspace into the primary native runtime root when healthy.
- Primary work:
  - define runtime directories: `bin`, `etc`, `logs`, `tmp`, `state`, `pkg`, `run`;
  - add boot-time directory preparation and read/write probe per directory class;
  - define `/cache` fallback behavior and visible warnings;
  - expose runtime status through `storage`, `bootstatus`, HUD warning, and `selftest`;
  - document SD missing/changed/corrupt rollback behavior.
- Non-goals:
  - no package manager;
  - no SSH/dropbear yet;
  - no Android data partition migration.
- Acceptance:
  - healthy SD becomes runtime root;
  - missing/unsafe SD falls back to `/cache` without blocking boot;
  - log path and helper path policy are deterministic.

### v98. Helper Deployment / Package Manifest

- Target: `A90 Linux init 0.8.29 (v98)` / `0.8.29 v98 HELPER DEPLOY`
- Goal: create a safe helper deployment model on SD runtime root.
- Primary work:
  - define a simple manifest format for static helpers;
  - add helper inventory command with path, size, mode, version/hash where available;
  - add controlled helper execution policy using `a90_run`;
  - add host-side deployment helper for copying/verifying SD userland files over NCM/TCP or serial fallback;
  - keep ramdisk helpers as recovery baseline and SD helpers as preferred optional layer.
- Non-goals:
  - no automatic download from internet;
  - no dynamic linker dependency;
  - no system/vendor partition writes.
- Acceptance:
  - helper inventory is visible from shell and logs;
  - bad/missing helper does not break boot;
  - rollback to ramdisk helper path is documented.

### v99. BusyBox Static Userland Evaluation

- Target: `A90 Linux init 0.8.30 (v99)` / `0.8.30 v99 BUSYBOX USERLAND`
- Goal: evaluate and optionally integrate a static BusyBox userland under SD runtime root.
- Primary work:
  - build or import static ARM64 BusyBox with a recorded config/hash;
  - validate core commands: `sh`, `ls`, `cat`, `mount`, `ip/ifconfig`, `ps`, `kill`, `dmesg` if available;
  - define how native shell launches BusyBox commands without replacing PID 1 shell;
  - compare BusyBox vs existing toybox for reliability and applet coverage.
- Non-goals:
  - no full distro bootstrap;
  - no replacing the native init shell;
  - no package manager.
- Acceptance:
  - BusyBox runs from SD runtime root or ramdisk fallback;
  - command failures return meaningful rc through `a90_run`;
  - native recovery functions remain independent from BusyBox.

### v100. TCP Shell / SSH Access Prototype

- Target: `A90 Linux init 0.9.0 (v100)` / `0.9.0 v100 REMOTE SHELL`
- Goal: add an optional remote shell path over verified USB NCM.
- Primary work:
  - choose between custom TCP shell first or dropbear SSH first based on risk;
  - keep serial bridge as rescue channel;
  - bind remote access only on `ncm0` by default;
  - add explicit enable/disable flag and status reporting;
  - document host connection steps and rollback.
- Non-goals:
  - no internet-facing service;
  - no Wi-Fi remote shell yet;
  - no authentication bypass for SSH if dropbear is used.
- Acceptance:
  - remote shell starts only when explicitly enabled;
  - NCM ping/tcpctl remains stable;
  - serial shell can stop the remote service.

### v101. Minimal Service Manager

- Target: `A90 Linux init 0.9.1 (v101)` / `0.9.1 v101 SERVICE MANAGER`
- Goal: turn ad-hoc service flags into a small service manager policy.
- Primary work:
  - define service metadata: name, enabled flag, pid, start/stop/reap/status, dependencies;
  - migrate `autohud`, `tcpctl`, optional remote shell, and ADB placeholder into a common view;
  - keep service start order explicit and boot-safe;
  - add `service list/status/start/stop/enable/disable` shell command if low-risk.
- Non-goals:
  - no full systemd/OpenRC clone;
  - no parallel boot dependency solver;
  - no daemon supervision loop that can wedge PID 1.
- Acceptance:
  - service status is consistent after crash/reap/stop;
  - enabled services do not block shell/HUD boot;
  - rollback flags are clear and documented.

### v102. Diagnostics / Log Bundle

- Target: `A90 Linux init 0.9.2 (v102)` / `0.9.2 v102 DIAGNOSTICS`
- Goal: make failures easy to collect and compare across versions.
- Primary work:
  - add `diag` command for version, bootstatus, selftest, storage, netservice, services, mounts, partitions, and recent logs;
  - add optional log bundle export to SD runtime root;
  - add host-side collector script over serial/NCM;
  - include artifact hashes and boot marker in collected output.
- Non-goals:
  - no large binary dump by default;
  - no partition image backup;
  - no private key or identity partition collection.
- Acceptance:
  - one command produces enough data to debug most boot/runtime regressions;
  - diagnostics are safe to run repeatedly;
  - collected output is documented and diffable.

### v103. Wi-Fi Read-Only Inventory

- Target: `A90 Linux init 0.9.3 (v103)` / `0.9.3 v103 WIFI INVENTORY`
- Goal: inventory Wi-Fi hardware, firmware, kernel modules, sysfs, Android/vendor dependencies without enabling Wi-Fi.
- Primary work:
  - collect read-only paths for WLAN device, rfkill, firmware, modules, properties, and vendor binaries;
  - compare Android/TWRP/native init visible state;
  - document required firmware/userspace components and risks;
  - add `wifiinv` or diagnostic subcommand if safe.
- Non-goals:
  - no Wi-Fi bring-up;
  - no firmware overwrite;
  - no Android vendor service mutation.
- Acceptance:
  - inventory report identifies concrete next bring-up prerequisites;
  - no writes beyond native log/diagnostic output;
  - USB NCM remains the primary control channel.

### v104. Wi-Fi Enablement Feasibility

- Target: `A90 Linux init 0.9.4 (v104)` / `0.9.4 v104 WIFI FEASIBILITY`
- Goal: run the smallest reversible Wi-Fi bring-up experiment if v103 shows a viable path.
- Primary work:
  - test rfkill/interface/firmware load path only if read-only inventory supports it;
  - keep NCM and serial active as rescue paths;
  - avoid persistent Android partition changes;
  - define hard stop conditions for missing firmware, kernel driver errors, or vendor daemon dependency.
- Non-goals:
  - no production Wi-Fi networking promise;
  - no WPA supplicant integration unless the device-side prerequisites are proven;
  - no disabling NCM.
- Acceptance:
  - either a minimal interface state is proven, or the blocker is documented precisely;
  - failed Wi-Fi experiments do not affect boot, storage, serial, or NCM recovery.

### v105. Long-Run Soak / Recovery Release Candidate

- Target: `A90 Linux init 0.9.5 (v105)` / `0.9.5 v105 SOAK RC`
- Goal: validate the v96-v104 stack as a stable recovery-friendly baseline.
- Primary work:
  - run long idle soak with HUD/log tail/menu hidden and visible states;
  - run NCM/tcpctl/remote shell soak if enabled;
  - run repeated reboot/recovery/TWRP/native init transitions;
  - test SD present/missing/fallback behavior;
  - verify cleanup retention and rollback image set;
  - update project docs around the new stable baseline.
- Non-goals:
  - no new feature unless required to fix a blocking stability defect;
  - no risky Wi-Fi or partition experiments during soak.
- Acceptance:
  - no orphan/zombie accumulation in normal operation;
  - serial and NCM recovery paths survive repeated reconnects;
  - diagnostics explain any warning state;
  - v105 can become the next known-good baseline after v48/v98.

## Delegation Guidance

When handing work to another agent or contributor:

- give only one version target at a time;
- include the exact baseline version and expected version string;
- specify forbidden writes and raw-control commands;
- require local build, static checks, flash validation, report update, and cleanup status;
- never ask for “improve everything” without a version boundary.

Suggested task packet format:

```text
Implement vNN from docs/plans/NATIVE_INIT_LONG_TERM_ROADMAP_2026-05-03.md.
Baseline: A90 Linux init X.Y.Z (vNN-1).
Target: A90 Linux init X.Y.Z (vNN).
Do not change: [explicit non-goals].
Validation required: [local build, flash, shell commands, report].
Commit only after verified.
```

## Current Next Action

v98 helper deployment is verified. The immediate next action is v99 planning:

1. inventory available static BusyBox candidates and their applets,
2. decide whether BusyBox runs from SD runtime root or ramdisk fallback,
3. define `busybox`/`userland` shell visibility and selftest checks,
4. keep dropbear/remote shell deferred until v100+.
