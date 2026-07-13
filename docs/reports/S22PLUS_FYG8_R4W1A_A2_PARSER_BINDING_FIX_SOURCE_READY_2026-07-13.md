# S22+ FYG8 R4W1-A A2 Parser Binding Fix Source Ready

Date: 2026-07-13 KST
Scope: host-only adversarial review, implementation, and static validation
Device contact, device write, reboot, Download transition, Odin, or flash: none

## Verdict

`PASS_R4W1A_PARSER_STREAM_BINDING_FIX_SOURCE_READY_HOST_ONLY`

The first connected dry-run remains valid historical evidence for its old
helper, but an adversarial pre-oracle review found one load-bearing gap: the
parser's independently opened host ZIP was not explicitly rebound to the SHA
and size recorded for the original stream. The current helper closes that gap.
Oracle policy remains inactive and the one-shot oracle rehearsal has not been
consumed.

## Finding And Fix

The previous flow proved `remote == stream` and proved that the parser input
was stable across its own file descriptor. It did not prove
`parser input == stream` across the second open. A local replacement in that
window could therefore have made a valid but unrelated ZIP supply the marker
classification.

`capture_oracle` now records `parser_stream_identity_match` and requires both:

- parser input SHA256 equals the original stream SHA256; and
- parser input size equals the original stream byte count.

Mismatch appends a hard error and blocks `success`. Reopening a future oracle
promotion record also requires this field to be exactly true. The resulting
load-bearing chain is `parser == stream == remote`.

A regression test makes the remote SHA equal the declared stream SHA while
leaving a different valid ZIP on disk for the parser. It proves cleanup may
still remove the exact run-created remote file, but the run cannot PASS or
create promotable evidence.

## Supersession

Current pins are:

- helper SHA256:
  `a429d65a0c01a5d5e3dd2c0f328593ac6a132f33ed0928d930e389e7ad6d1a62`;
- focused test SHA256:
  `386fca45a81e723cec6ab23abe26821d98b7724bba2e10a48d8aa176ab65721e`;
- inactive policy draft SHA256:
  `c17942eb1dba273cd021c416a0ad99fc63388ab0ecedab7fa9b747b853daf334`.

The old connected promotion record remains preserved at its original path and
hash `63dc2b8d...05db041`. The current helper cannot consume it: connected
promotion moved to
`workspace/private/state/s22plus_fyg8_r4w1a_connected_dry_run_pass_v2.json`
with schema `s22plus_fyg8_r4w1a_connected_pass_v2`. The v2 record is absent.

## Validation

- Python bytecode compilation passed;
- 23 focused live-helper tests passed;
- 44 related builder, checker, marker-oracle, and live-helper tests passed;
- the full helper offline gate reran the exact independent artifact checker
  and returned `PASS_R4W1A_LIVE_HELPER_OFFLINE_CHECK`;
- offline output reported `device_contact=false`, `device_write=false`,
  `flash=false`, and both policies inactive;
- `git diff --check` passed.

Claude Opus independently confirmed its prior MUST-FIX was closed, found no
new issue in the delta, returned `GO` for this host-only commit and a fresh
connected read-only dry-run request, and retained `NO-GO` for oracle policy
activation or capture.

## Next Gate

The next executable device step is one fresh-ack connected read-only dry-run
of the exact helper above to create the v2 promotion record. It performs no
`bugreportz`, device write, reboot, Download transition, Odin transfer, or
flash. The operator approval that preceded this review and source change is not
carried forward.

Only after the v2 record exists may its exact SHA be pinned into a separately
reviewed oracle ACTIVE clause. The one-capture oracle rehearsal then requires
another fresh attended acknowledgement. Candidate policy remains blocked.
