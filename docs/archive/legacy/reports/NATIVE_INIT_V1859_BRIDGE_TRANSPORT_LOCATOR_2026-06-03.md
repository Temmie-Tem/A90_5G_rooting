# Native Init V1859 Bridge Transport Locator

## Summary

- Cycle: `V1859`
- Type: host-only locator for repo-local native-init bridge transport
- Decision: `v1859-transport-locator-repo-bridge-ready-host-pass`
- Label: `transport-locator-repo-bridge-ready`
- Result: PASS
- Reason: Repo-local a90ctl/serial bridge tooling exists, an ACM tty is present, and localhost bridge port 54321 is already listening; V1858's PATH issue is narrowed to command invocation, not missing repo tooling
- Evidence: `tmp/wifi/v1859-bridge-transport-locator`

## Input

- V1858: `v1858-host-ready-device-command-missing-host-pass` / `host-ready-device-command-missing` / pass `True`

## Tooling

- PATH `a90ctl`: `False` path ``
- Repo `a90ctl.py`: `True` at `scripts/revalidation/a90ctl.py`, help rc `0`
- Repo `serial_tcp_bridge.py`: `True` at `scripts/revalidation/serial_tcp_bridge.py`, help rc `0`

## Host Transport

- git clean: `True`
- ACM tty present: `True` entries `[{'path': '/dev/ttyACM0', 'realpath': '/dev/ttyACM0'}]`
- `/dev/ttyACM0` present: `True`
- Samsung by-id entries: `[]`
- localhost `127.0.0.1:54321` listener: `True`
- listener lines: `['LISTEN 0      1               127.0.0.1:54321      0.0.0.0:*']`

## Documentation Cross-Check

- README bridge reference: tty `True`, port `True`, script `True`
- Flash/bridge guide reference: endpoint `True`, a90ctl `True`, tty `True`
- Approval matrix reference: explicit tty command `True`, read-only bridge row `True`

## Safety Scope

Host-only. This locator did not run an `a90ctl` device command, start a serial bridge, open a TCP bridge client probe, flash, reboot, stage properties, start actors, open `/dev/subsys_esoc0`, start `boot_wlan`, issue restart-PD request, force RC1, fake ONLINE state, write PMIC/GPIO/GDSC controls, perform eSoC notify, BOOT_DONE spoof, PCI rescan, platform bind/unbind, start Wi-Fi HAL, scan/connect, use credentials, configure DHCP/routes, or external ping.

## Next

- Use repo-local `python3 scripts/revalidation/a90ctl.py` instead of relying on PATH `a90ctl`.
- Next useful live-adjacent unit is a read-only bridge identity/status smoke that redacts version creator text and checks only prerequisites such as WLFW service 69 and `wlan0` presence.
- Do not proceed to Wi-Fi HAL/scan/connect unless WLFW service 69 and `wlan0` are present.
