# Native Init V2855 Audio Chime Bundled SET-cal Live Handoff

## Summary

- Cycle: `V2855`
- Track: post-promotion latest-candidate audio chime playback regression.
- Decision: `v2855-standalone-bundled-chime-pass-before-rollback`
- Result directory: `workspace/private/runs/audio/v2855-audio-late-manifest-wait-20260619-172123`
- Candidate tag/version: `v2853-audio-productization-marker-refresh` / `0.10.17`
- Candidate image SHA256: `780078e8932a98a87c6077c8622842511b65f3866cd226f5c3d1bd01ab93cc16`
- Rollback attempted: `1`
- Rollback recovery fallback used: `0`
- Rollback health: version_ok=`1` selftest_fail0=`1`
- Operator audible confirmation: `pending-human-listen-confirmation`

## Standalone Bundled Evidence

- Native command: `audio chime --duration-ms 1200 --amplitude-milli 80 --execute`
- Host artifact deployment performed: `0`
- Bundled manifest path: `/a90/audio/manifests/audio-setcal-internal-speaker-safe.manifest`
- Bundled root: `/a90/audio/setcal/internal-speaker-safe`
- Card ready after play start: `1` after `1` polls
- Card poll last summary: `{"dev_snd_line": "audio.dev_snd.count=61 control_like=1 pcm_like=59", "has_adsp_rpmsg": true, "has_sound_card": true, "has_sound_control": true, "no_soundcards": false, "proc_asound_cards_line": "audio.proc_asound_cards= 0 [sm8150tavilsndc]: sm8150-tavil-sn - sm8150-tavil-snd-card sm8150-tavil-snd-card", "rpmsg_line": "audio.rpmsg.count=20 adsp_like=7 cdsp_like=0", "sound_class_line": "audio.sound_class.count=128 card_like=1 control_like=1"}`
- Manifest wait started/ready/timeout: `1 / 1 / 0`

## Playback Evidence

- Worker status done/attempts: `1` / `2`
- Worker status stdout: `workspace/private/runs/audio/v2855-audio-late-manifest-wait-20260619-172123/13_candidate-audio-play-status-02.txt`
- Worker log stdout: `workspace/private/runs/audio/v2855-audio-late-manifest-wait-20260619-172123/14_candidate-audio-standalone-chime-worker-log.txt`
- Worker started/done: `1` / `1`
- Integrated done: `1`
- Sound-control ready/timeout: `1` / `0`
- SET-cal hold/all-set/dealloc: `1 / 1 / 1`
- Route apply/reset OK: `1 / 1`
- PCM write/done: `1 / 1`
- Safety amplitude/duration cap: `1 / 1`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is flashed; no runtime ACDB files are copied from the host in this unit.
- No forbidden partitions are touched.
- `audio chime` uses amplitude `80` milli and duration `1200` ms by default, below the source cap.
- Public report is metadata-only; private raw command transcripts stay under `workspace/private/`.
