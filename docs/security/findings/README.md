# Codex Security Findings Index

Source CSV: `docs/security/codex-security-findings-2026-05-05T16-26-57.929Z.csv`
Source split file: `docs/security/CODEX_SECURITY_FINDINGS_DETAIL_TEMPLATE_2026-05-06.md`
Fresh scan follow-up: `F032` and `F033` were imported from the 2026-05-07 Codex Cloud scan.

이 디렉터리는 Codex Cloud security finding 원문을 이슈별 파일로 분리한 보관소입니다.
관계 분석과 수정 큐는 별도 문서에서 이 `FNNN` 번호를 참조합니다.

## Analysis Documents

- Relationship analysis: `../SECURITY_FINDINGS_RELATIONSHIP_2026-05-06.md`
- Fix queue: `../SECURITY_FIX_QUEUE_2026-05-06.md`
- Current exposure map: `../SECURITY_FINDINGS_CURRENT_EXPOSURE_2026-05-06.md`
- Closure review: `../SECURITY_FINDINGS_CLOSURE_REVIEW_2026-05-07.md`
- Fresh local rescan: `../SECURITY_FRESH_SCAN_V133_2026-05-07.md`
- Fresh v134 local rescan: `../SECURITY_FRESH_SCAN_V134_2026-05-07.md`

## Findings

