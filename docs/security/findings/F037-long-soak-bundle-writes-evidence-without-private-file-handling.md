# F037. Long-soak bundle writes evidence without private file handling

## Metadata

| field | value |
|---|---|
| finding_id | `b8266569c9ac8191ba0a8cfb28a78416` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/b8266569c9ac8191ba0a8cfb28a78416 |
| severity | `medium` |
| status | `mitigated-v153` |
| detected_at | `2026-05-08 05:03:54 +0900` |
| committed_at | `2026-05-08 05:03:54 +0900` |
| commit_hash | `eba5e45` |
| relevant_paths | `scripts/revalidation/native_long_soak_bundle.py` |
| source | Codex Cloud fresh scan, pasted by operator |

## Summary

`scripts/revalidation/native_long_soak_bundle.py` creates long-soak evidence bundles with ordinary `mkdir`, `shutil.copy2`, and `Path.write_text`. Unlike `diag_collect.py`, it does not force private output directories/files and does not prevent destination symlink following. In a shared lab host or group-writable checkout, another local user can read status/timeline/selftest/netservice evidence or pre-create symlinks in the predictable bundle directory to redirect operator-writable outputs.

## Local Initial Assessment

- Valid class: host-side evidence bundle lacks the private-output pattern already used by diagnostics.
- This is related to F034 because both are longsoak host evidence export/trust-boundary failures.
- It should be fixed in v153 together with F034-F036 before more kernel/network feature work.

## Local Remediation

- Mitigated in v153 Longsoak Security Hardening.
- Add private host output helpers to `native_long_soak_bundle.py`.
- Force bundle directory to `0700`.
- Write command captures, `manifest.json`, and `README.md` with `os.open(..., 0600)` and no-follow semantics where available.
- Replace `shutil.copy2()` with explicit regular-file read and private destination write; do not follow destination symlinks.

## Codex Cloud Detail

Long-soak bundle writes evidence without private file handling
Link: https://chatgpt.com/codex/cloud/security/findings/b8266569c9ac8191ba0a8cfb28a78416?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium
Status: new

### Summary

Introduced: the new long-soak evidence bundle script lacks the private-output and symlink-safe write patterns used elsewhere for diagnostic artifacts.

The v151 commit adds `scripts/revalidation/native_long_soak_bundle.py`. The script creates the bundle directory with the process default umask, then copies evidence files with `shutil.copy2` and writes command transcripts, `manifest.json`, and `README.md` with `Path.write_text`. Unlike the existing diagnostic collector, it does not force `0700` directories/`0600` files and does not use no-follow or exclusive file creation. On a shared lab host or group-writable checkout, another local user can read the generated status/timeline/selftest/netservice evidence bundle, and if they can pre-create files or symlinks in the predictable bundle directory they may cause the operator to overwrite files writable by that operator. The captured data is not full root tokens, but it can expose device/runtime paths, service state, log locations, host evidence metadata, and operational transcripts from a root-control workflow.

### Validation

- Confirmed the added script uses ordinary `mkdir`/`write_text`/`copy2` rather than private/no-follow output helpers.
- A normal execution under permissive umask leaves bundle directory/files group/other readable.
- Pre-created destination symlinks for command/manifest/readme outputs are followed and overwrite target files.
- `copy_if_exists()`/`shutil.copy2()` follows a pre-created destination symlink for a copied evidence filename.
- Outputs contain operational evidence/transcripts/metadata, making disclosure meaningful.

### Evidence

- `scripts/revalidation/native_long_soak_bundle.py`: `copy_if_exists()` copies evidence with `shutil.copy2(source, dest)`.
- `scripts/revalidation/native_long_soak_bundle.py`: `run_capture()` writes command transcripts with `Path.write_text()`.
- `scripts/revalidation/native_long_soak_bundle.py`: `bundle_dir.mkdir(parents=True, exist_ok=True)` does not force private mode.
- `scripts/revalidation/native_long_soak_bundle.py`: `manifest.json` and `README.md` are written with `Path.write_text()`.
- Captured commands include `status`, `timeline`, `logpath`, `longsoak status verbose`, `netservice status`, and `selftest verbose`.

