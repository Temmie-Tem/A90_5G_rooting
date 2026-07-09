# V3416 S22+ O3F Freestanding ACM Live Gate Ready

## Verdict

`LIVE GATE READY`. The O3F artifact-only gate and connected read-only preflight
passed. A fresh exact one-shot `AGENTS.md` exception is active following the
operator's explicit approval of the next live run. No candidate flash has yet
occurred; the exception is unconsumed until `candidate_flash_start`.

## Exact Candidate

```text
target=SM-S906N/g0q/S906NKSS7FYG8
serial=S22O3FACM01
ap_tar_md5_sha256=73d0a03c066b236e8ebea07c03affda4c5b94633cc34dd2ca413ce8697eb8725
boot_img_sha256=c09ef0e8cbcb3b53c8ba22d76fce47cc03607ad416b0b8f2faf2adf1f18e9f70
boot_img_lz4_sha256=b25fff7af1d07fd0fd7799aac4ad1c8076f4fed7b7d8c64974cba5a2f5ecc922
o3f_init_sha256=d181cee7818cdf0566a8f618d1f861b0bdabb36501ca95e87ad3681a370d2a16
source_sha256=2018eacff28dd6e897e9d6f4d6eabd712b74f076ecdbb6192f03c59455ccfa38
protocol_header_sha256=3a53ebb9788b0ff23982ca2ed2bfc19cd27c5504f650660877868b588651403a
plan_tsv_sha256=a34ebbad3b5d770f133e37a450cc3007e4a84ab831788484680e88aad6b3d534
base_boot_sha256=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
kernel_sha256=bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff
tar_members=boot.img.lz4
```

The helper also pins Magisk rollback AP
`d2373bf…15a56`, stock fallback AP `2f6a8ac0…7c94`, and stock raw boot
`4150b962…40ae`.

## Gate Contract

The O3F wrapper reuses the O3 runner's established single-target preflight,
continuous USB observers, canonical eight-event timeline, exact boot hash
verification, mandatory attended rollback, post-rollback stability checks, and
retained-log collection. It replaces every candidate-specific artifact,
manifest, serial, marker, status, token, and exception pin.

PASS requires all of:

1. Exact USB serial `S22O3FACM01`.
2. 128/128 CRC-framed echoes with sequence and payload equality.
3. Successful host close/reopen at request 64.
4. `O3 STATUS` version `0.2`, all 59 modules registered through EOF, gate mask
   `0xff`, exact mode/UDC readbacks, and zero protocol errors.
5. Mandatory Magisk boot-only rollback and restored Android/root baseline.

Enumeration, candidate survival, or source intent is not PASS. O3F has no
reboot command; after the bounded candidate observation the operator must enter
Download mode manually for rollback.

## Preflight Evidence

Artifact-only run:

```text
workspace/private/runs/s22plus_o3f_freestanding_acm_live_gate_20260709T210649Z
result=offline-pass
```

Connected read-only run:

```text
workspace/private/runs/s22plus_o3f_freestanding_acm_live_gate_20260709T210656Z
adb_serial=<S22_SERIAL_REDACTED>
model=SM-S906N
device=g0q
incremental=S906NKSS7FYG8
verified_boot_state=orange
boot_completed=1
bootanim=stopped
root=uid 0, u:r:magisk:s0
boot_sha256=2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
stability_samples=4/4
concurrent_odin_devices=[]
result=dry-run-pass
```

The O3F build/live focused tests pass 12/12. The live command requires both
independent tokens:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_o3f_freestanding_acm_live_gate.py \
  --live \
  --ack S22PLUS-O3F-FREESTANDING-ACM-LIVE-GATE \
  --rollback-ack S22PLUS-O3F-FREESTANDING-ACM-ROLLBACK-FROM-DOWNLOAD
```
