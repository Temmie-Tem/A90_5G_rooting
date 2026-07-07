# S22+ Ramoops DTBO + M22 Sysrq Panic AGENTS Exception Draft (2026-07-08)

This is an inert draft. It does not authorize live work while it remains in
this document. Copy it into `AGENTS.md` only after explicit operator
authorization for the non-boot `dtbo` write, the M22 boot candidate flash, the
intentional kernel crash via sysrq-trigger-c, and the attended
rollback/restore flow.

## Copy Block

```text
   **Narrow operator-authorized exception (2026-07-08, S22+ ramoops DTBO + M22 sysrq-panic retained-console only):**
   after the DTBO status-only live gate proved that the patched DTBO enables
   live `/proc/device-tree/reserved-memory/ramoops_region/status=okay`, and
   after the DTBO+M13 positive-control consumed gate proved no retained passive
   M13 marker, Codex may perform one bounded attended S22+ ramoops DTBO + M22
   sysrq-panic retained-console run on the Samsung S22+ `SM-S906N`/`g0q`
   `S906NKSS7FYG8` using only the checked helper
   `workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py`
   and live ack token `S22PLUS-RAMOOPS-DTBO-M22-SYSRQ-PANIC-LIVE-GATE`.
   This exception authorizes exactly two partition classes and no others:
   first flash the patched `dtbo` AP.tar.md5 SHA256
   `4f82663a7c2175a41760ec099c0f662dd04b8932a5ae82ba46b3ecb401a14a00`,
   require Android/root to return, require current DTBO SHA256
   `1c90b54577cbb42e029818a0c4248e85ec3a0e40903b0887648d6556355c85ab`,
   require live `ramoops_region/status=okay`, then flash the M22 boot
   retained-console AP.tar.md5 SHA256
   `77c17e9d3fb62319823499e0e8e7fcd485cd180dd730e40d9c2a8112308c4852`.
   M22 is an intentional kernel crash positive-control: direct PID1 writes
   `S22_NATIVE_INIT_M22_KMSG_SYSRQ_PANIC` to `/dev/kmsg`, enables sysrq, writes
   `c` to `/proc/sysrq-trigger` (`sysrq-trigger-c`), and falls back to
   `reboot("download")` only if sysrq returns. After the M22 observation window,
   restore the boot partition using the pinned Magisk boot rollback AP.tar.md5
   SHA256 `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`
   with stock boot fallback AP.tar.md5 SHA256
   `1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e`,
   collect `pstore` and retained last_kmsg, then restore stock DTBO using the
   pinned stock DTBO rollback AP.tar.md5 SHA256
   `6f397421bee84f4ea0c80a8519be0f6f6af84119794970e8a1faaa05f261caaa`.
   The stock raw DTBO SHA256 must be
   `97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c`,
   the M22 padded boot.img SHA256 must be
   `c79bbe1fb1cee7d7e3c70ff4c249d6e0359760e203cc0bebb1c71d6cc0518802`,
   the M22 base known-booting Magisk boot SHA256 must be
   `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`,
   the M22 kernel SHA256 must be
   `bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff`,
   the M22 `/init` SHA256 must be
   `2b711b0fccf6cdd9b4c9beb5ba2f1a095d4e873b42bd03a02eb4655106873831`,
   and the M22 source SHA256 must be
   `a48818067b6b79578bdc6cd0e327d9e7c316b10bca1be7d838605c7d7e0e6444`.
   The M22 label is `M22_KMSG_SYSRQ_PANIC`. The DTBO APs must contain exactly
   one tar member, `dtbo.img.lz4`; the M22, Magisk rollback, and stock boot
   fallback APs must contain exactly one tar member, `boot.img.lz4`. If M22
   exposes no rollback transport, rollback requires operator manual
   download-mode entry and the helper mode
   `--rollback-boot-from-download --ack S22PLUS-RAMOOPS-M22-ROLLBACK-BOOT-FROM-DOWNLOAD`.
   Stock DTBO restore requires either
   `--restore-dtbo-from-android --ack S22PLUS-RAMOOPS-RESTORE-STOCK-DTBO` or
   `--restore-dtbo-from-download --ack S22PLUS-RAMOOPS-RESTORE-STOCK-DTBO`.
   The capture goal is M22 retained-console evidence with the live ramoops node
   enabled through DTBO. This path is a DTBO successor to the retired
   vendor_boot-only route: no vendor_boot write is authorized here. This
   exception does not authorize writing or flashing recovery, vendor_boot,
   vbmeta, vbmeta_system, BL, CP, CSC, super, userdata, persist, EFS, sec_efs,
   RPMB, keymaster, modem, bootloader, raw host `dd`, fastboot, Magisk modules,
   multidisabler, format data, M13/M15/M18/M21/QMP candidates, additional boot
   candidates, additional DTBO candidates, kernel rebuilds, or any A90 action.
```

## Gate Marker Coverage

The draft intentionally includes every authorization marker required by
`s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py`:

```text
S22+ ramoops DTBO + M22 sysrq-panic retained-console
workspace/public/src/scripts/revalidation/s22plus_ramoops_dtbo_m22_sysrq_panic_live_gate.py
4f82663a7c2175a41760ec099c0f662dd04b8932a5ae82ba46b3ecb401a14a00
6f397421bee84f4ea0c80a8519be0f6f6af84119794970e8a1faaa05f261caaa
1c90b54577cbb42e029818a0c4248e85ec3a0e40903b0887648d6556355c85ab
97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c
77c17e9d3fb62319823499e0e8e7fcd485cd180dd730e40d9c2a8112308c4852
c79bbe1fb1cee7d7e3c70ff4c249d6e0359760e203cc0bebb1c71d6cc0518802
2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
2b711b0fccf6cdd9b4c9beb5ba2f1a095d4e873b42bd03a02eb4655106873831
a48818067b6b79578bdc6cd0e327d9e7c316b10bca1be7d838605c7d7e0e6444
d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
S22PLUS-RAMOOPS-DTBO-M22-SYSRQ-PANIC-LIVE-GATE
S22PLUS-RAMOOPS-M22-ROLLBACK-BOOT-FROM-DOWNLOAD
S22PLUS-RAMOOPS-RESTORE-STOCK-DTBO
dtbo.img.lz4
boot.img.lz4
ramoops_region/status=okay
M22_KMSG_SYSRQ_PANIC
S22_NATIVE_INIT_M22_KMSG_SYSRQ_PANIC
intentional kernel crash
sysrq-trigger-c
restore stock DTBO
manual download-mode
no vendor_boot
```
