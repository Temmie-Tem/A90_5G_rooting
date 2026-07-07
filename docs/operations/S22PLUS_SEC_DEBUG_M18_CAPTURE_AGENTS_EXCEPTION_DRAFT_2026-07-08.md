# S22+ Sec Debug MID M18 Capture AGENTS Exception Draft (2026-07-08)

This is an inert draft. It does not authorize live work while it remains in this
document. Copy it into `AGENTS.md` only after explicit operator authorization
for the boot-only M18 candidate flash and attended rollback/capture flow.

## Copy Block

```text
   **Narrow operator-authorized exception (2026-07-08, S22+ sec_debug MID M18 capture boot-only):**
   after the S22+ sec_debug/MID sysrq positive control proved retained
   `/proc/last_kmsg` kernel panic evidence, Codex may perform one bounded
   attended S22+ sec_debug MID M18 capture boot-only run on the Samsung S22+
   `SM-S906N`/`g0q` `S906NKSS7FYG8` using only the checked helper
   `workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py`
   and live ack token `S22PLUS-SECDEBUG-M18-CAPTURE-LIVE-GATE`.
   The operator must keep Samsung SysDump DEBUG LEVEL at MID (`debug_level=MID`)
   and pass confirmation token `DEBUG_LEVEL_MID_SET_BY_OPERATOR`; the helper
   must verify Android/root, current boot hash, and sec_debug MID state before
   live flashing. This exception authorizes exactly one boot partition candidate
   flash using the M18 AP.tar.md5 SHA256
   `9382f91bf2cd3235410368ca08208b9343d8584da48c29b25c46a931b1f42805`.
   The M18 padded boot.img SHA256 must be
   `a99a09fa062d1aaa848a41037c649a43abc983f177714dfc24c39d0df4d84083`,
   the known-booting base Magisk boot SHA256 must be
   `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`,
   and the M18 retained marker is `S22_NATIVE_INIT_USB_ACM_M18_FULL`.
   After observation, restore the boot partition using the pinned Magisk boot
   rollback AP.tar.md5 SHA256
   `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`
   with stock boot fallback AP.tar.md5 SHA256
   `1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e`.
   The M18, Magisk rollback, and stock boot fallback APs must contain exactly
   one tar member, `boot.img.lz4`. If M18 leaves the phone in a panic/upload
   screen or exposes no rollback transport, rollback requires operator manual
   download-mode entry and the helper mode
   `--rollback-boot-from-download --ack S22PLUS-SECDEBUG-M18-ROLLBACK-BOOT-FROM-DOWNLOAD`.
   The capture goal is to collect Samsung sec_debug retained evidence from
   `/proc/last_kmsg` after boot rollback. This is boot partition only and no
   DTBO, no vendor_boot, no vbmeta, no recovery, no BL, no CP, no CSC, no super,
   no userdata, no persist, no EFS, no sec_efs, no RPMB, no keymaster, no modem,
   no bootloader, no raw host `dd`, no fastboot, no Magisk module, no
   multidisabler, no format data, no additional boot candidate, no additional
   debug-level panic, no kernel rebuild, and no A90 action is authorized.
```

## Gate Marker Coverage

The draft intentionally includes every authorization marker required by
`s22plus_sec_debug_m18_capture_live_gate.py`:

```text
S22+ sec_debug MID M18 capture boot-only
workspace/public/src/scripts/revalidation/s22plus_sec_debug_m18_capture_live_gate.py
SM-S906N/g0q/S906NKSS7FYG8
9382f91bf2cd3235410368ca08208b9343d8584da48c29b25c46a931b1f42805
a99a09fa062d1aaa848a41037c649a43abc983f177714dfc24c39d0df4d84083
2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
S22_NATIVE_INIT_USB_ACM_M18_FULL
d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
S22PLUS-SECDEBUG-M18-CAPTURE-LIVE-GATE
S22PLUS-SECDEBUG-M18-ROLLBACK-BOOT-FROM-DOWNLOAD
DEBUG_LEVEL_MID_SET_BY_OPERATOR
debug_level=MID
sec_debug
/proc/last_kmsg
boot.img.lz4
boot partition only
manual download-mode
no DTBO
no vendor_boot
no vbmeta
```
