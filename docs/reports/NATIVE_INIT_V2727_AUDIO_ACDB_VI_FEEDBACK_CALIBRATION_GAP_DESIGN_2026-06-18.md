# NATIVE_INIT V2727 — vi-feedback ACDB calibration gap design

Date: 2026-06-18
Scope: host-only analysis and next-unit design
Inputs: V2407/V2420 Android-good evidence, V2632 SET capture, V2590 arg-order RE, V2726 native replay live result

## Decision

`v2727-design-vi-feedback-acdb-capture-before-next-native-replay`

Do not rerun the V2725/V2726 native SET sequence unchanged. V2726 proved the corrected native
speaker SET replay reaches `/dev/msm_audio_cal` successfully: every ALLOCATE/SET/DEALLOCATE ioctl
returned `rc=0 errno=0`, and the stale per-subsystem custom topology path stayed silent. The
remaining failure moved downstream to PCM prepare, where the DSP rejects AFE/q6asm/ADM state.

The highest-value next branch is the Android-good `vi-feedback` ACDB path that runs immediately
before the speaker path and has never been byte-captured or replayed in native init.

## Evidence Re-read

### V2726 native frontier

V2726 replayed the corrected SET order:

`[39, 20, 20, 13, 9, 11, 12, 15, 23, 16, 21]`

The helper marker shows:

| ioctl | count | cal_type order | result |
| --- | ---: | --- | --- |
| `AUDIO_ALLOCATE_CALIBRATION` | 4 | `[39, 11, 15, 16]` | all `rc=0 errno=0` |
| `AUDIO_SET_CALIBRATION` | 11 | `[39, 20, 20, 13, 9, 11, 12, 15, 23, 16, 21]` | all `rc=0 errno=0` |
| `AUDIO_DEALLOCATE_CALIBRATION` | 4 | `[16, 15, 11, 39]` | all `rc=0 errno=0` |

The bounded PCM probe then failed at prepare:

```text
__afe_port_start: port id: 0x4000
afe_callback: cmd = 0x100ef returned error = 0x2
afe_apr_send_pkt: DSP returned error[ADSP_EBADPARAM]
afe_send_cal_block: AFE cal for port 0x4000 failed -22
q6asm_callback: cmd = 0x10da1 returned error = 0x12
q6asm_set_pp_params: DSP returned error[ADSP_ENEEDMORE]
q6asm_send_cal: audio audstrm cal send failed
msm_pcm_routing_get_app_type_idx: App type not available, fallback to default
adm_open:port 0x4000 path:1 rate:48000 mode:1 perf_mode:0,topo_id 0x10004000
adm_open:bit_width:0 app_type:0x11135 acdb_id:15
adm_open: DSP returned error[ADSP_EFAILED]
msm_pcm_playback_prepare: stream reg failed ret:-22
```

The old self-inflicted stale-topology signature did not return:

- no `send_asm_custom_topology`
- no `cmd = 0x10dbe`
- no per-subsystem `ASM_CMD_ADD_CUSTOM_TOPOLOGIES` failure

### Android-good vi-feedback path

V2407/V2397 Android-good logcat shows a `vi-feedback` route and ACDB calibration path before the
speaker RX path:

```text
audio_hw_primary: enable_snd_device: snd_device(295: vi-feedback)
audio_route: Apply path: vi-feedback
audio_hw_utils: audio_extn_utils_send_app_type_cfg: usecase->in_snd_device vi-feedback
ACDB -> send_audio_cal, acdb_id = 102, path = 1, app id = 0x11132, sample rate = 8000, afe_sample_rate = 8000
ACDB -> AUDIO_SET_AUDPROC_CAL cal_type[11] acdb_id[102] app_type[69938]
ACDB -> GET_AFE_TOPOLOGY_ID for adcd_id 102, Topology Id 1001025c
ACDB -> AUDIO_SET_AFE_CAL cal_type[17] acdb_id[102]
```

The speaker path follows later on the same playback edge:

```text
audio_hw_utils: send_app_type_cfg_for_device PLAYBACK app_type 69941, acdb_dev_id 15, sample_rate 48000
ACDB -> send_audio_cal, acdb_id = 15, path = 0, app id = 0x11135, sample rate = 48000, afe_sample_rate = 48000
ACDB -> AUDIO_SET_AUDPROC_CAL cal_type[11] acdb_id[15] app_type[69941]
ACDB -> AUDIO_SET_VOL_CAL cal type = 12
ACDB -> GET_AFE_TOPOLOGY_ID for adcd_id 15, Topology Id 1001025d
ACDB -> AUDIO_SET_AFE_CAL cal_type[16] acdb_id[15]
```

V2420 already called out this edge but did not capture raw ioctl request bytes:

- `acdb_id=102`
- `path=1`
- `app id=0x11132`
- `cal_type[17]`

### Existing capture coverage gap

V2632 captured the speaker SET manifest only:

- ordered cal_types: `[13, 9, 11, 12, 15, 23, 16, 21]`
- payload-backed cal_types: `[11, 15, 16]`
- header/no-payload cal_types: `[9, 12, 13, 21, 23]`

