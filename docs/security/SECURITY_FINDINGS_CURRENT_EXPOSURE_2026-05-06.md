# Security Findings Current Exposure Map

Date: 2026-05-06

Latest source baseline:

- Native init version: `A90 Linux init 0.9.22 (v122)` from `stage3/linux_init/a90_config.h:4`
- Latest entry point: `stage3/linux_init/init_v122.c`
- Source finding set: `docs/security/findings/README.md`
- Relationship analysis: `docs/security/SECURITY_FINDINGS_RELATIONSHIP_2026-05-06.md`
- Fix queue: `docs/security/SECURITY_FIX_QUEUE_2026-05-06.md`


Post-remediation note:

- Batch 1 was mitigated in `A90 Linux init 0.9.23 (v123)` for F001, F003, F005, F010, F014, with F021/F030 documented as accepted lab-boundary controls and F023 partially closed.
- Batch 2 was mitigated in `A90 Linux init 0.9.24 (v124)` for F002, F004, F011, F012, and the current-code class behind F013.
- Batch 3 was mitigated in host tooling for F008, F015, F016, F017, F018, F019, F020, F022, and F031. No native image bump was needed for Batch 3 itself.
- Batch 4 was mitigated in `A90 Linux init 0.9.25 (v125)` for F009, F024, and F025 through owner-only diagnostics/logs, private emergency fallback logs, and opt-in HUD log tail.
- Batch 5 was mitigated in host/rootfs tooling for F006 and F007. No native image bump was needed.
- The matrix below remains the original v122 exposure map used to choose fix order; use `SECURITY_FIX_QUEUE_2026-05-06.md` and finding index statuses for current remediation state.

## Status Vocabulary

| status | meaning |
|---|---|
| `current-runtime` | Latest v122/shared native-init runtime still has the same sink, activation path, or equivalent pattern. |
| `current-host-tool` | Active host-side tooling still has the same trust-boundary issue. |
| `current-partial` | Exact original old-version path changed, but the same risk class still exists in current code. |
| `current-legacy-build` | Not latest runtime behavior, but retained historical build/rollback sources are still affected. |
| `legacy-archived` | Current active path is absent; risky code exists only under archived/legacy tooling. |
| `legacy-only` | Finding is confined to old version snapshots unless that snapshot remains a supported rollback target. |

## Summary Counts

| bucket | count | findings |
|---|---:|---|
| Current native-init runtime/control surface | 16 | F001, F002, F003, F005, F009, F010, F011, F012, F013, F021, F023, F024, F025, F027, F029, F030 |
| Current host tooling | 12 | F004, F007, F008, F014, F015, F016, F017, F018, F019, F020, F022, F031 |
| Current historical build support issue | 1 | F026 |
| Legacy/archive only | 2 | F006, F028 |

Interpretation:

- Most findings should remain open for planning. They are not all latest-runtime remote bugs, but they are still represented in current code or active tooling.
- Wi-Fi work should not proceed before Batch 1 root-control hardening because Wi-Fi increases reachability of the same control-plane classes.
- Some USB ACM findings describe intentional lab-control behavior. Those still need an explicit trust model, default bind policy, and documentation rather than being silently dismissed.

## Finding Matrix

