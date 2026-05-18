# Native Init v250 QRTR Socket No-Start Probe Plan

## Summary

- target: v250 no-start AF_QIPCRTR socket probe
- baseline: v249 `cnss-runtime-gaps-classified`
- new device helper: `stage3/linux_init/helpers/a90_qrtr_probe.c`
- new host tool: `scripts/revalidation/wifi_qrtr_socket_probe.py`
- boot image change: none
- daemon start: not executed

v249 proved `QIPCRTR` is registered in `/proc/net/protocols`, but it did not
open an AF_QIPCRTR socket. v250 adds a tiny static helper that opens and binds a
local QRTR datagram socket without sending packets, doing service lookups, or
touching Wi-Fi state.

## Reference Basis

- Linux QRTR Kconfig describes Qualcomm IPC Router as the protocol used to
  communicate with services from other hardware blocks, and notes userspace
  service listing is needed for lookups:
  <https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux/+/refs/heads/master/net/qrtr/Kconfig>
- Linux `af_qrtr.c` creates only `SOCK_DGRAM` sockets for `AF_QIPCRTR` and
  supports autobind/ephemeral local ports:
  <https://codebrowser.dev/linux/linux/net/qrtr/af_qrtr.c.html>

## Scope

The helper may do only local socket operations:

- `socket(AF_QIPCRTR, SOCK_DGRAM | SOCK_CLOEXEC, 0)`
- `getsockopt(SO_DOMAIN/SO_TYPE)`
- `getsockname()` before/after bind
- `bind()` to local candidate node/ephemeral port
- close socket

## Explicit Non-Goals

v250 must not do any of the following:

- start `cnss-daemon`
- run `cnss_diag`
- send QRTR payloads
- connect to QRTR service nodes
- perform QRTR nameservice lookup packets
- unblock rfkill
- link up `wlan*`
- scan/connect Wi-Fi
- start supplicant/HAL/wificond/hostapd
- bind/unbind ICNSS
- write Android partitions
- reboot automatically

## Output

Recommended output directory:

```text
tmp/wifi/v250-qrtr-socket-probe/
├── manifest.json
├── qrtr-probe.txt
├── live-captures.json
├── summary.md
└── captures/*.txt
```

Decision labels:

- `qrtr-socket-local-bind-pass`: AF_QIPCRTR socket open and local bind worked.
- `qrtr-socket-open-only`: socket open worked but local bind failed.
- `qrtr-socket-blocked`: socket open failed or v249 prerequisite failed.

## Validation Plan

Build:

```bash
scripts/revalidation/build_qrtr_probe_helper.sh
```

Deploy:

```bash
python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_qrtr_probe \
  --toybox /cache/bin/toybox \
  install --local-binary stage3/linux_init/helpers/a90_qrtr_probe
```

Static:

```bash
python3 -m py_compile scripts/revalidation/wifi_qrtr_socket_probe.py
git diff --check
```

Live no-start:

```bash
python3 scripts/revalidation/wifi_qrtr_socket_probe.py \
  --out-dir tmp/wifi/v250-qrtr-socket-probe
```

Acceptance:

- helper is static ARM64 and installed at `/cache/bin/a90_qrtr_probe`
- no daemon start, no QRTR send/connect, no Wi-Fi operation
- `cnss-daemon` remains absent after validation
- result is documented as pass/open-only/blocked with errno details
