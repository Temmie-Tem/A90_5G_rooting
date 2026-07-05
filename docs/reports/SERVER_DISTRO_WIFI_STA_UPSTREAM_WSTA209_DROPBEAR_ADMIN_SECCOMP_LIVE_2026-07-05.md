# WSTA209 Dropbear Admin Seccomp Live

Date: 2026-07-05

## Verdict

PASS.  WSTA209 started the root-boundary `dropbear-admin-usb` daemon through
the WSTA161 gated seccomp helper, loaded the derived `dropbear-admin-usb`
profile, and proved the intended non-root admin login still works under
enforcement while root login remains rejected.

Private evidence:

```text
workspace/private/runs/server-distro/wsta209-dropbear-admin-seccomp-live-20260705T2020KST/wsta209_result.json
```

Decision:

```text
wsta209-dropbear-admin-seccomp-live-pass
```

The same result reclassifies as pass with the current runner after tightening
cleanup accounting.

## Live Markers

The live run observed:

```text
A90WSTA209_ADMIN_SECCOMP_STAGE_BEGIN
A90WSTA209_ASSET_PRESENT=1
A90WSTA209_SECCOMP_ASSETS_STAGED=1
A90WSTA209_ROOT_AUTHORIZED_KEYS_ABSENT=1
A90WSTA209_ADMIN_PASSWD_LINE=1
A90WSTA209_ADMIN_GROUP_LINE=1
A90WSTA209_ADMIN_SHADOW_LINE=1
A90WSTA209_ADMIN_AUTHORIZED_KEYS=1
A90WSTA209_DROPBEAR_PRESENT=1
A90WSTA209_LOADER_HELPER_PRESENT=1
A90WSTA209_DROPBEAR_ALIVE=1
A90WSTA209_DROPBEAR_LISTEN=1
A90WSTA209_SECCOMP_DROPBEAR_MARKERS=1
A90WSTA209_ADMIN_SECCOMP_STAGE_DONE
```

The Dropbear process log contained the WSTA161 proof markers:

```text
A90WSTA161_SECCOMP_LOAD=1
a90_seccomp_loader_decision=loaded
A90WSTA208_EXEC_AFTER_LOAD=1
```

SSH as `a90admin` returned UID/GID `3903/3903` and user/group
`a90admin/a90admin`.  SSH as `root` was rejected with return code `255` and
`Permission denied (publickey)`.

## Cleanup

The WSTA209 cleanup removed the temporary admin authorized key and staged
seccomp asset directory.  That immediate cleanup still saw a live Dropbear PID,
so the existing WSTA94 chroot cleanup performed the final process cleanup.  The
accepted result now requires either direct WSTA209 Dropbear absence or final
WSTA94 `dropbear_cleanup_ok=true`.

Final cleanup markers:

```text
A90D2_CLEANUP_DONE
A90D2 cleanup_mount_absent=1
A90D2 cleanup_loop_node_absent=1
A90D2 cleanup_dropbear_absent=1
A90D2_POSTCHECK_DONE
A90D2 post_mount_absent=1
A90D2 post_loop_node_absent=1
A90D2 post_dropbear_absent=1
```

## Safety

No boot image was built or flashed.  No native reboot, Wi-Fi connect, DHCP,
public tunnel, public smoke, packet-filter mutation, userdata write, or
switch-root occurred.  The live action was limited to the USB/NCM admin service
proof inside the SD work image.

Safety fields from the accepted result:

```text
boot_flash=false
native_reboot=false
wifi_connect=false
dhcp=false
public_tunnel=false
public_smoke=false
packet_filter_mutation=false
userdata_touch=false
switch_root=false
seccomp_filter_loaded=true
seccomp_enforced=true
service_functional_under_seccomp=true
root_login_negative_test=true
secret_values_logged=0
admin_public_key_value_logged=false
public_url_value_logged=false
```

Final native health:

```text
selftest: pass=12 warn=1 fail=0
```

## Code Changes

- Added `run_wsta209_dropbear_admin_seccomp_live.py`, a replayable live runner
  for the real `dropbear-admin-usb` service under seccomp.
- Hardened WSTA161 exec-after-load by clearing the load token environment before
  `execv()`ing the service target.
- Added focused WSTA209 tests for fail-closed gating, stage-script shape,
  marker parsing, root-login rejection requirements, cleanup accounting, and
  mocked pass classification.

## Next

The operator seccomp milestone now covers both a non-privileged service
(`dpublic-smoke-httpd`) and the root-boundary admin daemon
(`dropbear-admin-usb`).  Stop extending seccomp proof scaffolding unless a
profile changes.  The next hardening work should move to a different lever:
capability drop verification/apply, nftables default-drop apply, or AppArmor
feasibility.
