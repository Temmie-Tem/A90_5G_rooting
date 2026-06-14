# Native Init V679 Binder Registry Snapshot Live Report

## Summary

- helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- helper version: `a90_android_execns_probe v112`
- deploy wrapper: `scripts/revalidation/wifi_execns_helper_v112_deploy_preflight.py`
- live runner: `scripts/revalidation/native_wifi_v535_binder_registry_snapshot_orchestrator_v679.py`
- deploy evidence: `tmp/wifi/v679-execns-helper-v112-deploy-postfix/`
- live evidence: `tmp/wifi/v679-v535-binder-registry-snapshot-orchestrated-live/`
- decision: `v679-binder-registry-snapshot-captured`
- pass: `true`
- cleanup: pass
- scan/connect/DHCP/external ping: not executed

V679 added helper v112 and replayed the V535 property-seeded Android
userspace-order path with read-only Binder registry/debug snapshots. The live
run captured the snapshot phases and returned to healthy native control.

## Helper v112

| Item | Value |
| --- | --- |
| marker | `a90_android_execns_probe v112` |
| mode | `wifi-companion-service74-gated-android-userspace-cnss-retry-registry-snapshot-start-only` |
| sha256 | `a2c72c4157f6ddf089a40b2a5310288f3f0390ceced1f423519dcb8c1a8cc643` |
| build | static AArch64, no dynamic section |
| deploy | pass |

The first serial deploy attempt used an unsafe chunk size and was rejected by
the deploy guard before writing. The safe serial deploy wrote `739` chunks and
verified the target helper SHA.

## Live Result

| Marker | Count |
| --- | ---: |
| service-notifier `180` | `1` |
| service-notifier `74` | `1` |
| CNSS Binder transaction failure | `1` |
| Binder transaction failure | `1` |
| kernel warning | `1` |
| QMI server connected | `0` |
| WLFW start/request | `0` |
| BDF `regdb.bin` | `0` |
| BDF `bdwlan.bin` | `0` |
| WLAN firmware ready | `0` |
| `wlan0` | `0` |

Property surface stayed clean:

| Metric | Value |
| --- | ---: |
| property denial total | `0` |
| property denial unique | `0` |
| Binder failure count | `5` |

## Registry Snapshot

| Phase | End | Files | Dirs | Child Proc | Failed Tx Log |
| --- | --- | ---: | ---: | ---: | --- |
| `before_initial_cnss_cleanup` | `1` | `0` | `2` | `0` | not captured |
| `after_initial_cnss_cleanup` | `1` | `0` | `2` | `0` | not captured |
| `after_cnss_retry_spawn` | `1` | `0` | `2` | `0` | not captured |
| `window` | `1` | `0` | `2` | `0` | not captured |

The registry capture itself ran in all intended phases and saw the private
namespace property/socket directories. Binder debug files and per-child Binder
proc files were not captured, so the next blocker is Binder debugfs or alternate
Binder transaction observability rather than property layout.

## Cleanup

| Check | Result |
| --- | --- |
| version seen | pass |
| status healthy | pass |
| wait | `32.34s` |
| bridge reachable after run | pass |

## Interpretation

V679 confirms:

```text
V535 property root
  -> property denials remain 0
  -> Android userspace-order surface still starts
  -> service-notifier 180/74 still appears
  -> CNSS Binder transaction still fails
  -> Binder registry snapshot phases execute
  -> Binder debug files are unavailable/empty in this namespace
  -> WLFW/BDF/wlan0 remain absent
```

The next useful unit is V680: classify Binder debugfs availability and identify
an alternate way to observe the `cnss-daemon` vndbinder transaction target or
context-manager state. A Wi-Fi connection attempt is still premature because
`wlan0` does not exist.

## Validation

```sh
python3 -m py_compile \
  scripts/revalidation/native_wifi_v535_binder_registry_snapshot_v679.py \
  scripts/revalidation/native_wifi_v535_binder_registry_snapshot_orchestrator_v679.py \
  scripts/revalidation/wifi_execns_helper_v112_deploy_preflight.py

python3 scripts/revalidation/wifi_execns_helper_v112_deploy_preflight.py \
  --out-dir tmp/wifi/v679-execns-helper-v112-deploy-postfix \
  --transfer-method serial \
  --apply \
  --assume-yes \
  --approval-phrase "approve v679 deploy execns helper v112 only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/native_wifi_v535_binder_registry_snapshot_orchestrator_v679.py \
  --out-dir tmp/wifi/v679-v535-binder-registry-snapshot-orchestrated-live \
  --apply \
  --assume-yes \
  run
```

The validation passed with `v679-binder-registry-snapshot-captured`.
