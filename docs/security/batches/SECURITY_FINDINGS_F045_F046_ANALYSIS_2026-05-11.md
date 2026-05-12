# F045-F046 Security Findings Relationship and Fix Plan

Date: `2026-05-11`
Source CSV: `docs/security/scans/codex-security-findings-2026-05-11T07-54-55.648Z.csv`
Scope: post-v184 mixed-soak harness findings against CPU/memory workload and NCM/TCP preflight selection.

## Summary

F045 and F046 are valid and related. Both are host-harness issues where the
validation layer asks native init to execute a root-side operation using a path
whose trust boundary is too weak.

They are not kernel bugs and do not directly change the flashed native-init
image. They still matter because the harness is now used as serverization
evidence after the v184 24-hour readiness gate.

The shared failure pattern is:

```text
host harness builds/selects device path
  -> native init `run` executes as root/PID1
  -> mutable device filesystem state can redirect the operation
```

Before more mixed-soak, NCM/TCP, or Wi-Fi-facing work, these should be patched.

## Finding Table

| id | severity | status | class | priority |
|---|---|---|---|---|
| F045 | high | mitigated-host-batch-f | predictable shared `/tmp` root write target | P0 |
| F046 | medium | mitigated-host-batch-f | untrusted persistent helper fallback execution | P1 |

Priority interpretation:

- `P0`: patch before more CPU/memory mixed-soak evidence is trusted.
- `P1`: patch before NCM/TCP preflight is trusted as network readiness evidence.

## Relationship Groups

### G1. Mutable device paths used by root-side harness commands

Findings:

- F045: `cpu_memory_profiles.py` creates memory workload files at predictable
  `/tmp/<run-id>-<profile>-mem.bin` names, then runs root `dd of=<path>`.
- F046: `ncm_tcp_preflight.py` accepts `/cache/bin/a90_tcpctl` after a plain
  `stat`, then passes it to `tcpctl_host.py` as the binary that native init
  runs as root.

Shared cause:

- Host-side harness code treats device paths as simple strings.
- Existence or predictability is treated as sufficient trust.
- The actual privileged action happens later through native init `run`.

Required pattern:

```text
generate/select path through a trust policy
  -> verify path cannot be redirected or is integrity checked
  -> only then invoke native init `run`
```

### G2. Evidence runner became part of the trusted computing base

Both findings are in validation tooling, not the device image. That does not
make them ignorable. The project now uses long-running harness results to decide
whether the device is ready for serverization and Wi-Fi work. A harness that can
silently corrupt helper files or run an untrusted listener as root weakens the
evidence itself.

## Finding Analysis

### F045. Predictable `/tmp` root `dd` target

Relevant code:

- `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py`
- `scripts/revalidation/a90harness/scheduler.py`
- `stage3/linux_init/init_v73.c`

Assessment:

- Valid.
- Severity high is appropriate.
- The affected path is in the default mixed-soak workload.
- `/tmp` is world-writable on native init, and the filename is predictable from
  seconds-resolution time plus profile name.
- `dd of=<path>` follows symlinks. The later `sha256sum` can even pass if the
  symlink target now contains the expected zeroed bytes.

Implemented fix:

1. Stop writing workload files directly into shared `/tmp`.
2. Add an unpredictable `secrets.token_hex(8)` suffix to the run id.
3. Create a per-profile private directory on the device with a validated random
   name:

   ```text
   run /cache/bin/toybox mkdir -m 700 /tmp/a90-cpumem.<run-id>.<profile>
   ```

4. Validate the generated path on the host:

   - absolute path;
   - starts with `/tmp/a90-cpumem.`;
   - one safe final path component;
   - no whitespace/control/shell metacharacters.

5. Write only inside that private directory:

   ```text
   /tmp/a90-cpumem.<random>/<profile>-mem.bin
   ```

6. Cleanup only the private directory, not a predictable file path.

Why this is preferred over only adding `secrets.token_hex()` to the filename:

- Random filename lowers predictability but still writes directly into a shared
  directory.
- A private `mktemp -d` directory gives a stronger boundary because later writes
  happen under a root-created directory that should be mode `0700`.

