# F007. Unsafe archive extraction enables host file overwrite

## Metadata

| field | value |
|---|---|
| finding_id | `c8457f7684208191bd5de8b6dc45e470` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/c8457f7684208191bd5de8b6dc45e470 |
| severity | `high` |
| status | `new` |
| detected_at | `2026-04-28T11:11:23.623133Z` |
| committed_at | `2025-11-13 20:56:18 +0900` |
| commit_hash | `54cf98250b310814cf09e2e1486e821d7deaf9a2` |
| relevant_paths | `mkbootimg/gki/certify_bootimg.py` |
| has_patch | `false` |

## CSV Description

In `certify_bootimg_archive()`, untrusted `--boot_img_archive` input is extracted with `shutil.unpack_archive()` without a safety filter or path validation. A crafted tar can contain `../` entries (Zip Slip style) and write outside `unpack_dir`. After extraction, the script processes `boot*.img` entries and passes each path to `certify_bootimg()`, which uses `shutil.copy2()` for read/write. If a malicious archive provides symlinked `boot*.img` entries, `copy2()` can follow symlinks and overwrite files outside the temp extraction directory. This creates an arbitrary file write primitive on the host running the tool.

## Codex Cloud Detail

Unsafe archive extraction enables host file overwrite
Link: https://chatgpt.com/codex/cloud/security/findings/c8457f7684208191bd5de8b6dc45e470
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 54cf982
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 8:11:23
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
Introduced vulnerability: untrusted archive extraction and symlink-following file operations in mkbootimg GKI certification tooling can be abused for host filesystem overwrite.
In `certify_bootimg_archive()`, untrusted `--boot_img_archive` input is extracted with `shutil.unpack_archive()` without a safety filter or path validation. A crafted tar can contain `../` entries (Zip Slip style) and write outside `unpack_dir`. After extraction, the script processes `boot*.img` entries and passes each path to `certify_bootimg()`, which uses `shutil.copy2()` for read/write. If a malicious archive provides symlinked `boot*.img` entries, `copy2()` can follow symlinks and overwrite files outside the temp extraction directory. This creates an arbitrary file write primitive on the host running the tool.

# Validation
## Rubric
- [x] Confirm untrusted archive extraction occurs without sanitization in `certify_bootimg_archive()` (line 270).
- [x] Prove path traversal (`../`) can escape `unpack_dir` during archive processing with unmodified CLI.
- [x] Confirm extracted `boot*.img` entries are blindly processed and passed as output paths (lines 276-280).
- [x] Demonstrate symlink-following write behavior in `certify_bootimg()` copy flow (lines 254, 263) can modify external file.
- [x] Attempt crash/valgrind/debugger-based validation paths before finalizing (crash + LLDB attempted; valgrind unavailable).
## Report
I validated the finding with targeted dynamic PoCs against `mkbootimg/gki/certify_bootimg.py`.

Code points:
- `certify_bootimg_archive()` extracts untrusted archives with no path checks: `shutil.unpack_archive(boot_img_archive, unpack_dir)` (line 270).
- It then trusts extracted `boot*.img` entries and passes each as both input and output to `certify_bootimg()` (lines 276-280).
- `certify_bootimg()` performs `shutil.copy2(boot_img, boot_tmp)` and later `shutil.copy2(boot_tmp, output_img)` (lines 254 and 263), which follow symlinks by default.

Reproduction evidence:
1) Untrusted archive path traversal with unmodified CLI:
- Command used (with crafted tar containing `../cli2_hit.txt`): `PYTHONPATH=/workspace/A90_5G_rooting/mkbootimg python3 .../certify_bootimg.py --boot_img_archive /tmp/certify_cli2/evil.tar --algorithm SHA256_RSA2048 --key /etc/hosts -o /tmp/certify_cli2/out.tar`
- Output: `Making certified archive: /tmp/certify_cli2/out.tar`
- Evidence: `/tmp/cli2_hit.txt` was created outside extraction dir; content `CLI_TRAVERSAL_2` (`cli_traversal_evidence.txt`).

2) Symlink-following overwrite primitive through archive flow:
- PoC archive included:
  - `../poc_traversal_hit.txt` (path traversal)
  - `boot-owned.img` symlink -> `/tmp/certify_bootimg_archive_poc/victim.txt`
