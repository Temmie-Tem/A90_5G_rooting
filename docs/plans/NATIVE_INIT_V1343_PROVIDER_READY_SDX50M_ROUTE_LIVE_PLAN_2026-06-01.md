# Native Init V1343 — Provider-ready SDX50M Route Live Plan

- Date: 2026-06-01
- Cycle: `V1343` (project axis; no boot image or partition write implied)
- Native build: `A90 Linux init 0.9.68 (v724)` (unchanged)
- Type: bounded live gate plan
- Status: PLAN

## Goal

V1342 classified the next required lower trigger:

```text
V1341 provider-positive state
  -> no lower transition by itself

V1221 private cnss-daemon SDX50M route
  -> CNSS PM client registers SDX50M
  -> pm-service reaches /dev/subsys_esoc0
  -> mdm_subsys_powerup starts
```

V1343 should combine those facts in one current-helper gate:

1. refresh current-boot V490 SELinux policy load;
2. require `vndservicemanager` readiness and `vendor.qcom.PeripheralManager`
   provider-positive query;
3. use the V1221-proven private `cnss-daemon.sdx50m` route so CNSS registers
   `SDX50M`;
4. compactly observe the lower path:
   `/dev/subsys_esoc0`, `mdm_helper` `/dev/esoc-0`, `ks`, MHI, WLFW service 69,
   BDF markers, and `wlan0`.

## Current Facts

| Fact | Evidence |
| --- | --- |
| V1341 restored provider-positive PM state under proper domains | `docs/reports/NATIVE_INIT_V1341_ANDROID_PRE_CNSS_PROVIDER_POLICY_READY_2026-06-01.md` |
| V1342 classified provider-positive alone as insufficient | `docs/reports/NATIVE_INIT_V1342_PM_ACTIONABILITY_GAP_CLASSIFIER_2026-06-01.md` |
| V1221 proved private `cnss-daemon.sdx50m` registers `SDX50M` and moves PM to eSoC | `docs/reports/NATIVE_INIT_V1221_PRIVATE_CNSS_DAEMON_SDX50M_LIVE_2026-05-31.md` |
| helper v279 still supports `--pm-observer-private-cnss-daemon-sdx50m` and `--private-cnss-daemon-path` | `stage3/linux_init/helpers/a90_android_execns_probe.c` |
| helper v279 is already deployed by V1341 | `tmp/wifi/v1341-execns-helper-v279-deploy/manifest.json` |

## Proposed Gate

Add `scripts/revalidation/native_wifi_provider_ready_sdx50m_route_live_v1343.py`.

The runner should reuse existing V1221/V1341 components rather than adding new
kernel or init behavior:

- helper: `/cache/bin/a90_android_execns_probe`
- helper marker: `a90_android_execns_probe v279`
- helper SHA256: `2ec7c9584e0adb09755e1066ee01a986e3b7fd719c11b8a96aaf5c500d9dd15a`
- private CNSS artifact: `/cache/bin/cnss-daemon.sdx50m`
- private CNSS SHA256:
  `784fd7bd9b602d8e1f94c9ceef977845909f452611025c40fda589d0e57de5fd`

Required helper contract:

```text
--mode wifi-companion-pm-service-trigger-observer
--allow-pm-service-trigger-observer
--pm-observer-continue-after-provider
--pm-observer-start-cnss-after-provider
--pm-observer-start-cnss-before-per-proxy
--pm-observer-per-proxy-after-vndservice-provider
--pm-observer-private-cnss-daemon-sdx50m
--private-cnss-daemon-path /cache/bin/cnss-daemon.sdx50m
```

The runner must also run V490 first, using the same current-boot policy-load
proof contract as V1341.

## Success Labels

| Decision | Meaning | Next |
| --- | --- | --- |
| `v1343-sdx50m-route-wlfw-or-wlan0` | WLFW/BDF or `wlan0` appears | classify readiness, then plan Wi-Fi HAL/scan gate |
| `v1343-sdx50m-route-esoc-powerup-observed` | `/dev/subsys_esoc0` or `mdm_subsys_powerup` appears, but WLFW/`wlan0` does not | compare lower failure against V1222/V1324 response gap |
| `v1343-sdx50m-client-registered-no-esoc` | `SDX50M` client registration occurs but PM does not open eSoC | classify PM request/actionability despite SDX50M route |
| `v1343-provider-positive-no-sdx50m` | provider is positive but `SDX50M` CNSS client is not registered | inspect private bind/artifact/context |
| `v1343-precondition-failed` | V490, helper, private artifact, or provider query failed | repair precondition before retry |

## Safety Contract

V1343 may start bounded PM/CNSS actors and private `cnss-daemon.sdx50m` in the
helper namespace. It must not perform a Wi-Fi connection attempt.

Blocked:

- Wi-Fi HAL start beyond the PM/CNSS route under test.
- `wificond`.
- scan/connect/link-up.
- credential use.
- DHCP/routes.
- external ping.
- manual `/dev/subsys_esoc0` open outside the `pm-service` path.
- eSoC ioctl/notify/BOOT_DONE spoof.
- PMIC/GPIO/GDSC writes.
- boot image write, flash, or partition write.

Required cleanup:

- If helper output or postflight process checks show lingering PM/CNSS actors,
  perform bounded cleanup/reboot and verify `selftest fail=0`.
- If `pm-service` enters `mdm_subsys_powerup` and cannot be killed cleanly, treat
  reboot cleanup as required evidence, not as failure by itself.

## Validation

Before live:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_provider_ready_sdx50m_route_live_v1343.py
python3 scripts/revalidation/native_wifi_provider_ready_sdx50m_route_live_v1343.py plan
git diff --check
run the local secret-scan pattern without hard-coding credentials into docs
```

Live command should require explicit flags even under bypass mode:

```bash
python3 scripts/revalidation/native_wifi_provider_ready_sdx50m_route_live_v1343.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-policy-load \
  --allow-provider-ready-sdx50m-route \
  --allow-cleanup-reboot \
  --assume-yes \
  run
```

V1343 still does not satisfy the final Wi-Fi objective unless `wlan0` readiness
is followed by a separate Wi-Fi HAL/scan/connect/DHCP/external-ping gate.
