# Native Init v63 App Menu / CPU Stress Screen App Report

Date: `2026-04-26`

## Summary

`A90 Linux init v63`는 화면 메뉴를 앱 폴더 구조로 확장하고,
LOG/NETWORK/CPU STRESS 화면이 한 프레임만 보이고 사라지는 문제를 active app 상태로 고친다.

- Main menu: `APPS >`, `STATUS`, `NETWORK >`, `POWER >`, `HIDE MENU`
- App folders: `MONITORING`, `TOOLS`, `LOGS`
- CPU stress app: `5/10/30/60 SECONDS` 선택 후 전용 CPU dashboard 표시
- Menu polish: help/menu 간격 보정, 버튼 안내 글자 밝기 개선

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v63` | `062eb9a780c0fe71890e80d0c961b5b3016d3d35e0da19fa99e5289bbde04a00` |
| `stage3/ramdisk_v63.cpio` | `7b9d3f71f648e7f9765fc6c1827c66c0dcc422f714b1ec67a334f9cbca5f53ce` |
| `stage3/boot_linux_v63.img` | `99025fba4c17348057920eab06b7bd98a97b5cc5f6acff21190981288a0ad09d` |

## Source Changes

- `stage3/linux_init/init_v63.c`
  - `INIT_VERSION "v63"`
  - 계층형 `screen_menu_page`와 shared menu item table 추가
  - 자동 HUD 메뉴와 serial `screenmenu`가 같은 page/item 정의를 사용
  - `SCREEN_APP_LOG`, `SCREEN_APP_NETWORK`, `SCREEN_APP_CPU_STRESS` active app 상태 추가
  - CPU stress app용 worker fork/stop, timeout, dashboard draw 흐름 추가

## Menu Layout

```text
MAIN MENU
  APPS >
    MONITORING >
      LIVE STATUS
    TOOLS >
      CPU STRESS >
        5 SECONDS
        10 SECONDS
        30 SECONDS
        60 SECONDS
    LOGS >
      LOG SUMMARY
  STATUS
  NETWORK >
    NET STATUS
  POWER >
    RECOVERY
    REBOOT
    POWEROFF
  HIDE MENU
```

## Runtime Validation

- `stage3/boot_linux_v63.img` flash 후 bridge `version`에서 `A90 Linux init v63` 확인
- 자동 HUD menu에서 `APPS >`, `TOOLS >`, `CPU STRESS >` 계층 표시 확인
- `HIDE MENU`와 serial `hide`가 menu active state를 정상 해제하는 것 확인
- `VOLUP/DN MOVE PWR SELECT` 안내가 menu title과 겹치지 않도록 위치/밝기 보정

## Notes

- 자동 HUD 메뉴의 CPU stress app은 버튼으로 실행 시간을 선택하고, 실행 중 아무 버튼이나 누르면 취소/복귀한다.
- serial `screenmenu`는 blocking debug menu로 유지하며, 자동 HUD 메뉴가 주 UI 경로다.
- CPU-only stress에서는 GPU busy가 0%일 수 있다.

## Next

1. boot-time TEST 화면을 프로젝트 전용 splash로 교체
2. 앱 메뉴에 장기적으로 NCM/TCP, storage, sensor detail 화면 추가
3. full-screen app과 serial debug menu의 기능 차이를 문서에 계속 명시
