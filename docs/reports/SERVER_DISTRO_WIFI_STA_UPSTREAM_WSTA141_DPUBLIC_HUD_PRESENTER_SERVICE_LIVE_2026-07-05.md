# WSTA141 D-public HUD Presenter Service Live Gate

Date: 2026-07-05 09:34 KST

## Verdict

WSTA141 live-gated the V3399 durable native D-public HUD presenter service.
The checked flash path wrote only the boot partition, V3399 booted cleanly, and
`dpublic-hud-presenter-service start|status|stop` worked on-device without
`switch_root`.

The live gate also exposed one follow-up defect: after a fresh intent becomes
stale, the service currently logs the same stale reject every `100ms` while it
keeps polling the unchanged file.  The service was stopped cleanly, final health
remained clean, and this should be fixed before the Debian handoff survival
unit.

## Scope

- Candidate: `A90 Linux init 0.11.155 (v3399-dpublic-hud-presenter-service)`
- Boot image:
  `workspace/private/inputs/boot_images/boot_linux_v3399_dpublic_hud_presenter_service.img`
- Boot SHA256:
  `cd59b7a5eecc7dda464374c7fb412a60eeda7e2579ef7e2abe26d856277ff9dd`
- Run dir:
  `workspace/private/runs/server-distro/wsta141-dpublic-hud-presenter-service-live-20260705T0930KST`

No Wi-Fi association, DHCP, public tunnel/smoke, packet-filter mutation,
userdata mutation, Debian `switch_root`, forbidden partition write, PMIC,
regulator, GDSC, GPIO, backlight, or panel re-init action was performed.

## Flash And Health

Preconditions:

- v2321 rollback image SHA matched
  `ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb`.
- v2237 fallback image SHA matched
  `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
- v48 fallback image SHA matched
  `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`.
- TWRP artifacts were present under `workspace/private/inputs/firmware/twrp/`.
- Resident V3398 health was clean before flashing:
  `BOOT OK`, `selftest fail=0`, serial/NCM/tcpctl ready.

Checked flash:

- `native_init_flash.py --from-native` verified Android boot magic, local marker
  `0.11.155`, and local SHA.
- Recovery ADB came up before any boot write.
- Remote pushed image SHA matched the pinned local SHA.
- Boot prefix readback SHA matched the pinned local SHA.
- The helper's first post-reboot serial verify timed out at `30s` after the
  device re-enumerated; a follow-up checked `--verify-only` run with `60s`
  bridge timeout passed immediately.

Post-boot health:

- `version`: `0.11.155`, build `v3399-dpublic-hud-presenter-service`.
- `status`: `BOOT OK shell 5.1s`.
- `selftest`: `pass=12 warn=1 fail=0`.
- `transport.serial=ready`, `transport.ncm=ready`, `transport.tcpctl=ready`.
- Final health after service stop remained `selftest fail=0`.

## Service Proof

The menu was hidden before running the display/dangerous command.  Service start
then returned:

- `A90WSTA140 service=native-dpublic-hud-presenter`
- `A90WSTA140 owner=native-init-root`
- `A90WSTA140 survives_handoff=1`
- `A90WSTA140 start.run_dir=/run/a90-dpublic owner=root:a90hud mode=1770 rc=0`
- `A90WSTA140 start.autohud_stop_rc=0`
- `A90WSTA140 start.pid=651`
- `A90WSTA140 start.process_model=forked-native-child-survives-switch-root`
- `A90WSTA140 start.done=1`

Service status after start returned:

- `A90WSTA140 status.state=running`
- `A90WSTA140 status.pid=651`
- `A90WSTA140 status.drm_fd=1`
- `A90WSTA140 status.debian_direct_kms=0`

Runtime files showed `/run/a90-dpublic` as `root:3904` with sticky mode
`1770`, pidfile `651`, and status state `running`.

Fresh intent proof:

- A fresh `/run/a90-dpublic/hud-intent.json` with sequence `14101` was written.
- The presenter child printed
  `dpublic-hud-presenter-service: presented framebuffer 1080x2400 on crtc=133`.
- `/run/a90-dpublic/hud-presenter.status` reported:
  - `last_sequence=14101`
  - `present_rc=0`
  - `process_model=forked-native-child-survives-switch-root`
- Service status after intent still reported `status.drm_fd=1` and
  `status.debian_direct_kms=0`.

Stop proof:

- `dpublic-hud-presenter-service stop --pid-file ... --release-drm` returned
  `A90WSTA140 stop.done=1`.
- Follow-up status returned `A90WSTA140 status.state=stopped rc=-2`.
- Final `selftest` and `status` stayed clean.

## Follow-up

WSTA142 should fix the stale-intent poll loop so a previously consumed intent
does not emit repeated stale reject logs every poll.  The intended behavior is
latest-sequence de-duplication before noisy validation, or equivalent
per-file/sequence error throttling, while preserving fail-closed rejection for
new stale/forbidden/unknown intent content.
