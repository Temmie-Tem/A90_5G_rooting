# Native Init v250 QRTR Socket No-Start Probe Report

## Summary

- status: PASS
- decision: `qrtr-socket-local-bind-pass`
- boot image change: none
- daemon start: not executed
- QRTR payload send/connect: not executed
- output: `tmp/wifi/v250-qrtr-socket-probe/`
- device helper: `stage3/linux_init/helpers/a90_qrtr_probe.c`
- host tool: `scripts/revalidation/wifi_qrtr_socket_probe.py`

v250 added a static ARM64 helper that opens an `AF_QIPCRTR` datagram socket and
binds only a local ephemeral port. It does not send packets, connect to services,
perform nameservice lookup, start `cnss-daemon`, or touch Wi-Fi link state.

## Build And Deploy

Build:

```bash
scripts/revalidation/build_qrtr_probe_helper.sh
```

Artifact:

```text
stage3/linux_init/helpers/a90_qrtr_probe
sha256=92500fa51a7c910877d59b704210b915dfeed4abb0daca36d894b10f319be8a5
static ARM64, no INTERP, no dynamic section
```

Deploy:

```bash
python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_qrtr_probe \
  --toybox /cache/bin/toybox \
  install --local-binary stage3/linux_init/helpers/a90_qrtr_probe \
  --transfer-port 18087 --transfer-timeout 120.0
```

Device install result:

```text
installed /cache/bin/a90_qrtr_probe sha256=92500fa51a7c910877d59b704210b915dfeed4abb0daca36d894b10f319be8a5
```

## Validation

Static checks:

```bash
python3 -m py_compile scripts/revalidation/wifi_qrtr_socket_probe.py
git diff --check
```

Live no-start probe:

```bash
python3 scripts/revalidation/wifi_qrtr_socket_probe.py \
  --out-dir tmp/wifi/v250-qrtr-socket-probe
```

Result:

```text
decision: qrtr-socket-local-bind-pass
pass: True
```

Post-check:

```bash
python3 scripts/revalidation/a90ctl.py run /cache/bin/toybox pidof cnss-daemon || true
```

Result: `pidof` returned rc=1, so `cnss-daemon` was not running after v250.

## Probe Evidence

| Key | Value |
| --- | --- |
| `qrtr_probe.af` | `42` |
| `qrtr_probe.sockopt.domain` | `42` |
| `qrtr_probe.sockopt.type` | `2` |
| `qrtr_probe.socket.rc` | `0` |
| `qrtr_probe.initial.node` | `1` |
| `qrtr_probe.bind.selected_node` | `1` |
| `qrtr_probe.bind_post.port` | `16424` |
| `qrtr_probe.status` | `bind-pass` |
| `qrtr_probe.send_attempted` | `0` |
| `qrtr_probe.connect_attempted` | `0` |

## Interpretation

- QRTR is not blocked at the kernel socket-family level.
- Local QRTR ephemeral bind works in native init.
- Remaining QRTR risk is userspace nameservice/endpoint behavior, not basic
  socket creation.
- This does not prove `cnss-daemon` can complete initialization, and it does not
  authorize Wi-Fi scan/connect/link-up.

## References

- <https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux/+/refs/heads/master/net/qrtr/Kconfig>
- <https://codebrowser.dev/linux/linux/net/qrtr/af_qrtr.c.html>

## Guardrails Preserved

- no `cnss-daemon` execution
- no `cnss_diag`
- no QRTR send/connect/nameservice packet
- no rfkill unblock, `wlan*` link-up, scan/connect, credentials, DHCP, or routing
- no ICNSS bind/unbind, firmware mutation, Android partition write, or reboot

## Next Step

The first bounded live start-only attempt remains approval-gated. If approval is
still withheld, the next no-start candidate is QRTR nameservice visibility or
property-read surface analysis without sending Wi-Fi control commands.
