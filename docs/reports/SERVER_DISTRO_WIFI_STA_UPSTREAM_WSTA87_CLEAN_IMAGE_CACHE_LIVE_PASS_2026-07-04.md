# WSTA87 Clean Image Cache Live Pass

- Date: 2026-07-04
- Scope: WSTA80 -> WSTA58 live measurement after WSTA84/WSTA86
- Resident: `A90 Linux init 0.11.153 (v3397-wsta-execute-gate-screen)`
- Private run: `workspace/private/runs/server-distro/wsta87-clean-image-cache-live-20260704T123816Z/`
- Decision: `wsta80-persistent-operator-execute-gate-live-pass`

## Summary

WSTA87 reran the WSTA84 clean-image cache measurement after WSTA86 fixed the
WSTA28 post-reboot public-off cleanup gate.  The fresh WSTA72 -> WSTA80
default-off operator packet/status chain passed, WSTA80 preflight reached
`READY_FOR_EXPLICIT_WSTA58_LIVE_GATE`, and the explicit WSTA80 live delegation
completed successfully.

```text
wsta80: wsta80-persistent-operator-execute-gate-live-pass
wsta58: wsta58-renewal-manual-stop-live-pass
initial WSTA55: wsta55-short-lived-public-proof-live-pass
renewal WSTA55: wsta55-short-lived-public-proof-live-pass
```

WSTA58 started at `20260704T123816Z` and ended at `20260704T125157Z`.

## Clean-Image Cache Proof

Both nested WSTA42 runs reached the new WSTA84 image-preparation path:

```text
initial WSTA42:
  decision=wsta42-native-uplink-dpublic-tunnel-pass
  remote_clean_image_enabled=true
  remote_clean_install_present=true
  legacy_work_install_present=false
  remote_work_restore_from_clean.restored=true

renewal WSTA42:
  decision=wsta42-native-uplink-dpublic-tunnel-pass
  remote_clean_image_enabled=true
  remote_clean_install_present=false
  legacy_work_install_present=false
  remote_work_restore_from_clean.restored=true
```

The initial leg installed the clean image once because the clean cache was
missing, then restored the working image from that clean image.  The renewal leg
found the clean image already present with the expected SHA, did not upload from
the host, and restored the working image by device-side copy from the clean
image.  Neither leg used the legacy direct work-image `install` path.

The restored working image SHA in both legs matched the expected staged rootfs
SHA:

```text
210fc1f92d4eb8bf291fb5b362154a29ca2b579a22a0a41cb1aaa89b5b6cb0dc
```

## WSTA58 Checks

Top-level WSTA58 checks:

```text
initial_wsta55_pass=true
renewal_wsta55_pass=true
manual_stop_cleanup_ok=true
manual_stop_public_state_off=true
wsta48_redaction_ok=true
wsta48_all_pass=true
public_url_value_logged=false
secret_values_logged=0
```

Both WSTA55 legs reported:

```text
public_smoke_ok=true
dpublic_cleanup_ok=true
native_uplink_profile_cleanup_ok=true
chroot_cleanup_ok=true
final_selftest_fail_zero=true
ttl_expiry_stops_public=true
wsta48_redaction_ok=true
wsta48_all_pass=true
```

## Post-Run Health

After WSTA87, a separate resident health check reported:

```text
version: 0.11.153 build=v3397-wsta-execute-gate-screen
status: BOOT OK shell 5.3s
selftest: pass=12 warn=1 fail=0
transport: serial/ncm/tcpctl ready
storage: sd mounted rw
autohud: running
```

## Safety

- No boot image was built or flashed for WSTA87.
- No forbidden partition was touched.
- No userdata format/populate or switch-root ran.
- The run intentionally performed the explicitly gated native warm reboots,
  Wi-Fi association/DHCP, short-lived public tunnel publishes, public smoke
  checks, TTL expiry proof, and final manual-stop cleanup.
- WSTA58 returned the public state to `PUBLIC_OFF`.
- Public URL values, confirm-token values, raw wireless credentials, network
  identifiers, routable addresses, gateway/DNS values, lease IDs, and device
  serials are not committed here.
- Private raw artifacts remain under `workspace/private/` only.

## Conclusion

WSTA84 is now live-proven: repeated WSTA42/WSTA55/WSTA58 runs no longer need to
re-upload the mutable work image from the host.  The first run may install or
refresh the clean cache, but subsequent legs can restore the working image from
the device-side clean image and avoid the legacy direct work-image upload path.