- Ran PoC script (`poc_certify_bootimg_archive.py`) that invokes `certify_bootimg_archive()` and monkeypatches only external AVB operations; vulnerable `copy2` flow remains intact.
- Output (`poc_run.log`):
  - `TRAVERSAL_CREATED= True`
  - `VICTIM_CONTENT= b'ORIGINAL::MODIFIED::'`
- This confirms write-through to a file outside unpack dir via symlinked `boot*.img` entry.

Required method attempts:
- Crash attempt (unmodified script + symlinked boot image): got traceback ending in `FileNotFoundError: avbtool` after entering `certify_bootimg_archive -> certify_bootimg` (`crash_attempt.log`).
- Valgrind attempt: unavailable (`bash: command not found: valgrind`) (`valgrind_attempt.log`).
- Debugger attempt: non-interactive LLDB run captured same call chain and failure point (`debugger_attempt.log`).

Conclusion: the suspected vulnerability is valid. The commit contains exploitable archive extraction path traversal and symlink-following file operations enabling host file overwrite when processing attacker-controlled archives.

# Evidence
mkbootimg/gki/certify_bootimg.py (L253 to 255)
  Note: copy2() reads from attacker-controlled path, following symlinks.
```
        boot_tmp = os.path.join(temp_dir, 'boot.tmp')
        shutil.copy2(boot_img, boot_tmp)
```

mkbootimg/gki/certify_bootimg.py (L262 to 263)
  Note: copy2() writes back to attacker-controlled output path; if symlinked, this can overwrite external host files.
```
        # We're done, copy the temp image to the final output.
        shutil.copy2(boot_tmp, output_img)
```

mkbootimg/gki/certify_bootimg.py (L269 to 270)
  Note: Untrusted archive is extracted directly with shutil.unpack_archive() and no safe extraction filter/path sanitization.
```
    with tempfile.TemporaryDirectory() as unpack_dir:
        shutil.unpack_archive(boot_img_archive, unpack_dir)
```

mkbootimg/gki/certify_bootimg.py (L276 to 280)
  Note: All extracted boot*.img paths are trusted and processed; symlink entries can be included here.
```
        for boot_img in glob.glob(os.path.join(unpack_dir, 'boot*.img')):
            print(f'Certifying {os.path.basename(boot_img)} ...')
            certify_bootimg(boot_img=boot_img, output_img=boot_img,
                            algorithm=algorithm, key=key, extra_args=extra_args,
                            extra_footer_args=extra_footer_args)
```

Proposed patch:
diff --git a/mkbootimg/gki/certify_bootimg.py b/mkbootimg/gki/certify_bootimg.py
index 68a042e7f25564684478e390c172a1f2af87892e..62974ac151158cbb228107c9f25f6f493151f7ed 100755
--- a/mkbootimg/gki/certify_bootimg.py
+++ b/mkbootimg/gki/certify_bootimg.py
@@ -1,58 +1,94 @@
 #!/usr/bin/env python3
 #
 # Copyright 2022, The Android Open Source Project
 #
 # Licensed under the Apache License, Version 2.0 (the "License");
 # you may not use this file except in compliance with the License.
 # You may obtain a copy of the License at
 #
 #     http://www.apache.org/licenses/LICENSE-2.0
 #
 # Unless required by applicable law or agreed to in writing, software
 # distributed under the License is distributed on an "AS IS" BASIS,
 # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 # See the License for the specific language governing permissions and
 # limitations under the License.
 #

 """Certify a GKI boot image by generating and appending its boot_signature."""

 from argparse import ArgumentParser
 import glob
 import os
 import shlex
 import shutil
 import subprocess
+import tarfile
 import tempfile
+import zipfile

 from gki.generate_gki_certificate import generate_gki_certificate
 from unpack_bootimg import unpack_bootimg

 BOOT_SIGNATURE_SIZE = 16 * 1024


