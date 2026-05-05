# F009. Diagnostics bundles are written with weak file permissions

## Metadata

| field | value |
|---|---|
| finding_id | `71fb260b576881919fe7a2c0cc011ff7` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/71fb260b576881919fe7a2c0cc011ff7 |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-05-04T10:31:54.402241Z` |
| committed_at | `2026-05-04 00:09:02 +0900` |
| commit_hash | `53a0bf0612e05c526898ee4c4ad953a30da639da` |
| relevant_paths | `stage3/linux_init/a90_diag.c | stage3/linux_init/a90_runtime.c | scripts/revalidation/diag_collect.py` |
| has_patch | `false` |

## CSV Description

The commit adds a diagnostics bundle path that includes verbose system state plus native log tails, then stores that bundle with mode 0644 in the runtime log directory or /cache. The runtime log directory is created 0755, so the bundle is not protected by directory permissions. The new host collector also runs `diag full` and writes the resulting device diagnostics to a host file with `Path.write_text()` and no explicit 0600 mode or chmod, so on common umask 022 systems the output is world-readable. In a shared lab host or if the SD/cache contents are later exposed to Android/MTP/another operator, lower-privileged users can read diagnostic content such as mount/partition information, service/network state, helper paths, and native-init log tails. These diagnostics should be treated as sensitive and written with 0600 permissions in a 0700 directory, with optional redaction of log tails.

## Codex Cloud Detail

Diagnostics bundles are written with weak file permissions
Link: https://chatgpt.com/codex/cloud/security/findings/71fb260b576881919fe7a2c0cc011ff7
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 53a0bf0
Author: shs02140@gmail.com
Created: 2026. 5. 4. 오후 7:31:54
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced: v102 adds device and host diagnostic bundle creation but does not enforce restrictive permissions for the sensitive output files.
The commit adds a diagnostics bundle path that includes verbose system state plus native log tails, then stores that bundle with mode 0644 in the runtime log directory or /cache. The runtime log directory is created 0755, so the bundle is not protected by directory permissions. The new host collector also runs `diag full` and writes the resulting device diagnostics to a host file with `Path.write_text()` and no explicit 0600 mode or chmod, so on common umask 022 systems the output is world-readable. In a shared lab host or if the SD/cache contents are later exposed to Android/MTP/another operator, lower-privileged users can read diagnostic content such as mount/partition information, service/network state, helper paths, and native-init log tails. These diagnostics should be treated as sensitive and written with 0600 permissions in a 0700 directory, with optional redaction of log tails.

# Validation
## Rubric
- [x] Identify whether the new diagnostics actually contain sensitive operational data such as mounts, partitions, service/network state, helper paths, or native-init log tails.
- [x] Confirm the device-side bundle is created with non-restrictive file permissions and that its parent directory is not restrictive enough to prevent traversal/read.
- [x] Dynamically exercise the actual a90_diag_write_bundle() code path and verify resulting mode and unprivileged readability.
- [x] Confirm the host-side collector writes diagnostic output without explicit 0600/chmod and reproduce world-readable output under common umask 022.
- [x] Check introduction context by confirming the parent commit lacks the new diagnostics files/code paths.
## Report
Validated the finding. Source review shows the device diagnostics include sensitive operational content: stage3/linux_init/a90_diag.c:386-395 emits /proc/mounts, /proc/partitions, and native-init log tails; stage3/linux_init/a90_diag.c:443-447 creates diagnostic bundles with open(..., 0644); stage3/linux_init/a90_diag.c:455-457 writes the full verbose report into that file. The runtime directory creation does not compensate: stage3/linux_init/a90_runtime.c:48-63 creates runtime dirs, including logs, with 0755. The host collector similarly writes captured diag output with default permissions: scripts/revalidation/diag_collect.py:148-163 runs diag full/diag bundle and writes with Path.write_text() after mkdir(parents=True) without chmod.

Dynamic device-side PoC: I compiled /workspace/validation_work/diag_bundle_perm_poc.c, which includes the real a90_diag.c and stubs unrelated services. It configured a 0755 runtime logs directory, inserted a fake native-init secret into the log tail, and called the real a90_diag_write_bundle(). Output: bundle=/tmp/a90-poc/logs/a90-diag-42424242.txt, mode=0644, parent_mode=0755, contains_token=yes, bundle_stat=644, nobody_can_read_token=yes. This demonstrates an unprivileged local user can read the sensitive diagnostic bundle.

Crash/ASan/valgrind/debugger attempts: no crash is expected for this permission flaw; the direct PoC exited normally while reproducing the bug. ASan build also exited 0 and reproduced mode=0644. valgrind was attempted but unavailable (rc=127, 'command not found: valgrind'). LLDB was available and used non-interactively: breakpoint set on a90_diag_write_bundle stopped at a90_diag.c:434 with backtrace main -> a90_diag_write_bundle, then continued and printed the vulnerable mode=0644 result.

Host-side reproduction: with common umask 022, running python3 scripts/revalidation/diag_collect.py --timeout 1 --out /workspace/validation_work/host_diag_default.txt produced host_mode=644. The file was readable by nobody: 'A90 HOST DIAG' and nobody_can_read_host_diag=yes. This confirms Path.write_text() inherits a world-readable mode in the common configuration. I also confirmed the commit introduced these files: HEAD^ lacks both stage3/linux_init/a90_diag.c and scripts/revalidation/diag_collect.py.

# Evidence
scripts/revalidation/diag_collect.py (L148 to 163)
  Note: The host collector captures `diag full` output and writes it with Path.write_text() without forcing 0600 permissions or a private output directory.
```
    rc, text = run_a90ctl(args, ["diag", "full"])
    append_section(lines, "device diag full", text + f"\nrc={rc}")

    if args.device_bundle:
        rc, text = run_a90ctl(args, ["diag", "bundle"], timeout=max(args.timeout, 30))
        append_section(lines, "device diag bundle", text + f"\nrc={rc}")

    optional_network = collect_optional_network(args)
    if optional_network:
        append_section(lines, "optional network", optional_network)

    output = args.out
    if not output.is_absolute():
        output = REPO_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n")
