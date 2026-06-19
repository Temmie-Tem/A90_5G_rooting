# Native Init V2856 Audio Stop Execute Live Handoff

## Summary

- Cycle: `V2856`
- Track: post-promotion latest-candidate audio stop-execute regression.
- Decision: `v2856-stop-execute-pass-before-rollback`
- Result directory: `workspace/private/runs/audio/v2856-audio-late-manifest-wait-20260619-172950`
- Candidate tag/version: `v2853-audio-productization-marker-refresh` / `0.10.17`
- Candidate image SHA256: `780078e8932a98a87c6077c8622842511b65f3866cd226f5c3d1bd01ab93cc16`
- Rollback attempted: `1`
- Rollback recovery fallback used: `0`
- Rollback health: version_ok=`1` selftest_fail0=`1`

## Stop Execute Evidence

- Command: `audio stop internal-speaker-safe --execute`
- Stop rc: `0`
- Stop stdout: `workspace/private/runs/audio/v2856-audio-late-manifest-wait-20260619-172950/14_candidate-audio-stop-execute.txt`
- Execute supported/requested: `1` / `1`
- No-active playback/SET-cal markers: `1` / `1`
- Route reset mode/core/write-done: `1` / `1` / `1`
- Stop done/pass: `1` / `1`
- Refused/error/write-failed: `0` / `0` / `0`

## Boot Chime Settle

- Boot chime launch log: `/cache/a90-audio-play/boot-chime-launch.log`
- Boot chime launch log stdout: `workspace/private/runs/audio/v2856-audio-late-manifest-wait-20260619-172950/09_candidate-audio-boot-chime-launch-log-before-stop.txt`
- Boot chime started markers: `1`
- Worker done before stop/attempts: `1` / `1`
- Worker status stdout: `workspace/private/runs/audio/v2856-audio-late-manifest-wait-20260619-172950/10_candidate-audio-play-status-01.txt`
- Worker log stdout: `workspace/private/runs/audio/v2856-audio-late-manifest-wait-20260619-172950/11_candidate-audio-worker-log-before-stop.txt`
- Card ready before stop: `1` after `1` polls
- Card poll last summary: `{"dev_snd_line": "audio.dev_snd.count=61 control_like=1 pcm_like=59", "has_adsp_rpmsg": true, "has_sound_card": true, "has_sound_control": true, "no_soundcards": false, "proc_asound_cards_line": "audio.proc_asound_cards= 0 [sm8150tavilsndc]: sm8150-tavil-sn - sm8150-tavil-snd-card sm8150-tavil-snd-card", "rpmsg_line": "audio.rpmsg.count=20 adsp_like=7 cdsp_like=0", "sound_class_line": "audio.sound_class.count=128 card_like=1 control_like=1"}`

## Safety

- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py`.
- Only the boot partition is flashed; no host runtime artifacts are copied in this unit.
- The runner issues no PCM playback command; the only active command is one `audio stop --execute`.
- Stop execute is expected to write only the already-reviewed core route reset controls.
- No ACDB deallocate or fake PCM stop is attempted without an active native session.
- Public report is metadata-only; private raw command transcripts stay under `workspace/private/`.
