# Native Init Versioning

Date: `2026-05-04`

## Current Version

- latest verified official version: `0.9.10`
- latest verified build tag: `v110`
- latest verified display name: `A90 Linux init 0.9.10 (v110)`
- creator: `made by temmie0214`
- latest verified source: `stage3/linux_init/init_v110.c` + `stage3/linux_init/v110/*.inc.c` + `stage3/linux_init/helpers/a90_cpustress.c` + `stage3/linux_init/helpers/a90_rshell.c` + `stage3/linux_init/a90_config.h` + `stage3/linux_init/a90_util.c/h` + `stage3/linux_init/a90_log.c/h` + `stage3/linux_init/a90_timeline.c/h` + `stage3/linux_init/a90_console.c/h` + `stage3/linux_init/a90_cmdproto.c/h` + `stage3/linux_init/a90_run.c/h` + `stage3/linux_init/a90_service.c/h` + `stage3/linux_init/a90_kms.c/h` + `stage3/linux_init/a90_draw.c/h` + `stage3/linux_init/a90_input.c/h` + `stage3/linux_init/a90_hud.c/h` + `stage3/linux_init/a90_menu.c/h` + `stage3/linux_init/a90_metrics.c/h` + `stage3/linux_init/a90_shell.c/h` + `stage3/linux_init/a90_controller.c/h` + `stage3/linux_init/a90_storage.c/h` + `stage3/linux_init/a90_selftest.c/h` + `stage3/linux_init/a90_usb_gadget.c/h` + `stage3/linux_init/a90_netservice.c/h` + `stage3/linux_init/a90_runtime.c/h` + `stage3/linux_init/a90_helper.c/h` + `stage3/linux_init/a90_userland.c/h` + `stage3/linux_init/a90_diag.c/h` + `stage3/linux_init/a90_wifiinv.c/h` + `stage3/linux_init/a90_wififeas.c/h` + `stage3/linux_init/a90_app_about.c/h` + `stage3/linux_init/a90_app_displaytest.c/h` + `stage3/linux_init/a90_app_inputmon.c/h`
- latest verified boot image: `stage3/boot_linux_v110.img`
- latest local/pending build: none
- previous verified source-layout baseline: `stage3/linux_init/init_v80.c` + `stage3/linux_init/v80/*.inc.c`

## Local Artifact Retention

- 보존: latest verified `v110`, 직전 rollback `v109`, known-good fallback `v48`
- 정리 대상: ignored `stage3/boot_linux_v*.img`, `stage3/ramdisk_v*`, compiled `stage3/linux_init/init_v*` 중 보존 태그가 아닌 파일
- 정리 도구: `python3 scripts/revalidation/cleanup_stage3_artifacts.py --execute`
- 보고서의 artifact hash와 tracked source는 유지하므로, 오래된 local binary output은 필요 시 재생성한다.

## Version Format

공식 버전은 `MAJOR.MINOR.PATCH`를 사용하고, 실험/플래시 추적용 build tag는 `vNN`을 유지한다.

```text
A90 Linux init 0.9.10 (v110)
```

## Rules

- `MAJOR`: 구조가 크게 바뀌거나 호환성이 깨지는 업데이트
  - 예: rootfs/service manager 구조 변경, command 호환성 깨짐, 부팅/저장소 전략 대규모 변경
- `MINOR`: 기능/능력이 추가되는 업데이트
  - 예: USB NCM, TCP control, netservice, app menu, storage manager, SSH/dropbear
- `PATCH`: 작은 수정, 안정화, 화면/문구 조정
  - 예: splash 잘림, 색상, 글자 크기, footer 위치, 작은 버그픽스
- `vNN`: boot image와 실기 검증을 추적하는 build 번호
  - 새 boot image를 만들고 flash 검증할 때마다 증가시킨다.

## Current Mapping

