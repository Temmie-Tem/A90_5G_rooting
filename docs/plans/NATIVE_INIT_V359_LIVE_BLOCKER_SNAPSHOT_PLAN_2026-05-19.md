# v359 계획: V317 Live Blocker Snapshot

## Summary

- v359은 native init/boot image 변경 없이 V317 live 직전 blocker 상태를 manifest로 남기는 host-only 작업이다.
- 목표는 “현재 실행 가능한 것은 host-only check뿐이고, live proof는 exact approval phrase 하나 때문에 막혀 있다”를 기계적으로 재확인하는 것이다.
- V317 live proof, cleanup, daemon start, scan/connect/link-up, helper deploy, reboot/flash는 실행하지 않는다.

## Key Changes

- `scripts/revalidation/wifi_v317_blocker_snapshot.py`를 추가한다.
- 스냅샷은 내부에서 V357 pre-approval audit를 재실행한다.
- V357 manifest와 V350 checklist manifest를 읽어 다음을 확인한다.
  - V357 decision이 `v317-preapproval-audit-awaiting-approval`이다.
  - V357 evidence가 current clean HEAD다.
  - V357 remaining blocker가 `exact-v317-approval-phrase` 하나다.
  - V350 preferred live command가 V351 executor 경로다.
  - V350 preferred live command에 exact approval phrase가 포함되어 있다.
- 결과 decision은 성공 시 `v317-live-blocked-awaiting-exact-approval`로 둔다.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_v317_blocker_snapshot.py
git diff --check
python3 scripts/revalidation/wifi_v317_blocker_snapshot.py \
  --out-dir tmp/wifi/v359-v317-blocker-snapshot \
  snapshot
```

## Expected Result

- pre-commit dirty tree에서는 V357 clean-head 조건 때문에 blocked가 정상이다.
- clean HEAD에서는 `v317-live-blocked-awaiting-exact-approval`가 기대값이다.
- live execution은 여전히 exact approval phrase 전까지 blocked다.

## Assumptions

- V357/V358은 최신 host-only gate 기준으로 PASS다.
- v359는 host-only state snapshot이며 native init version을 올리지 않는다.
- exact approval phrase는 live mutation 승인 전용이며, broad approval이나 일반 동의 문장으로 대체하지 않는다.
