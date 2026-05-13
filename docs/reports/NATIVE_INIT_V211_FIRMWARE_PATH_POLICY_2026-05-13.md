# v211 Firmware Path / Vendor Layout Policy Report

## Summary

- status: `PASS`
- runtime: `A90 Linux init 0.9.59 (v159)`
- collector: `scripts/revalidation/native_firmware_path_policy_probe.py`
- evidence: `tmp/wifi/v211-firmware-path-policy`
- decision: `sysfs-path-update-needed`
- reason: isolated vendor firmware root resolves likely request names; future implementation needs guarded `firmware_class.path` update
- next: v212 guarded opt-in `firmware_class.path=/mnt/vendor/firmware` update and rollback test

v211 did not enable Wi-Fi. It did not write `firmware_class.path`, did not bind
mount `/vendor` or `/lib/firmware`, did not copy firmware, and did not start
`cnss-daemon`, `cnss_diag`, Wi-Fi HAL, `wificond`, supplicant, or hostapd.

## Validation

Static checks:

```text
python3 -m py_compile \
  scripts/revalidation/native_firmware_path_policy_probe.py \
  scripts/revalidation/native_vendor_asset_classifier.py \
  scripts/revalidation/a90harness/evidence.py
python3 - <<'PY'
import sys
sys.path.insert(0, 'scripts/revalidation')
import native_firmware_path_policy_probe
native_firmware_path_policy_probe.validate_policy_commands()
print('v211 command guard PASS')
PY
git diff --check
```

Live collector:

```text
python3 scripts/revalidation/a90ctl.py --json version
rm -rf tmp/wifi/v211-firmware-path-policy
python3 scripts/revalidation/native_firmware_path_policy_probe.py \
  --native-bridge \
  --v210-manifest tmp/wifi/v210-vendor-asset-classifier/manifest.json \
  --v209-manifest tmp/wifi/v209-vendor-ro-mount-probe/manifest.json \
  --out-dir tmp/wifi/v211-firmware-path-policy
```

Result:

```text
PASS out_dir=tmp/wifi/v211-firmware-path-policy decision=sysfs-path-update-needed reason=isolated vendor firmware root resolves likely request names; future implementation needs guarded firmware_class.path update
```

Artifact hashes:

```text
5ad7c822cf9d9214bc9803f393865a2f8a87a739b31de2cb4744d94a6d5c0c51  tmp/wifi/v211-firmware-path-policy/manifest.json
2ccf688181243c6f84f76f72c5d784a9c1ee39f88be34c10235d9d2726c01bdf  tmp/wifi/v211-firmware-path-policy/summary.md
```

## Evidence

Baseline:

- v209 decision: `vendor-assets-visible`
- v210 decision: `firmware-path-policy-needed`
- `sda29` major/minor: `259:22`
- ext4 available: `true`
- temporary mount: `run /cache/bin/toybox mount -t ext4 -o ro,noload /tmp/a90-v211-*/sda29 /tmp/a90-v211-*/vendor`
- mounted line: `ext4 ro,relatime,norecovery,i_version`
- cleanup rc: `0`
- leftover mount: `false`
- `firmware_class.path`: `/vendor/firmware_mnt/image`
- post-probe `firmware_class.path`: `/vendor/firmware_mnt/image`

Required firmware visible under the isolated vendor mount:

- `firmware/wlan/qca_cld/WCNSS_qcom_cfg.ini`
- `firmware/wlan/qca_cld/bdwlan.bin`
- `firmware/wlan/qca_cld/regdb.bin`
- `firmware/wlanmdsp.mbn`

## Policy Matrix

| candidate | result | detail |
| --- | --- | --- |
| current `/vendor/firmware_mnt/image` | reject as current state | resolves none of the likely request names |
| isolated `/mnt/vendor/firmware` root | preferred next step | resolves `wlan/qca_cld/*` and `wlanmdsp.mbn`; requires guarded sysfs update |
| synthetic `/vendor/firmware_mnt/image` bind | viable fallback | resolves the same likely names but requires later bind layout and cleanup policy |
| copy to `/lib/firmware` | reject | mutates firmware provenance/lifecycle and is unnecessary for the next step |

Likely request names resolved by the isolated root:

- `wlan/qca_cld/WCNSS_qcom_cfg.ini`
- `wlan/qca_cld/bdwlan.bin`
- `wlan/qca_cld/regdb.bin`
- `wlanmdsp.mbn`

Uncertain bare request names not resolved by the isolated root:

- `WCNSS_qcom_cfg.ini`
- `bdwlan.bin`
- `regdb.bin`

This is acceptable for v211 because Android/vendor evidence and visible layout
strongly point to the `wlan/qca_cld/*` names, but v212 must remain rollback-safe.
If real firmware requests later prove to be bare names, the fallback is not Wi-Fi
bring-up; it is a request-name evidence pass or a different read-only layout.

## Acceptance

- The collector uses private/no-follow evidence output.
- The command guard rejects Wi-Fi enablement, rfkill writes, module mutation,
  daemon starts, firmware copies, `firmware_class.path` writes, and persistent
  bind mounts.
- The only allowed mutation is temporary `/tmp/a90-v211-*` node/mount creation
  and cleanup.
- Required firmware files are visible through the isolated vendor mount.
- Cleanup succeeds and the temporary mount does not remain.
- The next implementation should be v212 guarded firmware path update, not
  Wi-Fi daemon bring-up.
