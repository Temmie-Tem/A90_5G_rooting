# WSTA155 Seccomp Launcher Dry-Run Rootfs Proof Pass

Date: 2026-07-05 12:20 KST

## Verdict

WSTA155 stages the seccomp dry-run launcher policy into a private rootfs
directory and proves the dry-run markers are observable before exec using a
fake `setpriv` binary.  This unit is host-only: it did not chroot, touch the
device, flash, reboot, connect Wi-Fi, run DHCP, open a public tunnel, mutate
packet filters, write userdata, build a seccomp filter, load a seccomp filter,
or enforce seccomp.

Result: PASS.  The launcher now has an opt-in dry-run gate controlled by
`A90_SERVICE_LAUNCH_SECCOMP_DRY_RUN=1`.  It reads a staged policy path plus a
line-oriented launcher map, emits WSTA154 markers, and keeps
`A90WSTA154_SECCOMP_FILTER_LOAD=0`.  A missing launcher map blocks before exec.

## Source Changes

- Updated
  `workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py`:
  - stages `etc/a90-dpublic/seccomp-policy.json` from the WSTA153 source
    policy when present.
  - stages `etc/a90-dpublic/seccomp-launcher-map.env`.
  - adds launcher dry-run marker logging before `setpriv` exec.
  - keeps filter load and enforcement disabled.
- Added
  `workspace/public/src/scripts/server-distro/run_wsta155_seccomp_launcher_dry_run_rootfs_proof.py`.
- Extended focused rootfs tests in `tests/test_prepare_wsta3_sta_rootfs.py`.
- Added focused runner tests in
  `tests/test_server_distro_wsta155_seccomp_launcher_dry_run_rootfs_proof.py`.

## Generated Proof

Proof run:

```text
workspace/private/runs/server-distro/wsta155-seccomp-launcher-dry-run-rootfs-proof-20260705T1220KST/
```

Input WSTA153 policy:

```text
workspace/private/runs/server-distro/wsta153-seccomp-policy-source-20260705T1207KST/wsta153_seccomp_policy.json
```

Decision:

```text
wsta155-seccomp-launcher-dry-run-rootfs-proof-pass
```

Primary launcher stdout:

```text
A90WSTA154_SECCOMP_POLICY_PRESENT=1
A90WSTA154_SECCOMP_DRY_RUN_ONLY=1
A90WSTA154_SECCOMP_FILTER_LOAD=0
A90WSTA154_SECCOMP_SERVICE=dpublic-hud
A90WSTA154_SECCOMP_POLICY_SERVICE=dpublic-hud-intent
A90WSTA154_SECCOMP_PROFILE=seccomp-dpublic-hud-intent-observed-v1
A90WSTA154_SECCOMP_ALLOWLIST_COUNT=22
a90_service_launcher_decision=exec
```

Missing-map negative proof:

```text
a90_service_launcher_decision=blocked-seccomp-map-missing
```

## Checks

WSTA155 fail-closes unless:

- the proof is explicitly gated.
- run directory and WSTA153 input policy are private.
- WSTA153 policy schema/state/enforcement state are exact.
- every WSTA153 allowlist is non-empty and not enforced.
- rootfs staging writes the policy JSON and launcher map.
- `dpublic-hud` maps to `dpublic-hud-intent`.
- launcher dry-run emits policy-present, dry-run-only, filter-load-disabled,
  service, policy-service, profile, and allowlist-count markers.
- launcher proceeds to `setpriv` only after marker emission.
- missing map exits `65` before exec.

## Validation

- `py_compile`:
  - `prepare_wsta3_sta_rootfs.py`
  - `run_wsta155_seccomp_launcher_dry_run_rootfs_proof.py`
  - `test_prepare_wsta3_sta_rootfs.py`
  - `test_server_distro_wsta155_seccomp_launcher_dry_run_rootfs_proof.py`
- Focused prepare-rootfs + WSTA155 tests: `36 tests OK`.
- Full server-distro regression: `541 tests OK`.
- WSTA155 proof generation from the real WSTA153 policy: pass.

## Next

WSTA156 should decide whether to run the same dry-run path inside an actual
private chroot/rootfs environment or proceed to compiling a non-loaded filter
artifact.  Enforcement remains unproven and must stay behind a separate live
gate.