+def _ensure_within_directory(path, directory):
+    """Checks whether |path| is within |directory|."""
+    normalized_directory = os.path.realpath(directory)
+    normalized_path = os.path.realpath(path)
+    common_path = os.path.commonpath([normalized_directory, normalized_path])
+    if common_path != normalized_directory:
+        raise ValueError(f'Archive entry escapes extraction dir: {path}')
+
+
+def safe_unpack_archive(archive_path, unpack_dir):
+    """Safely unpacks supported archive formats."""
+    archive_format = get_archive_name_and_format_for_shutil(archive_path)[1]
+    if archive_format in ('tar', 'gztar', 'bztar', 'xztar'):
+        with tarfile.open(archive_path) as archive:
+            for entry in archive.getmembers():
+                if entry.issym() or entry.islnk():
+                    raise ValueError(
+                        f'Archive contains link entry: {entry.name}')
+                _ensure_within_directory(
+                    os.path.join(unpack_dir, entry.name), unpack_dir)
+            archive.extractall(unpack_dir)
+        return
+
+    if archive_format == 'zip':
+        with zipfile.ZipFile(archive_path) as archive:
+            for entry in archive.infolist():
+                _ensure_within_directory(
+                    os.path.join(unpack_dir, entry.filename), unpack_dir)
+            archive.extractall(unpack_dir)
+        return
+
+    raise ValueError(f'Unsupported archive format: {archive_format}')
+
+
 def get_kernel(boot_img):
     """Extracts the kernel from |boot_img| and returns it."""
     with tempfile.TemporaryDirectory() as unpack_dir:
         unpack_bootimg(boot_img, unpack_dir)
         with open(os.path.join(unpack_dir, 'kernel'), 'rb') as kernel:
             kernel_bytes = kernel.read()
             assert len(kernel_bytes) > 0
             return kernel_bytes


 def add_certificate(boot_img, algorithm, key, extra_args):
     """Appends certificates to the end of the boot image.

     This functions appends two certificates to the end of the |boot_img|:
     the 'boot' certificate and the 'generic_kernel' certificate. The former
     is to certify the entire |boot_img|, while the latter is to certify
     the kernel inside the |boot_img|.
     """

     def generate_certificate(image, certificate_name):
         """Generates the certificate and returns the certificate content."""
         with tempfile.NamedTemporaryFile() as output_certificate:
             generate_gki_certificate(
                 image=image, avbtool='avbtool', name=certificate_name,
                 algorithm=algorithm, key=key, salt='d00df00d',
@@ -227,69 +263,75 @@ def parse_cmdline():
     if args.gki_info and args.boot_img_archive:
         parser.error('--gki_info cannot be used with --boot_image_archive. '
                      'The gki_info file should be included in the archive.')

     extra_args = []
     for a in args.extra_args:
         extra_args.extend(shlex.split(a))
     args.extra_args = extra_args

     extra_footer_args = []
     for a in args.extra_footer_args:
         extra_footer_args.extend(shlex.split(a))
     args.extra_footer_args = extra_footer_args

     if args.gki_info:
         load_gki_info_file(args.gki_info,
                            args.extra_args,
                            args.extra_footer_args)

     return args


 def certify_bootimg(boot_img, output_img, algorithm, key, extra_args,
                     extra_footer_args):
     """Certify a GKI boot image by generating and appending a boot_signature."""
+    if os.path.islink(boot_img):
+        raise ValueError(f'Input boot image must not be a symlink: {boot_img}')
+    if os.path.exists(output_img) and os.path.islink(output_img):
+        raise ValueError(
+            f'Output boot image must not be a symlink: {output_img}')
+
     with tempfile.TemporaryDirectory() as temp_dir:
         boot_tmp = os.path.join(temp_dir, 'boot.tmp')
         shutil.copy2(boot_img, boot_tmp)

         erase_certificate_and_avb_footer(boot_tmp)
         add_certificate(boot_tmp, algorithm, key, extra_args)

         avb_partition_size = get_avb_image_size(boot_img)
         add_avb_footer(boot_tmp, avb_partition_size, extra_footer_args)

         # We're done, copy the temp image to the final output.
         shutil.copy2(boot_tmp, output_img)


 def certify_bootimg_archive(boot_img_archive, output_archive,
                             algorithm, key, extra_args, extra_footer_args):
     """Similar to certify_bootimg(), but for an archive of boot images."""
     with tempfile.TemporaryDirectory() as unpack_dir:
-        shutil.unpack_archive(boot_img_archive, unpack_dir)
+        safe_unpack_archive(boot_img_archive, unpack_dir)

         gki_info_file = os.path.join(unpack_dir, 'gki-info.txt')
         if os.path.exists(gki_info_file):
             load_gki_info_file(gki_info_file, extra_args, extra_footer_args)

         for boot_img in glob.glob(os.path.join(unpack_dir, 'boot*.img')):
             print(f'Certifying {os.path.basename(boot_img)} ...')
             certify_bootimg(boot_img=boot_img, output_img=boot_img,
                             algorithm=algorithm, key=key, extra_args=extra_args,
                             extra_footer_args=extra_footer_args)

         print(f'Making certified archive: {output_archive}')
         archive_file_name, archive_format = (
             get_archive_name_and_format_for_shutil(output_archive))
         built_archive = shutil.make_archive(archive_file_name,
                                             archive_format,
                                             unpack_dir)
         # shutil.make_archive() builds *.tar.gz when then |archive_format| is
         # 'gztar'. However, the end user might specify |output_archive| with
         # *.tgz. Renaming *.tar.gz to *.tgz for this case.
         if built_archive != os.path.realpath(output_archive):
             print(f'Renaming {built_archive} -> {output_archive} ...')
             os.rename(built_archive, output_archive)

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Kept at High: exploitation path is concrete and validated (including executable PoC), impact is major integrity compromise on host filesystem, and affected component is in-scope host tooling. Not raised to Critical because it is not unauthenticated remote/network-triggered; exploitation needs user/CI execution of malicious archive and is bounded by local process privileges.
## Likelihood
medium - Requires attacker-controlled archive and operator execution, but that is plausible in firmware/tooling supply workflows and explicitly within threat model assumptions.
## Impact
high - Arbitrary file overwrite on host running the tool, within account permissions; can corrupt configs/startup files and potentially lead to persistence or code execution.
## Assumptions
- Attack scenario is supply-chain style: attacker can provide a crafted boot image archive to an operator/CI that runs certify_bootimg.
- Tool is executed on a trusted host with filesystem access of the invoking user (sometimes elevated in lab workflows).
- No external cloud APIs are in scope; analysis is repository-static plus provided validation evidence.
- Victim runs certify_bootimg with --boot_img_archive on attacker-controlled archive
- Archive contains traversal and/or symlinked boot*.img entries
- Process has write permission to attacker-chosen target path
## Path
Attacker archive -> --boot_img_archive -> unpack_archive(no safety)
        -> boot*.img selection -> copy2(..., output_img=boot_img)
        -> symlink/traversal resolves outside temp -> host overwrite
## Path evidence
- `mkbootimg/gki/certify_bootimg.py:204-207` - CLI exposes archive input (`--boot_img_archive`) as user-controlled entry point.
- `mkbootimg/gki/certify_bootimg.py:269-270` - Untrusted archive extracted via `shutil.unpack_archive` without path/link safety checks.
- `mkbootimg/gki/certify_bootimg.py:276-280` - All extracted `boot*.img` entries are trusted and re-used as output targets.
- `mkbootimg/gki/certify_bootimg.py:254` - Reads from attacker-controlled path via `copy2` (follows symlinks by default).
- `mkbootimg/gki/certify_bootimg.py:263` - Writes back via `copy2` to attacker-influenced output path; enables overwrite primitive.
- `mkbootimg/Android.bp:64-76` - Defines `certify_bootimg` as a host binary, confirming operational scope.
## Narrative
The finding is valid and reachable in normal tool usage. The CLI accepts attacker-controlled archives (`--boot_img_archive`), extracts them without safety filtering, and then processes extracted `boot*.img` entries as both input and output. Because `copy2()` follows symlinks, a crafted archive can force writes outside the temp extraction directory. This was also dynamically validated with PoCs showing traversal file creation and external file modification. Given threat-model inclusion of untrusted boot image artifacts in host workflows, this is a real host-compromise primitive, not a false positive.
## Controls
- Local CLI invocation required (user interaction)
- TemporaryDirectory used but ineffective against traversal/symlink escapes
- No archive member sanitization or symlink rejection in vulnerable path
## Blindspots
- Static review cannot determine how often this tool is run with root/sudo in real deployments.
- No runtime telemetry to measure prevalence of untrusted archive ingestion in production workflows.
- Could not assess downstream environment hardening (e.g., sandboxing, read-only workdirs, MAC policies).
