# v231 Plan: Linkerconfig Decision + Private Android Namespace Helper

## Summary

v231 follows v230 `android-exec-namespace-runtime-gap`. The goal is to close the
remaining `linkerconfig-need-unproven` blocker without starting Wi-Fi and without
running `cnss-daemon`.

v231 should add a private namespace helper and use Android linker `--list` mode
as the first executable dry-run. This verifies dependency resolution while
avoiding daemon entrypoint execution.

Current v230 evidence:

- fresh v229 preflight still returns `start-only-runtime-gap`.
- `/mnt/system/system/vendor` is a symlink to `/vendor`.
- vendor source is `needs-remount`: `sda29` is visible but not live-mounted into
  Android runtime paths.
- APEX runtime is available.
- remaining blocker is `linkerconfig-need-unproven`.

## Reference Notes

- Android linker namespaces isolate and link exported libraries between
  namespaces. Vendor process behavior can depend on namespace configuration, so
  v231 must not assume `/linkerconfig` absence is harmless.
- Android `linkerconfig` generates linker configuration from runtime state and
  APEX/library metadata. If `/linkerconfig` is absent in native init, v231 must
  either prove the target daemon links without it or record a narrower blocker.
- Android bionic linker supports direct invocation with `--list`, which behaves
  like `ldd` and exits before transferring control to the target executable.
  This is the preferred v231 dry-run because it loads/links dependencies without
  running `cnss-daemon` business logic.
- Linux mount namespaces are created with `unshare(CLONE_NEWNS)`. To prevent
  mount propagation back to PID1/global namespace, the helper must make the new
  namespace private or slave before mounting.

Reference URLs:

- https://source.android.google.cn/docs/core/architecture/vndk/linker-namespace?hl=en
- https://android.googlesource.com/platform/system/linkerconfig/
- https://android.googlesource.com/platform/bionic/+/refs/heads/main/linker/linker_main.cpp
- https://man7.org/linux/man-pages/man7/mount_namespaces.7.html

## Goal

Answer this question:

> Can native init create a private Android-like execution namespace where
> `/system/bin/linker64 --list /vendor/bin/cnss-daemon` resolves the daemon's
> dynamic dependencies, without executing the daemon and without global mounts?

Expected v231 decision labels:

- `android-linker-list-pass`: private namespace exists and `linker64 --list`
  resolves `cnss-daemon`.
- `android-linker-list-runtime-gap`: private namespace exists, but `--list`
  reports a missing library/path/linkerconfig/APEX component.
- `android-linkerconfig-documented-absent`: `/linkerconfig` is absent, but
  `linker64 --list` proves the daemon can still resolve dependencies through
  fallback/default namespace behavior.
- `android-linkerconfig-required`: `--list` or stderr proves
  `/linkerconfig`/namespace config is required before daemon start.
- `android-namespace-helper-blocked`: helper build/deploy/preflight/safety guard
  fails before private namespace work.
- `android-namespace-manual-review-required`: v230/v229 assumptions changed or
  postflight state drift is observed.

## Non-Goals

v231 must not perform:

- direct `cnss-daemon` execution;
- `cnss_diag` execution;
- Wi-Fi interface link-up, scan, connect, credential access, DHCP, routing, NAT,
  or DNS changes;
- ICNSS unbind/bind, `driver_override`, debugfs/sysfs recovery writes;
- global `/system`, `/vendor`, `/apex`, or `/linkerconfig` bind mounts;
- persistent writes under `/system`, `/vendor`, `/data`, `/efs`, firmware paths.

## Proposed Implementation

Add device-side static helper:

```text
stage3/linux_init/helpers/a90_android_execns_probe.c
```

Add build script:

```text
scripts/revalidation/build_android_execns_probe_helper.sh
```

Extend host tool:

```text
scripts/revalidation/wifi_android_exec_namespace_probe.py
```

The helper is a probe tool, not a service. It should exit after one run and leave
no live child process.

## Helper Contract

Recommended helper command:

```text
/cache/bin/a90_android_execns_probe \
  --system-root /mnt/system/system \
  --vendor-block /dev/block/sda29 \
  --vendor-fstype ext4 \
  --target /vendor/bin/cnss-daemon \
  --linker /system/bin/linker64 \
  --mode linker-list \
  --timeout-sec 10
```

