# Native Init V3147 DOOMGENERIC SFX Stream Sigpipe Safe Live Validation

## Summary

- Cycle: `V3147`
- Track: DOOM native SFX audio path over the large grouped HUD loop.
- Result: PASS for software audio path and process stability; physical audibility remains operator-heard validation.
- Flashed image: `workspace/private/inputs/boot_images/boot_linux_v3147_doomgeneric_sfx_stream_sigpipe_safe.img`
- Boot SHA256: `852ecc549c9e3d74c4e55a675940900aeb19d24161ca19418360886574041020`
- Init: `A90 Linux init 0.10.129 (v3147-doomgeneric-sfx-stream-sigpipe-safe)`

## Flash Gate

- Rollback precondition: v2321, v2237, and v48 rollback images existed and matched the expected SHA256 values.
- Recovery precondition: checked recovery image was present under the private firmware inputs.
- Flash path: `workspace/public/src/scripts/revalidation/native_init_flash.py --from-native`.
- Remote write/readback: boot partition prefix SHA256 matched the local V3147 image SHA256.
- Forbidden partitions: no forbidden partition write path was used.

## Health

- Native flash helper verification: `version` and `status` returned V3147 with status OK.
- Direct post-flash `status`: `BOOT OK`, selftest summary `pass=12 warn=1 fail=0`.
- Direct post-flash `selftest verbose`: PASS, `fail=0`.
- Note: one direct serial command immediately after boot hit input framing noise; a following standalone `version` command resynchronized and passed.

## DOOM SFX Validation

- `video demo doom loop-start 0 --wad runtime-private --sha256 1d7d43be501e67d927e415e0b8f3e29c3bf33075e859721816f652a526cac771` returned `rc=0`.
- Runtime WAD: present, regular, size OK, expected SHA256 configured.
- Active engine: `doomgeneric-private-link-v3147-sfx-stream-sigpipe-safe`.
- Sound mode: `native-doom-sfx-pcm-stream-sigpipe-safe-v3147`.
- Stream path: `/cache/a90-runtime/a90-doomgeneric-v3147-sfx.pcmstream`.
- Audio path markers: `video.demo.doom.audio.source=native-pcm-stream`, `video.demo.doom.audio.real_doom_sfx=1`, `audio.play.source=pcm-stream`, `audio.play.pcm_stream.path_allowed=1`.
- First loop-start audio worker completed the bounded 10 second stream: `frames_done=480000`, `bytes_done=1920000`, `done=1 rc=0`.
- After the audio worker exited, `video demo doom loop-status` still reported `active=1`, `continuous=1`, proving the helper no longer dies on FIFO reader close.
- Manual audio stream restart while the loop was active succeeded, followed by `doompad tap use` and `doompad tap fire`; the restarted worker also completed `done=1 rc=0` and the DOOM loop remained `active=1`.

## Root Cause Fixed

- V3143 opened the real SFX path but the PCM stream could hit `EPIPE` and kill playback.
- V3144 added nonblocking FIFO behavior but still treated `EAGAIN` as fatal.
- V3145 added PCM write retry but missed source FIFO `EAGAIN`.
- V3146 completed the 10 second stream, but the helper still exited after the audio reader closed.
- V3147 ignores SIGPIPE in the generated DOOM SFX backend and closes/reopens the FIFO writer instead of letting the helper die.

## Limits

- Music remains disabled with `-nomusic`; this validates DOOM SFX only.
- The native audio worker is still bounded by the existing 10 second safety cap. The DOOM loop survives after the worker exits, and a new `audio play --pcm-stream ...` command can reconnect while the loop remains active.
- No Wi-Fi connect, DHCP, or Wi-Fi ping was run.
