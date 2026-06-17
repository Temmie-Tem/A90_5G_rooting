# NATIVE_INIT V2629 — ACDB SET payload capture design

Date: 2026-06-17

## Scope

Host-only design for the next ACDB capture unit after V2628. No device code ran,
no Android handoff ran, no native replay `SET` ran, and no raw payload bytes were
published.

The design target is the actual `AUDIO_SET_CALIBRATION` packet that
libacdbloader would send for the AFE-topology path. V2628 proved that the direct
`0x13262` GET result is only `0x00000004` plus an indirect scalar
`0x00000001`, so it must not be treated as a native replay payload.

## Decision

- decision: `v2629-design-setcal-arg-plus-dmabuf-capture`
- native_replay_ready: `False`
- live_capture_ready: `design-only`
- next_unit: `V2630 build-only SET-cal capture helper/preload`
- replay_boundary: do not add any V2614/V2629-derived SET material to the native
  replay manifest until operator Gate-2 maps the captured SET records.

## Evidence Basis

### V2628 Gate-2 Rejection

- `0x130d8` returned topology ID `0x1001025d`.
- `0x13262` direct output was always `0x00000004`.
- `0x13262` indirect `ind-afe-topology` was always `0x00000001`.
- Therefore the V2627 four-byte indirect record is useful evidence, but not a
  cal_type 8/9 native replay block.

### V2614 Already Reached the Relevant SET Boundary

The V2614 meta-list post-init `send_audio_cal_v5` route produced fake
`AUDIO_SET_CALIBRATION` events while staying measurement-only. The important
point is that the missing AFE topology path is visible at the SET layer, not the
`0x13262` direct GET layer.

Observed SET metadata from the V2614 private `ioctl-trace-events.jsonl`:

| order | cal_type | data_size | cal_type_size | cal_size | mem_handle | role |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 13 | 40 | 24 | 0 | -1 | app / stream metadata |
| 2 | 9 | 52 | 36 | 0 | -1 | AFE topology-like header; candidate for V2393 cal_type 8/9 gate |
| 3 | 11 | 48 | 32 | 18084 | 15 | AUDPROC common payload |
| 4 | 12 | 48 | 32 | 0 | 17 | VOL/gain path returned no payload |
| 5 | 15 | 36 | 20 | 28 | 20 | AUDPROC/ASM stream payload |
| 6 | 23 | 48 | 32 | 0 | -1 | AFE topology ID header (`0x1001025d`) |
| 7 | 16 | 44 | 28 | 1560 | 21 | AFE common payload |
| 8 | 21 | 72 | 56 | 28 | -1 | speaker/VI-adjacent header |

This is the decisive design pivot: some relevant AFE topology records may be
header-only (`cal_size=0`, `mem_handle=-1`). A capture that only dumps dmabuf
contents will miss them. The next helper must capture the full ioctl argument
bytes as well as any referenced dmabuf bytes.

## Proposed Capture Mechanism

Build a new ARM32 combined preload, reusing the V2531 ioctl interposer and the
V2613 ACDB tap style:

1. Keep `A90_ACDB_FAKE_ALLOCATE=1`.
2. Intercept `AUDIO_ALLOCATE_CALIBRATION` and `AUDIO_DEALLOCATE_CALIBRATION` as
   fake success, as before.
3. Intercept `AUDIO_SET_CALIBRATION` as fake success; never call the kernel SET.
4. Before returning fake success for each SET:
   - copy `arg[0:data_size]` into a private raw file;
   - hash and log the full SET argument bytes;
   - parse `data_size`, `cal_type`, `cal_type_size`, `buffer_number`,
     `cal_size`, and `mem_handle`;
   - if `cal_size > 0` and `mem_handle >= 0`, `mmap` that fd inside the same
     process and copy exactly `cal_size` bytes into a second private raw file;
   - if `cal_size == 0` or `mem_handle < 0`, mark it as header-only and do not
     treat missing dmabuf bytes as failure.
5. Write ordered metadata to
   `/data/local/tmp/a90-acdb-ownget/setcal-events.jsonl`, including:
   - sequence, request, intercept result, errno;
   - parsed SET fields;
   - raw SET-arg size and SHA-256;
   - dmabuf mmap status, size, and SHA-256 when applicable;
   - no raw bytes in public output.

The preload must bound both copies:

- SET argument copy cap: `data_size <= 4096`;
- dmabuf copy cap: `cal_size <= 262144`;
- out-of-bounds values are reported as metadata-only and do not trigger broader
  reads.

## Driver Path

Use the V2611/V2613 path that already produced the relevant SET sequence:

```text
acdb_loader_init_v3("/vendor/etc/audconf/OPEN", delta_dir, empty_meta_list_head)
  -> a90_arm_capture()
  -> acdb_loader_send_audio_cal_v5(15, 1, 0x11135, 48000, 0, 48000, 1)
```

Rationale:

- V2614 proved this path reaches `AUDIO_SET_CALIBRATION` for cal_type 9, 11,
  12, 15, 16, 21, and 23.
- It already avoids the `arg2=0` early bail.
- It stays in the own-process Android-good measurement path, avoiding the
  closed in-HAL preload and cross-process dmabuf lines.
- It gives the operator the exact SET argument bytes for the header-only AFE
  topology records and dmabuf bytes for payload-backed records.

## Acceptance

Full capture success:

- Android handoff rolls back to V2321 and final selftest is `fail=0`;
- no real `AUDIO_SET_CALIBRATION` pass-through occurs;
- ordered SET records include at least cal_type `9` and `23`;
- every SET record has a private raw `arg[0:data_size]` dump and SHA-256;
- every SET record with `cal_size > 0` and `mem_handle >= 0` has a private
  dmabuf dump and SHA-256, or an explicit mmap failure reason;
- public report lists only metadata and hashes.

Partial success:

- cal_type `9` and/or `23` SET argument bytes are captured, but one or more
  dmabuf payload dumps fail. This is still operator-valuable because the AFE
  topology candidates appear header-only in V2614.

Failure:

- no cal_type `9`/`23` SET record appears;
- any real kernel `AUDIO_SET_CALIBRATION` is passed through;
- raw bytes are written outside private run storage;
- rollback to V2321 or selftest fails.

## Safety Boundary

- Measurement-only Android-good own-process capture.
- No native replay.
- No real kernel calibration SET.
- No speaker write.
- Raw SET args and dmabuf payloads stay private under
  `workspace/private/runs/audio/<run>/`.
- Public artifacts contain only ordered metadata and SHA-256 values.

## Future Unit Split

1. **V2630 build-only:** implement the SET-arg plus dmabuf capture preload and
   runner dry-run checks. Static validation must require:
   - fake SET mode is present;
   - real SET pass-through is forbidden in fake mode;
   - SET argument dump is present;
   - dmabuf mmap dump is present;
   - raw output path is private-only.
2. **V2631 live capture:** run the V2611/V2613 send path with the V2630 preload,
   pull private artifacts, rollback to V2321, and classify the ordered SET
   record set.
3. **Gate-2 handoff:** operator maps cal_type `9`/`23` and any dmabuf-backed
   records to the native replay manifest. Only after that can a multi-cal
   native replay gate be considered.

## Validation

- Host-only source/report review.
- `git diff --check`.