Later V2716/V2721/V2726 added the real-HAL cal_type `39` core topology and cal_type `20` speaker
protection headers. None of the accepted native manifests include the vi-feedback `acdb_id=102`
AFE path or a cal_type `17` payload.

## Interpretation

The native route controls are not the first suspect anymore:

- V2726 applies the Android-observed speaker controls and they return `rc=0`.
- Android-good enables `vi-feedback` and sends an ACDB path for `acdb_id=102` before speaker RX.
- Native V2726 shows WSA temperature and SP-feedback logging failures near the PCM failure window.
- The DSP errors are now in AFE/q6asm/ADM prepare after successful SET ioctl acceptance.

Therefore the next useful discriminator is whether native lacks Android's preceding
vi-feedback calibration. This is not a blind new mixer route; it is a logcat-proven HAL ACDB path
that is absent from all native replay manifests so far.

This is still a hypothesis, not a confirmed root cause. The q6asm `ADSP_ENEEDMORE` and
`App type not available` lines may also point to speaker cal_type `15` / app-type / session state.
But V2726 already replays speaker cal_type `15` with ioctl success. Capturing and replaying the
missing vi-feedback bytes is the smallest evidence-backed delta before deeper q6asm/ADM RE.

## Next Unit Design

### V2728 — Android-good vi-feedback SET capture build

Build a rooted own-process Android helper variant using the existing fake-allocate/fake-SET capture
mechanism. The helper should initialize ACDB, then call a vi-feedback calibration candidate rather
than the speaker-only path.

Candidate call derived from Android-good logcat plus V2590 arg-order RE:

```c
acdb_loader_send_audio_cal_v5(
    102,      /* acdb_id: vi-feedback */
    1,        /* path/capability: Android log path=1 */
    0x11132,  /* app type: 69938 */
    8000,     /* sample rate */
    0,        /* session/internal selector, as speaker corrected call */
    8000,     /* AFE sample rate */
    1);       /* instance/use-case flag */
```

This candidate must be treated as a design hypothesis until the fake-SET capture proves the emitted
records. Do not replay it natively from guessed geometry.

### V2729 — Android-good vi-feedback SET capture live

Run under the existing rollbackable Android-handoff/own-process capture pattern:

- fake `AUDIO_ALLOCATE_CALIBRATION` / `AUDIO_SET_CALIBRATION` / `AUDIO_DEALLOCATE_CALIBRATION`;
- do not pass real SET ioctls to Android kernel state;
- dump ordered SET arg bytes and any dma-buf payloads privately;
- reject zero-buffer false positives using the operator discriminator;
- rollback to V2321 and verify `selftest fail=0`.

Acceptance:

- at least one real record for `cal_type=17` with `acdb_id=102`;
- any paired vi-feedback `cal_type=11` / topology-header records captured in order;
- raw bytes private only, report metadata only.

If the candidate call emits no vi-feedback SET records, do not synthesize them. The next step would
be an Android-good in-HAL trace or more RE of the HAL usecase path.

### V2730+ — native replay extension only after capture verification

After operator/local verification of the vi-feedback capture, extend the native replay manifest by
prepending the captured vi-feedback records before the speaker records. The replay order must come
from the captured event order, not from this report's guess.

Operational invariants for later native live replay stay unchanged:

- runtime `/dev/msm_audio_cal` SET only;
- one-shot;
- exact captured arg bytes and payloads;
- reverse deallocate cleanup;
- bounded low-amplitude PCM probe;
- dmesg split before and after PCM;
- rollback to V2321.

## Branch Classifier

| Result | Meaning | Next action |
| --- | --- | --- |
| vi-feedback `cal_type=17`/`acdb_id=102` captured | Missing Android ACDB path becomes concrete | build manifest extension and replay in native |
| vi-feedback capture has records but no `17` | candidate arg tuple incomplete or wrapper semantics wrong | inspect emitted metadata, adjust from source/logcat, do not replay |
| vi-feedback own-process call emits no SET records | HAL path not reproduced by direct helper | use Android-good in-HAL or lower-function RE, do not guess |
| later native replay clears AFE/WSA but q6asm remains | vi-feedback was co-primary but not sufficient | focus cal_type `15` / app-type/session/q6asm state |
| later native replay still has same AFE/q6asm/ADM errors | vi-feedback not the gate | pivot to post-SET runtime trigger or q6asm/ADM state RE |

## Non-goals / Stops

- Do not rerun V2726 unchanged.
- Do not revive stale per-subsystem cal_types `10/14/24`.
- Do not add blind smart-amp gain/boost or unobserved mixer writes.
- Do not replay guessed vi-feedback geometry in native.
- Do not commit raw ACDB payloads, raw logs, proprietary vendor libraries, or identifiers.

## Validation

Host-only validation performed:

- Re-read `GOAL.md`, `AGENTS.md`, `CLAUDE.md`, and the ACDB operator spec.
- Re-read V2726 live result report and private V2726 ioctl/dmesg markers.
- Re-read Android-good V2407/V2397 vi-feedback logcat evidence.
- Re-read V2420 note that the vi-feedback edge existed but raw ioctl bytes were not captured.
- Re-read V2632 SET-capture coverage and V2590 `send_audio_cal_v5` argument-order RE.
- No device action in this unit.
