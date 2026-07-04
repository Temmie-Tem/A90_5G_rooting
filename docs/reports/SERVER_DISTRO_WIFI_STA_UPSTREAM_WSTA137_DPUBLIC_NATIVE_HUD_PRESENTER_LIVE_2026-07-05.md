# WSTA137 D-public Native HUD Presenter Live Proof

- Status: `PASS`
- Timestamp: `2026-07-05 08:49 KST`
- Candidate: `A90 Linux init 0.11.154 (v3398-dpublic-hud-presenter)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v3398_dpublic_hud_presenter.img`
- Boot SHA256: `b18be6a39eb41fb71a5256db3b23d5c648631fb164061b98b35a35ffba9f3a0c`
- Run dir: `workspace/private/runs/server-distro/wsta137-dpublic-native-presenter-live-20260705T0835KST`

## Summary

WSTA137 live-gated the WSTA136 native/root-owned HUD presenter. The device first
returned from the WSTA135 Debian userdata appliance to native V3397, then attempted a
no-flash hot-reload of the V3398 init ELF. Hot-reload reached the V3398 banner and
refreshed selftest/guard, but USB re-enumerated and the device returned to the V3397
boot image. V3397 health was clean afterward, so the live gate pivoted to the checked
flash path.

V3398 was flashed only through `native_init_flash.py --from-native` with the exact
pinned SHA. Recovery/TWRP came up, the pushed remote image SHA matched, the boot
readback prefix SHA matched, V3398 booted, and post-boot `version`/`status`/`selftest`
were clean.

## Evidence

- Rollback images were present with expected hashes:
  - v2321: `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`
  - v2237: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`
  - v48: `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`
- TWRP artifacts were present under `workspace/private/inputs/firmware/twrp/`.
- Checked flash total elapsed: `65.755s`.
- Candidate boot health:
  - `version: 0.11.154 build=v3398-dpublic-hud-presenter`
  - `boot: BOOT OK shell 5.1s`
  - `selftest: pass=12 warn=1 fail=0`
  - `transport.tcpctl=ready`
  - SD runtime remained mounted rw.

## Presenter Proof

Fresh intent validate pass:

- path: `/tmp/a90-wsta137-hud-intent.json`
- schema: `a90-dpublic-hud-intent-v1`
- sequence: `13701`
- age: `653ms`
- markers:
  - `policy.forbidden_fields=reject`
  - `policy.unknown_fields=reject`
  - `policy.stale_after_ms=2000`
  - `presenter.owner=native-init-root`
  - `presenter.debian_direct_kms=0`
  - `present.skipped=validate-only`

Fresh intent present pass:

- path: `/tmp/a90-wsta137-hud-intent-present.json`
- sequence: `13702`
- age: `556ms`
- `present.begin_frame_rc=0`
- `dpublic-hud-presenter: presented framebuffer 1080x2400 on crtc=133`
- `present.rc=0`
- `present.done=1`

Reject-path live checks also passed:

- forbidden `command` field rejected with `intent.reject=forbidden-key key=command` and `rc=-1`.
- stale `monotonic_ms=1` intent rejected with `intent.reject=stale ... stale_after_ms=2000` and `rc=-110`.

## Final State

The device is left resident on V3398. Post-proof cleanup removed the staged hot-reload
ELF from SD flash-staging. Final health stayed clean:

- `selftest: pass=12 warn=1 fail=0`
- `status`: `A90 Linux init 0.11.154 (v3398-dpublic-hud-presenter)`
- `transport.serial=ready`
- `transport.tcpctl=ready`
- `autohud=stopped` after the presenter took KMS ownership.

No Wi-Fi connect, DHCP, public tunnel, public smoke, packet-filter mutation, Debian
switch-root, or Debian direct DRM/KMS presenter ran in this WSTA137 proof.

## Next

WSTA138 should fold this live presenter proof into the operator/server status and then
decide the long-running handoff model: either keep the native presenter as an explicit
operator command, or design a bounded native presenter service that survives the Debian
handoff while Debian remains only the intent producer.
