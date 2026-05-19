# V319 Serial Transfer Append Plan

## Summary

- Native build: `A90 Linux init 0.9.61 (v319)`.
- Goal: add the minimum native primitive needed to transfer generated private property layout files over the existing ACM bridge without `toybox sh`, shell pipes, NCM, tcpctl, or daemon start.
- V318 proved that `toybox sh` is unavailable, while `uudecode -o`, `touch`, `base64`, `sha256sum`, and native `writefile` exist.
- V319 therefore adds scoped `appendfile` plus a larger shell/cmdv1x line buffer, then updates the V317 runner to use `appendfile` + `uudecode -o`.

## Key Changes

- Copy `v261` source tree to `v319` and bump native metadata to `0.9.61 (v319)`.
- Add `appendfile <path> <value...>` to the v319 shell.
  - Opens with `O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC|O_NOFOLLOW` and mode `0600`.
  - Allows only scoped runtime paths under `/mnt/sdext/a90`, `/cache/a90-runtime`, or `/tmp/a90-native`.
  - Rejects `..` traversal and paths outside the allowed workspaces.
- Increase shell input and `cmdv1x` decode buffers to 4096 bytes.
- Update `wifi_private_property_namespace_proof.py` transfer strategy:
  - generate uuencoded base64 text;
  - append chunks using `appendfile`;
  - decode with `toybox uudecode -o`;
  - verify with `toybox sha256sum`.

## Safety Boundaries

- No global `/dev/__properties__` replacement.
- No global bind mount over `/dev/__properties__`.
- No property service socket.
- No property mutation or setprop-like writes.
- No service-manager, HAL, Wi-Fi daemon, NCM, or tcpctl start as part of the transfer primitive.
- V317 live proof remains approval-gated by the existing exact phrase.

## Validation Plan

- Build static ARM64 init and v319 ramdisk/boot image.
- Verify strings markers:
  - `A90 Linux init 0.9.61 (v319)`
  - `A90v319`
  - `0.9.61 v319 SERIAL TRANSFER APPEND`
  - `appendfile <path> <value...>`
- Flash `stage3/boot_linux_v319.img` through TWRP handoff and verify `cmdv1 version/status`.
- Run appendfile transfer smoke:
  - write a small uuencoded payload under `/mnt/sdext/a90/tmp`;
  - decode with `uudecode -o`;
  - verify SHA-256;
  - verify `/tmp` outside allowed workspaces is rejected;
  - verify a 1500-byte `cmdv1x` append succeeds.
- Re-run V317 plan/refusal/audit/selftest without live V317 approval.

## Acceptance

- Device reports `A90 Linux init 0.9.61 (v319)`.
- `appendfile` smoke passes and cleanup removes temporary files.
- V317 plan uses the new transfer estimate: files `5`, bytes `524988`, chunks `471`, estimated commands `505`.
- V317 run/cleanup without exact approval still refuse with no device mutation.
