# V1053 Modem Pre-Holder Plain Open Fallback Plan

## Goal

Address the V1052 blocker where the private-root modem pre-holder reached
`/dev/subsys_modem` but the first `O_NONBLOCK` open returned `errno=14` before a
holder fd could be established.

## Evidence Basis

- V1052 proved:
  - `modem_pre_holder_child_chroot=1`
  - `modem_pre_holder_path=/dev/subsys_modem`
  - `modem_pre_holder_errno=14`
  - `modem_pre_holder_confirmed=0`
- Older lower-window holder experiments used shell/plain fd open semantics, not
  an explicit `O_NONBLOCK` open.

## Method

1. Bump helper marker from `v179` to `v180`.
2. In the pre-holder child, record the first nonblocking open result.
3. If the nonblocking open fails with any errno, retry a plain
   `open("/dev/subsys_modem", O_RDONLY | O_CLOEXEC)`.
4. Emit explicit diagnostics:
   - `modem_pre_holder_nonblock_opened`
   - `modem_pre_holder_nonblock_errno`
   - `modem_pre_holder_plain_retry`
   - `modem_pre_holder_first_errno`
5. Build only; do not deploy or execute on-device in V1053.

## Hard Gates

No device contact, helper deploy, daemon start, subsystem open, Wi-Fi HAL,
scan/connect, credentials, DHCP/routes, external ping, sysfs write, GPIO write,
partition write, boot image write, or firmware mutation.

## Success Criteria

- Helper builds as static aarch64.
- `strings` confirms marker `a90_android_execns_probe v180`.
- `strings` confirms the fallback diagnostics and PM full-contract order token.

## Next

V1054 should deploy helper `v180` only. V1055 should rerun the bounded live gate
and classify whether plain open succeeds, blocks, or returns another driver
errno.
