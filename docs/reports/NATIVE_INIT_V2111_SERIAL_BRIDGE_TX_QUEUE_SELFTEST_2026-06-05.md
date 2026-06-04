# Native Init V2111 Serial Bridge TX Queue Selftest

## Summary

- Cycle: `V2111`
- Decision: `v2111-serial-bridge-tx-queue-pty-pass`
- Label: `serial-bridge-tx-queue-pty-pass`
- Pass: `True`
- Reason: PTY bridge received the exact queued payload
- Evidence: `tmp/wifi/v2111-serial-bridge-txqueue-selftest`

## Matrix

| area | value | detail |
| --- | --- | --- |
| bridge_started | True | port=56327 |
| payload_bytes | 262144 | received=262144 |
| sha256_match | True | payload=54fa066488d3d8169474f6bbb9fa96c163c6e0539ad97601789039524a57b6ee received=54fa066488d3d8169474f6bbb9fa96c163c6e0539ad97601789039524a57b6ee |
| stdout | `tmp/wifi/v2111-serial-bridge-txqueue-selftest/bridge.stdout.txt` | |
| stderr | `tmp/wifi/v2111-serial-bridge-txqueue-selftest/bridge.stderr.txt` | |
| capture | `tmp/wifi/v2111-serial-bridge-txqueue-selftest/bridge.capture.log` | |

## Interpretation

- This is a host-only pseudo-terminal validation of the V2110 bridge fix.
- It proves the bridge no longer relies on a single nonblocking `os.write()` for client-to-serial bytes in this controlled PTY path.
- It does not prove live `/dev/ttyACM0` access or any WLAN producer behavior.

## Validation

- `python3 scripts/revalidation/serial_bridge_tx_queue_selftest_v2111.py`
- `python3 -m py_compile scripts/revalidation/serial_bridge_tx_queue_selftest_v2111.py scripts/revalidation/serial_tcp_bridge.py`
- `git diff --check`

## Safety

- No device serial node, flash, reboot, test boot, rollback, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, DIAG, AP QMI send, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan, bind/unbind, PMIC/GPIO/GDSC/regulator write, or firmware/partition write was used.

## Next

- Start the patched bridge against real `/dev/ttyACM0` as root/dialout and rerun V2107.
