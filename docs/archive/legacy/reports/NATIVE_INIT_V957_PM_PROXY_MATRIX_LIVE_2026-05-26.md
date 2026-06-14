# V957 PM-Proxy Matrix Live Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| live wrapper | `scripts/revalidation/native_wifi_pm_proxy_matrix_capture_v957.py` | `py_compile pass` |
| bounded live capture | `tmp/wifi/v957-pm-proxy-matrix-live/manifest.json` | `v957-wlfw-precondition-missing-no-open` |

V957 ran helper `v159` with
`service_manager_order=after-mdm-helper-esoc-fd-with-pm-proxy`. The run started
`pm-service`, then `pm-proxy`, then `mdm_helper`, waited for the
`/dev/esoc-0` fd, and then started service managers plus CNSS actors.

The run stayed fail-closed: WLFW did not appear and `/dev/subsys_esoc0` remained
unopened.

## Provider Finding

| Phase | svc | hwsvc | vndsvc | pm-service | pm-proxy | pm-proxy-helper | pm vndbinder |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `after_per_mgr_settle` | `0` | `0` | `0` | `1` | `0` | `0` | `1` |
| `after_pm_proxy_start` | `0` | `0` | `0` | `1` | `1` | `0` | `1` |
| `after_mdm_helper_spawn` | `0` | `0` | `0` | `1` | `1` | `0` | `1` |
| `after_service_manager_start` | `1` | `1` | `1` | `1` | `1` | `0` | `1` |
| `after_cnss_daemon_start` | `1` | `1` | `1` | `1` | `1` | `0` | `1` |
| `final` | `1` | `1` | `1` | `0` | `0` | `0` | `-1` |

Interpretation: `pm-proxy` repairs the provider-surface lifetime that V953 lost
when service managers started. It does not by itself make CNSS emit the WLFW
precondition.

## Guardrails

- No `pm_proxy_helper`.
- No Wi-Fi HAL start.
- No scan/connect/link-up.
- No credentials, DHCP/routes, or external ping.
- No controller eSoC notify or boot-done.
- No `/dev/subsys_esoc0` open.

## Device Health

Post-run checks:

- `bootstatus`: `BOOT OK`, `selftest: fail=0`
- `selftest`: `fail=0`
- `netservice`: flag disabled, `ncm0=present`, `tcpctl=stopped`

## Validation

Executed:

```bash
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/native_wifi_pm_proxy_matrix_capture_v957.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-cnss-service-manager-matrix \
  --allow-cleanup-reboot \
  --assume-yes \
  run
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py selftest
python3 scripts/revalidation/a90ctl.py netservice status
```

## Next

Classify V957 against V953 before any broader live action.
