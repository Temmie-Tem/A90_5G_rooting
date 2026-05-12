# F049. Predictable /tmp root dd target permits symlink overwrite

## Metadata

| field | value |
|---|---|
| finding_id | `b3b8fb043bfc8191a9758e058f94988b` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/b3b8fb043bfc8191a9758e058f94988b |
| severity | `high` |
| status | `closed-duplicate-of-F045` |
| detected_at | `2026-05-10T00:41:36.720530Z` |
| committed_at | `2026-05-09 04:54:29 +0900` |
| commit_hash | `31aae994b5b630caf254b13471905ab668fc5dbd` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py` <br> `scripts/revalidation/a90harness/scheduler.py` <br> `stage3/linux_init/init_v73.c` |
| source_csv | `docs/security/scans/codex-security-findings-2026-05-11T19-48-19.047Z.csv` |

## CSV Description

The commit adds cpu-memory-profiles and makes it the default mixed-soak CPU workload. The module builds a device-side path from int(time.time()) and a fixed profile name under /tmp, then invokes PID1's root `run /cache/bin/toybox dd ... of=<path>`. On this native init, /tmp is mounted mode 1777. Because the code does not create a private directory, use an unpredictable name, check for symlinks, or use no-follow/exclusive creation semantics, any device-local process able to write /tmp can prepopulate likely timestamp/profile symlink names. When the operator runs the harness, root dd follows the symlink and writes 4-16 MiB of zeros to the target before the later hash check fails. Targets could include persistent helper binaries, native-init flags/logs, or block devices, causing integrity loss or device availability failure. Cleanup removes the symlink path and does not undo the overwrite.

## Local Initial Assessment

- Full detail matches the previously tracked `F045` pattern. Current code no longer writes directly to predictable `/tmp/<run>-<profile>-mem.bin`; it creates a per-profile temp directory with safe component/path checks before the memory file. Treat as duplicate/reopened unless a fresh scan targets the current code.

## Local Remediation

- No new patch required from this finding unless Codex Cloud still reproduces against current code. Keep linked to `F045` closure evidence.

## Closure Evidence

- Closed in Batch H3 as a duplicate of `F045`; see `docs/security/batches/SECURITY_FINDINGS_F047_F053_H3_REPORT_2026-05-12.md`.
- Current `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py` creates a safe per-profile temp directory under `/tmp` using `require_safe_component()` and `require_path_under()`, then places the memory file inside that directory instead of writing to the old predictable `/tmp/<run>-<profile>-mem.bin` pattern.
- Local verification on 2026-05-12 confirmed the old timestamp-based path pattern is absent and `python3 -m py_compile scripts/revalidation/a90harness/modules/cpu_memory_profiles.py` passes.

## Codex Cloud Detail

Predictable /tmp root dd target permits symlink overwrite
Link: https://chatgpt.com/codex/cloud/security/findings/b3b8fb043bfc8191a9758e058f94988b?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 31aae99
Author: shs02140@gmail.com
Created: 2026. 5. 10. 오전 9:41:36
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
Introduced: the new cpu-memory-profiles module performs unsafe root writes to predictable /tmp paths, and scheduler.py makes the new module part of the default mixed-soak workload set.
The commit adds cpu-memory-profiles and makes it the default mixed-soak CPU workload. The module builds a device-side path from int(time.time()) and a fixed profile name under /tmp, then invokes PID1's root `run /cache/bin/toybox dd ... of=<path>`. On this native init, /tmp is mounted mode 1777. Because the code does not create a private directory, use an unpredictable name, check for symlinks, or use no-follow/exclusive creation semantics, any device-local process able to write /tmp can prepopulate likely timestamp/profile symlink names. When the operator runs the harness, root dd follows the symlink and writes 4-16 MiB of zeros to the target before the later hash check fails. Targets could include persistent helper binaries, native-init flags/logs, or block devices, causing integrity loss or device availability failure. Cleanup removes the symlink path and does not undo the overwrite.

# Validation
## Rubric
- [x] Confirm the commit introduced cpu-memory-profiles and that its run identifier/path names are predictable from int(time.time()) plus fixed profile names.
- [x] Confirm the memory write is performed through root/device-side dd to /tmp/<run_id>-<profile>-mem.bin without private directory creation, O_NOFOLLOW, O_EXCL, or symlink validation.
- [x] Confirm cleanup only unlinks the chosen /tmp path and cannot restore data written through a symlink.
- [x] Confirm exposure conditions: /tmp is intended to be world-writable/sticky on the native init target and scheduler defaults include cpu-memory-profiles.
- [x] Dynamically demonstrate the overwrite path with a targeted PoC and debugger trace; attempt crash/valgrind/gdb where applicable and document constraints.
## Report
Validated the finding. Source review shows the newly added module is introduced in commit 31aae994 and constructs a predictable path from seconds-resolution time: scripts/revalidation/a90harness/modules/cpu_memory_profiles.py:77-78 and :107. It then invokes the device command vector ["run", "/cache/bin/toybox", "dd", "if=/dev/zero", f"of={path}", f"bs={spec.mem_size_bytes}", "count=1"] at cpu_memory_profiles.py:127-140 without O_NOFOLLOW, O_EXCL, a private directory, or symlink checks. The cleanup at cpu_memory_profiles.py:155-160 only runs rm -f on that path. The scheduler makes this module the first default mixed-soak workload at scripts/revalidation/a90harness/scheduler.py:88-94, and native init mounts /tmp as mode=1777 at stage3/linux_init/init_v73.c:7137-7140. I created a local PoC that imports the real CpuMemoryProfilesModule, precreates /tmp/<run_id>-low-mem.bin as a symlink to a sentinel file, and uses a local DeviceClient stand-in that preserves the same dd/sha256sum/rm semantics. Direct PoC output showed: target_before size=26, module_profile_ok=True write_ok=True hash_ok=True cleanup_ok=True, symlink_exists_after_cleanup=False, target_after size=4194304, and target_overwritten_with_zeros=True. Thus dd followed the symlink, overwrote the target with 4 MiB of zeros, and cleanup removed only the symlink. A non-interactive pdb run broke at cpu_memory_profiles.py:108 and printed the generated path '/tmp/v180-cpumem-1778373999-low-mem.bin' and write size 4194304 before continuing to the same overwrite result. Valgrind and gdb were attempted but are not installed in the container; this is a Python/data-integrity bug, not a native memory-corruption crash. The container's own /tmp is 0700, so the PoC precreated the symlink as root; the target device condition is supported by repository code showing /tmp mounted 1777. One nuance: for a regular-file target, the module's later hash check can pass because it hashes the zeroed symlink target before unlinking the symlink, which is at least as severe as the suspected failure-after-overwrite behavior.

# Evidence
scripts/revalidation/a90harness/modules/cpu_memory_profiles.py (L107 to 139)
  Note: The module writes to a predictable /tmp path by running root toybox dd with of=<path>; dd follows symlinks and there is no no-follow, exclusive create, or private-directory protection.
```
        path = f"/tmp/{self._run_id}-{spec.name}-mem.bin"
        expected_hash = zero_sha256(spec.mem_size_bytes)

        ok, text, record = self._run_cmd(ctx, spec.name, "status-before", ["status"], timeout=ctx.timeout)
        profile["commands"].append(record)
        profile["samples"].append({"label": "before", "ok": ok, "status": parse_status(text)})

        ok, _text, record = self._run_cmd(
            ctx,
            spec.name,
            "cpustress",
            ["cpustress", str(spec.stress_sec), str(spec.stress_workers)],
            timeout=max(ctx.timeout, spec.stress_sec + 30.0),
        )
        profile["commands"].append(record)

        ok_after, text_after, record = self._run_cmd(ctx, spec.name, "status-after", ["status"], timeout=ctx.timeout)
        profile["commands"].append(record)
        profile["samples"].append({"label": "after", "ok": ok_after, "status": parse_status(text_after)})

        write_ok, _text, record = self._run_cmd(
            ctx,
            spec.name,
            "mem-write",
            [
                "run",
                "/cache/bin/toybox",
                "dd",
                "if=/dev/zero",
                f"of={path}",
                f"bs={spec.mem_size_bytes}",
                "count=1",
            ],
```

scripts/revalidation/a90harness/modules/cpu_memory_profiles.py (L155 to 160)
  Note: Cleanup removes the path after the write/hash step, but if the path was a symlink the target has already been overwritten.
```
        cleanup_ok, _text, record = self._run_cmd(
            ctx,
            spec.name,
            "mem-cleanup",
            ["run", "/cache/bin/toybox", "rm", "-f", path],
            timeout=max(ctx.timeout, 20.0),
```

scripts/revalidation/a90harness/modules/cpu_memory_profiles.py (L77 to 78)
  Note: The run identifier is based only on the current timestamp, making device-side filenames predictable enough to precreate over a time window.
```
    def __init__(self) -> None:
        self._run_id = f"v180-cpumem-{int(time.time())}"
```

scripts/revalidation/a90harness/scheduler.py (L88 to 94)
  Note: The scheduler now selects cpu-memory-profiles as the preferred default workload, increasing exposure of the unsafe write path during normal mixed-soak runs.
```
def default_workloads(profile: str, modules: dict[str, type[TestModule]]) -> list[str]:
    preferred = ["cpu-memory-profiles", "ncm-tcp-preflight", "storage-io"]
    if "cpu-memory-profiles" not in modules:
        preferred[0] = "cpu-mem-thermal"
    if profile in {"idle", "observer-only"}:
        return []
    return [name for name in preferred if name in modules]
```

stage3/linux_init/init_v73.c (L7137 to 7140)
  Note: Native init mounts /tmp as mode 1777, so device-local unprivileged processes can create names and symlinks under /tmp.
```
    mount("proc", "/proc", "proc", 0, NULL);
    mount("sysfs", "/sys", "sysfs", 0, NULL);
    mount("devtmpfs", "/dev", "devtmpfs", 0, "mode=0755");
    mount("tmpfs", "/tmp", "tmpfs", 0, "mode=1777");
```

Proposed patch:
diff --git a/scripts/revalidation/a90harness/modules/cpu_memory_profiles.py b/scripts/revalidation/a90harness/modules/cpu_memory_profiles.py
index b425a846e5400f88fbe63e97a3bb8c3c0d0827d7..9118616a0bfb8c53c0a0cb0b0d1e8d834a0264d5 100644
--- a/scripts/revalidation/a90harness/modules/cpu_memory_profiles.py
+++ b/scripts/revalidation/a90harness/modules/cpu_memory_profiles.py
@@ -1,32 +1,33 @@
 """CPU/memory workload profile module for mixed-soak validation."""
 
 from __future__ import annotations
 
 import hashlib
 import json
 import re
+import secrets
 import time
 from dataclasses import asdict, dataclass
 from typing import Any
 
 from a90harness.module import ModuleContext, StepResult, TestModule
 
 
 @dataclass(frozen=True)
 class CpuMemoryProfile:
     name: str
     stress_sec: int
     stress_workers: int
     mem_size_bytes: int
     cooldown_sec: float
 
     def to_dict(self) -> dict[str, Any]:
         return asdict(self)
 
 
 SMOKE_PROFILES: tuple[CpuMemoryProfile, ...] = (
     CpuMemoryProfile("low", 1, 1, 4 * 1024 * 1024, 1.0),
     CpuMemoryProfile("cooldown", 1, 1, 4 * 1024 * 1024, 1.0),
 )
 
 QUICK_PROFILES: tuple[CpuMemoryProfile, ...] = (
@@ -53,51 +54,51 @@ def parse_status(text: str) -> dict[str, Any]:
     if match := re.search(r"uptime:\s*([0-9.]+)s\s+load=([0-9.]+)", text):
         parsed["uptime_sec"] = float(match.group(1))
         parsed["load_1m"] = float(match.group(2))
     if match := re.search(r"thermal:\s*cpu=([0-9.]+)C\s+([0-9]+)%\s+gpu=([0-9.]+)C\s+([0-9]+)%", text):
         parsed["cpu_temp_c"] = float(match.group(1))
         parsed["cpu_usage_percent"] = int(match.group(2))
         parsed["gpu_temp_c"] = float(match.group(3))
         parsed["gpu_usage_percent"] = int(match.group(4))
     if match := re.search(r"memory:\s*([0-9]+)/([0-9]+)MB used", text):
         parsed["mem_used_mb"] = int(match.group(1))
         parsed["mem_total_mb"] = int(match.group(2))
     if match := re.search(r"battery:\s*([0-9]+)%\\s+([^\\r\\n]+?)\\s+temp=([0-9.]+)C", text):
         parsed["battery_percent"] = int(match.group(1))
         parsed["battery_state"] = match.group(2).strip()
         parsed["battery_temp_c"] = float(match.group(3))
     return parsed
 
 
 class CpuMemoryProfilesModule(TestModule):
     name = "cpu-memory-profiles"
     description = "run low/medium/spike/cooldown CPU and memory workload profiles"
     cycle_label = "v180"
     read_only = False
 
     def __init__(self) -> None:
-        self._run_id = f"v180-cpumem-{int(time.time())}"
+        self._run_id = f"v180-cpumem-{int(time.time())}-{secrets.token_hex(8)}"
 
     def _profiles(self, profile: str) -> tuple[CpuMemoryProfile, ...]:
         return QUICK_PROFILES if profile == "quick" else SMOKE_PROFILES
 
     def _run_cmd(self,
                  ctx: ModuleContext,
                  profile: str,
                  label: str,
                  command: list[str],
                  *,
                  timeout: float | None = None) -> tuple[bool, str, dict[str, Any]]:
         record, text = ctx.client.run(
             f"{self.name}-{profile}-{label}",
             command,
             timeout=timeout,
             transcript=str(ctx.store.path(f"modules/{self.name}/{profile}/commands/{label}.txt")),
         )
         ctx.store.write_text(f"modules/{self.name}/{profile}/commands/{label}.txt", text)
         return record.ok, text, record.to_dict()
 
     def _run_profile(self, ctx: ModuleContext, spec: CpuMemoryProfile) -> dict[str, Any]:
         profile: dict[str, Any] = {
             "spec": spec.to_dict(),
             "commands": [],
             "samples": [],

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Severity remains high, but not critical. Static evidence and the prior executable PoC support the core claim: a predictable /tmp path is used for a root dd output file, /tmp is world-writable, and the default mixed-soak schedule runs this module. This creates a credible local privilege-boundary violation where a non-root device-local actor can cause root-mediated destruction of arbitrary root-writable targets. The impact can be severe for device integrity/availability, including corruption of helper binaries or block devices. However, the attack is constrained to a single lab device, requires local /tmp write capability and operator execution of the harness, provides only zero-overwrite rather than arbitrary content write/RCE, and is not exposed to the Internet by default; those preconditions keep it below critical.
## Likelihood
medium - The vulnerable module is reachable in normal mixed-soak operation and the filename is predictable, but exploitation is not remote or unauthenticated from the network; it requires a local device foothold able to create /tmp symlinks and a concurrent/later operator harness run.
## Impact
high - Successful exploitation causes a root process to overwrite attacker-chosen symlink targets with 4-16 MiB of zeros. Content is not attacker-controlled beyond zeros and size/profile choice, but corruption of /cache helpers, native-init state, logs, or block devices can cause high integrity and availability impact on the device.
## Assumptions
- The native-init target is operated as described by the repository threat model: a trusted operator controls a tethered device through the host harness and may run the mixed-soak workflow.
- A realistic attacker for this finding has device-local, non-root ability to create entries in /tmp before or during the operator's harness run.
- The repository's native init mount configuration is representative of the device state when the harness runs.
- /cache/bin/toybox dd behaves with normal POSIX open semantics and follows symlinks for of=<path>.
- Device-local attacker can create symlinks in world-writable /tmp
- Operator runs cpu-memory-profiles directly or through the default mixed-soak schedule
- Attacker can predict or race the seconds-resolution run_id and fixed profile names
- The symlink target is writable by root and meaningful to corrupt
## Path
Device-local /tmp writer
  -> precreate /tmp/v180-cpumem-<ts>-low-mem.bin symlink
  -> operator runs mixed-soak default cpu-memory-profiles
  -> PID1/root run /cache/bin/toybox dd of=<path>
  -> symlink target overwritten with 4-16 MiB of zeros
## Path evidence
- `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py:77-78` - The run identifier is based only on seconds-resolution time, making the filename predictable over a small time window.
- `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py:107-140` - The module constructs the /tmp path and invokes root toybox dd with of=<path>, with no no-follow, exclusive-create, randomization, or private-directory protection.
- `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py:155-160` - Cleanup removes the selected path after the write; if the path was a symlink, the target has already been overwritten.
- `scripts/revalidation/a90harness/scheduler.py:88-94` - The scheduler selects cpu-memory-profiles as the first preferred default workload for non-idle mixed-soak runs.
- `stage3/linux_init/init_v73.c:7137-7140` - Native init mounts /tmp as tmpfs mode=1777, enabling device-local unprivileged creation of names and symlinks.
- `stage3/linux_init/init_v73.c:8278-8283` - The run command executes the supplied program through execve from the native-init root/PID1 context.
- `scripts/revalidation/a90harness/gate.py:30-49` - Safety gating only blocks modules that declare special requirements; cpu-memory-profiles is non-read-only but not declared destructive, so default mixed-soak does not require --allow-destructive for this root write.
## Narrative
The finding is real. The new CpuMemoryProfilesModule builds /tmp/v180-cpumem-<seconds>-<profile>-mem.bin from int(time.time()) and fixed profile names, then sends a root native-init run command that executes /cache/bin/toybox dd with of=<that path>. The native init mounts /tmp with mode=1777, so a device-local process can precreate matching symlinks. There is no private directory, random name, O_NOFOLLOW, O_EXCL, or symlink validation, and cleanup only runs rm -f on the /tmp path after the overwrite. The scheduler makes cpu-memory-profiles the preferred default mixed-soak workload. The impact is high integrity/availability loss on a single device because root can be induced to zero regular files, helper binaries, flags/logs, or potentially block devices; likelihood is lower than remote issues because exploitation requires a local device foothold and operator execution.
## Controls
- Host DeviceClient defaults to 127.0.0.1:54321, so this is not exposed as an Internet-facing path by default
- Safety gate framework exists for destructive/NCM/USB-rebind modules
- cpu-memory-profiles is not marked destructive and is therefore allowed by the gate without --allow-destructive
- Command execution uses argv/execve rather than shell expansion, which mitigates shell injection but not symlink following
- /tmp sticky/world-writable mode permits name creation and does not prevent privileged processes from following attacker-created symlinks
## Blindspots
- Static review cannot prove the exact runtime UID landscape or whether unprivileged third-party processes are normally present on the native-init device.
- Static review cannot confirm device kernel symlink-following protections or toybox dd implementation details on the actual target, though normal POSIX behavior and validation evidence support exploitability.
- The exact set of high-value writable targets depends on the mounted filesystems and device state during a harness run.
- The likelihood depends on how often operators run mixed-soak in environments where untrusted local device processes exist.
