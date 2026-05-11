# F047-F053 H3 Closure Report

Date: 2026-05-12

## Scope

Batch H3 closes the duplicate/reopened findings from the F047-F053 import:

- `F049`: duplicate of `F045`, predictable `/tmp` root `dd` target.
- `F053`: duplicate of `F046`, NCM preflight cache helper fallback.

No new code patch was required for H3. The current code already contains the
Batch F mitigations that remove the vulnerable patterns.

## F049 Verification

Current file: `scripts/revalidation/a90harness/modules/cpu_memory_profiles.py`

Observed current safeguards:

- Uses `require_safe_component()` for temp directory and file components.
- Uses `require_path_under()` for both the per-profile temp directory and memory file path.
- Builds paths under a private component prefix `a90-cpumem.<run_id>.<profile>` instead of the old direct `/tmp/<run>-<profile>-mem.bin` pattern.
- Creates the device temp directory with `mkdir -m 700`.

Validation:

```text
rg -n "DEVICE_TMP_ROOT|DEVICE_TMP_PREFIX|_profile_temp_dir|_profile_memory_path|require_path_under|require_safe_component|mkdir -m 700|int\\(time\\.time\\)|/tmp/\\{self\\._run_id\\}|\\{self\\._run_id\\}-\\{spec\\.name\\}-mem\\.bin" scripts/revalidation/a90harness/modules/cpu_memory_profiles.py
python3 -m py_compile scripts/revalidation/a90harness/modules/cpu_memory_profiles.py
```

Result: current safe helper/path code is present, the old direct predictable file pattern is absent, and `py_compile` passes.

Closure: `F049` is closed as `closed-duplicate-of-F045`.

## F053 Verification

Current file: `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py`

Observed current safeguards:

- Pins `TRUSTED_TCPCTL_BINARY` to `/bin/a90_tcpctl`.
- Probes only the trusted ramdisk helper.
- Explicitly refuses `/cache/bin` fallback if the trusted helper is missing.
- Passes `/bin/a90_tcpctl` as `--device-binary` to `tcpctl_host.py`.

Validation:

```text
rg -n "TRUSTED_TCPCTL_BINARY|/cache/bin/a90_tcpctl|for candidate|refusing /cache/bin fallback|--device-binary" scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py
python3 -m py_compile scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py scripts/revalidation/tcpctl_host.py
```

Result: trusted helper pinning and explicit cache fallback refusal are present, no candidate loop selects `/cache/bin/a90_tcpctl`, and `py_compile` passes.

Closure: `F053` is closed as `closed-duplicate-of-F046`.

## Acceptance

- `F049` and `F053` are duplicates of already mitigated host Batch F findings.
- No current-code reproduction path was found in the checked files.
- The findings index now marks both as closed duplicates.
