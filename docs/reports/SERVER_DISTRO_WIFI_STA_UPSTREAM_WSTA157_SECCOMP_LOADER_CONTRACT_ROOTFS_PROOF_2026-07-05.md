# WSTA157 Seccomp Loader Contract Rootfs Proof Pass

Date: 2026-07-05 12:36 KST

## Verdict

WSTA157 wires the WSTA156 non-loaded filter artifact into the private rootfs
staging surface and proves the launcher contract stays default-off.  This unit
is host-only: it did not chroot, touch the device, flash, reboot, connect
Wi-Fi, run DHCP, open a public tunnel, mutate packet filters, write userdata,
build a new filter, load BPF, load a seccomp filter, or enforce seccomp.

Result: PASS.  The launcher observes the staged filter artifact during dry-run,
continues to the existing `setpriv --no-new-privs` path with enforcement off,
and fail-closes before exec when `A90_SERVICE_LAUNCH_SECCOMP_ENFORCE=1` because
the loader is intentionally not implemented yet.

## Source Changes

- Updated
  `workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py`:
  - stages the WSTA156 manifest at
    `etc/a90-dpublic/seccomp-filter-manifest.json`.
  - stages the WSTA156 object at
    `usr/lib/a90-dpublic/seccomp/wsta156_seccomp_filters.o`.
  - verifies object SHA against the WSTA156 manifest before staging.
  - adds `A90WSTA157_SECCOMP_ARTIFACT_PRESENT` and
    `A90WSTA157_SECCOMP_ENFORCE_FLAG` launcher markers.
  - blocks `A90_SERVICE_LAUNCH_SECCOMP_ENFORCE=1` with
    `blocked-seccomp-enforce-unimplemented`.
- Added
  `workspace/public/src/scripts/server-distro/run_wsta157_seccomp_loader_contract_rootfs_proof.py`.
- Extended focused rootfs tests in `tests/test_prepare_wsta3_sta_rootfs.py`.
- Added focused runner tests in
  `tests/test_server_distro_wsta157_seccomp_loader_contract_rootfs_proof.py`.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta157-seccomp-loader-contract-rootfs-proof-20260705T1236KST/
```

Inputs:

```text
workspace/private/runs/server-distro/wsta153-seccomp-policy-source-20260705T1207KST/wsta153_seccomp_policy.json
workspace/private/runs/server-distro/wsta156-seccomp-nonloaded-filter-artifact-20260705T1227KST/wsta156_seccomp_filter_manifest.json
workspace/private/runs/server-distro/wsta156-seccomp-nonloaded-filter-artifact-20260705T1227KST/wsta156_seccomp_filters.o
```

Decision:

```text
wsta157-seccomp-loader-contract-rootfs-proof-pass
```

Default dry-run stdout:

```text
A90WSTA154_SECCOMP_POLICY_PRESENT=1
A90WSTA154_SECCOMP_DRY_RUN_ONLY=1
A90WSTA154_SECCOMP_FILTER_LOAD=0
A90WSTA154_SECCOMP_SERVICE=dpublic-hud
A90WSTA154_SECCOMP_POLICY_SERVICE=dpublic-hud-intent
A90WSTA154_SECCOMP_PROFILE=seccomp-dpublic-hud-intent-observed-v1
A90WSTA154_SECCOMP_ALLOWLIST_COUNT=22
A90WSTA157_SECCOMP_ARTIFACT_PRESENT=1
A90WSTA157_SECCOMP_ENFORCE_FLAG=0
a90_service_launcher_decision=exec
```

Enforcement-flag negative proof:

```text
A90WSTA157_SECCOMP_ARTIFACT_PRESENT=1
A90WSTA157_SECCOMP_ENFORCE_FLAG=1
a90_service_launcher_decision=blocked-seccomp-enforce-unimplemented
```

## Checks

WSTA157 fail-closes unless:

- the proof is explicitly gated.
- run directory, WSTA153 policy, WSTA156 manifest, and WSTA156 object are
  private.
- WSTA156 manifest says `SECCOMP_FILTER_ARTIFACT_COMPILED_NOT_LOADED`,
  `loaded=false`, and `enforced=false`.
- WSTA156 object SHA matches the manifest.
- rootfs staging writes policy, launcher map, filter manifest, and filter
  object.
- default dry-run shows artifact present and enforce flag `0`.
- default dry-run still reaches fake `setpriv`.
- enforce-flag run shows artifact present and enforce flag `1`.
- enforce-flag run exits `65` before exec with
  `blocked-seccomp-enforce-unimplemented`.

## Validation

- `py_compile`:
  - `prepare_wsta3_sta_rootfs.py`
  - `run_wsta157_seccomp_loader_contract_rootfs_proof.py`
  - `test_prepare_wsta3_sta_rootfs.py`
  - `test_server_distro_wsta157_seccomp_loader_contract_rootfs_proof.py`
- Focused prepare-rootfs + WSTA155 + WSTA156 + WSTA157 tests: `42 tests OK`.
- Full server-distro regression: `546 tests OK`.
- WSTA157 proof generation from the real WSTA153/WSTA156 artifacts: pass.

## Next

WSTA158 should choose the next enforcement-adjacent bounded step: either build a
separate loader helper with a default check-only mode, or run the full staged
rootfs in a private chroot dry-run.  Actual seccomp enforcement remains
unproven and must stay behind a later explicit live gate.
