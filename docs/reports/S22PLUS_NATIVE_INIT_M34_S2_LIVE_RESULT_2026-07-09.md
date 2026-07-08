# S22+ M34 S2 Live Result

Date: 2026-07-09 KST / 2026-07-08 UTC

Result: PASS for the S2 discriminator. The S1-proven stock configfs setup plus
the two off-stock pullup knobs, `max_speed=high-speed` and `usb_role=device`,
survived the full observation window without final UDC bind. Rollback completed
cleanly. No active live authorization remains.

## Scope

This was the one-shot M34 S2 boot-only live gate for:

- target: `SM-S906N/g0q/S906NKSS7FYG8`
- helper: `workspace/public/src/scripts/revalidation/s22plus_m34_s2_runtime_gadget_live_gate.py`
- run dir: `workspace/private/runs/s22plus_m34_s2_runtime_gadget_live_gate_20260708T194507Z`
- timeline: `workspace/private/runs/s22plus_m34_s2_runtime_gadget_live_gate_20260708T194507Z/timeline.json`

Candidate pins:

- AP.tar.md5 SHA256: `d235e6fd7c77c9fc2b63bd7280dcbf430783c9b62b5f361f43441c24687c38b3`
- padded `boot.img` SHA256: `f8838867e0b0fab5ffe5aa8717565d9304f635ef04487596a0baeb03b2dd7a70`
- direct `/init` SHA256: `fba33555bcc73d834a7dbfe87dc5e6fe3b622184d163ae72d478e18a0ce653b8`
- template source SHA256: `ac20dcf724cf6864540d65958332d561d45409e7e85785a8c014882b37e29193`
- module-list SHA256: `2291dc1c72add131c42d0b4ed6649880c20316d0598e0a2af942cc774949062c`
- known-booting Magisk boot base SHA256: `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

The AP contained exactly one tar member, `boot.img.lz4`.

## Candidate Contract

M34 S2 was deliberately limited to:

- stock-ordered configfs gadget/function/config
- `UDC=none`
- stock IDs `0x04E8:0x6860`
- link `functions/ss_acm.0`
- write `g1/max_speed=high-speed`
- write `usb_role=device`
- no final UDC bind
- no `UDC=a600000.dwc3`

It also had no reboot syscall, no Download beacon, no Android/Magisk handoff,
no persistent partition mount, no block write, no boot-ramdisk module binary
injection, and no non-boot partition payload.

## Timeline

The run produced the required single `events` timeline schema.

- `live_session_start`: 2026-07-08T19:45:18.117099Z
- `candidate_flash_start`: 2026-07-08T19:45:28.898014Z
- `candidate_flash_done`: 2026-07-08T19:45:30.367960Z
- `candidate_boot_ready`: 2026-07-08T19:45:31.633168Z
- `rollback_flash_start`: 2026-07-08T19:47:39.985608Z
- `rollback_flash_done`: 2026-07-08T19:47:41.349438Z
- `rollback_boot_ready`: 2026-07-08T19:48:26.461246Z
- `live_session_end`: 2026-07-08T19:48:26.730409Z

The helper also recorded `manual_after_survival_*` aliases for the manual
Download rollback path.

## Live Evidence

Preflight:

- Android ADB online as `RFCT519XWGK`
- `model=SM-S906N`
- `device=g0q`
- `bootloader=S906NKSS7FYG8`
- `incremental=S906NKSS7FYG8`
- `vbstate=orange`
- `boot_completed=1`
- Magisk root present: `uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0`
- current boot hash matched the known-booting Magisk boot:
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

Candidate flash:

- Download endpoint selected: `/dev/bus/usb/002/078`
- candidate Odin return code: `0`
- original Download endpoint disconnected after flash
- host observation started at `2026-07-08T19:45:31Z`

Observation:

- observation window: 90 seconds
- 18 snapshots taken about every 5 seconds
- no ADB endpoint returned during the window
- no Odin endpoint returned during the window
- operator observation during window: no bootloop
- `m34_s2_survival_window_pass=1`
- `m34_s2_result=survived-observation-window-manual-download-required`

Rollback:

- the operator observed RDX while entering manual recovery
- normal Download endpoint then appeared as `/dev/bus/usb/002/079`
- Magisk boot rollback Odin return code: `0`
- Android returned and reached boot complete
- restored boot hash matched:
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

Post-run ADB recheck confirmed:

- boot hash:
  `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`
- root: `uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0`
- `sys.boot_completed=1`
- `init.svc.bootanim=stopped`
- `ro.boot.verifiedbootstate=orange`
- `ro.boot.bootloader=S906NKSS7FYG8`
- `ro.build.PDA=S906NKSS7FYG8`

## Retained Evidence

Post-rollback retained evidence:

- pstore files: `[]`
- pstore marker found: `0`
- `/proc/last_kmsg` read return code: `0`
- `/proc/last_kmsg` bytes: `2097136`
- `/proc/last_kmsg` M34 S2 marker found: `0`
- overall retained marker found: `0`

Marker absence is not a failure for S2 because the positive proof is survival
past the reset window plus clean rollback.

## Interpretation

S2 removes these from the likely reset boundary:

- stock configfs gadget/function/config creation
- `UDC=none`
- stock IDs `0x04E8:0x6860`
- `functions/ss_acm.0` link
- `max_speed=high-speed`
- `usb_role=device`

The remaining isolated runtime step is now the final UDC bind/pullup:

1. S3: add only `UDC=a600000.dwc3` after the S2-proven setup and observe.
2. If S3 resets, the failure boundary is final pullup/controller connect.
3. If S3 survives, the original M32 failure likely involves post-pullup host
   interaction, tty endpoint behavior, or later runtime work not yet isolated.

S3 is the next high-information unit, but it is the first actual UDC pullup and
needs a fresh SHA-pinned `AGENTS.md` exception before live.

## Authorization State

The M34 S2 one-shot exception is consumed and retired in `AGENTS.md`. Its live
and rollback ack tokens are omitted as active authorization. No S2 repeat, S3,
final pullup, DTBO, vendor_boot, recovery, vbmeta, non-boot flash, raw host
`dd`, fastboot, EUD write, RDX PC dump retrieval, or A90 action is authorized
by this result.

