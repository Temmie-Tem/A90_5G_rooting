#!/usr/bin/env python3
"""V2428 exact-gated rerun of the fixed thread-set ACDB capture.

This is a thin identity wrapper around the shared V2424 live runner after V2427
fixed clone-child resume handling in the V2423 Android-side observer. It keeps
M0 transient Android/Magisk-root delivery and records the next live attempt under
a new V-iteration identity.
"""

from __future__ import annotations

from contextlib import contextmanager
import json

import native_audio_acdb_threadset_clone_follow_live_handoff_v2424 as base


RUN_ID = "V2428"
BUILD_TAG = "v2428-audio-acdb-threadset-clone-child-resume-live-rerun"


@contextmanager
def base_identity():
    previous_run_id = base.RUN_ID
    previous_build_tag = base.BUILD_TAG
    base.RUN_ID = RUN_ID
    base.BUILD_TAG = BUILD_TAG
    try:
        yield
    finally:
        base.RUN_ID = previous_run_id
        base.BUILD_TAG = previous_build_tag


def default_live_out_dir():
    with base_identity():
        return base.default_live_out_dir()


def dry_run(args):
    with base_identity():
        payload = base.dry_run(args)
    payload.update({
        "run_id": RUN_ID,
        "build_tag": BUILD_TAG,
        "decision": "v2428-acdb-threadset-clone-follow-capture-live-dry-run",
        "live_runner": base.rel(base.ROOT / "workspace/public/src/scripts/revalidation/native_audio_acdb_threadset_clone_follow_live_handoff_v2428.py"),
        "base_runner": base.rel(base.ROOT / "workspace/public/src/scripts/revalidation/native_audio_acdb_threadset_clone_follow_live_handoff_v2424.py"),
        "inherits_v2425_stage_adb_waits": True,
        "inherits_v2427_clone_child_resume": True,
    })
    return payload


def main() -> int:
    args = base.parse_args()
    if args.run_live:
        try:
            with base_identity():
                payload = base.run_live(args)
        except RuntimeError as error:
            payload = {
                "run_id": RUN_ID,
                "build_tag": BUILD_TAG,
                "decision": "v2428-acdb-threadset-clone-follow-capture-live-refused",
                "ok": False,
                "rolled_back": False,
                "reason": str(error),
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 1
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload.get("ok") and payload.get("rolled_back") else 1

    payload = dry_run(args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
