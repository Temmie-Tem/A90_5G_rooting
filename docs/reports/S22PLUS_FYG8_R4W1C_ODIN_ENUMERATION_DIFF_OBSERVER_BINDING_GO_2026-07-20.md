# S22+ FYG8 R4W1-C Odin Enumeration-Diff Observer Binding GO

Date: 2026-07-20 KST

Target: `SM-S906N/g0q/S906NKSS7FYG8`

Verdict: `BINDING_GO_TO_SEPARATE_POLICY_ONLY_ACTIVATION`

Scope: host-only binding generation, static validation, focused and adjacent
tests, deterministic private artifact generation, and independent read-only
review. No device, USB, ADB, reboot, Download transition, Odin execution,
enumeration, transfer, flash, partition write, policy edit, one-shot
consumption, or acceptance decision occurred.

## Exact Binding Snapshot

Source checkpoint:

`5056c2cda8b74802f9802b9266cd997ca3e43341`

```text
observer helper
  size    104055
  SHA256  90707b79c67080533c9c32f9d787f254d83c11ce98471b9a7bfb1c7d15871913

observer focused test
  size    87409
  SHA256  510bf46191f05096d716409f29a754c928c1f332b8ada767819495235998a545

inactive exception draft
  size    10848
  SHA256  ddcf158a40d4cf56853340c8219535038afb99e99f21b81a9b5f42f902b02c4a

AGENTS.md policy base
  size    459358
  SHA256  99bd5805e3e37e27f203d5b26a21e9730c54fa3d0bf2390524309850cdef5a18

binding generator
  size    34761
  SHA256  61c0d5cfac6c76ed2553119e1c32706e6bf86cfbc3dbb2a50c7968b48d6372e6

binding generator focused test
  size    21729
  SHA256  c65420fd541b4a8f136f4ff7b6dd406bee8abf6d76d331916e17ebb0f90be6ed

private binding packet
  size    2807
  SHA256  daeb71c7b5e0ab6ee331009c8c6fc2ed3bea16570f39ad84086a6c9c5a955ddd

private rendered clause
  size    5444
  SHA256  9f42de1cb609f9897799f82d1e59f11fd1ec24cc018da3ed9099adb1e89d497e

normalized clause-template digest
  SHA256  93d8959a7df8b52574ed4d734122d5799b5f36d0077e82532feed49d75aa2677

/usr/bin/odin4 data-only precondition
  size    3746744
  SHA256  6754aa54f2abe6e99ece32414cd34c8b23b28dbddde537a33203036813637c3b
```

The packet verdict remains
`PENDING_R4W1C_ENUM_DIFF_OBSERVER_INDEPENDENT_BINDING_REVIEW`; the independent
GO is this report, not a mutation of the private packet. Every packet field for
policy, device, reboot, Download, Odin execution/enumeration/transfer, flash,
partition writes, and acceptance is `false`.

## Hardened Generator

The generator has no observer import, dynamic import, code execution, process,
USB, ADB, or Odin execution surface. It renders the exact reviewed clause
locally from the frozen source identities and rejects any result other than the
known 5,444-byte clause.

All seven inputs are opened as direct no-follow regular-file FDs. Their complete
metadata, pathname inode, and bytes are held and repeatedly revalidated through
artifact closure. The output root is opened one component at a time from `/`
with held directory FDs. Both flat artifacts use `O_EXCL|O_NOFOLLOW`, stay open
through the run, and are compared against their complete expected bytes after
both initial artifact reads and immediately before closure.

Partial or stale output cannot become accepting evidence. A partial packet is
still `PENDING`, and later policy activation must independently reopen and
rehash the exact reviewed packet and clause after this generator's descriptors
have closed.

## Review History

Five fresh `gpt-5.6-sol` xhigh read-only sessions reviewed successive exact
binding snapshots. They did not execute or import Python, run tests or the
generator, contact a device, inspect USB/ADB, execute Odin, use the network, or
edit files.

Reviewer `019f7f99-45b3-70c2-852c-6def9e46701c` returned `BINDING_NO_GO` for a
pathname-based output-parent replacement window and a stale PASS-labelled
partial packet. Output artifacts were changed to FD-relative creation and the
private packet was made permanently `PENDING`.

Reviewer `019f7fa2-2ae7-7e60-8fac-518e4f73ed8b` returned `BINDING_NO_GO` for a
multi-component output-root acquisition race. Every output ancestor is now
opened and held from `/` with `O_DIRECTORY|O_NOFOLLOW`.

Reviewer `019f7fad-ce09-77f3-9efd-af1427f152dd` returned `BINDING_NO_GO` for a
transient rendered-clause snapshot and an invocation-created child-directory
replacement window. Clause identity is now tied to the qualified source
snapshot, and the child directory was removed in favor of two flat artifacts.

Reviewer `019f7fb9-35e3-7770-ab0b-15d25b6670fb` returned `BINDING_NO_GO` for
three remaining boundaries: pre-gate observer import, coordinated pathname
re-renders, and missing final byte validation after both output reads. The
observer import was removed, clause rendering now uses only held source bytes,
and final output validation rereads exact expected bytes for both artifacts.

Final reviewer `019f7fc7-dea1-7312-a4a8-fb7a41fea3be` independently reproduced
all identities, Git provenance, clause normalization, marker counts, inactive
state, and action-false packet fields. It found no HIGH or MEDIUM issue and
returned `BINDING_GO`.

The final review retained two LOW boundaries:

- after generator descriptors close, later policy activation must independently
  reopen and rehash the reviewed private artifacts; and
- the generator and its test were not objects in the source checkpoint, so this
  binding commit must preserve their exact reviewed bytes.

## Validation

```text
py_compile with ResourceWarning fatal           PASS
focused binding-generator tests                 21 passed
exact related R4W1-C regression suite           185 passed
offline binding-source verdict                  PASS_R4W1C_ENUM_DIFF_OBSERVER_BINDING_SOURCE_OFFLINE_CHECK
private packet emission verdict                 PASS_R4W1C_ENUM_DIFF_OBSERVER_BINDING_PACKET_EMITTED_HOST_ONLY
private packet semantic verdict                 PENDING_R4W1C_ENUM_DIFF_OBSERVER_INDEPENDENT_BINDING_REVIEW
policy BEGIN/END/ACTIVE counts in AGENTS.md      0/0/0
observer consumed state                         absent
policy/device/Odin/transfer/flash actions       false
git diff --check                                PASS
```

## Decision

Commit the exact generator, focused tests, this report, and the status update.
Do not edit `AGENTS.md` in this commit. The only next unit is a separate
policy-only activation that installs the exact reviewed clause, independently
reopens and rehashes all binding inputs and artifacts, reruns the inactive
precondition, and receives its own post-activation review before any attended
device approval. This binding GO itself authorizes no device contact or live
observer execution.
