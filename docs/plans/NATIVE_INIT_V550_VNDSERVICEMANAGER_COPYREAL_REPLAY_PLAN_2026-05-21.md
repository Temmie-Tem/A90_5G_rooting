# Native Init V550 Vnd Service-Manager Copy-Real Replay Plan

## Goal

Retry the V549 bounded companion replay with Android-captured real linkerconfig inputs.

## Basis

V549 started `vndservicemanager /dev/vndbinder` with the correct UID/GID/groups and
SELinux exec context, but the child exited before observation with:

```text
CANNOT LINK EXECUTABLE "/vendor/bin/vndservicemanager": cannot locate symbol "_ZNK7android8BpBinder6handleEv"
```

The V549 namespace used synthetic `minimal-vendor` linkerconfig. Earlier service-manager
proofs used Android-captured `copy-real` linkerconfig from:

- `/cache/bin/a90_real_ld.config.txt`
- `/cache/bin/a90_real_apex.libraries.config.txt`

Both files are currently present on device.

## Scope

Allowed:

- bounded `wifi-companion-vnd-service-manager-start-only` replay with helper v76;
- switch only `--linkerconfig-mode minimal-vendor` to `copy-real` and provide the real
  linkerconfig source files;
- start/cleanup service managers and companion daemons as in V549.
- omit the inherited `--capture-mode ptrace-lite` option so the `cmdv1` line stays
  within the native shell argument budget.

Forbidden:

- Wi-Fi HAL start;
- scan/connect/link-up, DHCP, routing, credentials, or external ping;
- boot image or partition writes.

## Success Criteria

- `vndservicemanager` becomes observable and cleans up, or
- the unresolved symbol persists under copy-real, proving the blocker is not only the
  synthetic linkerconfig.

## Implementation Note

The native serial shell accepts at most 31 parsed tokens per line, so `cmdv1` leaves
30 safe command arguments. V550 copy-real needs two extra source-path options; ptrace
capture is therefore intentionally disabled for this run to avoid truncating the final
argument and producing a false `--apex-libraries-source` parser error.