Longer-term stronger option:

- Add a tiny device helper that creates test files with `open(O_CREAT|O_EXCL|O_NOFOLLOW)`
  and writes zeros itself. This is stronger than shelling out to `dd`, but it is
  more work and not needed for the first patch.

### F046. NCM preflight untrusted `/cache/bin/a90_tcpctl` fallback

Relevant code:

- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py`
- `scripts/revalidation/tcpctl_host.py`
- `stage3/linux_init/a90_helper.c`

Assessment:

- Valid.
- Severity medium is appropriate.
- Exploitation requires the ramdisk `/bin/a90_tcpctl` to be unavailable and a
  stale or attacker-controlled `/cache/bin/a90_tcpctl` to exist.
- If triggered, native init executes the selected helper as root before the
  later transcript authentication checks can fail.

Implemented first fix:

1. Remove the direct `/cache/bin/a90_tcpctl` stat fallback from
   `ncm_tcp_preflight.py`.
2. For preflight, accept only the ramdisk helper:

   ```text
   /bin/a90_tcpctl
   ```

3. If `/bin/a90_tcpctl` is missing, fail or skip with an explicit message rather
   than falling back to persistent cache storage.

Optional stronger follow-up:

1. Query native init's helper inventory:

   ```text
   helpers path a90_tcpctl
   helpers verify a90_tcpctl
   ```

2. Accept a runtime/cache helper only when native init reports:

   - `preferred=<path>`;
   - `exec=yes`;
   - `hash_checked=yes`;
   - `hash_match=yes`;
   - no warning;
   - path is inside the expected runtime helper root.

For this batch, the safest patch is to remove cache fallback entirely. It keeps
the NCM preflight simple and avoids making host code duplicate the helper trust
policy.

## Patch Batches

### Batch A: CPU/memory workload private device temp directory

Files:

- `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py`

Changes implemented:

- Add a device temp-dir creation step using `toybox mkdir -m 700` with an
  unpredictable `secrets.token_hex(8)` run id.
- Store the created temp dir in the module report.
- Use profile files under that private directory.
- Cleanup the directory in `finally`-style module logic where possible.
- Keep host evidence file writes unchanged; they already go through `EvidenceStore`.

Validation:

```bash
python3 -m py_compile scripts/revalidation/a90harness/modules/cpu_memory_profiles.py
git diff --check
```

Device smoke when bridge is available:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  --modules cpu-memory-profiles \
  --profile smoke \
  --duration-sec 1
```

Expected:

- generated memory paths are under `/tmp/a90-cpumem.*`;
- no direct `/tmp/v180-cpumem-*-mem.bin` paths remain;
- cleanup removes the private test directory.

### Batch B: NCM preflight trusted helper selection

Files:

- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py`

Changes implemented:

- Probe `/bin/a90_tcpctl` only.
- Do not select `/cache/bin/a90_tcpctl` from a plain `stat`.
- Report missing ramdisk helper as a preflight failure or explicit skip.
- Keep `tcpctl_host.py` behavior unchanged for now because it is also used by
  explicit operator install/smoke flows.

Validation:

```bash
python3 -m py_compile scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py
git diff --check
rg -n '"/cache/bin/a90_tcpctl"|for candidate' scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py
```

Device/NCM validation when configured:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  --modules ncm-tcp-preflight \
  --profile smoke \
  --duration-sec 1
```

Expected:

- wrapper command uses `--device-binary /bin/a90_tcpctl`;
- authenticated smoke still checks `auth=required`;
- no cache helper is executed by preflight.

## Status Decision

- F045 and F046 are locally mitigated in host harness code.
- F045 has a short 실기 smoke PASS at `tmp/security/f045-cpumem-20260511-171146`.
- F046 has static/fake-client validation and a host-NCM-unreachable 실기 module
  PASS/SKIP at `tmp/security/f046-ncm-preflight-20260511-171218`.
- Fresh local rescan `../scans/SECURITY_FRESH_SCAN_F045_F046_2026-05-11.md` reports
  S029/S030 PASS and no FAIL.
- Cloud findings can be marked fixed after the next Codex Cloud scan agrees.
