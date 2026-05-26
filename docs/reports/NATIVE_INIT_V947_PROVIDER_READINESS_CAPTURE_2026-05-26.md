# V947 Provider-Readiness Capture Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| live wrapper | `scripts/revalidation/native_wifi_provider_readiness_capture_v947.py` | `py_compile pass` |
| bounded live capture | `tmp/wifi/v947-provider-readiness-capture-live/manifest.json` | `v947-provider-readiness-captured` |

V947 ran helper `v157` in the existing
`wifi-companion-mdm-helper-runtime-contract-capture` path and captured the new
`mdm_helper_provider_readiness.*` fields. The run remained bounded and cleanup
safe.

## Live Scope

Allowed actions:

- `mountsystem ro`;
- SELinuxfs mount and unmount;
- private property-service shim;
- `/vendor/bin/pm-service`;
- `/vendor/bin/mdm_helper`;
- read-only postflight surfaces.

Forbidden actions remained blocked:

- `pm_proxy_helper`;
- service-manager/CNSS/Wi-Fi HAL start;
- controller `/dev/subsys_esoc0` open;
- eSoC notify or boot-done;
- scan/connect/link-up, credentials, DHCP/routes, external ping.

## Key Findings

| Phase | svc | hwsvc | vndsvc | pm-service | pm-proxy | pm-proxy-helper | pm vndbinder | pm subsys_modem | pm subsys_esoc0 | mdm esoc0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `after_per_mgr_settle` | `0` | `0` | `0` | `1` | `0` | `0` | `1` | `0` | `0` | `-1` |
| `after_mdm_helper_spawn` | `0` | `0` | `0` | `1` | `0` | `0` | `1` | `0` | `0` | `0` |
| `window` | `0` | `0` | `0` | `1` | `0` | `0` | `1` | `0` | `0` | `1` |
| `final` | `0` | `0` | `0` | `1` | `0` | `0` | `1` | `0` | `0` | `1` |

Interpretation:

- private binder nodes were present;
- private property-service socket was present during the live window;
- `pm-service` opened `vndbinder`;
- `pm-service` did not hold `/dev/subsys_modem` or `/dev/subsys_esoc0`;
- `mdm_helper` reached `/dev/esoc-0`;
- `pm-proxy`, `pm_proxy_helper`, `ks`, MHI, WLFW, BDF, and `wlan0` did not
  appear.

## Cleanup and Health

- cleanup reboot: `false`
- postflight actors: clean
- postflight native health: `bootstatus` and `selftest` passed with `fail=0`

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_provider_readiness_capture_v947.py
python3 scripts/revalidation/native_wifi_provider_readiness_capture_v947.py plan
python3 scripts/revalidation/native_wifi_provider_readiness_capture_v947.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-runtime-contract-capture \
  --allow-cleanup-reboot \
  --assume-yes \
  run
python3 scripts/revalidation/a90ctl.py bootstatus
python3 scripts/revalidation/a90ctl.py selftest
```

## Next

Classify V947 before starting `pm_proxy_helper`, opening `/dev/subsys_esoc0`, or
expanding toward Wi-Fi HAL.
