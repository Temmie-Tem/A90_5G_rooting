# A90 Phone Wi-Fi Transfer Server

Date: `2026-06-09`

This runbook describes the phone-side test server used for native-init Wi-Fi
data-path validation. The goal is to avoid manual Termux setup while keeping
the A90 test bounded and reproducible.

## Scope

Use this only on a phone you own or are explicitly allowed to use.

The server supports:

- HTTP download from phone to A90;
- raw TCP upload from A90 to phone;
- generated test files with SHA256 manifests;
- upload SHA256 logging on the phone.

The server does not require Wi-Fi credentials and does not expose private A90
run artifacts by itself.

## Network Setup

Required:

- Phone and A90 are connected to the same router Wi-Fi/LAN.
- The router does not block client-to-client traffic.
- The phone is not on a guest network with AP/client isolation.
- The phone keeps Termux awake while the test runs.

Same band is not mandatory, but using the same SSID/band reduces variables.

## Termux One-Shot Server

Copy this repository script to the phone or paste it into Termux, then run:

```sh
bash a90_termux_wifi_lab.sh serve
```

If a previous server is still holding port `8080` or `9001`, restart it:

```sh
bash a90_termux_wifi_lab.sh restart
```

or stop it explicitly:

```sh
bash a90_termux_wifi_lab.sh stop
```

Script path in this repository:

```sh
workspace/public/src/scripts/phone/a90_termux_wifi_lab.sh
```

Default behavior:

- installs/checks Termux packages when `pkg` is available:
  `python`, `coreutils`, `iproute2`;
- requests `termux-wake-lock` when available;
- creates `$HOME/a90-wifi-lab`;
- generates `1MiB`, `8MiB`, and `32MiB` files;
- starts an HTTP server on port `8080`;
- starts a raw TCP upload receiver on port `9001`;
- exposes upload hash metadata over HTTP;
- prints the phone IPv4 candidates and A90 example commands.

On some Android/Termux builds, `ip -o -4 addr show` fails with:

```txt
Cannot bind netlink socket: Permission denied
```

That does not mean the server failed. It only means Android blocked that IP
enumeration path. The script also tries route/property/proc fallbacks. If it
still cannot print an IP, read it from Android:

```txt
Settings -> Wi-Fi -> current network -> Network details -> IP address
```

or use the router DHCP client list.

Useful overrides:

```sh
A90_WIFI_SIZES_MIB="1 8 64" bash a90_termux_wifi_lab.sh serve
A90_WIFI_HTTP_PORT=18080 A90_WIFI_UPLOAD_PORT=19001 bash a90_termux_wifi_lab.sh serve
A90_WIFI_LAB_INSTALL=0 bash a90_termux_wifi_lab.sh serve-no-install
```

Cleanup:

```sh
bash a90_termux_wifi_lab.sh stop
bash a90_termux_wifi_lab.sh clean-uploads
bash a90_termux_wifi_lab.sh clean-all
```

## A90 Test Shape

After A90 connects to the same Wi-Fi and DHCP succeeds, use the phone IP printed
by Termux.

Download example:

```sh
wget http://<PHONE_IP>:8080/test-32MiB.bin -O /cache/a90-wifi/test-32MiB.bin
sha256sum /cache/a90-wifi/test-32MiB.bin
```

Compare the digest with:

```sh
http://<PHONE_IP>:8080/SHA256SUMS.txt
```

Upload example:

```sh
cat /cache/a90-wifi/test-32MiB.bin | nc <PHONE_IP> 9001
```

The phone writes received uploads under:

```sh
$HOME/a90-wifi-lab/uploads/
```

Each upload gets a `.sha256` sidecar and an entry in:

```sh
$HOME/a90-wifi-lab/uploads/UPLOADS.jsonl
```

The same metadata is available over HTTP, so the host can collect upload hashes
without reading the phone screen:

```sh
curl http://<PHONE_IP>:8080/status.json
curl http://<PHONE_IP>:8080/uploads/latest.json
curl http://<PHONE_IP>:8080/uploads/UPLOADS.jsonl
```

The intended automated check is:

- record A90 source `sha256sum` before upload;
- send the file to `<PHONE_IP>:9001`;
- fetch `http://<PHONE_IP>:8080/uploads/latest.json`;
- compare `latest_upload.sha256` with the A90 source digest.

## Baseline Pass Criteria

For a bounded Wi-Fi data-path test:

- A90 `wifi connect` reaches carrier.
- A90 `wifi dhcp` succeeds.
- Gateway ping passes.
- HTTP download completes.
- Download SHA256 matches the phone manifest.
- Raw TCP upload completes.
- Upload SHA256 matches the file sent by A90.
- A90 `wifi cleanup` succeeds when cleanup is in scope.
- Final `selftest fail=0`.

## Failure Interpretation

- A90 cannot reach phone IP, but internet works:
  router/client isolation is likely.
- Download works, upload fails:
  phone upload receiver port/firewall/app sleep is likely.
- SHA mismatch:
  treat as a real data-path failure until reproduced.
- Server stalls after several minutes:
  check Android battery optimization and Termux wake lock.
- `Address already in use`:
  an old server is still running; use `bash a90_termux_wifi_lab.sh restart` or
  set alternate ports with `A90_WIFI_HTTP_PORT` and `A90_WIFI_UPLOAD_PORT`.
- `Permission denied: /proc/net/fib_trie`:
  older script revision; refresh the script. Current revisions ignore that
  Android permission restriction and continue with other IP detection methods.
