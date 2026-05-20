# Native Init V451 Wi-Fi Operator Script Validation Plan

Date: 2026-05-20

## Goal

V451 validates the generated V448 operator scripts themselves before the
operator enters Wi-Fi values.  V450 verifies structure and mode; V451 adds shell
syntax checks and bounded fail-closed prompt probes.

## Scope

Allowed:

- read latest V448 packet evidence;
- run `bash -n` against generated host preflight and live scripts;
- run generated scripts only with empty or cancellation input;
- clear `A90_WIFI_SSID` and `A90_WIFI_PSK` from child process env;
- verify prompt guards exit before V447/V445 success paths.

Not allowed:

- provide real Wi-Fi values;
- run successful V447 host preflight or live paths;
- boot/flash Android, enable Wi-Fi, scan, connect, or mutate the device;
- expose any server listener.

## Implementation

- Validator: `scripts/revalidation/wifi_operator_script_validation_v451.py`
  - `plan`: records validation plan;
  - `run`: validates latest V448 scripts with:
    - host preflight `bash -n`;
    - live `bash -n`;
    - host preflight empty-input fail-closed probe;
    - live cancellation fail-closed probe.

## Validation Plan

```text
python3 -m py_compile scripts/revalidation/wifi_operator_script_validation_v451.py

python3 scripts/revalidation/wifi_operator_script_validation_v451.py \
  --out-dir tmp/wifi/v451-operator-script-validation-plan-<ts> \
  plan

python3 scripts/revalidation/wifi_operator_script_validation_v451.py \
  --out-dir tmp/wifi/v451-operator-script-validation-run-<ts> \
  run

git diff --check
```

## Expected Decisions

- `v451-operator-script-validation-plan-ready`
- `v451-operator-script-validation-needs-v448-packet`
- `v451-operator-script-validation-v448-not-ready`
- `v451-operator-script-validation-missing-scripts`
- `v451-operator-script-validation-failed`
- `v451-operator-script-validation-pass`

## Pass Criteria

V451 passes only when:

- latest V448 packet exists and passed;
- both generated scripts pass `bash -n`;
- host preflight exits fail-closed with empty input;
- live script exits fail-closed with cancellation input;
- no successful preflight/live path, device command, or Wi-Fi bring-up occurs.

## Next Gate

Run the generated host preflight script and enter Wi-Fi values locally.  After
completion, rerun V449/V450 to route the live step.

Server exposure remains blocked.