Required helper behavior:

1. Validate all arguments against exact allowlists from the host wrapper.
2. Create a private mount namespace with `unshare(CLONE_NEWNS)`.
3. Immediately call `mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL)` or
   equivalent private/slave propagation.
4. Create a temp root under `/tmp/a90-v231-<pid>/root`.
5. Create all mountpoint directories before `chroot`: `<root>/system`,
   `<root>/vendor`, `<root>/proc`, `<root>/apex`, and optional `<root>/dev` or
   `<root>/sys` if explicitly needed.
6. Bind `/mnt/system/system` read-only to `<root>/system`.
7. Mount `sda29` read-only with `noload` to `<root>/vendor`.
   - `needs-remount` means the helper must mount vendor for every probe inside
     the private namespace.
   - The helper must track whether it mounted vendor and must unmount
     `<root>/vendor` on every normal/error/timeout exit path before removing temp
     directories.
   - If vendor is already live-mounted in a future run, it may use a read-only
     bind instead, but the source must be recorded in `helper-result.json`.
8. Preserve `/system/vendor -> /vendor` by relying on the symlink already present
   in the mounted system tree.
9. Mount minimal `/proc` at `<root>/proc` before `chroot`, not after `chroot`.
   The default should be `proc` with `nosuid,nodev,noexec` in the private
   namespace. This is required before the linker process starts because bionic may
   inspect `/proc/self/exe` or fall back to argv during executable discovery.
10. Bind `/sys` and `/dev` only if dry-run proves they are required; default
    should avoid broad writable device exposure.
11. Bind `/mnt/system/system/apex` to `<root>/apex` if present.
12. Do not synthesize `/linkerconfig` unless a later explicit plan proves a safe
    generated config is required and reviewed.
13. `chroot(<root>)`, then execute only:

```text
/system/bin/linker64 --list /vendor/bin/cnss-daemon
```

14. Capture stdout/stderr, exit code, duration, and missing-library messages.
15. Kill the child on timeout.
16. Unmount helper-created mounts in reverse order inside the private namespace.
17. Exit and let the private namespace tear down automatically.
18. Post-run, host wrapper verifies no global `/tmp/a90-v231-*` mount remains.

## Host Tool Changes

Extend `wifi_android_exec_namespace_probe.py`:

- `probe` should check `/cache/bin/a90_android_execns_probe` first.
- If helper is absent, return a safe blocker with deploy/build instructions.
- If helper is present, require:

```text
--allow-temp-namespace
--assume-yes
--allow-linker-list
```

- Before helper execution:
  - rerun v230-style inventory;
  - require fresh v229 `start-only-runtime-gap`;
  - require `/mnt/system/system/vendor -> /vendor`;
  - require vendor source `needs-remount` or `live-mounted`;
  - require APEX runtime available or documented absence.
- After helper execution:
  - rerun `version`, `netservice status`, `selftest verbose`;
  - compare `/proc/mounts`, `/proc/net/dev`, ICNSS uevent, rfkill, and Wi-Fi
    interface inventory against preflight;
  - write `linker-list.txt`, `helper-result.json`, and `postflight.json`.

## Linkerconfig Decision Rule

`/linkerconfig` is considered closed only if one of these is true:

1. `/linkerconfig/ld.config.txt` or equivalent generated config is visible inside
   the private namespace and `linker64 --list` passes; or
2. `/linkerconfig` is absent, but `linker64 --list /vendor/bin/cnss-daemon`
   passes and the report records `android-linkerconfig-documented-absent`.

If `--list` fails with namespace/config/permitted-path/library resolution
errors, v231 must return `android-linkerconfig-required` or
`android-linker-list-runtime-gap`. It must not continue to daemon start.

## Linker Output Classification

The host wrapper must classify `linker64 --list` output deterministically. The
helper should return raw `stdout`, raw `stderr`, numeric `exit_code`, and
`timed_out` without making policy decisions.

Classification rules:

