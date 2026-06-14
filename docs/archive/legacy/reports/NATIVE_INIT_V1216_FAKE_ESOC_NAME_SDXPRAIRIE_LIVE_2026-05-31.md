# Native Init V1216 Fake eSoC Name SDXPRAIRIE Live Report

Date: `2026-05-31`

## Result

- Decision: `v1216-peripheral-modem-unexpected`
- Pass: `false`
- Helper: `a90_android_execns_probe v250`
- Helper SHA256: `db9531f09f2c69b7028fe2fcb10ffdbed1051f81542787a43c36fb8a553e7886`
- Deploy evidence: `tmp/wifi/v1216-execns-helper-v250-deploy/manifest.json`
- Live evidence: `tmp/wifi/v1216-fake-esoc-name-sdxprairie/manifest.json`

## Summary

V1216 deployed helper `v250` and ran the private-namespace fake
`esoc_name=SDXPRAIRIE` gate.  The helper successfully bind-mounted the fake
name file, but `cnss-daemon` still registered only `peripheral="modem"`.
`per_mgr` did not open `/dev/subsys_esoc0`, `mdm_subsys_powerup` did not appear,
and `wlan0` stayed absent.

| key | value |
| --- | --- |
| fake bind rc | `0` |
| fake content | `SDXPRAIRIE` |
| fake target | `/tmp/a90-v231-1769/root/sys/devices/platform/soc/soc:qcom,mdm3/esoc0/esoc_name` |
| `/dev/esoc-0` mknod rc | `-1` |
| `/dev/esoc-0` mknod errno | `17` / `EEXIST` |
| registered peripherals | `["modem"]` |
| `SDXPRAIRIE` registered | `false` |
| `per_mgr_esoc0_any` | `false` |
| `mdm_subsys_powerup_any` | `false` |
| `wlan0_up` | `false` |

## Interpretation

The V1215 disassembly-based hypothesis is not yet sufficient as implemented.
The fake bind mount exists and reports the expected content marker, but the
runtime path used by `libmdmdetect.so`/`cnss-daemon` still resolves to the
`modem` peripheral path.

The most likely remaining gaps are:

- the helper bound the real platform-path file, while the detection code may
  read a different sysfs alias or derived path inside the chroot;
- the fake file was not read back through the exact path used by
  `get_system_info()`, so the bind proof is currently source/target-only rather
  than read-path-positive;
- `cnss-daemon` may choose the first type-1 `modem` registration path before any
  second type-0 `SDXPRAIRIE` path can become actionable.

## Safety

- Wi-Fi HAL start: `false`
- scan/connect/link-up: `false`
- credentials: `false`
- DHCP/routes: `false`
- external ping: `false`
- boot image or partition write: `false`
- Device postflight: `A90 Linux init 0.9.68 (v724)`, `selftest fail=0`
- Netservice postflight: disabled, `ncm0=absent`, `tcpctl=stopped`

## Next Gate

V1217 should prove the exact `libmdmdetect` read path before another
PM/CNSS live attempt:

1. add helper readback markers after the fake bind for:
   - `/sys/devices/platform/soc/soc:qcom,mdm3/esoc0/esoc_name`
   - `/sys/bus/esoc/devices/esoc0/esoc_name`
   - `/sys/class/esoc-dev/*` symlink targets and readable name/link files
2. capture the resulting values from inside the same private chroot before
   `cnss-daemon` starts;
3. only if the exact detection path reads `SDXPRAIRIE`, rerun the bounded PM
   observer; otherwise repair the bind target/path first.

