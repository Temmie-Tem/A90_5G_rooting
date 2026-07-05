# WSTA159 Seccomp Loader Check-Only Rootfs Proof Pass

Date: 2026-07-05 12:52 KST

## Verdict

WSTA159 stages the WSTA158 check-only loader helper into the private rootfs and
wires the service launcher so `A90_SERVICE_LAUNCH_SECCOMP_ENFORCE=1` calls the
helper in check-only mode before the launcher still blocks actual
load/enforcement.  This unit is host-only: it did not chroot, touch the device,
flash, reboot, connect Wi-Fi, run DHCP, open a public tunnel, mutate packet
filters, write userdata, load BPF, load a seccomp filter, or enforce seccomp.

Result: PASS.  The rootfs now carries the WSTA158 helper manifest and helper
binary, the launcher observes helper presence, and the enforce path executes
the staged ARM64 helper through `qemu-aarch64` for proof while keeping
`A90WSTA158_SECCOMP_LOAD=0` and ending at
`blocked-seccomp-enforce-unimplemented`.

## Source Changes

- Updated
  `workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py`:
  - adds default WSTA158 helper manifest/binary inputs.
  - stages the helper manifest at
    `etc/a90-dpublic/seccomp-loader-helper-manifest.json`.
  - stages the helper binary at
    `usr/lib/a90-dpublic/seccomp/a90-seccomp-loader-checkonly`.
  - validates helper SHA, check-only state, load disabled, and enforcement
    disabled before staging.
  - adds launcher markers `A90WSTA159_SECCOMP_HELPER_PRESENT` and
    `A90WSTA159_SECCOMP_HELPER_CHECK_ONLY`.
  - makes the enforce flag call the helper as
    `--service "$SERVICE" --check-only` when present, then still blocks
    actual load/enforcement.
- Added
  `workspace/public/src/scripts/server-distro/run_wsta159_seccomp_loader_checkonly_rootfs_proof.py`.
- Extended `tests/test_prepare_wsta3_sta_rootfs.py`.
- Added
  `tests/test_server_distro_wsta159_seccomp_loader_checkonly_rootfs_proof.py`.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta159-seccomp-loader-checkonly-rootfs-proof-20260705T1252KST/
```

Inputs:

```text
workspace/private/runs/server-distro/wsta153-seccomp-policy-source-20260705T1207KST/wsta153_seccomp_policy.json
workspace/private/runs/server-distro/wsta156-seccomp-nonloaded-filter-artifact-20260705T1227KST/wsta156_seccomp_filter_manifest.json
workspace/private/runs/server-distro/wsta156-seccomp-nonloaded-filter-artifact-20260705T1227KST/wsta156_seccomp_filters.o
workspace/private/runs/server-distro/wsta158-seccomp-loader-checkonly-helper-20260705T1243KST/wsta158_seccomp_loader_helper_manifest.json
workspace/private/runs/server-distro/wsta158-seccomp-loader-checkonly-helper-20260705T1243KST/a90-seccomp-loader-checkonly
```

Decision:

```text
wsta159-seccomp-loader-checkonly-rootfs-proof-pass
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
A90WSTA159_SECCOMP_HELPER_PRESENT=1
A90WSTA159_SECCOMP_HELPER_CHECK_ONLY=1
a90_service_launcher_decision=exec
fake_setpriv_args=--no-new-privs --reuid a90hud --regid a90hud --init-groups -- /bin/true
```

Enforce-flag check-only stdout:

```text
A90WSTA157_SECCOMP_ENFORCE_FLAG=1
A90WSTA159_SECCOMP_HELPER_PRESENT=1
A90WSTA159_SECCOMP_HELPER_CHECK_ONLY=1
A90WSTA158_LOADER_CHECK_ONLY=1
A90WSTA158_SECCOMP_LOAD=0
A90WSTA158_PROFILE service=dpublic-hud policy_service=dpublic-hud-intent profile=seccomp-dpublic-hud-intent-observed-v1 len=49
a90_seccomp_loader_decision=check-only
A90WSTA159_SECCOMP_HELPER_CHECK_ONLY_OK=1
a90_service_launcher_decision=blocked-seccomp-enforce-unimplemented
```

## Checks

WSTA159 fail-closes unless:

- the proof is explicitly gated.
- run directory, WSTA153 policy, WSTA156 artifact, and WSTA158 helper inputs are
  private.
- WSTA156 object SHA matches its manifest.
- WSTA158 helper SHA matches its manifest.
- WSTA158 helper manifest says check-only, `load_enabled=false`, and
  `enforced=false`.
- the staged helper target is executable.
- dry-run with enforcement off reaches fake `setpriv`.
- enforce flag runs the helper in check-only mode.
- helper output proves `A90WSTA158_SECCOMP_LOAD=0`.
- the launcher exits `65` before exec with
  `blocked-seccomp-enforce-unimplemented`.

## Validation

- `py_compile`:
  - `prepare_wsta3_sta_rootfs.py`
  - `run_wsta159_seccomp_loader_checkonly_rootfs_proof.py`
  - `test_prepare_wsta3_sta_rootfs.py`
  - `test_server_distro_wsta159_seccomp_loader_checkonly_rootfs_proof.py`
- Focused prepare-rootfs + WSTA155 + WSTA156 + WSTA157 + WSTA158 + WSTA159
  tests: `48 tests OK`.
- Full server-distro regression: `551 tests OK`.
- WSTA159 proof generation from the real WSTA153/WSTA156/WSTA158 artifacts:
  pass.

## Next

WSTA160 should run a private full-rootfs launcher dry-run that uses the staged
helper path exactly as it will exist on ARM64, without enabling actual seccomp
load/enforcement.  Actual enforcement remains unproven and must stay behind a
later explicit live gate.
