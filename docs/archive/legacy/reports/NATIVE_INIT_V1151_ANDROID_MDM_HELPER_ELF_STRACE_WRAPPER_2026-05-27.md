# Native Init V1151 Android `mdm_helper` ELF strace Wrapper Report

Date: `2026-05-27`

## Result

- Decision: `v1151-magisk-strace-module-elf-wrapper-install-ready`
- Pass: `true`
- Wrapper source: `stage3/linux_init/helpers/a90_mdm_helper_strace_wrapper.c`
- Build script: `scripts/revalidation/build_mdm_helper_strace_wrapper.sh`
- Scaffold updated: `scripts/revalidation/native_wifi_android_mdm_helper_strace_module_v1147.py`
- Handoff verifier updated: `scripts/revalidation/android_mdm_helper_strace_handoff_v1149.py`
- Rebuilt module manifest: `tmp/wifi/v1147-android-mdm-helper-strace-module/manifest.json`
- Dry-run manifest: `tmp/wifi/v1151-android-elf-wrapper-dryrun/manifest.json`

## Why

The repaired V1149 live retry proved the Magisk overlay was mounted over both
`/vendor/bin/mdm_helper` and `/system/vendor/bin/mdm_helper`, but the shell
wrapper never entered its body. Android dmesg showed `mdm_helper` faulting in
the kernel script loader path:

```text
Comm: mdm_helper
search_binary_handler
load_script
do_execveat_common
SyS_execve
```

That means the overlay path was correct, but using a shell script as the vendor
service executable is unsafe on this device. V1151 replaces the live wrapper
with a static AArch64 ELF executable so init executes an ELF directly instead
of hitting `load_script`.

## Wrapper Contract

The ELF wrapper:

- appends startup evidence to `/data/local/tmp/a90-wifi/mdm_helper.wrapper.log`;
- records pid, uid/gid, argv, and `/proc/self/attr/current`;
- refuses recursive originals such as `/vendor/bin/mdm_helper`;
- selects the original from the Magisk mirror or module fallback;
- executes static strace from `/data/adb/modules/a90_mdm_trace/bin/strace`;
- traces `openat,ioctl,read,write,execve` with `-f -tt -s 256`;
- writes the trace to `/data/local/tmp/a90-wifi/mdm_helper.strace.txt`.

The expected command shape is:

```text
strace -f -tt -s 256 -e trace=openat,ioctl,read,write,execve \
  -o /data/local/tmp/a90-wifi/mdm_helper.strace.txt \
  <original-mdm_helper> "$@"
```

## Build Artifact

Executed:

```bash
scripts/revalidation/build_mdm_helper_strace_wrapper.sh
```

Result:

```text
artifact: external_tools/userland/bin/a90_mdm_helper_strace_wrapper-aarch64-static
sha256: faa7d7f972cbc516f3eba4e32052724ce7a9f37368675aba390afa3cfbf0c26a
file: ELF 64-bit LSB executable, ARM aarch64, statically linked, stripped
dynamic: There is no dynamic section in this file.
```

## Validation

Executed:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_android_mdm_helper_strace_module_v1147.py \
  scripts/revalidation/android_mdm_helper_strace_handoff_v1149.py

python3 scripts/revalidation/native_wifi_android_mdm_helper_strace_module_v1147.py \
  --strace-binary external_tools/userland/bin/strace-aarch64-static-7.0 \
  --wrapper-binary external_tools/userland/bin/a90_mdm_helper_strace_wrapper-aarch64-static

python3 scripts/revalidation/android_mdm_helper_strace_handoff_v1149.py \
  --out-dir tmp/wifi/v1151-android-elf-wrapper-dryrun \
  --native-image stage3/boot_linux_v724.img \
  --native-expect-version 'A90 Linux init 0.9.68 (v724)' \
  --allow-android-boot-flash \
  --assume-yes \
  --i-understand-native-rollback \
  dry-run
```

Results:

```text
scaffold decision: v1151-magisk-strace-module-elf-wrapper-install-ready
scaffold pass: true
install_ready: true
dry-run decision: v1149-handoff-dryrun-ready
dry-run pass: true
module_ok: true
module_problems: []
```

The dry-run ZIP contains ELF payloads at:

```text
bin/strace
system/vendor/bin/mdm_helper
vendor/bin/mdm_helper
```

## Guardrails

- Host-only build and dry-run validation.
- No Android boot in V1151 validation.
- No Wi-Fi HAL start, scan/connect, DHCP/routes, credentials, or external ping.
- No native `/dev/subsys_esoc0` retry.
- No native eSoC ioctl.
- No boot partition write during V1151 validation.

## Next

Run the V1149 live handoff again with the V1151 module root. Expected
discriminator:

- if `mdm_helper.wrapper.log` appears, the ELF wrapper fixed the vendor init
  `load_script` crash;
- if `mdm_helper.strace.txt` appears and contains `/dev/esoc-0`, classify the
  Android `mdm_helper`/`ks` eSoC request contract for the next native repair;
- if wrapper starts but strace fails, classify SELinux or ptrace denial from
  wrapper log and dmesg.

## Live Retry Result

Executed V1149 live with the V1151 module:

```text
out_dir: tmp/wifi/v1151-android-elf-wrapper-live-20260527-175219
decision: v1149-android-strace-wrapper-not-started-rollback-complete
pass: False
rollback: complete, native v724 verified
```

Important evidence:

```text
/vendor/bin/mdm_helper: ELF wrapper, 729008 bytes, vendor_mdm_helper_exec
/system/vendor/bin/mdm_helper: ELF wrapper, 729008 bytes, vendor_mdm_helper_exec
init: starting service 'vendor.mdm_helper'
init: Service 'vendor.mdm_helper' (pid 1169) exited with status 127
init: Service 'vendor.mdm_helper' (pid 2063) exited with status 127
mdm_helper.wrapper.log: absent
mdm_helper.strace.txt: absent
```

This is different from the previous shell-wrapper run. The `load_script`
SIGSEGV path disappeared; the ELF overlay is accepted by init but exits with
status `127`. Because the wrapper returns `127` when `strace` is inaccessible
or `execv(strace)` fails, and because the wrapper log is also absent, the likely
blocker is Android SELinux/path access from `vendor_mdm_helper` to the current
module/log locations:

```text
strace path: /data/adb/modules/a90_mdm_trace/bin/strace
log path:    /data/local/tmp/a90-wifi/mdm_helper.wrapper.log
trace path:  /data/local/tmp/a90-wifi/mdm_helper.strace.txt
```

Android still brought the lower Wi-Fi chain up during this run:

```text
mss modem ONLINE
qrtr Modem QMI Readiness RX/TX
sysmon-qmi modem SSCTL connection
service-notifier 74/180
cnss-daemon running
wlan firmware ready markers
```

## V1152 Direction

Keep the Magisk overlay approach, but avoid `/data/adb/modules` as the runtime
exec path for the traced process:

- stage `strace` under an overlaid vendor executable path such as
  `/vendor/bin/a90_strace`;
- update the ELF wrapper to use that vendor path for `execv`;
- write wrapper/trace evidence to a path that `vendor_mdm_helper` can access,
  or write a minimal failure code through an already-allowed sink before
  starting full strace;
- update the handoff classifier to treat `vendor.mdm_helper exited with status
  127` as `elf-wrapper-exit127`, not as plain wrapper-not-started.
