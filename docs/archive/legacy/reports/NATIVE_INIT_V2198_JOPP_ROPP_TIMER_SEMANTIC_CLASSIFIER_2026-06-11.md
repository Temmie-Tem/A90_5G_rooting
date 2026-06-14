# Native Init V2198 JOPP/ROPP Timer Semantic Classifier (2026-06-11)

대상: A90 native boot `0.9.261 (v2189-security-p0-stage-fix)` stock kernel
symbolization artifacts.

목적: V2197에서 남은 slide ambiguity를 JOPP magic, source-derived timer callback
semantics, ROPP stack/callsite evidence로 다시 분해한다.

범위: host-only parser 구현·실행 + 기존 V2195/V2196/V2197 evidence 재분석. 새 live
device 명령, flash, reboot, Wi-Fi scan/connect, credential, DHCP/routes, external
ping, `probe_write_user`, cgroup attach 없음.

---

## 1. 결론

V2198은 JOPP magic-only slide oracle을 refute했고, timer semantic filter가 필요한
방향임을 확인했다. 그러나 현재 evidence만으로는 slide를 유일하게 확정하지 않는다.

```text
decision: v2198-classifier-provisional-multiple-semantic-timer-slides
reason: timer semantic candidates exist but do not uniquely select one slide
```

핵심 판단:

- `CONFIG_RKP_CFP_JOPP=y` + `CONFIG_RKP_CFP_ROPP=y`라 기존 stack return-address
  callsite 전제는 약하다.
- JOPP magic `0x00be7bad`는 stock blob 안에 `73,404`회 존재한다. magic은 필요조건이지
  충분조건이 아니다.
- source-derived timer callback whitelist는 false-positive slide를 줄인다. 단 dominant
  timer 하나만으로는 여러 plausible callback slide가 남는다.
- V2195 기존 stack은 top timer semantic candidates를 독립 cross-confirm하지 못했다.
- 따라서 V2197의 provisional 판정은 유지한다. `exact_symbolization`은 아직 금지다.

---

## 2. 산출물

| 항목 | 값 |
| --- | --- |
| Analyzer | `workspace/public/src/scripts/revalidation/a90_kernel_v2198_jopp_ropp_classifier.py` |
| Private JSON | `workspace/private/runs/kernel/v2198-jopp-ropp-classifier/result.json` |
| Private summary | `workspace/private/runs/kernel/v2198-jopp-ropp-classifier/result.md` |
| Stock map input | `workspace/private/runs/kernel/v2197-stock-kallsyms/System.map` |
| Stock kernel input | `workspace/private/runs/kernel/v2196-boot-kernel-compare/unpack/kernel` |
| Timer input | `workspace/private/runs/kernel/v2196-p1b-symbolization/logs/host/timer-function-freq.stdout.txt` |
| Stack input | `workspace/private/runs/kernel/v2195-stackmap-dump-20260611-203700/rerun/logs/host/helper-stackdump.stdout.txt` |
| Source input | `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source` |

Command:

```sh
python3 workspace/public/src/scripts/revalidation/a90_kernel_v2198_jopp_ropp_classifier.py \
  --system-map workspace/private/runs/kernel/v2197-stock-kallsyms/System.map \
  --stock-json workspace/private/runs/kernel/v2197-stock-kallsyms/stock-kallsyms.json \
  --kernel workspace/private/runs/kernel/v2196-boot-kernel-compare/unpack/kernel \
  --timer-log workspace/private/runs/kernel/v2196-p1b-symbolization/logs/host/timer-function-freq.stdout.txt \
  --stack-log workspace/private/runs/kernel/v2195-stackmap-dump-20260611-203700/rerun/logs/host/helper-stackdump.stdout.txt \
  --source-root tmp/wifi/v766-icnss-qcacld-patch-apply-build/source \
  --out-json workspace/private/runs/kernel/v2198-jopp-ropp-classifier/result.json \
  --out-md workspace/private/runs/kernel/v2198-jopp-ropp-classifier/result.md
```

---

## 3. Config Classifier

The analyzer extracts IKCFG from the stock kernel wrapper and confirms:

```text
CONFIG_RKP_CFP=y
CONFIG_RKP_CFP_JOPP=y
CONFIG_RKP_CFP_JOPP_MAGIC=0x00be7bad
CONFIG_RKP_CFP_ROPP=y
CONFIG_RKP_CFP_ROPP_SYSREGKEY=y
CONFIG_GCC_PLUGINS=n
```

Implications:

- `__cfi*` is not the path here. The active forward-edge mechanism is Samsung RKP CFP
  JOPP.
- `jopp_springboard_blr_x*` exists in the stock map. There are 29 symbol names but
  28 unique addresses because two names alias the same address.
- ROPP protects stack return-address material, so raw stack IPs cannot be treated as
  ordinary return addresses until classified.

