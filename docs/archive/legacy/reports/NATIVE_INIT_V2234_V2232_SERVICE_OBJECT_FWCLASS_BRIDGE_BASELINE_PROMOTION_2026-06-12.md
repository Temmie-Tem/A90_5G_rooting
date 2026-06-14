# Native Init V2234 V2232 Service-Object FWClass Bridge Baseline Promotion

## Summary

- Promoted baseline: `A90 Linux init 0.9.266 (v2232-service-object-fwclass-bridge)`.
- Promotion run: `V2234`.
- Promoted artifact tag: `v2232-service-object-fwclass-bridge`.
- Decision: `v2234-v2232-service-object-fwclass-bridge-baseline-promotion-pass`.
- Result: PASS.
- Boot image:
  `workspace/private/inputs/boot_images/boot_linux_v2232_service_object_fwclass_bridge.img`.
- Boot SHA256:
  `dd56aa2dd8c0d9b2bafd1c12e23a3db6ba7095bea5e632ab03c5785fac69786c`.
- Helper marker string: `a90_android_execns_probe v427`.
- Helper SHA256:
  `062c7a491bee66bcb7112850f4581e53e58d923719d85dbbe651d9df285ee910`.
- Previous baseline:
  `A90 Linux init 0.9.261 (v2189-security-p0-stage-fix)`.
- Previous baseline boot image:
  `workspace/private/inputs/boot_images/boot_linux_v2189_security_p0_stage_fix.img`.
- Previous baseline SHA256:
  `f54becb2b720ad198413c2a0089912626ca295c79a96f13e0921cf4f05b39f51`.
- Emergency fallback:
  `workspace/private/inputs/boot_images/boot_linux_v2169_transport_contract.img`.

## Evidence

- Source/build report:
  `docs/reports/NATIVE_INIT_V2232_SERVICE_OBJECT_FWCLASS_BRIDGE_SOURCE_BUILD_2026-06-12.md`.
- Rollbackable live WLAN handoff:
  `docs/reports/NATIVE_INIT_V2233_SERVICE_OBJECT_FWCLASS_BRIDGE_HANDOFF_RUNNER_2026-06-12.md`.
- Baseline flash validation:
  `native_init_flash.py --from-native --expect-sha256 dd56aa2dd8c0d9b2bafd1c12e23a3db6ba7095bea5e632ab03c5785fac69786c`.
- Post-promotion read-only status checks:
  `a90ctl.py version`, `a90ctl.py selftest`, `a90ctl.py status`, `a90ctl.py wifi status`, and `busybox ifconfig wlan0`.

V2233 proved the service-object-visible route now reaches real native `wlan0`:

- helper supervisor ended `wlan0-ready`;
- `wlan0_present=1`;
- service-manager/PM registration, WLFW cap QMI, BDF result, FW_READY, and driver registration all completed;
- post-FW_READY `/sys/kernel/boot_wlan/boot_wlan` executed successfully;
- the bounded QCACLD firmware_class feeder supplied the observed `WCNSS_qcom_cfg.ini` request;
- rollback to V2189 ended with `selftest fail=0`.

The V2234 baseline flash proved:

- local image SHA matched the caller-pinned expected SHA;
- recovery ADB received the sealed image and remote SHA matched the local SHA;
- boot partition prefix readback SHA matched the local SHA;
- rebooted native init reported `A90 Linux init 0.9.266 (v2232-service-object-fwclass-bridge)`;
- `status` reported `selftest: pass=11 warn=1 fail=0`;
- explicit `selftest` reported `pass=11 warn=1 fail=0`;
- USB transport contract remained intact with `transport.contract=1`, `ncm=ready`, and `tcpctl=ready`;
- at uptime `245.33s`, `wifi status` reported `wlan0_present=1` and decision `wifi-status-wlan0-present`;
- `busybox ifconfig wlan0` showed the native `wlan0` netdev with redacted MAC evidence and no association attempted.

## Promotion Scope

V2234 promotes the already-built and live-validated V2232 artifact as the current native-init baseline. It changes the normal rollback/test starting point from V2189 to V2232.

The promoted baseline includes:

- all V2189 security P0 staged-artifact hardening;
- the existing USB ACM bridge, USB NCM, tcpctl, Wi-Fi lifecycle, HUD/menu, and screenapp command contracts;
- the service-object-visible service-manager/PM route that makes CNSS `libperipheral_client` registration visible;
- the post-FW_READY driver-start tail that runs the bounded `/sys/kernel/boot_wlan/boot_wlan` trigger;
- the bounded firmware_class fallback feeder for observed QCACLD firmware request nodes.

## Safety Scope

The promotion validation did not run Wi-Fi scan, association, credential use, DHCP, route/DNS changes, or external ping.

The only active WLAN driver-start action in the promoted route is the already bounded post-FW_READY `boot_wlan` write plus bounded firmware_class fallback writes for observed QCACLD request nodes. It does not use `/dev/subsys_esoc0`, forced RC1/case, eSoC notify/BOOT_DONE spoofing, PCI rescan, platform bind/unbind, PMIC/GPIO/GDSC/regulator writes, module load/unload, or `sda29` writes.

## Rollback And Fallback

- Current baseline/normal rollback target:
  `workspace/private/inputs/boot_images/boot_linux_v2232_service_object_fwclass_bridge.img`.
- Previous conservative rollback:
  `workspace/private/inputs/boot_images/boot_linux_v2189_security_p0_stage_fix.img`.
- Older UI/security fallback:
  `workspace/private/inputs/boot_images/boot_linux_v2187_screenapp_ui_validation.img`.
- Emergency transport fallback:
  `workspace/private/inputs/boot_images/boot_linux_v2169_transport_contract.img`.
- Known-good early fallback:
  `workspace/private/inputs/boot_images/boot_linux_v48.img`.

## Accepted Risk

- `wlan0` appears after the long native helper window, not immediately at shell-ready time. The observed post-promotion check reached `wlan0_present=1` at uptime `245.33s`.
- The helper binary marker string remains `a90_android_execns_probe v427`; use the helper SHA256 above to distinguish the V2232 route-specific helper build.
- V2234 promotes native `wlan0` readiness, not Wi-Fi connectivity. Scan/connect/DHCP/ping remain separate bounded validation scopes.

## Decision

`v2232-service-object-fwclass-bridge` is promoted as the current native-init baseline by V2234. Future normal rollback/test cycles should start from V2232 unless a test explicitly validates an older image.
