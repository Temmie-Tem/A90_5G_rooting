# NATIVE_INIT_V2347_BRIDGE_A90_LNX_SERIAL_AUTODETECT

Date: 2026-06-15
Scope: host-side bridge readiness fix for the current V2321 USB identity
Device mutation: none
Flash: none
Audio/ADSP: not touched

## Reason

The active device is resident on the V2321 rollback checkpoint and exposes the current
USB ACM by-id identity as:

- `/dev/serial/by-id/usb-A90-LNX_A90_Linux_ARM64_A90NATIVE001-if00`

The bridge wrappers still defaulted to the old Samsung-only by-id glob. Manual control
worked when the operator launched the bridge with `/dev/ttyACM0`, but wrapper status and
auto-start could report no serial candidates under the current clean A90-LNX identity.

The operator message in this iteration was not the exact AUD-3 approval phrase. Therefore
no AUD-3 flash, ADSP boot, `/dev/snd` materialization, ALSA open/ioctl, mixer, tinyalsa,
or playback command ran.

Required AUD-3 phrase remains:

```text
AUD-3-preflight go: materialize ALSA /dev/snd nodes only on V2334, no open/ioctl/mixer/playback, rollback to V2321
```

## Change

Updated the host bridge defaults to accept an ordered multi-glob identity list:

1. current clean A90-LNX identity, exact by-id symlink;
2. legacy Samsung Android by-id glob.

Touched surfaces:

- `a90_bridge.py`: ordered multi-glob serial candidate discovery, de-duplication, and updated ambiguity wording.
- `serial_tcp_bridge.py`: same ordered multi-glob resolver for auto device selection.
- `a90_transport.py`: shared default bridge identity list.
- `local_security_rescan.py`: S003 now asserts the current A90-LNX identity and legacy Samsung fallback.
- Regression tests for both wrappers.

## Validation

Host/static:

```bash
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/a90_bridge.py \
  workspace/public/src/scripts/revalidation/serial_tcp_bridge.py \
  workspace/public/src/scripts/revalidation/a90_transport.py \
  workspace/public/src/scripts/revalidation/local_security_rescan.py \
  tests/test_a90_bridge.py \
  tests/test_serial_tcp_bridge.py

python3 -m unittest discover -s tests -p 'test_a90_bridge.py'
python3 -m unittest discover -s tests -p 'test_serial_tcp_bridge.py'
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Result:

- focused bridge tests: 14 passed
- focused serial bridge tests: 12 passed
- full test suite: 1016 passed
- whitespace check: passed

Read-only live checks on the resident V2321 device:

```bash
PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/a90_bridge.py status --json
python3 workspace/public/src/scripts/revalidation/a90ctl.py selftest verbose
PYTHONPATH=workspace/public/src/harness:workspace/public/src/scripts/revalidation \
  python3 workspace/public/src/scripts/revalidation/native_audio_snd_nodes_preflight_handoff_v2335.py --dry-run
```

Result:

- bridge status selected `/dev/serial/by-id/usb-A90-LNX_A90_Linux_ARM64_A90NATIVE001-if00`
- selected realpath was `/dev/ttyACM0`
- ambiguity was false
- bridge probe was connected
- `selftest verbose` returned `fail=0`
- V2335 AUD-3 runner dry-run preflight was OK and confirmed V2334/V2321/V2237/V48 images are present

Private local security rescan:

- S003 now passes for the current A90-LNX plus legacy Samsung serial identity contract.
- The private scan still reports unrelated historical S010 architecture debt; this was not changed in this iteration.

## Outcome

V2347 is a host-side bridge readiness fix. It removes the current A90-LNX USB identity
from the critical path before any future exact-gated AUD-3 retry.

AUD-3 `/dev/snd` materialization remains pending and still requires the exact phrase above.