---

## 4. Magic-Only Refutation

V2198 scans the bit-exact stock blob for the little-endian JOPP magic:

```text
jopp_magic_occurrences: 73404
```

That density makes magic-only slide solving unsafe. It produced full timer coverage
false positives in exploratory checks, including mappings to non-timer semantics such as
`sys_setreuid`, `attach_pid`, `rpmsg_eptdev_release`, and `profile_dead_cpu`.

Therefore the accepted rule is:

```text
JOPP magic = necessary condition
timer callback semantics + frequency + stack cross-check = required discriminators
```

Springboard proximity is also not evidence by itself. The useful springboard fact is
instruction-level: a stack callsite classifier must allow both direct `BL/BLR` and
`BL jopp_springboard_blr_x*` return patterns.

---

## 5. Timer Semantic Filter

The analyzer derives a timer callback candidate set from source patterns:

```text
scanned_files: 56765
high_confidence_count: 726
low_confidence_count: 608
```

High-confidence patterns:

- `DEFINE_TIMER(...)`
- `setup_timer(...)`
- `timer_setup(...)`

Low-confidence patterns:

- `->function = ...`
- `.function = ...`

This must stay a scoring signal, not a hard reject, because grep-style extraction can
miss multiline initializers, dynamic callback assignment, vendor wrappers, or module-local
patterns. It also intentionally targets `timer_list` callbacks; hrtimer callback evidence
must be handled separately.

Top semantic candidate:

```text
slide: -0x17a074
magic: 3/8, weight 350/415
known-callback: 1/8, weight 348/415
dominant timer: 0xffffff80083108fc -> key_gc_timer_func+0x0
```

The dominant timer maps cleanly to `key_gc_timer_func` with JOPP magic and ROPP prologue
evidence, but this is not enough to make the slide unique. Other slides map the same
dominant runtime pointer to plausible high-confidence callbacks such as
`do_nocb_deferred_wakeup_timer` or `poll_spurious_irqs`.

---

## 6. Stack Cross-Check

V2198 reuses the V2195 six raw stack IPs and tests candidate slides for mapped frames,
direct callsites, and springboard callsites.

Important result:

```text
V2197 slides 0x7f08c / 0x7f0dc / 0x7f730 / 0x7f780:
  mapped=6/6
  direct_callsite=0
  springboard_callsite=0

Top timer semantic slides -0x17a074 / -0x17a078:
  mapped=6/6
  direct_callsite=0
  springboard_callsite=0
```

There are unrelated slides with one or two direct-callsite hits, but they do not
cross-confirm the timer semantic winner and are not accepted as authority.

Interpretation:

- The existing stack capture is useful as negative evidence against overclaiming.
- It does not currently resolve the timer semantic ambiguity.
- ROPP/JOPP stack recovery likely needs either same-boot multi-stack diversity or an
  explicit ROPP decode/joint-key pass before stack can act as a strong slide oracle.

---

## 7. Capability Map Delta

| Capability | V2197 | V2198 |
| --- | --- | --- |
| bit-exact stock `System.map` | pass | pass |
| JOPP/ROPP config classification | partial | **pass** |
| magic-only slide oracle | suspected weak | **refuted** |
| source-derived timer callback scoring | absent | **implemented** |
| timer semantic slide uniqueness | not solved | **not solved** |
| stack callsite cross-check | provisional | **implemented, non-confirming** |
| exact symbolization | false | false |
| kernel write / `probe_write_user` | forbidden | forbidden |

V2198 strengthens the methodology but does not change the final boundary: data and
control-flow observation remain open, while exact symbol names still require a unique
slide. Kernel write remains out of scope.

---

## 8. Next

Recommended next unit:

1. Improve semantic scoring with source xref context: only count callbacks whose address
   is actually assigned to `struct timer_list.function` or passed to timer setup APIs.
2. Capture same-boot timer-start stack/caller diversity with the existing read-only BPF
   path, if host-only evidence remains ambiguous.
3. Add a ROPP/JOPP stack recovery pass: classify decoded vs encoded frames, allow direct
   and springboard callsites, and solve for a single SYSREGKEY-derived stack key only as
   an offline inference. Do not execute write helpers.
4. Keep downstream WLAN/cfg80211 symbolization gated on `stack_slide_unique=true` or on a
   report that explicitly labels every symbol as provisional.

Follow-up:

- `docs/reports/NATIVE_INIT_V2199_TIMER_XREF_SLIDE_SCORER_2026-06-11.md` implements
  source xref scoring. It moves the leading semantic target from broad-whitelist
  `key_gc_timer_func` to the RCU no-CB `do_nocb_deferred_wakeup_timer` path, but keeps
  `exact_symbolization=false` because the `+0/+4` slide pair remains unresolved.