| official | build | summary |
|---|---|---|
| `0.9.10` | `v110` | app controller auto-menu IPC cleanup |
| `0.9.9` | `v109` | post-v108 structure audit and cleanup boundary |
| `0.9.8` | `v108` | input monitor/layout UI app module extraction |
| `0.9.7` | `v107` | displaytest/cutoutcal UI app module extraction |
| `0.9.6` | `v106` | ABOUT/changelog UI app module extraction |
| `0.9.5` | `v105` | soak/recovery release candidate and host quick-soak validator |
| `0.9.4` | `v104` | Wi-Fi feasibility gate from read-only inventory evidence |
| `0.9.3` | `v103` | Wi-Fi read-only inventory command and host collector |
| `0.9.2` | `v102` | diagnostics/log bundle command and host collector |
| `0.9.1` | `v101` | minimal service manager command/view |
| `0.9.0` | `v100` | custom token TCP remote shell over USB NCM |
| `0.8.30` | `v99` | BusyBox static userland evaluation |
| `0.8.29` | `v98` | helper deployment / package manifest |
| `0.8.28` | `v97` | SD runtime root promotion |
| `0.8.27` | `v96` | structure audit / refactor debt cleanup |
| `0.8.26` | `v95` | netservice/USB gadget true `.c/.h` API extraction |
| `0.8.25` | `v94` | boot selftest non-destructive module smoke test API |
| `0.8.24` | `v93` | storage state, SD probe, cache fallback API extraction |
| `0.8.23` | `v92` | shell/controller metadata and busy policy API extraction |
| `0.8.22` | `v91` | CPU stress external helper process separation |
| `0.8.21` | `v90` | metrics true `.c/.h` API module extraction |
| `0.8.20` | `v89` | menu control true `.c/.h` API module extraction + nonblocking `screenmenu` |
| `0.8.19` | `v88` | HUD true `.c/.h` API module extraction |
| `0.8.18` | `v87` | input true `.c/.h` API module extraction |
| `0.8.17` | `v86` | KMS/draw true `.c/.h` API module extraction |
| `0.8.16` | `v85` | run/service process lifecycle true `.c/.h` API module extraction |
| `0.8.15` | `v84` | cmdproto `cmdv1/cmdv1x` frame/decode true `.c/.h` API module extraction |
| `0.8.14` | `v83` | console fd/attach/readline/cancel true `.c/.h` API module extraction |
| `0.8.13` | `v82` | log/timeline true `.c/.h` API module extraction |
| `0.8.12` | `v81` | config/util true `.c/.h` base module extraction |
| `0.8.11` | `v80` | source layout split into include modules |
| `0.8.10` | `v79` | boot-time SD health check and cache fallback |
| `0.8.9` | `v78` | ext4 SD workspace and mountsd storage manager |
| `0.8.8` | `v77` | display test multi-page app + cutout calibration |
| `0.8.7` | `v76` | short AT serial fragment filter |
| `0.8.6` | `v75` | quiet idle serial reattach success logs |
| `0.8.5` | `v74` | cmdv1x length-prefixed argument encoding |
| `0.8.4` | `v73` | cmdv1/A90P1 shell protocol and a90ctl host wrapper |
| `0.8.3` | `v72` | display test screen and XBGR8888 color fix |
| `0.8.2` | `v71` | live log tail panel for HUD/menu spare area |
| `0.8.1` | `v70` | input monitor app and raw/gesture trace |
| `0.8.0` | `v69` | physical-button input gesture layout and debug command |
| `0.7.5` | `v68` | HUD log tail and expanded changelog history |
| `0.7.4` | `v67` | compact ABOUT typography and per-version changelog detail screens |
| `0.7.3` | `v66` | ABOUT app, versioning, changelog, creator display |
| `0.7.2` | `v65` | boot splash safe layout |
| `0.7.1` | `v64` | custom boot splash |
| `0.7.0` | `v63` | hierarchical app menu and CPU stress screen app |
| `0.6.0` | `v62` | CPU stress gauge and `/dev/null`/`/dev/zero` guard |
| `0.5.0` | `v60` | opt-in netservice and reconnect validation |
| `0.4.0` | `v55` | NCM operations and TCP control foundation |
| `0.3.0` | `v53` | screen menu polish and busy gate |
| `0.2.0` | `v40`~`v45` | shell/log/timeline/HUD/cancel stabilization |
| `0.1.0` | early native init | PID 1 native init, serial shell, KMS/input probes |

## 1.0.0 Criteria

`1.0.0`은 아직 아껴 둔다.

권장 기준:

- serial/NCM/TCP 제어 경로가 장시간 안정화됨
- 화면/버튼만으로 recovery/poweroff/status 확인 가능
- safe storage 정책과 복구 경로가 문서화됨
- `/cache/bin` 도구와 runtime service 운용 정책이 정리됨
- known-good fallback이 유지됨
