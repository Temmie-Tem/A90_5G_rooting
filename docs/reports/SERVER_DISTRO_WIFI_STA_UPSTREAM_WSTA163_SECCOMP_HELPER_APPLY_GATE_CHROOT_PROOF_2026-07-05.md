# WSTA163 Seccomp Helper Apply Gate Chroot Proof Pass

Date: 2026-07-05 13:18 KST

## Verdict

WSTA163 wires a future launcher path that can call the staged seccomp loader
helper with `--apply`, but keeps that path behind an explicit launcher-side
gate.  This proves the service launcher can reach the WSTA161 gated-apply
binary inside the full private rootfs while still failing closed before any
real seccomp load attempt.

This unit is host-only: it did not touch the device, flash, reboot, connect
Wi-Fi, run DHCP, open a public tunnel, mutate packet filters, write userdata,
load BPF, load a seccomp filter, or enforce seccomp.  It did run a
host-private `unshare -r chroot` proof only.

Result: PASS.  The missing-gate path exits before invoking the helper with
`blocked-seccomp-helper-apply-gate-required`.  The gate-present path invokes
the WSTA161 helper with `--apply`, but the helper exits at its own load-token
gate with `blocked-load-gate-required` and does not print
`A90WSTA161_SECCOMP_LOAD_ATTEMPT=1`.

## Source Changes

- Updated
  `workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py`:
  - adds `A90_SERVICE_LAUNCH_SECCOMP_HELPER_MODE`, defaulting to
    `check-only`.
  - adds `A90_SERVICE_LAUNCH_SECCOMP_HELPER_APPLY_GATE`.
  - preserves the existing check-only helper path by default.
  - adds an `apply` helper mode that requires
    `WSTA163-ALLOW-HELPER-APPLY` before calling
    `"$loader_helper_path" --service "$SERVICE" --apply`.
  - blocks invalid helper modes with `blocked-seccomp-helper-mode-invalid`.
  - records launcher metadata for the WSTA163 helper mode marker, apply call,
    and apply gate.
- Added
  `workspace/public/src/scripts/server-distro/run_wsta163_seccomp_helper_apply_gate_chroot_proof.py`.
- Added focused tests in
  `tests/test_server_distro_wsta163_seccomp_helper_apply_gate_chroot_proof.py`.
- Extended `tests/test_prepare_wsta3_sta_rootfs.py` for the new launcher
  metadata and apply-gate marker.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta163-seccomp-helper-apply-gate-chroot-proof-20260705T1318KST/
