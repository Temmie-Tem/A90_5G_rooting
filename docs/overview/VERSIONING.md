# Native Init Versioning

Date: `2026-04-27`

## Current Version

- official version: `0.8.7`
- build tag: `v76`
- display name: `A90 Linux init 0.8.7 (v76)`
- creator: `made by temmie0214`
- latest source: `stage3/linux_init/init_v76.c`
- latest boot image: `stage3/boot_linux_v76.img`

## Version Format

공식 버전은 `MAJOR.MINOR.PATCH`를 사용하고, 실험/플래시 추적용 build tag는 `vNN`을 유지한다.

```text
A90 Linux init 0.8.7 (v76)
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
