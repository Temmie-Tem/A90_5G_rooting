# Native Init v252 CNSS Data Wi-Fi Runtime Surface Plan

## Summary

- target: v252 no-start `/data/vendor/wifi` runtime filesystem/socket surface
- baseline: v251 `cnss-property-read-only-surface`
- new host tool: `scripts/revalidation/wifi_cnss_data_wifi_surface.py`
- boot image change: none
- daemon start: not executed

v251 found `cnss-daemon` strings for `/data/vendor/wifi/sockets/cnss_user_server`
and `/data/vendor/wifi/sockets/cnss_user_client`. v252 checks whether the native
init environment currently exposes the expected `/data/vendor/wifi` runtime path
without creating directories or starting services.

## Scope

Read-only evidence only:

- v251 manifest decision
- current `cnss-daemon` absence
- `stat`/`ls -ld` for `/data`, `/data/vendor`, `/data/vendor/wifi`,
  `/data/vendor/wifi/sockets`
- bounded `find /data -maxdepth 4` for Wi-Fi/CNSS/socket hints
- host-side reuse of v251 string evidence

## Non-Goals

- do not create `/data/vendor/wifi`
- do not mount Android userdata
- do not change ownership/permissions
- do not start `cnss-daemon`
- do not scan/connect/link-up Wi-Fi

## Output

```text
tmp/wifi/v252-cnss-data-wifi-surface/
├── manifest.json
├── data-wifi-surface.json
├── live-captures.json
├── summary.md
└── captures/*.txt
```

Decision labels:

- `cnss-data-wifi-surface-ready`: expected directories/sockets are present.
- `cnss-data-wifi-surface-missing`: expected runtime path is absent but safely
  classified without mutation.
- `cnss-data-wifi-surface-blocked`: control path or prerequisite failed.

## Validation Plan

```bash
python3 -m py_compile scripts/revalidation/wifi_cnss_data_wifi_surface.py
git diff --check
python3 scripts/revalidation/wifi_cnss_data_wifi_surface.py \
  --out-dir tmp/wifi/v252-cnss-data-wifi-surface
python3 scripts/revalidation/a90ctl.py run /cache/bin/toybox pidof cnss-daemon || true
```
