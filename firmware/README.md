# Firmware Index

현재 `firmware/`는 재검증에 직접 쓰는 이미지 세트를 보관합니다.

## Layout

- `SAMFW.COM_SM-A908N_KTC_A908NKSU5EWA3_fac/`
  stock firmware 4-file 세트
  - `BL`
  - `AP`
  - `CP`
  - `CSC` / `HOME_CSC`
- `magisk/`
  patched AP / Magisk 관련 tar
- `twrp/`
  TWRP recovery image와 Odin용 tar

## Rule

- stock baseline 복구에는 stock firmware 디렉토리를 사용합니다.
- rooted baseline 복귀에는 `magisk/` 안의 patched AP를 사용합니다.
- recovery 경로 검증에는 `twrp/`를 사용합니다.
- 새 이미지 파일을 추가할 때는 출처와 목적을 함께 기록합니다.
