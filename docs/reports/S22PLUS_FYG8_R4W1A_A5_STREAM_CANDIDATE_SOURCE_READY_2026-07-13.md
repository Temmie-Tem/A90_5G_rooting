# S22+ FYG8 R4W1-A A5 Stream-Candidate Source Ready

Date: 2026-07-13 KST

Target: `SM-S906N/g0q/S906NKSS7FYG8`

Verdict: `PASS_R4W1A_STREAM_CANDIDATE_SOURCE_READY_HOST_ONLY_INACTIVE`

## Decision

The A4-qualified marker-absent stream is sufficient as the baseline for one
future R4W1-A candidate run. A new successor helper and complete inactive policy
source are ready for independent adversarial review.

The consumed v1 helper, its FAIL result, consumed record, RETIRED binding
clause, and absent old oracle PASS remain unchanged. A5 does not rerun the
device baseline, activate policy, contact a device, enumerate USB, invoke Odin,
create candidate consumed state, or flash anything.

## Implementation

Successor helper:
`workspace/public/src/scripts/revalidation/s22plus_fyg8_r4w1a_stream_candidate_live_gate.py`

- schema: `s22plus_fyg8_r4w1a_stream_candidate_live_gate_v2`;
- source SHA256:
  `b89d71763bcca1b9e088a0bc16acd0fc47521cd0d8aedb3abce5fb3c439f1489`;
- focused test SHA256:
  `99db688814e6bc8d65d057448b7809c3bc046b32af0ac37567f45fc768cbb509`;
- inactive policy draft SHA256:
  `e6bdb9289d351961a5a971dd30d0ff00974b8b34d572ede014aa7053d37dd8c2`.

Policy source:
`docs/operations/S22PLUS_FYG8_R4W1A_STREAM_CANDIDATE_AGENTS_EXCEPTION_DRAFT_2026-07-13.md`

The draft carries state `DRAFT_INACTIVE`. Binding `AGENTS.md` contains no
`S22PLUS_FYG8_R4W1A_STREAM_CANDIDATE_POLICY_STATE=ACTIVE` whole-line sentinel.
The helper computes its own current source and test hashes and requires both in
any future binding clause, in addition to every A4, candidate, oracle, and
rollback pin.

## A4 Dependency

The helper pins and reruns:

- A4 validator SHA256
  `fa940a5ff225d0d42c7d31214458ebc4625b33be7eb0f5b32ec543342b5bcf3c`;
- A4 test SHA256
  `592e982d70a808e3f6f68429d4b8fb8891e78b2dd476b656c958d208b0e9cbb3`;
- A4 result SHA256
  `077885c4f785760720463763905e4db3453c6e262021524e6fff97700bf6b12a`;
- exact verdict
  `PASS_R4W1A_STREAM_ORACLE_EVIDENCE_QUALIFIED_HOST_ONLY`.

Fresh A4 output must equal the pinned JSON. The helper also requires the
historical v1 helper/test hashes, old RETIRED policy, absent old oracle PASS,
and absent candidate consumed state. It does not synthesize a replacement v1
promotion record.

## Corrected Stream Contract

The successor implements the Android stream model directly:

1. snapshot direct `/bugreports` inventory;
2. execute one bounded `adb exec-out bugreportz -s`;
3. fsync stdout ZIP and separately bounded stderr;
4. require rc=0, EOF, nonzero bounded size, and empty stderr;
5. snapshot inventory again and require exact equality with the first snapshot;
6. perform no remote deletion under success or failure;
7. parse the exact host ZIP with same-file pre/post size and SHA checks; and
8. require all ZIP CRCs plus exactly one marker-family and exact marker
   occurrence in both the complete archive and the complete
   `LAST KMSG (/proc/last_kmsg)` section.

An added, removed, or changed remote path is non-PASS and is not deleted.
Marker absence, duplication, foreign/partial marker evidence, parser/stream
identity mismatch, stderr, timeout, malformed ZIP, unsafe entry, or CRC failure
is non-PASS.

