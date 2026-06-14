# Native Init v253 Private Data Wi-Fi Materialization Report

## Summary

- status: PASS
- decision: `private-data-wifi-materialization-pass`
- boot image change: none
- helper update: `a90_android_execns_probe v9`
- helper SHA-256: `80e8afb1b77fdba23dfbc71d6a8e17e5a2a095ed1de728474fd2855923c351a1`
- daemon start: not executed
- output: `tmp/wifi/v253-private-data-wifi-probe/`
- host tool: `scripts/revalidation/wifi_cnss_private_data_wifi_probe.py`

v253 added helper-only `--data-wifi-mode private-empty`. The helper can now
materialize `/data/vendor/wifi/sockets` inside its temporary private root while
leaving real `/data/vendor/wifi` absent and unchanged.

## Build And Deploy

Build:

```bash
scripts/revalidation/build_android_execns_probe_helper.sh
```

Deploy:

```bash
python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_android_execns_probe \
  --toybox /cache/bin/toybox \
  install --local-binary stage3/linux_init/helpers/a90_android_execns_probe \
  --transfer-port 18088 --transfer-timeout 120.0
```

Device install result:

```text
installed /cache/bin/a90_android_execns_probe sha256=80e8afb1b77fdba23dfbc71d6a8e17e5a2a095ed1de728474fd2855923c351a1
```

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_cnss_private_data_wifi_probe.py \
  scripts/revalidation/wifi_cnss_start_only_runner.py \
  scripts/revalidation/wifi_cnss_runtime_primitives_preflight.py \
  scripts/revalidation/wifi_cnss_runtime_gap_classifier.py
git diff --check
python3 scripts/revalidation/wifi_cnss_private_data_wifi_probe.py \
  --out-dir tmp/wifi/v253-private-data-wifi-probe
python3 scripts/revalidation/a90ctl.py stat /data/vendor/wifi || true
python3 scripts/revalidation/a90ctl.py run /cache/bin/toybox pidof cnss-daemon || true
```

Result:

```text
decision: private-data-wifi-materialization-pass
pass: True
```

Post-checks:

- real `/data/vendor/wifi`: still missing, rc=-2
- `pidof cnss-daemon`: rc=1

## Private Namespace Evidence

| Path | State |
| --- | --- |
| `/data` | exists, uid=0 gid=0 mode=0771 |
| `/data/vendor` | exists, uid=0 gid=0 mode=0771 |
| `/data/vendor/wifi` | exists, uid=1000 gid=1010 mode=0770 |
| `/data/vendor/wifi/sockets` | exists, uid=1000 gid=1010 mode=0770 |

The helper remained in no-allow mode:

```text
cnss_start.result=start-only-blocked
cnss_start.exec_attempted=0
cnss_start.reason=missing-allow-cnss-start-only
```

## Interpretation

- The `/data/vendor/wifi` runtime filesystem gap can be closed inside the helper
  private namespace without mutating real `/data`.
- This makes a bounded start-only attempt less likely to fail on missing runtime
  directory creation alone.
- It still does not recreate Android property service, SELinux domain
  transition, framework service manager, or Wi-Fi scan/connect state.

## Guardrails Preserved

- no real `/data/vendor/wifi` creation
- no userdata mount/remount
- no ownership/permission mutation outside helper temp root
- no `cnss-daemon` execution
- no rfkill unblock, `wlan*` link-up, scan/connect, credentials, DHCP, or routing
- no ICNSS bind/unbind, firmware mutation, Android partition write, or reboot

## Next Step

The first bounded live start-only attempt remains approval-gated. If approval is
still withheld, the next safe task is updating the start-only runner dry-run plan
to include `--data-wifi-mode private-empty` and `--null-device-mode dev-null-selinux`
as the proposed live profile, without running it.
