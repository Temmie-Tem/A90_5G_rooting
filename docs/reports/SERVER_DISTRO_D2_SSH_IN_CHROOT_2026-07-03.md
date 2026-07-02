# Server Distro Endgame - D2 SSH In Chroot

- Date: 2026-07-03 KST / 2026-07-02 UTC
- Unit: D2 SSH-in-chroot.
- Design: `docs/plans/NATIVE_INIT_SERVER_DISTRO_ENDGAME_DESIGN_2026-06-30.md`
- Decision: `server-distro-d2-ssh-in-chroot-pass`
- Device action: non-destructive SD-only runtime work. No flash, no format, no `userdata`
  mount/write, no public tunnel exposure.
- End state: resident stayed `v2321-usb-clean-identity-rodata`; final standalone
  `selftest pass=11 warn=1 fail=0`; no `distro-root` mount, `/dev/loop*` node, dropbear process,
  or D2 SSH listener remained.

## Scope

D2 proved the next chroot bring-up target from the locked server-distro design: `dropbear` can run
directly inside the Debian chroot, and the host can authenticate over the native-init USB/NCM path
with a temporary per-run key.

Raw command output, host private key, public key, and known-host material are private only:

`workspace/private/runs/server-distro/d2-ssh-in-chroot-20260702T210357Z/`

The committed report contains only the redacted proof and health classification needed to charter
D3.

## Implementation

Added a reusable host-side D2 runner:

`workspace/public/src/scripts/server-distro/run_d2_ssh_in_chroot.py`

The runner reuses the D1 image verification/staging helpers, then:

1. Generates a per-run temporary Ed25519 SSH key under `workspace/private/runs/server-distro/`.
2. Refuses to proceed unless the resident device reports v2321 and baseline selftest `fail=0`.
3. Verifies the SD-staged Debian image SHA-256:
   `210fc1f92d4eb8bf291fb5b362154a29ca2b579a22a0a41cb1aaa89b5b6cb0dc`.
4. Loop-mounts the Debian image at `/mnt/sdext/a90/runtime/distro-root`.
5. Temporarily writes `root/.ssh/authorized_keys` inside the mounted image.
6. Temporarily rewrites root's shadow password field from locked to password-disabled/key-only form,
   with the original shadow file backed up for restoration.
7. Generates a temporary dropbear host key inside the chroot and starts dropbear with password auth
   disabled and forwarding disabled.
8. Runs a host SSH command with `BatchMode=yes` and public-key-only auth, expecting the
   `A90D2_SSH_MARKER` marker from Debian.
9. Stops dropbear, restores `etc/shadow`, removes temporary SSH files, unmounts, detaches/removes the
   runtime loop node, and performs a separate post-cleanup absence check.

The setup was intentionally split into smaller serial commands after live validation exposed a
cmdv1x payload length limit. Cleanup also uses a separate postcheck because the dropbear child can
remain visible briefly during the cleanup command itself.

## Live Result

Private summary:

- `decision`: `server-distro-d2-ssh-in-chroot-pass`
- `remote_image`:
  `/mnt/sdext/a90/runtime/debian-bookworm-arm64-20260701-024412.img`
- `remote_sha256`:
  `210fc1f92d4eb8bf291fb5b362154a29ca2b579a22a0a41cb1aaa89b5b6cb0dc`
- `debian_version`: `12.14`
- `dropbear_started`: `true`
- `dropbear_pid_observed`: `true`
- `hostkey_type`: `ed25519`
- `ssh_marker_returned`: `true`
- `stage_marker_present`: `true`
- `shadow_restored`: `true`
- `postcheck_mount_absent`: `true`
- `postcheck_loop_node_absent`: `true`
- `postcheck_dropbear_absent`: `true`
- `final_v2321`: `true`
- `final_selftest_fail0`: `true`
- `userdata_touched`: `false`
- `flash_performed`: `false`

Relevant SSH proof marker:

```text
A90D2_SSH_MARKER
debian_version=12.14
stage_marker=present
```

Relevant post-cleanup markers:

```text
A90D2_POSTCHECK_BEGIN
A90D2 post_mount_absent=1
A90D2 post_loop_node_absent=1
A90D2 post_dropbear_absent=1
A90D2_POSTCHECK_DONE
```

## Safety Result

- No boot image was built or flashed.
- No rollback flash was needed because resident v2321 was maintained throughout.
- No forbidden partition was touched.
- `userdata=/dev/block/sda33` stayed untouched; D4 remains the only possible future
  `userdata` reformat gate.
- No public exposure was attempted; D-public remains a later explicit gate.
- Temporary SSH credentials and host-key material stayed under `workspace/private/` and were not
  committed.

## Validation

Host validation:

- `PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile workspace/public/src/scripts/server-distro/run_d2_ssh_in_chroot.py tests/test_server_distro_d2_ssh_in_chroot.py`
- `PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest tests.test_server_distro_d2_ssh_in_chroot`
  - `Ran 3 tests ... OK`

Device validation:

- Baseline `version/status/selftest` passed before D2.
- The staged image SHA matched the expected host image SHA.
- Chrooted dropbear started and returned a bounded host SSH marker from Debian.
- Cleanup restored `etc/shadow` and removed temporary SSH files.
- Postcheck verified no mount, loop node, or dropbear process/listener remained.
- Final runner health and standalone post-run `selftest` both reported `fail=0`.

## D3 Readiness

D3 is unblocked as the next non-destructive rung: prove the `switch_root`/PID1 handoff path using
the same SD-backed Debian image. D3 must remain recoverable to v2321 and must not touch `userdata`.
