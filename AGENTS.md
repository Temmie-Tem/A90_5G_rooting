# AGENTS.md

> **Active delegated task:** build the host-only regression test harness described in
> [`GOAL.md`](GOAL.md). Read `GOAL.md` first — it is the contract and the progress
> ledger. These rules govern that run. Remove or revise this file once the goal is done.

## Hard rules (non-negotiable)

1. **Scope:** modify ONLY files under `tests/`, plus `GOAL.md` (checklist/log) and this
   `AGENTS.md`. Read anything in the repo; change nothing else. Do not edit analyzers,
   `a90harness`, `a90_wifi.c`, boot scripts, docs, or config.
2. **No device interaction of any kind:** no flashing, no boot-image builds, no serial
   bridge, no `a90ctl`, no Wi-Fi scan/connect/dhcp/ping, no live BPF/uprobe/perf probes.
   This harness is pure host-side and needs none of that.
3. **No network, no installs:** Python **stdlib `unittest` only**. No `pip`, no new
   dependencies. (Tests run offline.)
4. **Characterize, do not fix:** tests pin the analyzer's CURRENT behavior. Never edit an
   analyzer to make a test pass. If an analyzer genuinely looks buggy, add a
   `# KNOWN-DIVERGENCE:` comment, assert the current behavior, and note it in `GOAL.md` —
   do not change the analyzer.

## Working cadence (one unit per commit, for easy recovery)

For each unit of work:

1. Open `GOAL.md`, take the **first unchecked** `[ ]` target.
2. Read its source to learn the real behavior of its pure functions.
3. Write `tests/test_<name>.py` with `unittest`, covering accepted inputs and the
   edge/reject cases (for validators, the inputs that must raise).
4. Run it: `python3 -m unittest discover -s tests -p 'test_*.py' -v`. It MUST be green.
   If red, fix the TEST until green (never the analyzer).
5. Flip the target to `[x]` in `GOAL.md` and append a Progress-log line.
6. **Commit this single unit:**
   ```
   git add tests/ GOAL.md AGENTS.md
   git commit -m "test(harness): cover <name> (<N> cases)"
   ```
   Never `git add -A` / `git add .` — stage only the paths above so unrelated in-flight
   work is never swept into the commit. Commit only when the suite is green.

## Stop conditions

- All checklist targets `[x]` and the full suite green → mark the goal achieved and stop.
- Blocked or ambiguous → write a note in `GOAL.md` and stop. Do NOT widen scope, invent
  device steps, or guess behavior to keep going.