| id | status | current exposure assessment | primary evidence | recommended batch |
|---|---|---|---|---|
| F001 | `current-runtime` | `rshell` is token-gated, but `rshell_start_service()` can start `a90_netservice_start()`, which starts unauthenticated `tcpctl`; the side-effect remains current. | `stage3/linux_init/v122/70_storage_android_net.inc.c:846`, `stage3/linux_init/v122/70_storage_android_net.inc.c:895`, `stage3/linux_init/a90_netservice.c:246`, `stage3/linux_init/helpers/a90_rshell.c:294` | Batch 1 |
| F002 | `current-runtime` | Helper manifest path can still become the preferred helper path even when sha256 is only recorded as unchecked; `cpustress` uses the preferred helper path. | `stage3/linux_init/a90_helper.c:202`, `stage3/linux_init/a90_helper.c:283`, `stage3/linux_init/a90_helper.c:323`, `stage3/linux_init/a90_helper.c:408`, `stage3/linux_init/v122/60_shell_basic_commands.inc.c:219` | Batch 2 |
| F003 | `current-runtime` | Persistent netservice flag still lives under `/cache`; boot path starts NCM/tcpctl when enabled. | `stage3/linux_init/a90_config.h:21`, `stage3/linux_init/a90_netservice.c:93`, `stage3/linux_init/a90_netservice.c:122`, `stage3/linux_init/v122/90_main.inc.c:236` | Batch 1 |
| F004 | `current-host-tool` | `tcpctl_host.py install` still uses a device-side netcat/dd transfer flow to write the runtime helper; this remains a host/deploy trust issue. | `scripts/revalidation/tcpctl_host.py:344`, `scripts/revalidation/tcpctl_host.py:352`, `scripts/revalidation/tcpctl_host.py:378`, `scripts/revalidation/tcpctl_host.py:386` | Batch 2 |
| F005 | `current-runtime` | `a90_tcpctl` still advertises and executes `run <absolute-path>` without authentication and listens on all interfaces. | `stage3/linux_init/a90_tcpctl.c:227`, `stage3/linux_init/a90_tcpctl.c:284`, `stage3/linux_init/a90_tcpctl.c:306`, `stage3/linux_init/a90_tcpctl.c:333`, `stage3/linux_init/a90_tcpctl.c:517` | Batch 1 |
| F006 | `legacy-archived` | Active `scripts/utils` and `scripts/magisk_module` paths are absent; matching default-root SSH automation exists under `scripts/archive/legacy`. | `scripts/archive/legacy/utils/create_rootfs.sh:309`, `scripts/archive/legacy/utils/create_rootfs.sh:314`, `scripts/archive/legacy/magisk_module/systemless_chroot/service.d/boot_chroot.sh:133` | Batch 5 |
| F007 | `current-host-tool` | `certify_bootimg.py` still calls `shutil.unpack_archive()` on user-provided archive input without member filtering. | `mkbootimg/gki/certify_bootimg.py:266`, `mkbootimg/gki/certify_bootimg.py:270` | Batch 5 |
| F008 | `current-host-tool` | Soak validator still calls relative `scripts/revalidation/a90ctl.py` and carries a stale default expected version. | `scripts/revalidation/native_soak_validate.py:50`, `scripts/revalidation/native_soak_validate.py:64` | Batch 3 |
| F009 | `current-runtime` | Diagnostics still emit runtime/helper/service paths, log tails, and create device bundles with `0644`; host collector writes report without explicit restrictive mode. | `stage3/linux_init/a90_diag.c:269`, `stage3/linux_init/a90_diag.c:299`, `stage3/linux_init/a90_diag.c:454`, `stage3/linux_init/a90_diag.c:543`, `scripts/revalidation/diag_collect.py:205` | Batch 4 |
| F010 | `current-runtime` | `tcpctl`, `adbd`, and `rshell` service descriptors are dangerous, but shell command `service` is registered with `CMD_NONE` and can start/enable those services. | `stage3/linux_init/a90_service.c:45`, `stage3/linux_init/a90_service.c:56`, `stage3/linux_init/a90_service.c:65`, `stage3/linux_init/v122/80_shell_dispatch.inc.c:576`, `stage3/linux_init/v122/80_shell_dispatch.inc.c:923` | Batch 1 |
| F011 | `current-runtime` | Runtime directory creation accepts `EEXIST` via shared `ensure_dir()`, and RW probes open predictable files with `O_CREAT|O_TRUNC` without no-follow semantics. | `stage3/linux_init/a90_runtime.c:56`, `stage3/linux_init/a90_runtime.c:82`, `stage3/linux_init/a90_runtime.c:88`, `stage3/linux_init/a90_util.c:22` | Batch 2 |
| F012 | `current-runtime` | `mountsd rw/init` can redirect log path to SD after mounting; log files use `0644` and no no-follow protection. | `stage3/linux_init/a90_storage.c:571`, `stage3/linux_init/a90_storage.c:627`, `stage3/linux_init/a90_storage.c:640`, `stage3/linux_init/a90_log.c:42`, `stage3/linux_init/a90_log.c:98` | Batch 2 |
| F013 | `current-partial` | Exact v79 bug is historical, but the same symlink/root-clobber class persists through current runtime and storage probes. | `stage3/linux_init/init_v79.c`, `stage3/linux_init/a90_runtime.c:88`, `stage3/linux_init/a90_storage.c:640` | Batch 2 |
| F014 | `current-host-tool` | Physical reconnect checker still logs cleanup failure in `finally` without converting the run to failure; reconnect soak records final stop failures but broader fail-closed policy is inconsistent. | `scripts/revalidation/physical_usb_reconnect_check.py:104`, `scripts/revalidation/physical_usb_reconnect_check.py:109`, `scripts/revalidation/netservice_reconnect_soak.py:473` | Batch 1 |
| F015 | `current-host-tool` | `a90ctl` still retries cmdv1 exchange until timeout after socket/serial-missing failures, so non-idempotent commands can be replayed. | `scripts/revalidation/a90ctl.py:144`, `scripts/revalidation/a90ctl.py:153`, `scripts/revalidation/a90ctl.py:166`, `scripts/revalidation/a90ctl.py:176` | Batch 3 |
| F016 | `current-host-tool` | `a90ctl` still searches raw output for the first `A90P1 END` marker, so command output can spoof framed results. | `scripts/revalidation/a90ctl.py:128`, `scripts/revalidation/a90ctl.py:130`, `scripts/revalidation/a90ctl.py:171` | Batch 3 |
| F017 | `current-host-tool` | Reconnect soak still selects host interface by device-reported MAC and then runs `sudo ip` against that interface. | `scripts/revalidation/netservice_reconnect_soak.py:191`, `scripts/revalidation/netservice_reconnect_soak.py:245`, `scripts/revalidation/netservice_reconnect_soak.py:260` | Batch 3 |
| F018 | `current-host-tool` | NCM host setup still parses `ncm.host_addr`, finds a matching host NIC by MAC, and runs `sudo ip addr/link` without explicit interface pinning. | `scripts/revalidation/ncm_host_setup.py:158`, `scripts/revalidation/ncm_host_setup.py:205`, `scripts/revalidation/ncm_host_setup.py:271`, `scripts/revalidation/ncm_host_setup.py:275` | Batch 3 |
| F019 | `current-host-tool` | Bridge defaults to auto by-id glob; it is localhost-bound, but auto re-enumeration still trusts a broad Samsung ACM glob rather than a pinned device identity. | `scripts/revalidation/serial_tcp_bridge.py:16`, `scripts/revalidation/serial_tcp_bridge.py:17`, `scripts/revalidation/serial_tcp_bridge.py:331` | Batch 3 |
| F020 | `current-host-tool` | Flash tool still embeds CLI path arguments directly into remote `adb shell` strings for sha256 and dd. | `scripts/revalidation/native_init_flash.py:165`, `scripts/revalidation/native_init_flash.py:168`, `scripts/revalidation/native_init_flash.py:276` | Batch 3 |
| F021 | `current-runtime` | USB ACM root shell remains the primary control channel after boot. This is intentional lab behavior, but it is still unauthenticated local root control and needs explicit trust-boundary documentation. | `stage3/linux_init/v122/90_main.inc.c:303`, `stage3/linux_init/v122/90_main.inc.c:305`, `scripts/revalidation/serial_tcp_bridge.py:333` | Batch 1 |
| F022 | `current-host-tool` | BusyBox static build script still writes readelf validation output to predictable `/tmp/a90_busybox_dynamic_check.txt` and then trusts that same path. | `scripts/revalidation/build_static_busybox.sh:152`, `scripts/revalidation/build_static_busybox.sh:153`, `scripts/revalidation/build_static_busybox.sh:154` | Batch 3 |
| F023 | `current-partial` | Old auto-menu bypass was improved, but current `service` command still provides a wrapper path around dangerous command flags. | `stage3/linux_init/a90_controller.c:65`, `stage3/linux_init/a90_controller.c:76`, `stage3/linux_init/v122/80_shell_dispatch.inc.c:923`, `stage3/linux_init/v122/80_shell_dispatch.inc.c:687` | Batch 1 |
| F024 | `current-runtime` | HUD log-tail is still an enabled display feature and reads native logs onto the screen. | `stage3/linux_init/a90_config.h:13`, `stage3/linux_init/a90_hud.c:449`, `stage3/linux_init/a90_hud.c:507`, `stage3/linux_init/a90_hud.c:522` | Batch 4 |
| F025 | `current-runtime` | Fallback log remains `/tmp/native-init.log` and log files are created `0644`. | `stage3/linux_init/a90_config.h:11`, `stage3/linux_init/a90_log.c:42`, `stage3/linux_init/a90_log.c:79`, `stage3/linux_init/a90_log.c:98` | Batch 4 |
| F026 | `current-legacy-build` | Latest shared headers no longer expose old HUD metrics types, while retained old version trees still reference them. This affects historical rebuild support, not latest v122 runtime. | `stage3/linux_init/a90_hud.h`, `stage3/linux_init/a90_metrics.h`, `stage3/linux_init/v89/60_shell_basic_commands.inc.c:123`, `stage3/linux_init/v89/40_menu_apps.inc.c:3350` | Batch 6 |
| F027 | `current-runtime` | v84 changelog action maps to a changelog app id, but latest autohud renderer does not handle changelog app ids and falls through to the default HUD/log-tail branch. | `stage3/linux_init/a90_menu.c:60`, `stage3/linux_init/a90_menu.c:269`, `stage3/linux_init/v122/40_menu_apps.inc.c:154`, `stage3/linux_init/v122/40_menu_apps.inc.c:165`, `stage3/linux_init/v122/40_menu_apps.inc.c:187` | Batch 6 |
| F028 | `legacy-only` | The stdin-cancel bug is visible in `init_v42.c`; current `a90_run` uses null stdin/process-group control for helper execution. | `stage3/linux_init/init_v42.c:3589`, `stage3/linux_init/init_v42.c:3597`, `stage3/linux_init/a90_run.c:42`, `stage3/linux_init/a90_run.c:63` | Batch 6 |
| F029 | `current-runtime` | Latest v122 still accepts any argument beginning with `event` as an event name and builds sysfs/dev paths from it. | `stage3/linux_init/v122/10_core_log_console.inc.c:141`, `stage3/linux_init/v122/10_core_log_console.inc.c:157`, `stage3/linux_init/v122/40_menu_apps.inc.c:522`, `stage3/linux_init/v122/40_menu_apps.inc.c:562` | Batch 6 |
| F030 | `current-runtime` | ACM shell and localhost TCP bridge remain unauthenticated control paths. Bridge now defaults to `127.0.0.1`, but this still needs explicit trusted-host policy. | `scripts/revalidation/serial_tcp_bridge.py:17`, `scripts/revalidation/serial_tcp_bridge.py:54`, `scripts/revalidation/serial_tcp_bridge.py:345`, `stage3/linux_init/v122/90_main.inc.c:305` | Batch 1 |
| F031 | `current-host-tool` | Baseline capture still interpolates device-discovered `by_name` into remote `su -c` shell commands. | `scripts/revalidation/capture_baseline.sh:90`, `scripts/revalidation/capture_baseline.sh:91`, `scripts/revalidation/capture_baseline.sh:106`, `scripts/revalidation/capture_baseline.sh:117` | Batch 3 |

