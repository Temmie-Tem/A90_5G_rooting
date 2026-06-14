# Native Init V2110 Serial Bridge TX Queue

## Summary

- Cycle: `V2110`
- Decision: `v2110-serial-bridge-tx-queue-source-fix-pass-live-restart-needed`
- Label: `serial-bridge-partial-write-fixed`
- Result: SOURCE PASS / LIVE BLOCKED
- Reason: V2107 could not reach the V2106 producer window because host command input was corrupted before the test boot. The serial bridge wrote client payloads to the nonblocking ACM fd with a single `os.write()`, so partial writes dropped bytes. The observed device parser errors (`stophud` becoming `stpu`, `cmdv1 version` becoming fragments like `cd1vrin`) match partial host-to-serial loss, not a WLAN producer result.

## Change

- Added a `serial_tx_buffer` queue in `scripts/revalidation/serial_tcp_bridge.py`.
- Serial writes now append client bytes, flush until `EAGAIN`, and keep `EVENT_WRITE` enabled until the queued bytes are fully written.
- Serial disconnect clears the pending TX queue.

## Validation

- `python3 -m py_compile scripts/revalidation/serial_tcp_bridge.py`
- `git diff --check`

## Live State

- The stale root-owned bridge was stopped so the patched bridge could be used.
- This shell cannot reopen `/dev/ttyACM0`: device mode is `root:dialout 0660`, the current user is not in `dialout`, and passwordless sudo is unavailable (`sudo: interactive authentication is required`).
- No valid V2106/V2107 producer-window run was performed after the bridge patch.

## Safety

- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, DIAG, AP QMI send, `tftp_server` ptrace, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan, bind/unbind, PMIC/GPIO/GDSC/regulator write, or firmware/partition write was used.
- A raw Ctrl-C over the existing bridge cancelled the stale long-running `run` command and returned v724 control output; no WLAN route mutation was attempted.

## Next

- Restart the patched bridge with a principal that can open `/dev/ttyACM0`, for example `sudo python3 ./scripts/revalidation/serial_tcp_bridge.py --port 54321 --device /dev/ttyACM0 --capture tmp/bridge-v2110-txqueue.log`.
- Verify `python3 scripts/revalidation/a90ctl.py --timeout 12 --hide-on-busy version` and `selftest` parse cleanly.
- Re-run `python3 scripts/revalidation/native_wifi_tftp_persist_parent_traverse_handoff_v2107.py` to test the V2106 parent-traverse producer gate.
