# Server-Distro D-public No-Exposure Preflight

- Date: 2026-07-03
- Unit: D-public test preparation, no public exposure.
- Script: `workspace/public/src/scripts/server-distro/prepare_dpublic_preflight.py`
- Private run: `workspace/private/runs/server-distro/dpublic-preflight-20260703T145320Z`

## Verdict

D-public is **not live-ready yet**, but the no-exposure test preparation is now
mechanically checkable.

The preflight confirms the D4 foundation and host tunnel client are present, and it
records the remaining live-publish gate without starting `cloudflared`, publishing a
URL, flashing, rebooting, or writing the device.

## Evidence

The preflight was run twice:

```text
python3 workspace/public/src/scripts/server-distro/prepare_dpublic_preflight.py
python3 workspace/public/src/scripts/server-distro/prepare_dpublic_preflight.py --device-check
```

Observed result from the read-only device run:

```text
decision=dpublic-preflight-complete-no-public-exposure
d4_foundation_docs_present=true
host_cloudflared_ready=true
host_cloudflared_sha256=59816ce9b16db71f5bc2a86d59b3632a96c8c3ee934bde2bc8641ee83a6070eb
device_check_performed=true
device_final_v2321=true
device_final_selftest_fail0=true
device_tunnel_artifacts_present=false
live_publish_ready=false
live_publish_performed=false
public_exposure_performed=false
device_write_performed=false
operator_gate=D-PUBLIC-LIVE-PUBLISH
```

The staged host artifact is the D0 `cloudflared` linux-arm64 binary:

```text
workspace/private/builds/server-distro/tunnel/cloudflared-linux-arm64
size=36980327
sha256=59816ce9b16db71f5bc2a86d59b3632a96c8c3ee934bde2bc8641ee83a6070eb
```

## Live-Test Gap

The following are still required before the first public tunnel exposure:

1. Choose the live exposure mode: named Cloudflare Tunnel token/hostname, or an
   explicitly approved quick tunnel.
2. Put any tunnel credentials under `workspace/private/secrets/`, or explicitly choose
   quick-tunnel mode for the live test.
3. Stage `cloudflared` into the userdata Debian appliance with target mode `0755`,
   without starting it.
4. Stage a minimal local HTTP smoke service bound to loopback/LAN inside the appliance.
5. Boot a D4-capable appliance image and prove outbound internet from the appliance.
6. Only then run the public publish command after the operator gives the literal gate
   `D-PUBLIC-LIVE-PUBLISH`.

## Safety

- No public tunnel or external URL was opened.
- No device write was performed.
- No flash or reboot was performed.
- The device remained on v2321 with `selftest fail=0`.
- The first live D-public exposure remains a separate operator-confirm gate.
