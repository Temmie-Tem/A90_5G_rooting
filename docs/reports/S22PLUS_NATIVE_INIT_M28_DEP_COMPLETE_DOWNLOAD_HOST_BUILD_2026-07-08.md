# S22+ Native-Init M28 Dependency-Complete Download Host Build (2026-07-08)

## Verdict

HOST-BUILD PASS / NO LIVE AUTH: M28 replaces the abandoned blind `P01..P08`
prefix sweep with a stock `modules.dep`-respecting dependency-complete module
order. It rebuilds the M25 HS-only module closure with hard suppliers restored,
keeps the QMP/EUD/watchdog exclusions, and produces download-beacon boot-only
candidates. No flash, reboot, rollback, partition write, sysfs write, or device
action was performed.

## Why This Unit Exists

The stock FYG8 `modules.dep` proved the M25/M26/M27 40-module list was
dependency-incomplete. The previous M25 closure cut three hard suppliers:

```text
abc.ko
minidump.ko
sec_debug.ko
```

M28 re-includes those suppliers where required and fails the build if any hard
dependency still points into the remaining excluded set:

```text
eud.ko
gh_virt_wdt.ko
phy-msm-ssusb-qmp.ko
qcom_wdt_core.ko
sec_debug_region.ko
ucsi_glink.ko
```

The load order is topological over `modules.dep` with stock
`modules.load.recovery` positions used only as tie-breakers. This is deliberate:
suppliers load before consumers, instead of using the old flat M25 DTS-seed
order.

## Artifacts

Builder:

```text
workspace/public/src/scripts/revalidation/build_s22plus_m28_dep_complete_download.py
```

Runtime source:

```text
workspace/public/src/native-init/s22plus_init_m28_dep_complete_download.c
```

Output:

```text
workspace/private/outputs/s22plus_native_init/m28_dep_complete_download_v0_1
```

Source and manifest SHA256:

```text
8da6b157f2f868487a21caced8027e7c80c5e46a3adc3124e0f7d34aafa998fa  build_s22plus_m28_dep_complete_download.py
0c029dd3de42074c3c942efa23266fb383522750d1ffd9d826c67898db6bde6c  s22plus_init_m28_dep_complete_download.c
4986940e214dcb32916f5e06806f0cb2342479e82347abec0244edb2a09a250e  manifest.json
```

Inherited M25 DTBO context:

```text
M25 high-speed DTBO AP: 35afd774444066fd8e2ffe831da11dd73ee47dce3bdd5b1e37675f82344e56b6
patched raw DTBO:       8962cbbded722c85dbdebfbdc2eba5476b9a64e2a2933888b81f947159eddc17
stock DTBO rollback AP: 6f397421bee84f4ea0c80a8519be0f6f6af84119794970e8a1faaa05f261caaa
stock raw DTBO:         97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c
```

Vendor module metadata:

```text
vendor_ramdisk:             41b2481b779ff48863c300250dabf1b3dcc45c7f58fab421fcf6df1245145193
modules.dep:                21eae389f1d8b0a9fc93cec0b12d36e736cfac656d91ae55055c793f2ed67b27
modules.load:               8491b842e6e05cfba42694ad003301a6598e8d152ec10cc8f0cc6fb17f10e232
modules.load.recovery:      616bdb71f2b68d76eca23f72883aea25d5202d4e14f5c99dd934720df863ac10
modules.softdep:            21d6a678d186356c2fb0349a8a9a5190e6e225dab0feb5012e495a100c33afb0
```

## Candidates

Each AP contains exactly one tar member, `boot.img.lz4`.

| Label | Purpose | Modules | Modules SHA256 | AP.tar.md5 SHA256 | boot.img SHA256 | /init SHA256 |
| --- | --- | ---: | --- | --- | --- | --- |
| `S24` | Prove the dependency-complete first 24 M25 substrate modules can reach `reboot(download)` | 26 | `8c605e2c69aad74f80191bdbc1843b002539d22d49bcffa86bb85bbcb343e5e4` | `c684f6a21bcc9aa50b066b447f4356958fe6d7bfed93edf0ac1b7dcaae8ce75f` | `a1459931001bfd6e17593dd329fc682f00ab61f4841b6543791f5349dd012cd0` | `5c04a2023b2b56ef98746da6f7168121b62d7859cee81c756b80d1a382c1964e` |
| `F43` | Full M25 HS-only 40-module closure with hard suppliers restored, still no configfs/ACM/UDC action | 43 | `430050d648d85dd6c3fea459a6cd627a58fd234afe1b485820ccc1f2eb65f87b` | `003ea5760d9e33402750afd7a52b6b95727e4b4cff3f4d3cf66c559eabbb38d1` | `6453b8f2dd685757148056ba8767c2820b0547123f4e5e5e423c4adb0c70496c` | `68de58cd3f05fd77af00984027948ad5ab953ae128dc4133d336e0a521cd588f` |

`S24` module order:

```text
smem.ko
minidump.ko
sec_debug.ko
qcom_ipc_logging.ko
cmd-db.ko
qcom_rpmh.ko
clk-rpmh.ko
debug-regulator.ko
proxy-consumer.ko
gdsc-regulator.ko
clk-qcom.ko
clk-dummy.ko
gcc-waipio.ko
icc-bcm-voter.ko
icc-debug.ko
socinfo.ko
icc-rpmh.ko
rpmh-regulator.ko
iommu-logger.ko
qnoc-qos.ko
qnoc-waipio.ko
phy-generic.ko
qcom_iommu_util.ko
qcom-scm.ko
sec_class.ko
secure_buffer.ko
```

`F43` extends `S24` with:

```text
arm_smmu.ko
abc.ko
usb_notify_layer.ko
switch_class.ko
common_muic.ko
vbus_notifier.ko
pdic_notifier_module.ko
usb_typec_manager.ko
usb_f_ss_mon_gadget.ko
phy-msm-snps-hs.ko
repeater.ko
phy-msm-snps-eusb2.ko
redriver.ko
if_cb_manager.ko
qc_usb_audio.ko
dwc3-msm.ko
usb_f_ss_acm.ko
```

## Validation

Completed:

- `py_compile` for the M28 builder.
- Unit tests for M28 builder behavior and current private manifest.
- Host builder run with `--force`.
- AArch64 freestanding compile and strip for `S24` and `F43`.
- `readelf` confirms no interpreter.
- `objdump` confirms raw syscall path, `__NR_finit_module`, and
  `__NR_reboot`.
- MagiskBoot no-change repack is byte-identical to the known booting Magisk
  boot base.
- Patched boot images preserve the base kernel.
- Every candidate AP has exactly one `boot.img.lz4` member.
- Manifest safety flags remain `host_only_build=true`,
  `live_flash_authorized=false`, `device_action=false`.

## Next

The next live-capable unit should add a guarded live helper plus a fresh
SHA-pinned `AGENTS.md` exception for this exact M28 matrix. The live order
should be `S24` first. If `S24` fails or requires manual Download, stop and do
not run `F43`. If `S24` cleanly self-enters Download, rollback boot, then `F43`
can be considered under the same explicitly authorized policy. Any operator
manual Download must be recorded as contamination, not as candidate
self-download proof.