| id | severity | status | title | file | relevant paths |
|---|---|---|---|---|---|
| F001 | `high` | `mitigated-v123` | rshell start exposes unauthenticated tcpctl root command port | [`F001-rshell-start-exposes-unauthenticated-tcpctl-root-command-port.md`](F001-rshell-start-exposes-unauthenticated-tcpctl-root-command-port.md) | stage3/linux_init/v100/70_storage_android_net.inc.c <br> stage3/linux_init/a90_netservice.c <br> stage3/linux_init/a90_tcpctl.c |
| F002 | `high` | `mitigated-v124` | Helper manifest can redirect cpustress to unverified code | [`F002-helper-manifest-can-redirect-cpustress-to-unverified-code.md`](F002-helper-manifest-can-redirect-cpustress-to-unverified-code.md) | stage3/linux_init/a90_helper.c <br> stage3/linux_init/v98/60_shell_basic_commands.inc.c <br> stage3/linux_init/a90_run.c |
| F003 | `high` | `mitigated-v123` | Boot flag enables persistent unauthenticated tcpctl exposure | [`F003-boot-flag-enables-persistent-unauthenticated-tcpctl-exposure.md`](F003-boot-flag-enables-persistent-unauthenticated-tcpctl-exposure.md) | stage3/linux_init/init_v60.c <br> stage3/linux_init/a90_tcpctl.c |
| F004 | `high` | `mitigated-v124` | tcpctl_host install race allows root helper replacement | [`F004-tcpctl-host-install-race-allows-root-helper-replacement.md`](F004-tcpctl-host-install-race-allows-root-helper-replacement.md) | scripts/revalidation/tcpctl_host.py |
| F005 | `high` | `mitigated-v123` | Unauthenticated NCM tcpctl allows root command execution | [`F005-unauthenticated-ncm-tcpctl-allows-root-command-execution.md`](F005-unauthenticated-ncm-tcpctl-allows-root-command-execution.md) | stage3/linux_init/a90_tcpctl.c |
| F006 | `high` | `mitigated-host-batch5` | Hardcoded root SSH credentials enabled by automation scripts | [`F006-hardcoded-root-ssh-credentials-enabled-by-automation-scripts.md`](F006-hardcoded-root-ssh-credentials-enabled-by-automation-scripts.md) | scripts/archive/legacy/utils/create_rootfs.sh <br> scripts/archive/legacy/magisk_module/systemless_chroot/service.d/boot_chroot.sh <br> scripts/archive/legacy/magisk_module/headless_boot_v2/service.sh |
| F007 | `high` | `mitigated-host-batch5` | Unsafe archive extraction enables host file overwrite | [`F007-unsafe-archive-extraction-enables-host-file-overwrite.md`](F007-unsafe-archive-extraction-enables-host-file-overwrite.md) | mkbootimg/gki/certify_bootimg.py |
| F008 | `medium` | `mitigated-host-batch3` | Soak validator can execute a90ctl from an untrusted CWD | [`F008-soak-validator-can-execute-a90ctl-from-an-untrusted-cwd.md`](F008-soak-validator-can-execute-a90ctl-from-an-untrusted-cwd.md) | scripts/revalidation/native_soak_validate.py |
| F009 | `medium` | `mitigated-v125` | Diagnostics bundles are written with weak file permissions | [`F009-diagnostics-bundles-are-written-with-weak-file-permissions.md`](F009-diagnostics-bundles-are-written-with-weak-file-permissions.md) | stage3/linux_init/a90_diag.c <br> stage3/linux_init/a90_runtime.c <br> scripts/revalidation/diag_collect.py |
| F010 | `medium` | `mitigated-v123` | Service command bypasses dangerous-command gating | [`F010-service-command-bypasses-dangerous-command-gating.md`](F010-service-command-bypasses-dangerous-command-gating.md) | stage3/linux_init/a90_service.c <br> stage3/linux_init/v101/80_shell_dispatch.inc.c <br> stage3/linux_init/a90_controller.c <br> stage3/linux_init/a90_tcpctl.c |
| F011 | `medium` | `mitigated-v124` | Runtime SD probes follow symlinks as root | [`F011-runtime-sd-probes-follow-symlinks-as-root.md`](F011-runtime-sd-probes-follow-symlinks-as-root.md) | stage3/linux_init/a90_config.h <br> stage3/linux_init/v97/90_main.inc.c <br> stage3/linux_init/a90_runtime.c <br> stage3/linux_init/a90_util.c |
| F012 | `medium` | `mitigated-v124` | mountsd redirects logs to unverified SD media | [`F012-mountsd-redirects-logs-to-unverified-sd-media.md`](F012-mountsd-redirects-logs-to-unverified-sd-media.md) | stage3/linux_init/a90_config.h <br> stage3/linux_init/a90_storage.c <br> stage3/linux_init/a90_log.c |
| F013 | `medium` | `mitigated-v124` | v79 SD probe enables symlink-based root file clobber | [`F013-v79-sd-probe-enables-symlink-based-root-file-clobber.md`](F013-v79-sd-probe-enables-symlink-based-root-file-clobber.md) | stage3/linux_init/init_v79.c |
| F014 | `medium` | `mitigated-v123` | Reconnect checker can silently leave tcpctl running | [`F014-reconnect-checker-can-silently-leave-tcpctl-running.md`](F014-reconnect-checker-can-silently-leave-tcpctl-running.md) | scripts/revalidation/physical_usb_reconnect_check.py <br> scripts/revalidation/netservice_reconnect_soak.py <br> stage3/linux_init/a90_tcpctl.c |
| F015 | `medium` | `mitigated-host-batch3` | Cmdv1 retry can replay privileged commands on reconnect | [`F015-cmdv1-retry-can-replay-privileged-commands-on-reconnect.md`](F015-cmdv1-retry-can-replay-privileged-commands-on-reconnect.md) | scripts/revalidation/a90ctl.py <br> scripts/revalidation/serial_tcp_bridge.py <br> stage3/linux_init/init_v73.c |
| F016 | `medium` | `mitigated-host-batch3` | cmdv1 framing can be spoofed by injected A90P1 END output | [`F016-cmdv1-framing-can-be-spoofed-by-injected-a90p1-end-output.md`](F016-cmdv1-framing-can-be-spoofed-by-injected-a90p1-end-output.md) | scripts/revalidation/a90ctl.py <br> stage3/linux_init/init_v73.c |
| F017 | `medium` | `mitigated-host-batch3` | Untrusted MAC can trigger sudo reconfig of wrong host NIC | [`F017-untrusted-mac-can-trigger-sudo-reconfig-of-wrong-host-nic.md`](F017-untrusted-mac-can-trigger-sudo-reconfig-of-wrong-host-nic.md) | scripts/revalidation/netservice_reconnect_soak.py |
| F018 | `medium` | `mitigated-host-batch3` | Untrusted device MAC drives sudo host network reconfiguration | [`F018-untrusted-device-mac-drives-sudo-host-network-reconfiguration.md`](F018-untrusted-device-mac-drives-sudo-host-network-reconfiguration.md) | scripts/revalidation/ncm_host_setup.py |
| F019 | `medium` | `mitigated-host-batch3` | Auto re-enumeration check allows serial bridge device hijack | [`F019-auto-re-enumeration-check-allows-serial-bridge-device-hijack.md`](F019-auto-re-enumeration-check-allows-serial-bridge-device-hijack.md) | scripts/revalidation/serial_tcp_bridge.py |
| F020 | `medium` | `mitigated-host-batch3` | ADB shell command injection via unsanitized CLI path options | [`F020-adb-shell-command-injection-via-unsanitized-cli-path-options.md`](F020-adb-shell-command-injection-via-unsanitized-cli-path-options.md) | scripts/revalidation/native_init_flash.py |
| F021 | `medium` | `accepted-lab-boundary` | Unauthenticated USB ACM root shell enabled at boot | [`F021-unauthenticated-usb-acm-root-shell-enabled-at-boot.md`](F021-unauthenticated-usb-acm-root-shell-enabled-at-boot.md) | stage3/linux_init/init_v30.c |
| F022 | `low` | `mitigated-host-batch3` | Predictable /tmp file in BusyBox build validation | [`F022-predictable-tmp-file-in-busybox-build-validation.md`](F022-predictable-tmp-file-in-busybox-build-validation.md) | scripts/revalidation/build_static_busybox.sh |
| F023 | `low` | `mitigated-v127` | Auto-menu busy-gate bypass allows risky root commands | [`F023-auto-menu-busy-gate-bypass-allows-risky-root-commands.md`](F023-auto-menu-busy-gate-bypass-allows-risky-root-commands.md) | stage3/linux_init/init_v72.c <br> stage3/linux_init/init_v70.c |
| F024 | `low` | `mitigated-v125` | HUD log-tail feature introduces on-screen info disclosure | [`F024-hud-log-tail-feature-introduces-on-screen-info-disclosure.md`](F024-hud-log-tail-feature-introduces-on-screen-info-disclosure.md) | stage3/linux_init/init_v68.c |
| F025 | `low` | `mitigated-v125` | World-readable fallback log leaks command activity to local users | [`F025-world-readable-fallback-log-leaks-command-activity-to-local-users.md`](F025-world-readable-fallback-log-leaks-command-activity-to-local-users.md) | stage3/linux_init/init_v41.c |
| F026 | `informational` | `mitigated-v126` | Metrics refactor breaks older init source builds | [`F026-metrics-refactor-breaks-older-init-source-builds.md`](F026-metrics-refactor-breaks-older-init-source-builds.md) | stage3/linux_init/a90_hud.h <br> stage3/linux_init/a90_metrics.h <br> stage3/linux_init/v89/60_shell_basic_commands.inc.c <br> stage3/linux_init/v89/40_menu_apps.inc.c |
| F027 | `informational` | `mitigated-v126` | v84 changelog detail screen is not rendered | [`F027-v84-changelog-detail-screen-is-not-rendered.md`](F027-v84-changelog-detail-screen-is-not-rendered.md) | stage3/linux_init/v84/40_menu_apps.inc.c |
| F028 | `informational` | `mitigated-v126` | v42 run cancel logic steals child stdin and aborts on 'q' | [`F028-v42-run-cancel-logic-steals-child-stdin-and-aborts-on-q.md`](F028-v42-run-cancel-logic-steals-child-stdin-and-aborts-on-q.md) | stage3/linux_init/init_v42.c |
| F029 | `informational` | `mitigated-v126` | Input event name path traversal in probing helpers | [`F029-input-event-name-path-traversal-in-probing-helpers.md`](F029-input-event-name-path-traversal-in-probing-helpers.md) | stage3/linux_init/init_v10.c |
| F030 | `informational` | `accepted-lab-boundary` | Unauthenticated root shell exposed via USB ACM and TCP bridge | [`F030-unauthenticated-root-shell-exposed-via-usb-acm-and-tcp-bridge.md`](F030-unauthenticated-root-shell-exposed-via-usb-acm-and-tcp-bridge.md) | stage3/linux_init/init_v8.c <br> scripts/revalidation/serial_tcp_bridge.py |
| F031 | `informational` | `mitigated-host-batch3` | Command injection via unquoted by_name in su -c commands | [`F031-command-injection-via-unquoted-by-name-in-su-c-commands.md`](F031-command-injection-via-unquoted-by-name-in-su-c-commands.md) | scripts/revalidation/capture_baseline.sh |
| F032 | `low` | `mitigated-retained-source` | Volume hold timer can spin autohud in non-repeat screens | [`F032-volume-hold-timer-can-spin-autohud-in-non-repeat-screens.md`](F032-volume-hold-timer-can-spin-autohud-in-non-repeat-screens.md) | stage3/linux_init/v131/40_menu_apps.inc.c <br> stage3/linux_init/v132/40_menu_apps.inc.c <br> stage3/linux_init/v133/40_menu_apps.inc.c |
| F033 | `low` | `mitigated-shared-controller` | Menu policy allows mountsd side effects with no subcommand | [`F033-menu-policy-allows-mountsd-side-effects-with-no-subcommand.md`](F033-menu-policy-allows-mountsd-side-effects-with-no-subcommand.md) | stage3/linux_init/a90_controller.c <br> stage3/linux_init/a90_storage.c <br> stage3/linux_init/v128/80_shell_dispatch.inc.c |

## Notes

- 원문 상세는 각 finding 파일의 `Codex Cloud Detail` 섹션에 그대로 보관합니다.
- 이 index는 분류/관계 분석 전 단계이며, severity/status는 CSV 원본 값을 유지합니다.
