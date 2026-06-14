# Native Init V1065 Helper v181 Deploy Report

Date: `2026-05-27`

## Summary

V1065 deployed helper `a90_android_execns_probe v181` to `/cache/bin/a90_android_execns_probe` over the authenticated NCM/TCP path. No Android daemon, CNSS, Wi-Fi HAL, scan/connect, DHCP, external ping, eSoC, subsystem trigger, firmware, boot image, or partition mutation was performed.

## Evidence

Local artifact:

```text
path=tmp/wifi/v1064-pm-service-trigger-observer-helper/a90_android_execns_probe
sha256=74eaa88bf8221715ed2afae654e53eb7571037655dd6b8e0df0966ab454ef9ce
size=1188336
```

Deploy command:

```bash
python3 scripts/revalidation/tcpctl_host.py \
  --device-ip 192.168.7.2 \
  --tcp-port 2325 \
  --tcp-timeout 20 \
  --device-binary /cache/bin/a90_android_execns_probe \
  --toybox /cache/bin/toybox \
  install \
  --local-binary tmp/wifi/v1064-pm-service-trigger-observer-helper/a90_android_execns_probe \
  --transfer-port 18084 \
  --transfer-delay 0.5 \
  --transfer-timeout 120
```

Transfer result:

```text
1188336 bytes copied, 0.020 s, 57 MB/s
remote tmp sha256=74eaa88bf8221715ed2afae654e53eb7571037655dd6b8e0df0966ab454ef9ce
installed /cache/bin/a90_android_execns_probe sha256=74eaa88bf8221715ed2afae654e53eb7571037655dd6b8e0df0966ab454ef9ce
```

Remote parity:

```text
74eaa88bf8221715ed2afae654e53eb7571037655dd6b8e0df0966ab454ef9ce  /cache/bin/a90_android_execns_probe
a90_android_execns_probe v181
wifi-companion-pm-service-trigger-observer
--allow-pm-service-trigger-observer
```

Post-deploy health:

```text
selftest: pass=11 warn=1 fail=0
netservice: ncm0=present tcpctl=running pid=551
netservice: auth=required
```

## Outcome

- PASS: helper `v181` was deployed to `/cache/bin/a90_android_execns_probe`.
- PASS: remote sha256 equals local artifact sha256.
- PASS: remote usage exposes the new PM-service trigger observer mode and allow flag.
- PASS: native health and authenticated NCM/TCP remained available after deploy.

## Next Step

V1066 should run the bounded PM-service trigger observer live using helper `v181`. The live gate must still avoid `mdm_helper`, CNSS, Wi-Fi HAL, scan/connect, DHCP, external ping, eSoC ioctl, and subsystem trigger operations.
