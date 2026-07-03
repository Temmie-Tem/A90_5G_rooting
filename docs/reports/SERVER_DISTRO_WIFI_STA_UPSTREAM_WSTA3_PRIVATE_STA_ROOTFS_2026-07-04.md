# SERVER_DISTRO_WIFI_STA_UPSTREAM_WSTA3_PRIVATE_STA_ROOTFS_2026-07-04

## Verdict

WSTA3 private STA rootfs staging is host-only PASS.

The run prepared a private Debian userdata rootfs copy with the Wi-Fi STA opt-in files staged, while keeping SSID/PSK values, raw `wpa_supplicant` text, and secret-derived archive hashes out of public output.

## Inputs

- Source rootfs: `workspace/private/builds/server-distro/d3-sysvinit-usrmerge-wsta-20260704T0225Z-rootfs`
- Private Wi-Fi env: `workspace/private/secrets/a90-wifi-test.env`
- Public tool: `workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py`
- Test module: `tests/test_prepare_wsta3_sta_rootfs.py`

The Wi-Fi env file was checked as owner-private mode `0600`. Raw values were not printed or copied into this report.

## Host Run

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py \
  --run-id wsta3-sta-rootfs-20260703T173658Z
```

Result:

- Decision: `wsta3-private-rootfs-prepared`
- Run dir: `workspace/private/runs/server-distro/wsta3-sta-rootfs-20260703T173658Z`
- Target rootfs: `workspace/private/runs/server-distro/wsta3-sta-rootfs-20260703T173658Z/rootfs`
- Private tarball: `workspace/private/runs/server-distro/wsta3-sta-rootfs-20260703T173658Z/a90-wsta3-userdata-rootfs.tar`
- Tarball size: `272035840` bytes
- Tarball SHA: redacted by design because the archive contains private STA config

Mode checks:

- Run dir: `0700`
- Generated config: `0600`
- Rootfs staged config: `0600`
- Rootfs opt-in marker: `0600`
- Private tarball: `0600`

Tarball content check confirmed required entries:

- `./etc/a90-dpublic/wifi-sta-enable`
- `./etc/a90-dpublic/wpa_supplicant-wlan0.conf`
- `./usr/local/bin/a90-dpublic-wifi-sta`

Summary leak scan found no `ssid=`, `psk=`, `A90_WIFI`, key material, serial, MAC/BSSID, PARTUUID, URL, or token patterns in `summary.json`.

## Device Scope

No device action was performed:

- No flash
- No reboot
- No userdata format or mount
- No Wi-Fi association
- No DHCP
- No ping
- No public tunnel

WSTA2 live remains the gate before using this private rootfs in a device STA association run.

## Validation

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py \
  tests/test_prepare_wsta3_sta_rootfs.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_prepare_wsta3_sta_rootfs \
  tests.test_server_distro_wsta2_native_materialization \
  tests.test_server_distro_wifi_sta_upstream_plan \
  tests.test_dpublic_smoke_helpers \
  tests.test_server_distro_debian_rootfs_builder \
  tests.test_server_distro_d3_sysvinit_rootfs \
  tests.test_prepare_d4c_userdata_rootfs_tarball

git diff --check
```

Result: 35 tests passed, `git diff --check` clean.

## Next

Recover native cmdv1 or recovery ADB under the checked recovery envelope, run the WSTA2 V3384 native `wlan0` materialization live gate, then use this private STA rootfs/tarball for the bounded WSTA3 Debian association/DHCP/default-route validation.
