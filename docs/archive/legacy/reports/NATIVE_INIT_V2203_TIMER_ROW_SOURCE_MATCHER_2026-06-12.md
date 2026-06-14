# Native Init V2203 Timer Row Source Matcher (2026-06-12)

대상: V2202 timer object histogram rows + V2198 slide candidates + stock System.map +
OSRC/source timer API xrefs.

목적: V2202가 만든 raw timer rows를 source-backed timer setup pattern에 맞춰 보고,
한 global KASLR slide가 top rows의 object invariant를 동시에 만족하는지 확인한다.

범위: host-only analysis. Live boot 없음. BPF attach 없음. Firmware/kernel/partition write 없음.

---

## 1. 결론

```text
decision: v2203-row-matcher-no-exact-slide
result: workspace/private/runs/kernel/v2203-timer-row-source-matcher/result.json
source_files_scanned: 44202
rows_analyzed: 8
```

V2203는 V2202 rows를 source xref와 결합했지만, exact slide를 만들지 못했다. 이유는
명확하다: 한 slide가 top row와 RCU-like row를 동시에 source-consistent하게 설명하지
못한다.

핵심 판단:

- best candidate `slide=-0xa9984`는 row0 `0xffffff80083108fc`를 `commit_timeout+0`에
  매칭해 높은 점수를 얻는다.
- 같은 slide에서 row1 `0xffffff80081db824`는 `rcu_preempt` context임에도
  `__free_zspage+80`으로 매핑되어 hard conflict가 생긴다.
- row1을 `do_nocb_deferred_wakeup_timer+0`에 맞추려면 `slide=+0x87de4`가 필요하다.
- 그러나 `slide=+0x87de4`에서는 row0/row2/row3가 각각 `do_dentry_open+0x98`,
  `compat_sys_sigpending+0x1b0`, `cacheinfo_cpu_pre_down+0x48`로 밀려 global slide가
  깨진다.
- 따라서 timer rows만으로는 exact symbolization을 켤 수 없다.

```text
row_source_matcher: pass
best_slide: -0xa9984
best_slide_conflicts: 1
rcu_row_standalone_slide: +0x87de4
exact_symbolization: false
```

---

## 2. 산출물

| 항목 | 값 |
| --- | --- |
| Analyzer | `workspace/public/src/scripts/revalidation/a90_kernel_v2203_timer_row_source_matcher.py` |
| Input V2202 | `workspace/private/runs/kernel/v2202-timer-object-histogram-20260612-010308/summary.json` |
| Input V2198 | `workspace/private/runs/kernel/v2198-jopp-ropp-classifier/result.json` |
| Stock map | `workspace/private/runs/kernel/v2197-stock-kallsyms/System.map` |
| Private JSON | `workspace/private/runs/kernel/v2203-timer-row-source-matcher/result.json` |
| Private MD | `workspace/private/runs/kernel/v2203-timer-row-source-matcher/result.md` |

Command:

```sh
python3 workspace/public/src/scripts/revalidation/a90_kernel_v2203_timer_row_source_matcher.py
```

---

## 3. Best Candidate

From the private result:

```text
slide=-0xa9984
weighted_score=28696
hard_conflicts=1
top_row_score=200
rcu_row_score=-80
```

Top row mappings:

```text
row0 0xffffff80083108fc comm=a90_bpf_timer_o count=1396
  -> commit_timeout+0
  score=200
  notes: entry offset; source xref score 145; embedded data delta matches struct-field timer

row1 0xffffff80081db824 comm=rcu_preempt count=152
  -> __free_zspage+80
  score=-80
  notes: non-entry offset; no timer xref; rcu row maps to non-rcu source pattern

row2 0xffffff80081510c4 comm=kworker/7:1 count=139
  -> tp_perf_event_destroy+160
  score=5
  notes: non-entry offset; no timer xref
```

`commit_timeout` is now a plausible source pattern for row0, but the same slide fails the
RCU-like row. That prevents exact slide promotion.

---

## 4. RCU Row Standalone Check

Raw arithmetic against stock System.map:

```text
row1 runtime = 0xffffff80081db824
stock do_nocb_deferred_wakeup_timer = 0xffffff8008153a40
required slide = +0x87de4
```

Under `slide=+0x87de4`:

```text
row0 0xffffff80083108fc -> do_dentry_open+0x98
row1 0xffffff80081db824 -> do_nocb_deferred_wakeup_timer+0x0
row2 0xffffff80081510c4 -> compat_sys_sigpending+0x1b0
row3 0xffffff8008a1e884 -> cacheinfo_cpu_pre_down+0x48
```

This confirms that the RCU row can be explained alone, but not as a global slide solution.
The RCU-like row is useful as a semantic discriminator, not as a standalone slide anchor.

---

## 5. Interpretation

V2203 changes the model again:

- V2199's `do_nocb_deferred_wakeup_timer` lead was not completely meaningless; RCU-like
  behavior exists in V2202.
- The mistake was binding RCU semantics to the dominant row `0xffffff80083108fc`.
- V2202/V2203 show the timer rows are affected by more than one ambiguity source:
  JOPP/ROPP entry effects, object timing, and imperfect slide candidates.
- Source xref alone can rank plausible rows, but it still cannot name raw function pointers
  exactly.

Therefore every downstream WLAN/cfg80211 object-chain label must remain raw/provisional
unless another independent slide anchor is introduced.

---

## 6. Next

Recommended next unit:

1. Stop trying to extract exact KASLR slide from timer rows alone.
2. Use V2202/V2203 rows as sanity checks only.
3. Find a cleaner non-timer anchor where runtime pointer semantics and source symbol are
   independently known, for example:
   - tracepoint record function pointer with stable exact source owner;
   - file_operations/proc_ops pointer from a known opened file;
   - netdev/wiphy ops pointer with object path verified by source offsets.
4. Keep exact symbol labels disabled until that independent anchor gives one global slide
   that also passes V2202 row sanity checks.
