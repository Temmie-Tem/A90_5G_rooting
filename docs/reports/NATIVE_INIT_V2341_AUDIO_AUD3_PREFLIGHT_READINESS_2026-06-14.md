# Native Init V2341 Audio AUD-3 Preflight Readiness

## Summary

- Cycle: `V2341`
- Track: audio AUD-3 preflight readiness, live read-only/no-flash.
- Decision: `v2341-aud3-readiness-pass-awaiting-exact-gate`
- Result: PASS for readiness; AUD-3 materialization not run.
- Device flash: `no`.
- Device mutation: `none`.
- Private evidence: `workspace/private/runs/audio/v2341-readiness-20260614-231812/`.

## Reason

V2339 fixed the V2338 card-wait parser bug and V2340 moved live serial
observation commands onto shared recovery. The only remaining substantive
frontier is the exact-gated V2334 AUD-3 preflight live retry. The current operator
wording in chat is intentionally not the exact gate, so this iteration performed
only a read-only readiness check:

- confirm the serial bridge is reachable,
- confirm the resident rollback checkpoint still verifies as V2321,
- confirm `selftest verbose` still returns `fail=0`,
- confirm the V2335/V2340 runner dry-run preflight still has all required image
  hashes and helper paths.

## Readiness Evidence

- `a90_bridge.py status --json`: bridge process listening on `127.0.0.1:54321`;
  probe state `connected-no-immediate-error`.
- `native_init_flash.py ... --verify-only`: PASS.
  - Resident version: `A90 Linux init 0.9.285 (v2321-usb-clean-identity-rodata)`.
  - Verify protocol: `selftest`.
  - Result: `cmdv1 verify passed: selftest rc=0 status=ok fail=0`.
- `a90ctl.py selftest verbose`: PASS.
  - `selftest: pass=11 warn=1 fail=0`.
  - Existing warning remains `helpers ... manifest=no`; no new failure.
- `native_audio_snd_nodes_preflight_handoff_v2335.py --dry-run`: PASS.
  - `preflight_ok=true`.
  - V2334 candidate SHA: OK.
  - V2321 rollback SHA: OK.
  - V2237 fallback SHA: OK.
  - V48 fallback exists: OK.

An initial host command typo attempted `a90ctl.py 'selftest verbose'` as one
argument and failed before reaching the device command encoder. It was corrected
to `a90ctl.py selftest verbose`; no device mutation resulted from the typo.

## Safety Boundary

- No V2334 flash.
- No ADSP boot command.
- No `/dev/snd` materialization.
- No ALSA open/ioctl, mixer, tinyalsa, PCM, HAL, playback, or `adsprpc`.
- No partition write.

## Current Gate

The next substantive step remains the V2334 AUD-3 preflight materializer. It
must not run until the exact operator phrase is provided:

```text
AUD-3-preflight go: materialize ALSA /dev/snd nodes only on V2334, no open/ioctl/mixer/playback, rollback to V2321
```

## Validation

- `python3 workspace/public/src/scripts/revalidation/a90_bridge.py status --json`: PASS.
- `python3 workspace/public/src/scripts/revalidation/native_init_flash.py workspace/private/inputs/boot_images/boot_linux_v2321_usb_clean_identity_rodata.img --expect-version 0.9.285 --expect-sha256 ca978551aabe4b39563abaf529ccf2522054952d8b2ad852e632d26da88168cb --verify-protocol selftest --bridge-timeout 260 --recovery-timeout 260 --verify-only`: PASS.
- `python3 workspace/public/src/scripts/revalidation/a90ctl.py --timeout 120 --input-mode slow --hide-on-busy selftest verbose`: PASS.
- `python3 workspace/public/src/scripts/revalidation/native_audio_snd_nodes_preflight_handoff_v2335.py --dry-run`: PASS.
- `git diff --check`: PASS.
