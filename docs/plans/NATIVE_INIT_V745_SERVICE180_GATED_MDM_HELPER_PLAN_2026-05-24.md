# Native Init V745 Service180-gated MDM Helper Plan

- date: `2026-05-24 KST`
- helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- helper version: `a90_android_execns_probe v123`
- runner: `scripts/revalidation/native_wifi_mdm_helper_service180_live_v745.py`
- deploy wrapper: `scripts/revalidation/wifi_execns_helper_v123_deploy_preflight.py`

## Goal

Repair the V741 gated `mdm_helper` decision point by using the service-notifier
`180` marker that V744 proved is reproducible with helper v122. The proof still
starts `mdm_helper` only after lower/CNSS-only service publication and remains
below service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and
external ping.

## Change

Add a new helper mode:

```text
wifi-companion-service180-gated-mdm-helper-start-only
```

Expected order:

```text
qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon,service180_gate,mdm_helper
```

The implementation reuses the existing bounded companion window and klog
service-notifier state capture, but sets the gate target to service `180`
instead of service `74`.

## Safety Boundary

- Allowed: firmware read-only mounts, `subsys_modem` holder, lower companion
  stack, `cnss_diag`, `cnss-daemon`, service `180` gate, and bounded
  `mdm_helper` start-only if the gate opens.
- Forbidden: service-manager, Wi-Fi HAL, scan/connect/link-up, credentials,
  DHCP/routes, external ping, boot/partition writes.

## Success Criteria

1. Helper v123 static build passes and contains the new mode/order markers.
2. V745 runner plan passes with helper v123 metadata.
3. v123 deploy preflight passes and shows remote helper needs deploy.
4. Live deploy and V745 run remain separate, explicit next gates.
