# Server-Distro D3B Switchroot Attempt 4 SHA Parse Noise

- Date: `2026-07-03`
- Scope: D3B live checked `switch_root` handoff attempt with SD pre-stage and auto-menu hide/retry
- Candidate: `A90 Linux init 0.11.130 (v3369-server-distro-switchroot)`
- Candidate boot SHA256: `13fa09320a42d98af7cc2712347dba0c35283af0085b7f87c12f81691f737505`
- Rollback target: `v2321-usb-clean-identity-rodata`
- Result: `FAIL-RECOVERED`

## Live Attempt

- Keyed D3 sysvinit image was installed on SD before the candidate flash.
- Pre-flash SD SHA matched the keyed image SHA.
- Candidate flash passed and post-flash native-init verify reported `selftest fail=0`.
- Post-flash SHA retry handled the initial auto-menu `busy` response by sending `hide`.
- The second SHA command returned `rc=0` and included the expected keyed-image SHA, but serial output
  was prefixed with residual command-echo hex, so the generic 64-hex word-boundary parser did not extract it.
- The runner treated the parsed SHA as missing and rolled back before `switch_root`.

## Recovery

- Checked rollback to `v2321` through `native_init_flash.py` passed.
- Final after-error checks recorded:
  - `version`: `0.9.285 build=v2321-usb-clean-identity-rodata`
  - `selftest`: `pass=11 warn=1 fail=0`

## Follow-Up Fix

The post-flash SHA helper now accepts the expected keyed-image SHA. If the generic parser fails but the
expected SHA appears in an `rc=0` command transcript, the runner accepts that value and proceeds.

No `switch_root` was executed in this attempt. No userdata format/mount/write was performed. No forbidden
partition was touched. No public tunnel was exposed.
