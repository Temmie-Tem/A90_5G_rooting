# Server-Distro D-public Live Publish

- Date: 2026-07-04 KST
- Unit: D-public live gate, operator-confirmed with `D-PUBLIC-LIVE-PUBLISH`.
- Private run: `workspace/private/runs/server-distro/dpublic-live-20260703T150145Z`
- Public URL: redacted from committed report; stored privately in the run directory.

## Verdict

D-public live publish **passed**.

The userdata Debian appliance served a loopback-only HTTP smoke endpoint, `cloudflared`
created a quick Tunnel, and a host-side public HTTPS request through the Cloudflare edge
returned the expected device marker.

## Live Evidence

Device/appliance state:

```text
pid1_comm=init
debian_version=12.14
cloudflared_version=2026.6.1
cloudflared_sha256=59816ce9b16db71f5bc2a86d59b3632a96c8c3ee934bde2bc8641ee83a6070eb
smoke_httpd_sha256=84c2124e9bd158db243d38c218edaf018ce9c7a377d5e4101ce397f4e593a3c9
smoke_get_sha256=e19705456003f4e2a29590c077c078d960a062ab9cb514c6004f415c649f3ab2
smoke_bind=127.0.0.1:8080
```

The device-local smoke probe returned:

```text
A90_DPUBLIC_SMOKE_OK
service=loopback-http
public_exposure=outbound-tunnel-only
```

The public HTTPS request to the quick Tunnel URL returned the same marker:

```text
A90_DPUBLIC_SMOKE_OK
service=loopback-http
public_exposure=outbound-tunnel-only
```

`cloudflared` connectivity prechecks passed for DNS, UDP/QUIC, TCP/HTTP2, and Cloudflare API reachability.

## Corrections During Live Gate

- The first quick Tunnel attempt created a URL but exited immediately because the appliance lacked
  `localhost` in `/etc/hosts`, causing the default metrics listener lookup to fail. Fixed by staging
  `/etc/hosts` and restarting `cloudflared` with `--metrics 127.0.0.1:0`.
- The appliance clock initially carried the old 2018 timestamp, causing TLS certificate validation to
  fail before any public URL was usable. Fixed by setting the appliance UTC time from the host.
- The D4D proof firstboot had a mandatory 120 second autoreboot. For D-public, `/etc/a90-d3-firstboot`
  was backed up and replaced with a D-public profile that disables proof-only autoreboot, brings up
  `lo` and `ncm0`, installs default route/DNS, starts key-only dropbear, and starts the smoke server.

## Safety Boundary

- Public exposure was limited to a loopback-only smoke service through an outbound Cloudflare quick Tunnel.
- No inbound port was opened on the device.
- No forbidden partition was touched.
- No tunnel credentials were committed or used; this was an accountless quick Tunnel.
- The public URL is intentionally not committed.
- The live tunnel was left running for operator inspection at report time.

## Cleanup

To stop the public exposure:

```text
ssh -i workspace/private/run/d4d-handoff-20260703T132358Z/d4d_ssh_key_ed25519 \
  -p 2222 root@192.168.7.2 'kill $(cat /run/a90-dpublic/cloudflared-live.pid)'
```

After inspection, roll boot back to v2321 through `native_init_flash.py` if a clean resident native-init
baseline is desired immediately.
