# S22+ FYG8 R4W1-C2 USBFS Repair Codex Adversarial GO

Date: 2026-07-21 KST

## Verdict

`GO_TO_EXACT_REACTIVATION`

An independent ephemeral `gpt-5.6-sol` reviewer inspected commit `10d44120`
against parent `eacdc481`, the exact pre-consumption failure evidence, corrected
helper and tests, binding generator, private packet, rendered clause, and
current `AGENTS.md` block. It returned no MUST-FIX finding.

This review was host-only and read-only. It authorized only exact policy-block
replacement, not device contact or live execution.

## Confirmed Findings

- The live result truthfully records the exact measured-identity error,
  `candidate_transfer_attempted=false`, and
  `FAIL_R4W1C2_PRECONSUMPTION_NO_CANDIDATE_FLASH`.
- The standalone timeline equals the embedded timeline and contains only
  `live_session_start` and `live_session_end`.
- The connected preflight equals the result baseline, and the consumed state is
  absent.
- The parent helper returned `immutable_identity` but rejected that field in
  the complete-sample schema, so an otherwise successful retry was impossible.
- The repair retries the exact snapshot-change condition only before the first
  complete sample. The same condition after stabilization starts is fatal.
- Arbitrary USBFS errors remain fatal.
- Complete samples require canonical
  `usbfs-immutable-v1:<64-lowercase-hex>` identity and compare path, device,
  inode, rdev, and digest replacement-sensitively.
- Focused tests cover initial race, late-race rejection, missing digest, inode
  replacement, and digest-only replacement.
- The new clause is exactly `13442` bytes, SHA256
  `cae20071b1f23b0e8e7944dd3632955c334cb438f54a5a7a73559ceafdb1fe3b`.
- Its only differences from the current block are the reviewed helper and test
  hashes. Rollback, boot-only, one-shot, physical-continuity, and fresh-
  acknowledgement semantics are unchanged.

## Residuals

- Initial udev metadata settlement is a plausible and code-consistent causal
  diagnosis, but the durable result records only the wrapped measured-identity
  error. It is not promoted to independently proven device evidence.
- The reviewer inspected test coverage but intentionally did not rerun tests or
  source-check under its read-only scope. Codex separately ran the related
  `162/162` suite and exact source-check successfully.
- Binding `--source-check` is intentionally preactivation-only. Post-activation
  qualification must use the live helper offline gate.

## Reviewer Identity

- Model: `gpt-5.6-sol`, reasoning effort `xhigh`.
- Session: `019f8060-e450-79a1-ae7c-170d4dcfbbc6`.
- Reported tokens used: `108638`.
- Sandbox: read-only; no file edits, device commands, builds, tests, or USB
  probes were permitted.

An earlier Claude Opus delta-review attempt consumed output and cache budget but
hit its rolling session limit before a verdict. It is not an approval and was
not used as activation authority.

## Approved Next Step

Replace only the exact R4W1-C2 block in `AGENTS.md` with the reviewed private
clause unchanged, commit that policy edit separately, then rerun the related
tests and live-helper offline check. Device contact remains forbidden until
those pass and the operator supplies the live acknowledgement again. The old
acknowledgement does not carry.