```

stage3/linux_init/a90_diag.c (L386 to 395)
  Note: The verbose diagnostics report includes /proc mount/partition data and native-init log tails, which are sensitive operational diagnostics.
```
static void diag_emit_proc_files(struct a90_diag_sink *sink, bool include_logs, size_t log_tail_bytes) {
    diag_emit(sink, "[mounts]\r\n");
    diag_emit_file_tail(sink, "/proc/mounts", 16384);
    diag_emit(sink, "[partitions]\r\n");
    diag_emit_file_tail(sink, "/proc/partitions", 16384);
    diag_emit(sink, "[logs]\r\n");
    diag_emit(sink, "path=%s ready=%s\r\n", a90_log_path(), diag_yesno(a90_log_ready()));
    if (include_logs && a90_log_ready()) {
        diag_emit_file_tail(sink, a90_log_path(), log_tail_bytes);
    }
```

stage3/linux_init/a90_diag.c (L443 to 457)
  Note: Device-side diagnostic bundles are created with mode 0644 and populated with the full verbose report, making them readable to other users/processes if the storage is exposed.
```
    snprintf(path, sizeof(path), "%s/a90-diag-%ld.txt", dir, monotonic_millis());
    fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (fd < 0 && strcmp(dir, CACHE_STORAGE_ROOT) != 0) {
        snprintf(path, sizeof(path), "%s/a90-diag-%ld.txt", CACHE_STORAGE_ROOT, monotonic_millis());
        fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    }
    if (fd < 0) {
        int saved_errno = errno;
        snprintf(out_path, out_size, "%s", path);
        return -saved_errno;
    }

    sink.fd = fd;
    sink.console = false;
    (void)diag_emit_report(&sink, true, true, A90_DIAG_BUNDLE_TAIL_BYTES);
```

stage3/linux_init/a90_runtime.c (L48 to 63)
  Note: Runtime directories, including the log directory used by the diagnostics bundle, are created 0755, so directory permissions do not compensate for the bundle's 0644 mode.
```
static int runtime_ensure_dirs(void) {
    const char *dirs[] = {
        runtime_state.root,
        runtime_state.bin,
        runtime_state.etc,
        runtime_state.logs,
        runtime_state.tmp,
        runtime_state.state,
        runtime_state.pkg,
        runtime_state.run,
    };
    size_t index;

    for (index = 0; index < sizeof(dirs) / sizeof(dirs[0]); ++index) {
        if (ensure_dir(dirs[index], 0755) < 0) {
            return -1;
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: low | Policy adjusted: low
## Rationale
Medium is appropriate. The issue is in active, in-scope runtime and host tooling, and static evidence shows sensitive diagnostic content is written with weak permissions. Earlier executable validation also reproduced 0644 device and host outputs readable by an unprivileged `nobody` user. The impact is confidentiality exposure of operational logs and configuration, which the project threat model treats as security-relevant. It should not be raised to high/critical because the attack path is local, requires diagnostic generation by an operator, and does not directly yield root command execution, privilege escalation, credential theft, or integrity compromise.
## Likelihood
medium - The vulnerable paths are reachable in normal diagnostics workflows and world-readable output is the default on common umask 022 systems. However, exploitation requires local/shared-host or exposed-device-storage read access and user/operator action to generate the diagnostics; there is no public network exposure.
## Impact
medium - The exposed files can reveal sensitive operational diagnostics: native-init log tails, mount and partition layout, helper paths, service/network state, and runtime configuration. This is meaningful confidentiality loss in a rooted-device research environment, but it does not directly provide code execution, privilege escalation, signing-key compromise, or partition writes.
## Assumptions
- The diagnostics output is used in the intended lab workflow for native-init troubleshooting.
- Host systems may use the common umask 022 unless the operator has explicitly hardened it.
- A lower-privileged local user, another lab operator, or later consumer of exposed device cache/SD contents may be able to read world-readable files.
- Native-init log tails and device topology data are sensitive in this project because they can reveal rooted-device configuration, helper paths, service state, network settings, and operator command/output history.
- An operator runs the host diagnostics collector or invokes the device-side `diag bundle` command.
- The generated host or device diagnostics file is created under default or otherwise permissive filesystem permissions.
- An attacker has local read access to the shared lab host, repository output directory, or later-exposed device cache/SD storage.
## Path
Operator -> diag_collect.py / native-init `diag bundle`
         -> verbose report with proc/service/network/log-tail data
         -> 0644 or default-umask output file
         -> lower-privileged local reader
         -> operational data disclosure
## Path evidence
- `stage3/linux_init/a90_diag.c:386-395` - Verbose diagnostics include `/proc/mounts`, `/proc/partitions`, and native-init log tails.
- `stage3/linux_init/a90_diag.c:398-417` - The full verbose report includes storage, runtime, helper, service, network, rshell, and proc/log sections.
- `stage3/linux_init/a90_diag.c:443-457` - Device-side bundle files are created with mode 0644 and then populated with the verbose report.
- `stage3/linux_init/a90_runtime.c:48-64` - Runtime directories, including logs, are created with 0755 permissions, so the parent directory does not compensate for the 0644 bundle.
- `stage3/linux_init/v102/80_shell_dispatch.inc.c:700-732` - The native-init shell exposes `diag full` and `diag bundle`, making the vulnerable bundle-writing path reachable through the active command dispatcher.
- `scripts/revalidation/diag_collect.py:122-128` - The host diagnostics collector defaults to localhost serial bridge settings and has an option to trigger the device-side bundle.
- `scripts/revalidation/diag_collect.py:148-163` - The host collector captures `diag full` and optional `diag bundle` output, creates parent directories without private mode, and writes the file using `Path.write_text()` without chmod.
## Narrative
The finding is real and in scope. Device diagnostics intentionally collect sensitive operational state, including mount/partition information and native-init log tails, and `diag bundle` writes that full report to a 0644 file. The runtime directories are created 0755, so directory permissions do not prevent traversal or reads. The host collector also captures `diag full` and optional `diag bundle` output and writes it with `Path.write_text()` without forcing 0600, so it commonly becomes 0644 under umask 022. The reachable attacker is not an internet user; exploitation requires operator diagnostic collection plus local/shared-host or exposed-device-storage read access. That supports medium severity for confidentiality exposure, not high/critical compromise.
## Controls
- Serial bridge host defaults to 127.0.0.1 rather than a public interface.
- Device-side bundle creation requires an explicit `diag bundle` command or `--device-bundle` option.
- The project threat model assumes a single trusted operator with physically controlled USB.
- No authentication or authorization protects lower-privileged local users from reading 0644 diagnostic files.
- No explicit 0600 file mode, 0700 diagnostics directory, or diagnostics redaction control is present for these outputs.
## Blindspots
- No live device was queried in this attack-path stage; conclusions are based on repository artifacts and provided validation evidence.
- Actual sensitivity of native-init log tails depends on operator commands and runtime environment.
- Real exploitability depends on host multi-user settings, umask, filesystem ACLs, and whether device cache/SD contents are later exposed to other users or systems.
- Repository artifacts do not show all deployment practices for storing, sharing, or cleaning diagnostics bundles.
