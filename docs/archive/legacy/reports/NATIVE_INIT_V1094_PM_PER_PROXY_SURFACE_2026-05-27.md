# Native Init V1094 PM Per-Proxy Surface Report

## Summary

V1094 passed. The PM observer now continues past `pm-service` provider
registration, starts `pm-proxy`, verifies the provider remains visible, and
captures the lower surface again. The result is still mdm3/WLFW negative.

Decision:

```text
v1094-per-proxy-no-pm-fd-mdm3-still-offline
```

This closes the hypothesis that merely adding `pm-proxy` after the provider
appears will make `pm-service` or `pm_proxy_helper` open `/dev/subsys_modem`.
The next blocker is a missing lower PM client/voter trigger or eSoC trigger,
not PM provider registration.

## Evidence

| item | path |
| --- | --- |
| helper source | `stage3/linux_init/helpers/a90_android_execns_probe.c` |
| deploy wrapper | `scripts/revalidation/wifi_execns_helper_v205_deploy_preflight.py` |
| live wrapper | `scripts/revalidation/native_wifi_pm_per_proxy_surface_live_v1094.py` |
| helper artifact | `tmp/wifi/v1094-execns-helper-v205-build/a90_android_execns_probe` |
| deploy evidence | `tmp/wifi/v1094-execns-helper-v205-deploy/manifest.json` |
| live evidence | `tmp/wifi/v1094-pm-per-proxy-surface-live/manifest.json` |
| V490 evidence | `tmp/wifi/v490-native-selinux-policy-load-proof/manifest.json` |

## Result

```text
helper: a90_android_execns_probe v205
sha256: 0b93ada5ceaf868cd907d3ad2fcd5986485024fa05bdfe3780daee945984af0f
vndservicemanager_ready: True
vndservice_provider_seen: True
after_per_mgr_query: True
after_per_proxy_query: True
post_provider_surface_present: True
post_provider_mdm3_state: OFFLINING
post_provider_wlfw_service69_seen: False
pm_service_subsys_modem_seen: False
pm_proxy_helper_subsys_modem_seen: False
wifi_hal_start_executed: False
wifi_bringup_executed: False
external_ping_executed: False
```

The after-`pm-proxy` fd snapshot returned:

```text
pm_service_trigger_observer.after_per_proxy.per_mgr_subsys_modem_count=0
pm_service_trigger_observer.after_per_proxy.pm_proxy_helper_subsys_modem_count=0
pm_service_trigger_observer.after_per_proxy.per_mgr_vndbinder_count=1
pm_service_trigger_observer.after_per_proxy.pm_proxy_helper_vndbinder_count=0
```

The after-`pm-proxy` lower surface returned:

```text
pm_service_trigger_observer.post_provider_surface.after_per_proxy.mdm3_state=OFFLINING
pm_service_trigger_observer.post_provider_surface.after_per_proxy.mdm3_crash_count=0
pm_service_trigger_observer.post_provider_surface.after_per_proxy.mdm3_firmware_name=esoc0
pm_service_trigger_observer.post_provider_surface.after_per_proxy.qcwlanstate_exists=0
pm_service_trigger_observer.post_provider_surface.after_per_proxy.wlan0_exists=0
```

Both provider queries exited cleanly:

```text
wifi_vndservice_query.pm_observer_after_per_mgr_probe.result=query-exit-zero
wifi_vndservice_query.pm_observer_after_per_proxy_probe.result=query-exit-zero
```

QRTR readback for services `69`, `74`, and `180` completed but saw no service
events in the after-`pm-proxy` window.

## Implementation Notes

- `a90_android_execns_probe v205` adds `--pm-observer-continue-after-provider`
  and records `after_per_proxy` fd/lower-surface snapshots.
- The helper also bounds inherited-pipe handling in `vndservice list`; this
  prevents a daemonized child from keeping the query pipe open after the query
  process exits.
- The V1094 live wrapper uses serial `a90ctl` for helper execution and post-run
  checks. This avoids the `a90_tcpctl run` 10 second device-side timeout that
  made earlier V1094 attempts look like helper-mode failures.

## Safety

- No Wi-Fi HAL, scan/connect/link-up, DHCP, route, credential use, or external
  ping executed.
- No CNSS daemon or `mdm_helper` executed.
- No eSoC open/ioctl, GPIO write, partition write, flash, or reboot executed in
  the passing run.
- QRTR readback used nameservice lookup/readback only and sent no QMI payload.
- Device remained healthy: post-run `selftest` reported `fail=0`.

## Interpretation

V1071-era `pm-service exit 255` and BPF/uprobe work is no longer the active
blocker for the current path. V1092 through V1094 prove that the provider can be
registered and can remain visible through `pm-proxy`, but the PM stack still
does not produce a `/dev/subsys_modem` fd or advance mdm3/WLFW.

Candidate next checks:

1. Classify what Android provides after provider registration that creates the
   first lower PM client/voter trigger.
2. Compare Android-good PM/eSoC timing against the V1094 provider-positive,
   no-fd window.
3. Keep V1094 as the PM upper-layer precondition; do not expand to Wi-Fi HAL or
   scan/connect until mdm3/WLFW moves.

## Validation

Executed:

```bash
scripts/revalidation/build_android_execns_probe_helper.sh tmp/wifi/v1094-execns-helper-v205-build/a90_android_execns_probe
python3 -m py_compile scripts/revalidation/native_wifi_pm_post_provider_surface_live_v1093.py scripts/revalidation/native_wifi_pm_per_proxy_surface_live_v1094.py scripts/revalidation/wifi_execns_helper_v205_deploy_preflight.py
python3 scripts/revalidation/wifi_execns_helper_v205_deploy_preflight.py --approval-phrase "approve v1094 deploy execns helper v205 only; no daemon start and no Wi-Fi bring-up" --apply --assume-yes run
python3 scripts/revalidation/native_selinux_policy_load_proof_v490.py --helper-sha256 0b93ada5ceaf868cd907d3ad2fcd5986485024fa05bdfe3780daee945984af0f --approval-phrase "approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up" --apply --assume-yes run
python3 scripts/revalidation/native_wifi_pm_per_proxy_surface_live_v1094.py --helper-sha256 0b93ada5ceaf868cd907d3ad2fcd5986485024fa05bdfe3780daee945984af0f --helper-marker "a90_android_execns_probe v205" --local-helper tmp/wifi/v1094-execns-helper-v205-build/a90_android_execns_probe --helper-timeout-sec 16 --toybox-timeout-sec 100 --allow-mountsystem-ro --allow-selinuxfs-mount --allow-pm-service-trigger-observer --allow-cleanup-reboot --assume-yes run
```

Result:

```text
decision: v1094-per-proxy-no-pm-fd-mdm3-still-offline
pass: True
```