```

Inputs:

```text
workspace/private/builds/server-distro/d3-sysvinit-usrmerge-wsta-20260704T0225Z-rootfs
workspace/private/runs/server-distro/wsta153-seccomp-policy-source-20260705T1207KST/wsta153_seccomp_policy.json
workspace/private/runs/server-distro/wsta156-seccomp-nonloaded-filter-artifact-20260705T1227KST/wsta156_seccomp_filter_manifest.json
workspace/private/runs/server-distro/wsta156-seccomp-nonloaded-filter-artifact-20260705T1227KST/wsta156_seccomp_filters.o
workspace/private/runs/server-distro/wsta161-seccomp-loader-gated-apply-helper-20260705T1307KST/wsta161_seccomp_loader_helper_manifest.json
workspace/private/runs/server-distro/wsta161-seccomp-loader-gated-apply-helper-20260705T1307KST/a90-seccomp-loader-gated-apply
```

Decision:

```text
wsta163-seccomp-helper-apply-gate-chroot-proof-pass
```

Missing launcher apply-gate stdout:

```text
A90WSTA154_SECCOMP_POLICY_PRESENT=1
A90WSTA154_SECCOMP_DRY_RUN_ONLY=1
A90WSTA154_SECCOMP_FILTER_LOAD=0
A90WSTA154_SECCOMP_SERVICE=dpublic-hud
A90WSTA154_SECCOMP_POLICY_SERVICE=dpublic-hud-intent
A90WSTA154_SECCOMP_PROFILE=seccomp-dpublic-hud-intent-observed-v1
A90WSTA154_SECCOMP_ALLOWLIST_COUNT=22
A90WSTA157_SECCOMP_ARTIFACT_PRESENT=1
A90WSTA157_SECCOMP_ENFORCE_FLAG=1
A90WSTA159_SECCOMP_HELPER_PRESENT=1
A90WSTA159_SECCOMP_HELPER_CHECK_ONLY=1
A90WSTA163_SECCOMP_HELPER_MODE=apply
a90_service_launcher_decision=blocked-seccomp-helper-apply-gate-required
```

Launcher apply-gate present, helper load-token absent stdout:

```text
A90WSTA154_SECCOMP_POLICY_PRESENT=1
A90WSTA154_SECCOMP_DRY_RUN_ONLY=1
A90WSTA154_SECCOMP_FILTER_LOAD=0
A90WSTA154_SECCOMP_SERVICE=dpublic-hud
A90WSTA154_SECCOMP_POLICY_SERVICE=dpublic-hud-intent
A90WSTA154_SECCOMP_PROFILE=seccomp-dpublic-hud-intent-observed-v1
A90WSTA154_SECCOMP_ALLOWLIST_COUNT=22
A90WSTA157_SECCOMP_ARTIFACT_PRESENT=1
A90WSTA157_SECCOMP_ENFORCE_FLAG=1
A90WSTA159_SECCOMP_HELPER_PRESENT=1
A90WSTA159_SECCOMP_HELPER_CHECK_ONLY=1
A90WSTA163_SECCOMP_HELPER_MODE=apply
A90WSTA161_LOADER_GATED_APPLY=1
A90WSTA161_SECCOMP_LOAD=0
A90WSTA161_LINKED_SERVICE_COUNT=4
A90WSTA161_AUDIT_ARCH_AARCH64=3221225655
A90WSTA161_PROFILE service=dpublic-hud policy_service=dpublic-hud-intent profile=seccomp-dpublic-hud-intent-observed-v1 len=49
a90_seccomp_loader_decision=blocked-load-gate-required
a90_service_launcher_decision=blocked-seccomp-helper-apply-failed
```

## Checks

WSTA163 fail-closes unless:

- the proof is explicitly gated.
- source rootfs and all WSTA153/WSTA156/WSTA161 inputs are private.
- the WSTA161 helper schema is
  `a90-wsta161-seccomp-loader-gated-apply-helper-v1`.
- the WSTA161 helper manifest says apply code is compiled.
- missing launcher apply gate exits `65`.
- missing launcher apply gate blocks before helper output appears.
- launcher apply gate present invokes the helper in `apply` mode.
- helper output proves `A90WSTA161_SECCOMP_LOAD=0`.
- helper output does not include `A90WSTA161_SECCOMP_LOAD_ATTEMPT=1`.
- the helper blocks on `blocked-load-gate-required`.
- the launcher exits `65` before fake `setpriv`/exec.

## Validation

- `py_compile`:
  - `prepare_wsta3_sta_rootfs.py`
  - `run_wsta163_seccomp_helper_apply_gate_chroot_proof.py`
  - `test_prepare_wsta3_sta_rootfs.py`
  - `test_server_distro_wsta163_seccomp_helper_apply_gate_chroot_proof.py`
- Focused prepare-rootfs + WSTA162 + WSTA163 tests: `40 tests OK`.
- Full server-distro regression: `560 tests OK`.
- WSTA163 proof generation from the real full source rootfs and real
  WSTA153/WSTA156/WSTA161 artifacts: pass.

## Next

WSTA164 should decide the next bounded live gate: either observe this staged
helper-apply path on device without the WSTA161 load token, or add the final
host-side launch contract for the eventual real-load token.  Actual seccomp
load/enforcement remains unproven and must stay behind a later explicit gate.
