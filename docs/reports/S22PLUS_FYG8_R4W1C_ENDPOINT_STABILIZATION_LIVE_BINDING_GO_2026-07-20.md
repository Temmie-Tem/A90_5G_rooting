# S22+ FYG8 R4W1-C Endpoint Stabilization Live Binding GO

Date: 2026-07-20 KST

Target: `SM-S906N/g0q/S906NKSS7FYG8`

Verdict: `BINDING_GO_TO_SEPARATE_R4W1C_LIVE_POLICY_ACTIVATION`

Scope: deterministic host-only live-binding generation, complete evidence
reopening, and independent read-only review. No device enumeration or contact,
ADB action, reboot, Download transition, Odin transfer, flash, partition write,
candidate consumption, or live-policy activation occurred.

## Frozen Source

The endpoint-stabilized source is fixed by commit:

```text
69b37554 s22plus: harden R4W1C endpoint arrival
```

Its load-bearing identities are:

```text
live helper SHA256       65c137586b2decf160800f841b7243f3332108332043dbcaa548d7698e080c99
live focused test SHA256 c5966fb411983bed5b72e39400e8c8d15304ec0257e34e435ad5aae075ca1fbb
inert template SHA256    06f28538c4fa358dabd5e35c6bab5e0cd5a83c6e78c39d9ba1a6c1516ced5497
binding generator SHA256 1a7ab0cd1ef1883e4db7e676203155a2ee402510914e7ccba5b749ed040e62e3
binding test SHA256      8c8a4edc01fa1814946c2e1a424bef501cb87bad152e9a39084877011305ffbd
```

## Binding Packet

The pinned generator emitted:

```text
directory
  workspace/private/outputs/s22plus-r4w1c-live-binding-20260719T205737Z

packet.json
  size    5451
  SHA256  a2a4aa676af903f29f8ad43d05644efc3f4c3b461da9f6f9f171b59c055ea3c6

AGENTS_R4W1C_LIVE_CLAUSE.md
  size    9382
  SHA256  09a0388f533ffa9525d9d3b6264e5f53b377507aa00ec76b7e294b9596d90fe2

connected PASS
  size    976
  SHA256  4b8bd44ee171341592e987171137007376dec71432df05b39a29a083c0914f20

connected result
  size    12821
  SHA256  f954c9b7238932f97d0a51c85cd5623ae2deced5b6d4c443992fb73bb0906e3a
```

The packet verdict is
`PASS_R4W1C_LIVE_BINDING_PACKET_EMITTED_HOST_ONLY`. It records `false` for
device contact, device writes, reboot, Download transition, Odin transfer,
flash, and policy editing. Candidate, Magisk rollback, and stock cleanup APs
are regular archives containing exactly one regular `boot.img.lz4` member.
The candidate consumed state remains absent.

## Independent Review

The existing `gpt-5.6-sol` xhigh read-only review session reopened the exact
source commit, packet, rendered clause, connected PASS/result, raw observers,
receipts, transaction indexes, all source and artifact pins, each AP archive,
and the complete 9.68 GB FYG8 firmware evidence.

It confirmed:

- exact byte rendering from the pinned template;
- one begin marker, one end marker, one ACTIVE sentinel, and no placeholder;
- exact endpoint-stabilization and pre/post-sysfs node-continuity language;
- one candidate transfer maximum and mandatory bounded Magisk rollback;
- complete forbidden mechanism and partition scope;
- direct regular connected evidence, empty observer stderr, byte-identical
  duplicate `last_kmsg`, and complete receipts/indexes;
- current `AGENTS.md` remains RETIRED and grants no live authority.

The review found no HIGH, MEDIUM, or LOW issue and returned:

`BINDING_GO`

## Decision

Commit this host-only binding verdict first. Then replace the exact fenced
R4W1-C live block in `AGENTS.md` with the reviewed 9,382-byte clause in a
separate policy-only commit. The installed block must compare byte-for-byte to
the private rendered clause. Post-activation syntax, 181-test, full offline,
and independent post-activation checks remain mandatory.

This report does not authorize device contact or live execution. A later ACTIVE
policy still requires a fresh exact operator acknowledgement
`S22PLUS-FYG8-R4W1C-DIRECT-PID1-LIVE`.
