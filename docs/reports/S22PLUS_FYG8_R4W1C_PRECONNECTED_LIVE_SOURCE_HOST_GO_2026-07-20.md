# S22+ FYG8 R4W1-C Preconnected Live Source Host GO

Date: 2026-07-20 KST

Verdict: `GO_TO_EXACT_R4W1C_CONNECTED_READ_ONLY_ACK`

Scope: host-only design, implementation, static validation, artifact
qualification, and independent read-only review. No device was enumerated or
contacted. No ADB action, reboot, Download transition, Odin transfer, flash,
partition write, connected PASS, candidate consumption, or live-policy
activation occurred.

## Result

The deterministic preconnected packet returned:

`PASS_R4W1C_PRECONNECTED_SOURCE_PACKET_HOST_ONLY`

The live helper's complete artifact gate returned:

`PASS_R4W1C_LIVE_GATE_OFFLINE_CHECK`

Both results reported every device action field as false. This is source
readiness only and grants no device contact or live execution.

## Exact Sources

```text
live helper
  size    83485
  SHA256  db52c25340c9416e0b1c70bfc109b9389cd5010995ff00a6cb66e8b4a2cc69e5

live focused test
  size    48167
  SHA256  560d6aac50a6e9fc7557e3c4d2d07966ad8c801f420b2b5b3350dfcc09772402

inactive live template
  size    8584
  SHA256  80a893773529c83dd677ee035cee3b0a6c32919bd98aa1bb016a9a79608e3492

binding packet generator
  size    11595
  SHA256  40657d6f0fdbb4f776f411d08f34dba59dd7525eabfe71b3b1683e932b0ddccd

binding packet focused test
  size    7111
  SHA256  8c8a4edc01fa1814946c2e1a424bef501cb87bad152e9a39084877011305ffbd
```

The frozen connected helper/test/clause pins are respectively
`fa4e9b0a...516b9`, `98938da6...0251`, and `35f1d2cf...17ffa`.

## Closed Risks

- one write-sealed Odin descriptor is retained across every enumeration,
  revalidation, and transfer in each live or recovery invocation;
- candidate, Magisk, and stock AP bytes are independently write-sealed and
  rechecked as exact one-member boot-only archives before launch;
- endpoint tickets bind generation, character-device identity, physical USB
  topology, and USB serial digest;
- final Magisk Android must match the original exact ADB serial and complete
  USB binding, so a substitute handset fails closed;
- a PASS requires exact candidate transfer, Odin disappearance, the full
  requested 120-second observation, exact Magisk rollback, complete first
  retained observer, and all eight truthful timeline events;
- recovery is append-only, never repeats candidate, permits at most one
  separately acknowledged ambiguous Magisk retry, and stops after two numbered
  attempts;
- policy rendering binds current live source plus the canonical connected PASS
  and result identities without editing `AGENTS.md`.

## Independent Review

The existing independent `gpt-5.6-sol` xhigh read-only review session first
returned SOURCE NO-GO for Odin pathname TOCTOU, substitute-device acceptance,
and incomplete-observation PASS. After the fixes and focused tests, it reviewed
the stable final snapshot again and found no HIGH, MEDIUM, or LOW source issue.
Final verdict:

`SOURCE GO`

Residual items were test-depth observations only: no single real-memfd unit
test spans every enumeration call, same-topology/different-USB-serial is
rejected by exact production dictionary equality but lacks its own final-ADB
test case, and postconnected packet tests necessarily await a real connected
evidence tree.

## Validation

```text
focused live and packet tests            44 passed
shared-core and R4W1-B/C regressions     169 passed
py_compile                               PASS
git diff --check                         PASS
full 9.68 GB offline artifact gate       PASS
preconnected packet check                PASS
connected policy                         active
live policy                              inactive
connected PASS                           absent
candidate consumed                       false
device contact/write/flash               false/false/false
```

The artifact gate reopened exact candidate, Magisk rollback, stock cleanup,
Odin4, source pins, and the full FYG8 ZIP
`f831e5fb8abe1c7a9d8c38fe9c033a3fce7e77651776383641c385c2bb85a2c8`.

## Next Gate

Commit this host-only packet. The attending operator must then supply exactly:

`S22PLUS-FYG8-R4W1C-CONNECTED-READ-ONLY-DRY-RUN`

Generic approval is insufficient. After connected PASS, use the already
committed generator to emit and independently review the exact live binding,
rerun its source gate and all host checks while live policy is inactive, then
commit that clause separately. After activation, rerun tests and the live
helper's complete offline gate, not the now-inapplicable packet generator. Only
then request the fresh live acknowledgement. This report grants no live
authority.
