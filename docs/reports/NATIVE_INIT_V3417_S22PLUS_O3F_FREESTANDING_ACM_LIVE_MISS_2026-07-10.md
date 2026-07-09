# V3417 S22+ O3F Freestanding ACM Live Miss

## Verdict

`CANDIDATE PROOF FAIL; ROLLBACK PASS; PHASE UNVERIFIABLE`.

The exact O3F boot-only candidate transferred and the original Odin endpoint
disconnected. The operator observed no bootloop, but no candidate USB device
enumerated in the 120-second window. There was therefore no O3F tty, framed
roundtrip, or status proof. The one-shot exception is consumed and must not be
reused.

The mandatory attended rollback restored the exact Magisk boot baseline.
Android, root, boot hash, and stability are healthy.

## Exact Run

```text
workspace/private/runs/s22plus_o3f_freestanding_acm_live_gate_20260709T210930Z
candidate_ap_sha256=73d0a03c066b236e8ebea07c03affda4c5b94633cc34dd2ca413ce8697eb8725
candidate_boot_sha256=c09ef0e8cbcb3b53c8ba22d76fce47cc03607ad416b0b8f2faf2adf1f18e9f70
result=candidate-proof-failed
rc=9
error=O3 ACM tty with exact serial did not appear
roundtrip=null
status=null
tty_path=null
```

Result evidence hashes:

```text
result_json_sha256=4234a06f572a6385f7032e099dca7f6e9aaeabda26b0a50b38e78a6935a14df0
timeline_json_sha256=f8ba47eff55d15044f52f65554a5e6c8100b91243925a15354459e2488bc489f
last_kmsg_sha256=b02d2c13d438ba5259bd5fa5ba9cc8c4acd18b14ba8645b6dd6a0d2dd22139b4
```

## Timeline

```text
live_session_start    2026-07-09T21:09:41.278639Z
candidate_flash_start 2026-07-09T21:09:52.238076Z
candidate_flash_done  2026-07-09T21:09:53.761948Z
rollback_flash_start  2026-07-09T21:12:40.382024Z
rollback_flash_done   2026-07-09T21:12:41.735581Z
rollback_boot_ready   2026-07-09T21:13:20.917008Z
live_session_end      2026-07-09T21:13:32.036375Z
```

`candidate_boot_ready` is absent by design because exact serial
`S22O3FACM01` never appeared. The canonical timeline is therefore honestly
incomplete rather than backfilled from survival.

## Host USB Evidence

The original Android USB disconnected at 21:09:43Z. Candidate Download mode
appeared as Samsung `04e8:685d`, and disconnected at 21:09:54Z after the Odin
transfer. No USB add, bind, tty, reset, or descriptor event occurred from that
disconnect until the operator manually entered Download mode at 21:12:40Z.

Both continuous observers started and exited cleanly:

```text
udevadm monitor returncode=0
journalctl -kf returncode=0
```

This excludes a transient candidate tty hidden between periodic polls. It does
not prove whether direct PID1 reached the marker, module plan, gates, configfs,
or UDC bind.

## Retained Evidence

```text
pstore_files=[]
last_kmsg_collected=true
last_kmsg_bytes=2097136
marker=S22_NATIVE_INIT_O3F_FREESTANDING_ACM
marker_found=false
```

Marker absence keeps the internal phase `UNVERIFIABLE`. Operator-observed
no-bootloop is survival evidence only; it cannot be promoted to source branch
execution.

## Rollback Proof

The operator entered Download mode after the bounded observation. The helper
flashed only the pinned Magisk boot AP; Odin returned rc=0. Post-rollback:

```text
adb_serial=<S22_SERIAL_REDACTED>
boot_completed=1
bootanim=stopped
root=uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
boot_sha256=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
stability_samples=4/4
rollback_target=magisk
rollback_rc=0
```

An independent post-run check repeated boot completion, Magisk uid 0, stopped
boot animation, and exact boot SHA.

## Interpretation And Next Bound

O3F answered its named discriminator: removing static glibc startup, daemon
exec, and two-process ownership did not produce host-visible ACM. This does not
prove glibc was irrelevant to unobserved internal execution; it proves only
that another startup variant is not a justified next live flash.

Do not repeat O3F, widen the module plan, add Samsung composite/Type-C/PMIC
behavior, or advance to NCM. The next unit is host-only design for a direct-PID1
checkpoint that uses the already proven sec_debug MID retained
`/proc/last_kmsg` channel and deliberately forces retention after a marker.
No fault trigger or live flash is currently authorized; that path needs a new
narrow exception and attended gate after static review.