## Current High-Risk Chains

### Chain A: NCM tcpctl unauthenticated root execution

```text
netservice flag or command
  -> /cache/bin/a90_usbnet ncm
  -> ifconfig ncm0 192.168.7.2
  -> /cache/bin/a90_tcpctl listen 2325
  -> tcpctl run <absolute-path>
  -> root execve
```

Current findings in chain: F003, F005, F010, F014, F021, F023, F030.

### Chain B: rshell starts token shell but also starts tcpctl

```text
rshell start / boot rshell enabled
  -> if NCM missing, a90_netservice_start()
  -> tcpctl comes up as side effect
  -> token-gated rshell is not the only TCP shell/control surface anymore
```

Current findings in chain: F001, F005.

### Chain C: runtime storage controls helper/log behavior

```text
SD/cache runtime or manifest writable
  -> helper preferred path or log path changed
  -> PID1 executes helper or writes logs as root
  -> persistence, clobber, or code execution depending on path
```

Current findings in chain: F002, F011, F012, F013.

### Chain D: host automation trusts device/untrusted local input

```text
device output, CWD, CLI path, MAC, archive member, or temp path
  -> host script runs sudo/adb/subprocess
  -> wrong host NIC, command injection, spoofed PASS, or host file overwrite
```

Current findings in chain: F004, F007, F008, F015, F016, F017, F018, F019, F020, F022, F031.

## Batch Impact

Immediate implementation order remains correct:

1. Batch 1 first: root-control surface hardening.
   - Main target: F005 `a90_tcpctl` authentication/bind policy.
   - Then remove accidental activation paths: F001/F003/F010/F014/F023.
   - Document trusted-lab semantics for F021/F030.
2. Batch 2 second: runtime/helper trust.
   - Without this, runtime helper or SD/cache content can reintroduce root execution after Batch 1.
3. Batch 3 third: host tooling trust.
   - These are not all device-runtime bugs, but they affect flashing, validation, and sudo host setup safety.
4. Batch 4 complete: logs and diagnostics.
5. Batch 5 complete: legacy high-impact tooling.
6. Batch 6 next: historical reproducibility and retained rollback support cleanup.

## Runtime Verification Still Needed

Static review confirms code paths exist. Before fixing each batch, collect one live v122 snapshot to avoid stale assumptions:

- `version`
- `status`
- `service list`
- `netservice status`
- `rshell audit`
- `helpers verbose`
- `runtime`
- `diag paths`
- `selftest verbose`

Do not use Wi-Fi bring-up or broader network exposure until Batch 1 has at least tcpctl auth/bind hardening.
