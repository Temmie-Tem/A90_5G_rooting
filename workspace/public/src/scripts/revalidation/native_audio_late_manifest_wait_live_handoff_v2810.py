#!/usr/bin/env python3
"""V2810 retry wrapper for the late-manifest native audio play handoff.

This reuses the V2808 live runner after the V2809 tcpctl install-target fix,
but records the device iteration under a fresh V2810 run/report identity.
"""

from __future__ import annotations

import native_audio_late_manifest_wait_live_handoff_v2808 as runner

runner.CYCLE = "V2810"
runner.REPORT_PATH = (
    runner.ROOT / "docs/reports/NATIVE_INIT_V2810_AUDIO_LATE_MANIFEST_WAIT_RETRY_LIVE_2026-06-19.md"
)


if __name__ == "__main__":
    raise SystemExit(runner.main())