| Condition | Decision | Notes |
| --- | --- | --- |
| timeout or helper killed child | `android-namespace-helper-blocked` | cleanup/postflight still required |
| helper setup/mount/chroot/exec failure before linker starts | `android-namespace-helper-blocked` | include failing syscall/path |
| `exit_code == 0` and output contains no `CANNOT LINK EXECUTABLE`, `not found`, `cannot locate`, `not accessible for the namespace`, or `linkerconfig` error | `android-linker-list-pass` or `android-linkerconfig-documented-absent` | choose documented-absent when `/linkerconfig` is absent in inventory |
| output contains `not accessible for the namespace`, `permitted.paths`, `namespace`, `ld.config`, or `linkerconfig` | `android-linkerconfig-required` | namespace policy/config blocker |
| output contains `library \"...\" not found`, `cannot locate`, `needed by`, or missing library names from v221 dependency graph | `android-linker-list-runtime-gap` | dependency/source mapping blocker |
| output contains `No such file or directory` for `/system/bin/linker64`, `/vendor/bin/cnss-daemon`, `/apex`, `/proc`, or mount paths | `android-linker-list-runtime-gap` | namespace materialization blocker |
| any unknown nonzero failure | `android-namespace-manual-review-required` | preserve full stdout/stderr for review |

If multiple patterns match, priority is:

```text
timeout/helper setup > linkerconfig/namespace > missing dependency/path > unknown nonzero > pass
```

The report must include `classification_patterns_matched` so later scans can
audit why a label was selected.

## Safety Guard

The host wrapper and helper must both enforce:

- no daemon direct exec path except as the argument to `linker64 --list`;
- no `cnss_diag`;
- no shell command string execution;
- no global bind mount;
- no network interface activation;
- no persistent Android partition writes;
- timeout and child process cleanup;
- private evidence output with no-follow file handling.

## Test Plan

Static build:

```bash
scripts/revalidation/build_android_execns_probe_helper.sh
file stage3/linux_init/helpers/a90_android_execns_probe
aarch64-linux-gnu-readelf -l stage3/linux_init/helpers/a90_android_execns_probe
```

Static host checks:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_android_exec_namespace_probe.py \
  scripts/revalidation/a90ctl.py

git diff --check
```

Device preflight:

```bash
python3 scripts/revalidation/wifi_android_exec_namespace_probe.py \
  --out-dir tmp/wifi/v231-android-linker-list-preflight \
  inventory
```

Helper deploy check:

```bash
python3 scripts/revalidation/helper_deploy.py push \
  stage3/linux_init/helpers/a90_android_execns_probe \
  a90_android_execns_probe \
  --role android-exec-namespace-probe
```

`helper_deploy.py` already exists and prints operator-safe deploy instructions.
v231 reuses it; the v231 implementation may add
`a90_android_execns_probe` to its known helper manifest list, but must not turn
`push` into an automatic copy path unless a separate deploy plan is reviewed.

Opt-in linker-list probe:

```bash
python3 scripts/revalidation/wifi_android_exec_namespace_probe.py \
  --out-dir tmp/wifi/v231-android-linker-list-probe \
  probe \
  --allow-temp-namespace \
  --allow-linker-list \
  --assume-yes
```

Postflight:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py netservice status
python3 scripts/revalidation/a90ctl.py selftest verbose
python3 scripts/revalidation/wifi_android_exec_namespace_probe.py \
  --out-dir tmp/wifi/v231-android-linker-list-postflight \
  inventory
```

## Acceptance

v231 is accepted if:

- private namespace helper builds as a static ARM64 binary;
- helper refuses unsafe arguments;
- helper performs only private namespace work;
- `linker64 --list` result is captured without daemon entrypoint execution;
- `/linkerconfig` status is converted from `unknown` to either documented absent,
  required, or a concrete runtime gap;
- postflight shows no global mount/network/ICNSS drift;
- helper result records vendor mount source, cleanup status, and no leftover
  global `/tmp/a90-v231-*` mountpoints;
- v229/v230 guardrails remain intact.

## Next Work After v231

If v231 returns `android-linker-list-pass` or
`android-linkerconfig-documented-absent`, v232 can consider a bounded
`cnss-daemon` start-only attempt inside the same private namespace. If v231
returns a runtime gap, v232 must close that exact dependency/config gap first.