This matches AOSP behavior: `dumpstate -s` copies the completed ZIP to its
control socket, `bugreportz_stream()` copies that socket to stdout until EOF,
and `adb bugreport --stream` invokes `bugreportz -s` directly:

- [AOSP dumpstate stream finalization](https://android.googlesource.com/platform/frameworks/native/+/android16-release/cmds/dumpstate/dumpstate.cpp#2559);
- [AOSP bugreportz stdout loop](https://android.googlesource.com/platform/frameworks/native/+/3ea58dbc1d/cmds/bugreportz/bugreportz.cpp#71);
- [ADB `--stream` implementation](https://android.googlesource.com/platform/packages/modules/adb/+/refs/tags/android-14.0.0_r27/client/bugreport.cpp#217).

No exact public `SM-S906N/FYG8 + rebuilt kernel + retained last_kmsg stream`
precedent was found. The local exact-source and live-derived A4 evidence remain
the device-specific basis.

## Candidate And Recovery Envelope

The future live path remains one-shot and boot-only:

- exact candidate raw boot SHA256
  `a2bba0ef907af14e57508ca55d247d571c3f89936dd7020293e51ebfa8f8d133`;
- exact candidate AP SHA256
  `cb2c078f001af6e263dc3f533a2efe3294a5c80201f50952a45bb88254e4d895`;
- exact Magisk rollback AP SHA256
  `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`;
- cleanup-only stock AP SHA256
  `2f6a8ac093587a0f03c423d8e21f65c6fe3a8d2ce9915297170cdaa2cac37c94`.

Connected baseline checks include exact Android/Magisk identities, raw observer
marker absence, and pstore-console absence. Candidate observation requires
stable Android samples, candidate pstore-console absence, and the exact
marker-positive stream. Candidate flash start creates one exclusive v2
consumed state. Rollback-from-download rejects absent, historical, malformed,
or helper-mismatched consumed state.

The only full PASS remains
`PASS_R4W1A_ANDROID_INIT_EXEC_WITNESS_RETAINED_AND_ROLLED_BACK`. It requires
candidate Android, exact streamed marker proof, unchanged remote inventory, and
exact Magisk Android/root/boot/DTBO/recovery return. Stock cleanup, absent
marker, or unverified rollback cannot PASS.

## Validation

Private offline output:
`workspace/private/work/s22plus_fyg8_r4w1a_a5/offline_check.json`

- output SHA256:
  `7e2d1634a00783dcb0f46347ee0fc2ecc603baecface42dd4cd4025ffb889fda`;
- verdict: `PASS_R4W1A_STREAM_CANDIDATE_OFFLINE_CHECK`;
- A4 verdict: exact PASS;
- static checker verdict: `PASS_R4W1A_THREE_REPRO_STATIC_CONTRACT`;
- `policy.active=false` and `policy.state=DRAFT_INACTIVE`;
- `candidate_consumed=false`;
- `device_contact=false`, `device_write=false`, and `flash=false`.

Validation results:

- Python bytecode compilation: PASS;
- new focused adversarial tests: `15/15` PASS;
- full `test_s22plus_fyg8_r4w1*.py` family: `96/96` PASS;
- candidate builder tests: `8/8` PASS;
- total unique tests in those two suites: `104/104` PASS;
- source scan found no remote cleanup, old PASS promotion, non-boot payload,
  fastboot, raw `dd`, panic, RDX, or dump path in the successor helper;
- final staged `git diff --check`: PASS;
- `black` and `ruff` are unavailable on this host and were not installed.

## Boundary And Next Gate

A5 is source-ready, not live-ready. It does not prove candidate boot,
marker-positive retention, or rollback. The next unit is an independent
adversarial review of the final helper, focused tests, exact artifacts, offline
result, and inactive policy draft.

Only after that review may a separate commit copy an exact SHA-pinned ACTIVE
clause into binding `AGENTS.md`. The operator must then provide a fresh
candidate-specific attended approval. No current message or document
authorizes the live run.
