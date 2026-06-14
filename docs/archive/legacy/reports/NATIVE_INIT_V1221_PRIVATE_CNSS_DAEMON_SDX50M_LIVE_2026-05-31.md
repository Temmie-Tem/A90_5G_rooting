# V1221 Private CNSS Daemon SDX50M Live Gate

- date: 2026-05-31
- cycle: V1221
- objective: use a private patched `cnss-daemon` artifact that selects real eSoC name `SDX50M`, then verify whether `pm-service` advances from modem-only registration to the eSoC path.
- safety scope: bounded PM/CNSS observer only; no Wi-Fi HAL, scan/connect/link-up, credentials, DHCP/routes, external ping, boot image write, or vendor partition write.

## Artifacts

- helper: `stage3/linux_init/helpers/a90_android_execns_probe.c` / remote `/cache/bin/a90_android_execns_probe`
- helper version: `a90_android_execns_probe v253`
- helper sha256: `d61cae5e8b6de997aff6c06ca08140e8d8b38951ca408b3e91b6e39577329f36`
- private CNSS artifact: `/cache/bin/cnss-daemon.sdx50m`
- private CNSS sha256: `784fd7bd9b602d8e1f94c9ceef977845909f452611025c40fda589d0e57de5fd`

## Evidence

- helper deploy: `tmp/wifi/v1221-execns-helper-v253-deploy/manifest.json`
- artifact deploy: `tmp/wifi/v1221-cnss-daemon-sdx50m-artifact-deploy/manifest.json`
- live gate: `tmp/wifi/v1221-private-cnss-daemon-sdx50m-live/manifest.json`
- dmesg tail: `tmp/wifi/v1221-private-cnss-daemon-sdx50m-live/host/post-dmesg-wifi-esoc-tail.txt`

## Result

- decision: `v1221-sdx50m-per-mgr-esoc0`
- pass: `true`
- private bind: `private_cnss_daemon.bind_rc=0`
- CNSS PM client registrations: `['modem', 'SDX50M']`
- `pm-service` / binder path reached eSoC: `__subsystem_get(): esoc0 count:0`
- MDM power-up path observed: `mdm_subsys_powerup` in PM thread wchan samples
- `wlan0`: not present
- `mdm3`: remained `OFFLINING`

## Interpretation

V1221 closes the V1219/V1220 selection gap. The private patched `cnss-daemon` was mounted in the helper namespace, registered `SDX50M`, and caused `pm-service` to reach the `subsys_esoc0` path. That is the first native-init evidence that the CNSS path can trigger the eSoC subsystem-open route without fake `esoc_name`.

The next blocker moved lower: eSoC subsystem power-up starts but does not complete. Current evidence still lacks WLFW service 69, BDF download, `FW ready`, or `wlan0`.

Note: the extra V1219-style CNSS selection uprobes were still aimed at `/mnt/vendor/bin/cnss-daemon`, while V1221 executes the private `/cache/bin/cnss-daemon.sdx50m` inode through a bind mount. Therefore the decisive V1221 proof is the PM client registration trace plus dmesg/subsystem evidence, not the old stock-binary selection offsets.

## Safety Audit

- `cnss_daemon_start_executed=true` as intended for this gate.
- `wifi_hal_start_executed=false`.
- `scan_connect_executed=false`.
- `external_ping_executed=false`.
- `wifi_bringup_executed=false`.
- postflight native health: `A90 Linux init 0.9.68 (v724)`, `selftest fail=0`.

## Next

V1222 should observe the eSoC power-up completion boundary after `subsys_esoc0` opens: MDM crash/down markers, `mdm3` state transitions, WLFW service 69, BDF markers, and `wlan0`. Do not move to Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping until WLFW/BDF/`wlan0` readiness is proven.
