# Native Init V443 Wi-Fi Private Policy Materialize Plan

Date: 2026-05-20

## Goal

V443 prepares the private untracked target policy required by V442 before any
explicit scan/connect test.

V442 intentionally does not accept raw SSID/BSSID/PSK values in tracked files or
evidence.  V443 therefore reads `A90_WIFI_SSID` and, for `wpa2`/`wpa3`,
`A90_WIFI_PSK` only from the process environment after explicit approval, then
writes a private policy containing only hashes and env references.

## Scope

Allowed:

- inspect whether required Wi-Fi env variables are present;
- with explicit approval, read env values in-process;
- write private evidence `wifi-target-policy.private.json`;
- validate the materialized policy through the V442 validator.

Not allowed:

- device commands or device mutations;
- writing raw SSID/BSSID/password/passphrase/PSK values;
- scan/connect;
- server exposure or external probes.

## Implementation

- Materializer: `scripts/revalidation/wifi_android_private_policy_materialize_v443.py`
  - requires `--allow-read-wifi-env` and
    `--i-understand-wifi-secret-env` before reading env values;
  - supports `open`, `owe`, `wpa2`, and `wpa3`;
  - hashes `A90_WIFI_SSID` with SHA-256;
  - stores only `ssid_sha256`, `ssid_source`, `credential_source`, and policy
    flags;
  - validates the generated policy through V442's `validate_policy()`.

## Validation Plan

```text
python3 -m py_compile scripts/revalidation/wifi_android_private_policy_materialize_v443.py

python3 scripts/revalidation/wifi_android_private_policy_materialize_v443.py \
  --out-dir tmp/wifi/v443-private-policy-materialize-plan-<ts> \
  plan

python3 scripts/revalidation/wifi_android_private_policy_materialize_v443.py \
  --out-dir tmp/wifi/v443-private-policy-materialize-env-missing-<ts> \
  --allow-read-wifi-env --i-understand-wifi-secret-env \
  run

git diff --check
```

Without env values, the run is expected to fail with
`v443-wifi-private-policy-env-missing`.

## Expected Decisions

- `v443-wifi-private-policy-materialize-plan-ready`
- `v443-wifi-private-policy-materialized-pass`
- `v443-wifi-private-policy-env-missing`
- `v443-wifi-private-policy-approval-required`
- `v443-wifi-private-policy-validation-failed`

## Operator Input Needed

For a `wpa2`/`wpa3` target:

```text
export A90_WIFI_SSID='<private lab ssid>'
export A90_WIFI_PSK='<private lab passphrase>'
```

Then run V443 with:

```text
python3 scripts/revalidation/wifi_android_private_policy_materialize_v443.py \
  --out-dir tmp/wifi/v443-private-policy-materialize-live-<ts> \
  --allow-read-wifi-env --i-understand-wifi-secret-env \
  run
```

The env values must not be pasted into chat, committed, or written into tracked
files.

## Next Gate Rule

V444 explicit scan/connect preflight may consume the private
`wifi-target-policy.private.json` only after V443 returns
`v443-wifi-private-policy-materialized-pass`.
