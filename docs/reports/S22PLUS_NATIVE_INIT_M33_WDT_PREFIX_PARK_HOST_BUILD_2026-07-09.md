# S22+ M33 Watchdog Prefix-Park Host Build

Date: 2026-07-09 02:19 KST / 2026-07-08 17:19 UTC

## Verdict

PASS: built a host-only M33 prefix-park matrix to split the failed M32
watchdog-managed HS ACM candidate before any new live gate.

No live flash was performed. No connected device was required. There is no
active live authorization for these artifacts.

## Why This Unit Exists

M31B proved the watchdog-managed park shape can survive the prior PMIC/PON
dwell ceiling. M32 then added the full dependency-complete HS/ACM stack plus
runtime configfs/ACM setup and failed: no ACM appeared, the operator observed a
bootloop, and the host saw an unexpected Download endpoint at about 35.6 s.

M33 separates those two changes:

- Same M31B park runtime shape.
- Same known-booting Magisk boot base.
- Watchdog-managed module loading remains enabled.
- No Download reboot request.
- No configfs runtime gadget.
- No ACM setup, no `ttyGS0`, no `ss_acm.0`.
- Only the module prefix grows by variant.

If a high prefix survives, the M32 failure moves toward configfs/ACM setup. If a
specific prefix bootloops, the failure localizes to the added module boundary.

## Output

Private output:

`workspace/private/outputs/s22plus_native_init/m33_wdt_prefix_park_matrix_v0_1`

Top-level manifest:

`workspace/private/outputs/s22plus_native_init/m33_wdt_prefix_park_matrix_v0_1/manifest.json`

Base Magisk boot SHA256:

`2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

No-change MagiskBoot repack SHA256:

`2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e`

This proves the MagiskBoot base repack path remains byte-identical before M33
patching.

## Variant Matrix

| Variant | Prefix | Modules | Boundary | AP.tar.md5 SHA256 | boot.img SHA256 |
|---|---:|---:|---|---|---|
| P12 | 12 | 21 | early clocks/interconnect; no SMMU/PHY/DWC3/ACM | `47a7acd9f953de4464848aa02413b629064c512e2250356da0e33df5c46a3ce0` | `72afa113caf0bd8fc2f3c4d2a27108f3be94dd00f405071d3b7e609af8d8a2f2` |
| P18 | 18 | 26 | RPMh/provider layer; no SMMU/PHY/DWC3/ACM | `9bbb3bebe866754c208c4d2660baf527bdbf0d2d1a18276b33cf02c98743aebe` | `80752104a3a8d299257fb7f86b0555663cfece03882f280bb4e23badf22bb849` |
| P25 | 25 | 29 | includes `arm_smmu.ko`; no HS PHY/DWC3/ACM | `1ae65c1d994137237f2227f95b86700f74d00791d6cfec53b1bcf245f0aa18d7` | `fd29255237b34df959102e11fa60bd654678fe3eda93c710dbf314e5485e6651` |
| P27 | 27 | 40 | includes HS/eUSB2 PHY; no DWC3/ACM | `9110e793f5cc812c856dedf35aaa4cc2f2c692f8561bba9dbe10c7b1e8a29371` | `16efd35b4bb340b2c8d5d5b99e3e3d3e19d4c01a60e87f6ed3cf60acc90386ea` |
| P28 | 28 | 44 | includes `dwc3-msm.ko`; no ACM function target | `4c76ef4df814356a7acfa9ce9a00c2fe003208ff8289c2874535e26b7e1c3f07` | `3bc59d6df58b5c7130e6ca531a6a6cd3a4d35e14ff7fd6667da72e2bd40e9e29` |
| P30 | 30 | 45 | includes `usb_f_ss_acm.ko`; no configfs runtime setup | `e7cadd856da852e577adf32e088c0fee668904f265cdad1e9309072ccb2b18fd` | `0a972bcb4af2b75d5177ae9767e34a4caa8b8c94237afa708bb4a577b2ba7bfe` |
| P40 | 40 | 45 | full M32 module closure; no configfs runtime setup | `420986c447df5cd155aee1ea32ece8ec5a7b021793dd9058d4fe6bc3744b7c34` | `b07bbc97a36f63c92db915829b322ef8200ceb5944a244b0a8406780b46a9621` |

P40's closure exactly matches M32's 45-module closure. P30 also reaches 45
modules because dependencies pull the same completed closure once the ACM
function target is included. The difference from M32 is runtime behavior, not
module membership: M33 never creates configfs or binds ACM.

## Safety Properties

Manifest safety flags:

- `boot_only=true`
- `host_only_build=true`
- `live_flash_authorized=false`
- `requires_new_sha_pinned_agents_exception_before_flash=true`
- `auto_reboot=false`
- `intended_reboot_syscall=false`
- `reboot_request=null`
- `configfs_runtime_gadget=false`
- `acm=false`
- `module_binary_injection=false`
- `block_device_writes=false`
- `persistent_partition_mount=false`

Every variant AP contains exactly one tar member: `boot.img.lz4`.

Excluded modules remain excluded:

- `eud.ko`
- `phy-msm-ssusb-qmp.ko`
- `sec_debug_region.ko`
- `ucsi_glink.ko`

## Validation

Commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest -q tests/test_s22plus_m33_wdt_prefix_park_build.py
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 workspace/public/src/scripts/revalidation/build_s22plus_m33_wdt_prefix_park.py --force
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest -q \
  tests/test_s22plus_m31b_wdt_managed_park_build.py \
  tests/test_s22plus_m32_wdt_hs_acm_build.py \
  tests/test_s22plus_m33_wdt_prefix_park_build.py
```

Results:

- M33 tests: 5 passed.
- Adjacent M31B/M32/M33 tests: 14 passed.
- Builder completed all 7 variants.
- `manifest["matrix"]["full_prefix_matches_m32_modules"] == true`.
- AP tar member check passed for every variant.

## Next Gate Shape

A future live gate should be a fresh, SHA-pinned, boot-only `AGENTS.md`
exception. Do not reuse the consumed M32 authorization.

Recommended live order:

1. P12: if this fails, the issue is in early supplier module loading plus WDT
   management, before SMMU/PHY/DWC3.
2. P25 or P27: distinguishes SMMU/secure-buffer from HS PHY expansion.
3. P28: tests DWC3 module loading without ACM function target.
4. P30 or P40: tests full M32 module closure without configfs/ACM setup.

Interpretation:

- P30/P40 survive: M32 failure is likely configfs/ACM runtime setup, not module
  loading.
- P28 fails while P27 survives: DWC3 boundary is suspect.
- P27 fails while P25 survives: HS/eUSB2 PHY boundary is suspect.
- P12 fails: revisit early supplier closure and sec_debug/minidump additions
  before any USB work.
