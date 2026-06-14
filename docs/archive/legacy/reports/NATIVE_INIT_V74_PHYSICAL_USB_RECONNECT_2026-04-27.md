# Native Init v74 Physical USB Reconnect Report (2026-04-27)

## Summary

- Version: `A90 Linux init 0.8.5 (v74)`
- Goal: verify recovery after a real host cable unplug/replug, not only software UDC re-enumeration.
- Result: PASS.
- Scope:
  - USB ACM serial bridge recovery
  - USB NCM host/device link recovery
  - `a90_tcpctl` TCP command channel recovery

## Tooling

- Added `scripts/revalidation/physical_usb_reconnect_check.py`.
- The runner:
  - checks bridge `version`
  - starts netservice if needed
  - validates NCM ping and tcpctl before unplug
  - waits for `/dev/ttyACM*` disappearance
  - waits for bridge recovery after replug
  - revalidates NCM ping and tcpctl after replug
  - restores ACM-only mode if it started netservice

Command used:

```bash
python3 ./scripts/revalidation/physical_usb_reconnect_check.py \
  --manual-host-config \
  --manual-host-timeout 600 \
  --disconnect-timeout 600 \
  --bridge-ready-timeout 240 \
  --interface-timeout 180
```

## Host Manual Step

Noninteractive sudo was unavailable:

```text
sudo-rs: interactive authentication is required
```

The script printed the required host IP commands, and the user ran them manually before and after replug:

```bash
sudo ip addr replace 192.168.7.1/24 dev enx0644eea6f44d
sudo ip link set enx0644eea6f44d up
```

Observed host NCM interface:

- interface: `enx0644eea6f44d`
- host MAC: `06:44:ee:a6:f4:4d`
- host IP: `192.168.7.1/24`
- device IP: `192.168.7.2`

## Baseline Before Unplug

- `version` returned `A90 Linux init 0.8.5 (v74)`.
- netservice was initially disabled, so the runner started it.
- Device USB gadget switched to composite:
  - `functions: ncm.usb0,acm.usb0`
  - `ncm.ifname: ncm0`
  - `ncm.dev_addr: ba:10:51:9a:a7:75`
  - `ncm.host_addr: 06:44:ee:a6:f4:4d`
- Host ping before unplug:
  - `3 packets transmitted, 3 received, 0% packet loss`
- `tcpctl ping`:
  - `pong`
  - `OK`
- `tcpctl status`:
  - `OK`
- `tcpctl run /cache/bin/toybox uptime`:
  - exit `0`
  - `OK`

## Physical Reconnect

The runner printed `READY`, then the cable was unplugged and replugged.

Observed:

- ACM disappeared:
  - `ACM disconnected; current devices: <none>`
- bridge recovered after replug:
  - `A90 Linux init 0.8.5 (v74)`
- NCM returned with the same host interface:
  - `enx0644eea6f44d`
- During the reconnect window, one short `cmdv1` check fell back to raw bridge because the framed END marker was unavailable.
  - This was non-blocking; the next framed `cmdv1` check succeeded.

## Post-Replug Validation

- Host IP was re-applied manually because the interface lost its address after replug.
- Host ping after replug:
  - `3 packets transmitted, 3 received, 0% packet loss`
  - RTT `min/avg/max/mdev = 1.456/1.952/2.935/0.694 ms`
- `tcpctl ping`:
  - `pong`
  - `OK`
- `tcpctl status`:
  - `OK`
- `tcpctl run /cache/bin/toybox uptime`:
  - exit `0`
  - `OK`

Final runner result:

```text
PASS: ACM bridge, NCM ping, and tcpctl survived physical reconnect
```

## Cleanup

- Because the runner started netservice, it restored ACM-only mode at the end.
- Final `netservice status`:
  - `ncm0=absent`
  - `tcpctl=stopped`

## Notes

- The only manual step was host-side IP restore caused by unavailable noninteractive sudo.
- Physical reconnect reliability is good enough to keep ACM serial as the rescue channel and NCM/tcpctl as the server-style control channel.
