# Native Init v414 Static Runtime Target Classifier Plan

## Scope

V414 classifies V413 static VINTF Wi-Fi declarations into ranked runtime target
candidates for later comparison with V411 binderized `lshal` output.

V414 is host-only.  It reads existing V413 evidence and must not execute
bridge/device commands, deploy helpers, start service-manager, start Wi-Fi HALs,
scan/connect/link-up, or perform Wi-Fi bring-up.

## Rationale

V413 proved there are many Wi-Fi-looking declarations, but the list mixes
framework compatibility matrices, device compatibility matrix entries,
framework manifests, and system_ext manifests.  Moving directly from that broad
list to a client proof would be weak.

V414 separates the declarations by source and ranks the candidates.  The target
set can then be compared against V411 runtime registration output after helper
v27 is deployed and the bounded binderized query runs.

## Implementation

Add:

```text
scripts/revalidation/wifi_v414_static_runtime_target_classifier.py
```

Inputs:

- V413 `manifest.json`
- V413 captured VINTF XML files under `native/cat-vintf-*.txt`

Outputs:

- `manifest.json`
- `summary.md`
- ranked `top_records`
- complete `all_records`

## Ranking Rules

Positive signals:

- device compatibility matrix source;
- provider manifest source;
- `vendor.samsung.hardware.wifi`;
- `android.hardware.wifi`;
- primary interfaces `ISehWifi` or `IWifi`;
- `default` instance.

Negative signals:

- `hostapd`;
- `supplicant`;
- `wifidisplay`;
- `keystore`;
- `offload`;
- `wifilearner`;
- `wifimyftm`.

## Success Criteria

- Executes no device command.
- Evidence output remains private.
- Reads V413 evidence successfully.
- Produces a ranked primary Wi-Fi target.
- Keeps current live gate unchanged: exact-approved V411 helper v27 deploy only.

## Next Use

After V411 helper v27 deploy and bounded binderized `lshal` query:

1. compare V411 runtime registrations against V414 top records;
2. if primary target appears registered, plan a no-scan/no-link HIDL client proof;
3. if runtime query still fails, route to a narrower micro `hwservicemanager`
   query using V414 target names.
