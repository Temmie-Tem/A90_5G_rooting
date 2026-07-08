# S22+ M34 S3 Live Gate Ready

Date: 2026-07-09 KST / 2026-07-08 UTC

Status: S3 host-side live gate helper is ready and fail-closed. The operator
has approved live in-thread, but the run is still blocked until a fresh active
SHA-pinned `AGENTS.md` exception is added and committed.

## Context

M34 S1 and S2 both survived the full 90 second observation window and rolled
back cleanly. S2 proved that the following runtime-gadget setup is not the
observed reset boundary when final UDC pullup is absent:

- full 45-module closure including `dwc3-msm.ko` and `usb_f_ss_acm.ko`
- stock-ordered configfs gadget/function/config creation
- `UDC=none`
- stock IDs `0x04E8:0x6860`
- `functions/ss_acm.0` link
- `g1/max_speed=high-speed`
- `usb_role=device`

M34 S3 is the next isolated discriminator. It adds only the final
`UDC=a600000.dwc3` bind/pullup after the S2-proven setup.

## Helper

New helper:

`workspace/public/src/scripts/revalidation/s22plus_m34_s3_runtime_gadget_live_gate.py`

The helper is copied from the S2 live-gate structure but pins S3-specific
artifacts and semantics. It also scans host `/dev/ttyACM*` during observation
and treats a Samsung `04e8:6860` ACM endpoint as a successful S3 pullup proof
that still requires manual Download rollback.

Candidate pins:

- AP.tar.md5 SHA256: `0ef55db2d38bec3df83cb77cd83f8ee6644054447ae7da10f8ecaecc8faa2957`
- padded `boot.img` SHA256: `87351f4955740aa4d83567406567c1ef4d6fcfa217d9ee5b0d7c446f2db09142`
- direct `/init` SHA256: `2f391e50ff271b2dfe14dce31dbfdd0f0fb2b6d353ae89a2079acad5b46e668f`
- template source SHA256: `ac20dcf724cf6864540d65958332d561d45409e7e85785a8c014882b37e29193`
- module-list SHA256: `2291dc1c72add131c42d0b4ed6649880c20316d0598e0a2af942cc774949062c`
- preserved kernel SHA256: `bceca73edbfca3499148e16741c939779157925949ef6bc8a8e31d6b68fc2cff`
- known-booting Magisk boot base SHA256: `2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

The default candidate AP path is:

`workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_2/S3/odin4/AP.tar.md5`

## Contract

The S3 manifest gate requires:

- stage `S3`
- stock-ordered configfs gadget/function/config
- `UDC=none`
- stock IDs `0x04E8:0x6860`
- `functions/ss_acm.0` link
- `max_speed_high_speed=true`
- `usb_role_force=true`
- `udc_bind=true`
- final `UDC=a600000.dwc3`
- safety marker `stage_s3_binds_only_a600000_dwc3=true`

The helper also verifies:

- boot-only single-member AP
- exact S3 AP/boot/init/source/module/kernel/base hashes
- no reboot syscall in the S3 `/init`
- no Android/Magisk handoff
- no persistent partition mount
- no block write
- no module binary injection into boot ramdisk
- `phy-msm-ssusb-qmp.ko` excluded
- EUD excluded
- rollback AP hashes pinned

## Validation

Commands passed:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_m34_s3_runtime_gadget_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests/test_s22plus_m34_s3_runtime_gadget_live_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_m34_s3_runtime_gadget_live_gate.py \
  --offline-check
```

The S3 helper also failed closed without an active `AGENTS.md` exception:

```text
AGENTS.md missing M34 S3 runtime-gadget authorization markers
```

That failure occurs after artifact verification and before Android/flash
actions.

## Live Outcomes

- ACM appears as Samsung `04e8:6860`: final UDC pullup works far enough to
  enumerate an ACM endpoint. Manual Download rollback remains required.
- Survives 90 seconds with no ACM: final UDC pullup is not the reset wall, but
  there is still no host ACM proof; inspect device and host USB state next.
- PMIC/RDX/Odin/Android appears before the survival window: final UDC pullup is
  the boundary. Stop and split `max_speed`, `usb_role`, and final bind details
  before any broader channel work.

## Next Gate

Before live:

1. Add a fresh SHA-pinned active S3 one-shot exception to `AGENTS.md`.
2. Commit that active authorization.
3. Run the helper with `--live` and its S3 live ack token.

No S3 live flash is authorized by this report alone.
