# WSTA208 Real Service Seccomp Smoke Live

Date: 2026-07-05

## Verdict

PASS.  WSTA208 loaded and enforced the derived seccomp profile on the real
`dpublic-smoke-httpd` service, then proved the service still returned the
loopback smoke marker under enforcement.

Private evidence:

```text
workspace/private/runs/server-distro/wsta208-real-service-seccomp-smoke-live-20260705T1936KST/wsta208_result.json
```

Decision:

```text
wsta208-real-service-seccomp-smoke-live-pass
```

## Live Markers

The live run observed:

```text
A90WSTA208_REAL_SERVICE_BEGIN
A90WSTA208_LOOPBACK_UP_RC=0
A90WSTA208_LOOPBACK_ADDR_PRESENT=1
A90WSTA208_SMOKE_STARTED=1
A90_DPUBLIC_SMOKE_OK
A90WSTA208_LOOPBACK_OK=1
a90_service_launcher_decision=exec-seccomp
a90_service_launcher_service=dpublic-smoke-httpd
a90_service_launcher_user=a90www
A90WSTA161_SECCOMP_LOAD_ATTEMPT=1
A90WSTA161_SECCOMP_LOAD=1
a90_seccomp_loader_decision=loaded
A90WSTA208_EXEC_AFTER_LOAD=1
A90WSTA208_SECCOMP_REAL_SERVICE_MARKERS=1
A90WSTA208_REAL_SERVICE_PASS
```

`a90-service-launch` first dropped to the service identity (`a90www`), then the
WSTA161 helper loaded the `dpublic-smoke-httpd` seccomp profile and immediately
`execv()`ed the real smoke server.  The loopback HTTP client received
`A90_DPUBLIC_SMOKE_OK` from that service process.

Note: the helper HTTP client reported `A90WSTA208_HTTP_RC=1` after reading the
full response because the server closed the connection after serving the body.
The proof key is the body marker plus the runner's zero exit and pass markers,
matching the existing WSTA94 convention that validates the response content
rather than relying only on the helper's process return code.

## Safety

No boot image was built or flashed.  No native reboot, Wi-Fi connect, DHCP,
public tunnel, public smoke, packet-filter mutation, userdata write, or
switch-root occurred.  The only live action was the bounded SSH/chroot service
run over USB/NCM with temporary Dropbear.

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
ssh_chroot_transport=true
dropbear_over_ncm=true
seccomp_filter_loaded=true
seccomp_enforced=true
service_functional_under_seccomp=true
secret_values_logged=0
```

Final native health:

```text
selftest: pass=12 warn=1 fail=0
```

## Code Changes

- Added WSTA161 exec-after-load support so the helper can load seccomp and
  `execv()` a service target in the same filtered process.
- Added the service-launcher opt-in
  `A90_SERVICE_LAUNCH_SECCOMP_EXEC_AFTER_LOAD=1`, preserving the existing
  fail-closed `blocked-seccomp-enforce-unimplemented` path unless explicitly
  enabled.
- Added `run_wsta208_real_service_seccomp_smoke_live.py`, a replayable live
  runner for the real `dpublic-smoke-httpd` service proof.
- Added focused tests for the new runner and launcher/helper contract.

## Next

The operator seccomp DoD is satisfied for the first real service:
`seccomp_enforced=true` and `service_functional_under_seccomp=true` with final
native `selftest fail=0`.  Do not continue adding no-load seccomp scaffolding.
Next hardening work should move to a new real lever or target, such as
`dropbear-admin` under seccomp, capability drop verification, or nftables
default-drop apply.
