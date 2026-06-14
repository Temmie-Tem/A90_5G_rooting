# Native Init V1217 Fake eSoC Name Readback Report

Date: `2026-05-31`

## Result

- Decision: `v1217-readback-path-positive`
- Pass: `true`
- Helper: `a90_android_execns_probe v252`
- Helper SHA256: `4511f11399d4f86f5265d79eb57b2db04ae5ad869ab543565f2c657b97af8587`
- Deploy evidence: `tmp/wifi/v1217-execns-helper-v252-deploy/manifest.json`
- Live evidence: `tmp/wifi/v1217-fake-esoc-name-readback/manifest.json`

## Summary

V1217 added a readback-only branch to the execns helper.  The branch creates the
same private namespace and fake `esoc_name=SDXPRAIRIE` bind mount as V1216, then
exits before starting any PM/CNSS/service-manager/Wi-Fi process.

The readback proof passed.  Both the direct platform path and the bus alias that
`libmdmdetect.so` is expected to follow read `SDXPRAIRIE`, and
`/sys/class/esoc-dev` is visible inside the same private namespace.

| key | value |
| --- | --- |
| platform path | `/sys/devices/platform/soc/soc:qcom,mdm3/esoc0/esoc_name` |
| platform readback | `SDXPRAIRIE` |
| bus alias | `/sys/bus/esoc/devices/esoc0/esoc_name` |
| bus alias readback | `SDXPRAIRIE` |
| `/sys/class/esoc-dev` opendir | `0` |
| `/sys/class/esoc-dev` entries | `1` |
| daemon start | `0` |
| service-manager start | `0` |
| Wi-Fi HAL start | `0` |
| scan/connect/link-up | `0` |
| credentials | `0` |
| DHCP/routes | `0` |
| external ping | `0` |

## Interpretation

V1216's failed `peripheral='modem'` result is no longer explained by the fake
file being unreadable through the obvious platform or bus sysfs paths.  In the
same private namespace, before daemon start:

- direct platform `esoc_name` reads `SDXPRAIRIE`;
- `/sys/bus/esoc/devices/esoc0/esoc_name` reads `SDXPRAIRIE`;
- `/sys/class/esoc-dev` is present and enumerable.

The next blocker is therefore downstream of simple read-path visibility.  V1218
should rerun the bounded PM/CNSS observer with helper `v252` and require direct
tracefs evidence of whether `cnss-daemon` still registers only `modem` or now
emits the expected `SDXPRAIRIE` registration.

## Notes

- Helper `v251` was built first but its readback-only command still hit
  `stat host selinux status: No such file or directory` in native init.
- Helper `v252` fixes that by skipping selinuxfs materialization for
  `--pm-observer-fake-esoc-name-readback-only`, because this branch starts no
  daemon and does not need SELinux runtime surface.

## Safety

- No daemon start: confirmed by helper control markers.
- No service-manager start: confirmed by helper control markers.
- No Wi-Fi HAL start: confirmed by helper control markers.
- No scan/connect/link-up: confirmed by helper control markers.
- No credentials/DHCP/routes/external ping: confirmed by helper control markers.
- No boot image or partition write.
- Device postflight: `selftest fail=0`; netservice cleanup left `ncm0=absent`
  and `tcpctl=stopped`.

## Next Gate

V1218 should rerun the bounded PM/CNSS observer with helper `v252` and the same
fake `SDXPRAIRIE` bind.  Success criteria:

1. `pm_client_register_entry peripheral='SDXPRAIRIE'` appears for
   `cnss-daemon`;
2. `per_mgr` opens `/dev/subsys_esoc0`;
3. if MDM advances, capture WLFW/BDF/`wlan0` markers without scan/connect.
