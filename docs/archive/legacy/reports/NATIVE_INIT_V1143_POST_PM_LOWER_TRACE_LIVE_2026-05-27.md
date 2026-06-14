# Native Init V1143 Post-PM Lower-Trace Live Report

Date: `2026-05-27`

## Result

- Decision: `v1143-post-pm-lower-trace-no-advance`
- Pass: `true`
- Runner: `scripts/revalidation/native_wifi_post_pm_lower_trace_live_v1143.py`
- Manifest: `tmp/wifi/v1143-post-pm-lower-trace-live/manifest.json`
- Summary: `tmp/wifi/v1143-post-pm-lower-trace-live/summary.md`
- V401 evidence: `tmp/wifi/v1143-r2-v401-selinuxfs-mount`
- V490 evidence: `tmp/wifi/v1143-r2-v490-policy-load-after-system`
- Preserved ptrace trial: `tmp/wifi/v1143-post-pm-lower-trace-live-ptrace`

## Summary

V1143 reused the V1139 post-policy PM/CNSS route with helper `v215` and enabled
the new lower-trace flag:

```text
--allow-post-pm-mdm-helper-lower-trace
```

The final live run intentionally did not force `--capture-mode ptrace-lite`.
The earlier ptrace trial was preserved because it changed timing enough that
`mdm_helper` was not observable in the post-PM lower window.

## Observed State

| key | value |
| --- | --- |
| PM register/connect | `0x0` / `0x0` |
| `mss` | `OFFLINING -> ONLINE -> ONLINE` |
| `mdm3` | `OFFLINING -> OFFLINING -> OFFLINING` |
| QRTR services `69/74/180` | all `0` after observer |
| lower trace samples | `3` |
| `mdm_helper` pid state | alive, `S` |
| `mdm_helper` fd `/dev/esoc-0` | `1` |
| `mdm_helper` fd `/dev/subsys_esoc0` | `0` |
| `mdm_helper` fd MHI pipe | `0` |
| `/vendor/bin/ks` process | `0` |
| WLFW/service69/wlan0 | not observed |

The useful thread-level finding is stable across all three samples:

```text
mdm_helper main thread: SyS_nanosleep
mdm_helper worker thread: esoc_dev_ioctl
ioctl fd=3 request=0x8004cc02
fd 3 target=/tmp/a90-v231-823/root/dev/esoc-0
```

## Interpretation

The upper route is no longer the active blocker:

```text
policy-loaded Android domains
  -> service-manager trio
  -> PM provider
  -> cnss-daemon PM register/connect OK
  -> mdm_helper starts after CNSS
```

The remaining blocker is lower:

```text
mdm_helper /dev/esoc-0 ioctl waits
  -> no /dev/subsys_esoc0 fd
  -> no MHI pipe
  -> no ks process
  -> no mdm3 ONLINE
  -> no WLFW service69
```

So V1071 `pm-service exit 255`/BPF-uProbe remains obsolete. The next useful
unit should classify the specific `esoc_dev_ioctl` request `0x8004cc02` and the
expected userspace response/contract for Samsung's proprietary eSoC path.

## Safety

- Wi-Fi HAL start: `false`
- Scan/connect/link-up: `false`
- Credential use: `false`
- DHCP/route: `false`
- External ping: `false`
- Boot image/partition write/flash: not executed
- Cleanup reboot completed; post-reboot version/selftest were healthy.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_post_pm_lower_trace_live_v1143.py
python3 scripts/revalidation/wifi_selinuxfs_toybox_mount_live_executor.py \
  --out-dir tmp/wifi/v1143-r2-v401-selinuxfs-mount \
  --apply --assume-yes \
  --approval-phrase 'approve v401 toybox mount selinuxfs runtime surface only; no daemon start and no Wi-Fi bring-up' \
  run
python3 scripts/revalidation/a90ctl.py --timeout 20 mountsystem ro
python3 scripts/revalidation/native_selinux_policy_load_proof_v490.py \
  --out-dir tmp/wifi/v1143-r2-v490-policy-load-after-system \
  --helper-sha256 7bf107db54e4e3b2f9bbee196d40564ab4c62b2de1bcaa392ba843a6a6f3419e \
  --apply --assume-yes \
  --approval-phrase 'approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up' \
  run
python3 scripts/revalidation/native_wifi_post_pm_lower_trace_live_v1143.py \
  --allow-vendor-mount \
  --allow-selinuxfs-mount \
  --allow-tracefs-mount \
  --allow-tracefs-write \
  --allow-pm-service-trigger-observer \
  --allow-cnss-daemon-start \
  --assume-yes \
  run
python3 scripts/revalidation/a90ctl.py --timeout 8 version
python3 scripts/revalidation/a90ctl.py --timeout 8 selftest
```

## Next

V1144 should be host-only/source analysis first: map `ESOC_*` ioctl request
`0x8004cc02` against Samsung OSRC headers, linux-msm eSoC references, and
captured `mdm_helper` behavior. Do not retry HAL/scan/connect until the
`esoc_dev_ioctl` wait contract is understood.
