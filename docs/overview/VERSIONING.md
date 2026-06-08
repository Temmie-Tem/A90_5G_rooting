# Native Init Versioning

Updated: `2026-06-07`

This is the short reader-facing summary. The normative policy is
`docs/operations/VERSIONING_POLICY.md`.

## Axes

| Axis | Format | Meaning | Example |
| --- | --- | --- | --- |
| Run ID | `VNNNN` | project run/report/validation/promotion number | `V2175` |
| Native init version | `MAJOR.MINOR.PATCH` | device-visible native init build | `0.9.251` |
| Build tag | `vNNNN-purpose` | flashed boot/init baseline role | `v2174-wifi-urandom-connect` |
| Helper version | `helper-vNNN` | helper binary marker stream | `a90_android_execns_probe helper-v427` |
| Artifact hash | `sha256:<hex>` | exact binary/evidence identity | boot image SHA256 |

## Rules

- Run IDs (`V2167`, `V2168`, `V2169`, `V2175`) are global project execution
  numbers.
- Native init versions (`0.9.246`, `0.9.247`, `0.9.251`) change only when the
  boot artifact that can be flashed changes.
- Build tags name the boot/init baseline and should not be confused with helper
  markers.
- Helper versions must be written with the `helper-` prefix in summaries:
  `helper-v427`, not bare `v427`.
- SHA256 is the final artifact identity. If the boot SHA changes and the image is
  promoted as a rollback/test baseline, give it a new run/build identity.

## Current Verified Example

```text
Run ID: V2175
Native init: A90 Linux init 0.9.251 (v2174-wifi-urandom-connect)
Build tag: v2174-wifi-urandom-connect
Helper: a90_android_execns_probe helper-v427
Boot image: workspace/private/inputs/boot_images/boot_linux_v2174_wifi_urandom_connect.img
Boot SHA256: cda957e4302d66e407fc97a95932501f0ef2ac655ee264c94519111fece0b3ba
Evidence: V2174 source/build and live validation reports plus V2175 promotion
report
```

## Next Baseline Naming

The next promoted baseline after V2175 should use a new global run/build
identity, not an unrelated helper number and not a recycled validation run:

```text
Run ID: V2176
Native init: A90 Linux init 0.9.252
Build tag: v2176-<purpose>
Boot image: workspace/private/inputs/boot_images/boot_linux_v2176_<purpose>.img
Helper: a90_android_execns_probe helper-v427
```

## Historical Note

Earlier project phases often used `vNNN` for both project cycles and boot image
build tags because most cycles produced a boot image. During Wi-Fi bring-up,
host-only classifiers and rollbackable test boots made these streams diverge.
Use the table above for current work.

## Local Artifact Retention

- Keep current verified baseline artifacts, previous rollback artifacts, and
  known-good fallback artifacts.
- Current cleanup defaults should preserve `v48`, `v724`, `v725`, `v726`,
  `v2169`, and `v2174`.
- Cleanup tools are dry-run first:

```bash
python3 scripts/revalidation/cleanup_tmp_wifi_artifacts.py
python3 scripts/revalidation/cleanup_stage3_artifacts.py
```
