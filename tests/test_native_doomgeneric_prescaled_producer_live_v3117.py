from __future__ import annotations

import argparse
import unittest

from _loader import load_script


runner = load_script("workspace/public/src/scripts/revalidation/native_doomgeneric_prescaled_producer_live_validation_v3117.py")


class NativeDoomgenericPrescaledProducerLiveV3117Tests(unittest.TestCase):
    def test_identity_and_candidate_contract(self) -> None:
        self.assertEqual(runner.RUN_ID, "V3117")
        self.assertEqual(runner.CANDIDATE_VERSION, "0.10.113")
        self.assertEqual(runner.CANDIDATE_TAG, "v3116-doomgeneric-prescaled-producer")
        self.assertEqual(
            runner.CANDIDATE_SHA256,
            "4c7ca0757aad988dc8a500d3c06b3fe140dc4005f97e46beaf558591444462d3",
        )
        self.assertIn("boot_linux_v3116_doomgeneric_prescaled_producer.img", str(runner.CANDIDATE_IMAGE))

    def test_parse_loop_output_classifies_clean_prescaled_path(self) -> None:
        parsed = runner.parse_loop_output(
            "\r\n".join([
                "video.demo.doom.loop=doomgeneric-sd-wad-visible-playable-loop",
                "video.demo.doom.loop.verify.ok=1",
                "video.demo.doom.dashboard.pre_scaled_large_frame=1",
                "video.demo.doom.dashboard.frame_mode=minimal-large-pre-scaled-producer",
                "video.demo.doom.dashboard.frame_scale=1:1-pre-scaled",
                "video.demo.doom.dashboard.scale_path=producer-pre-scaled-raw-rowcopy",
                "video.demo.doom.loop.frames_presented=180",
                "video.demo.doom.loop.rc=0",
                "video.demo.doom.loop.timing_probe=1",
                "video.demo.doom.loop.timing.draw.avg_us=4100",
                "video.demo.doom.loop.timing.draw.max_us=7200",
                "video.demo.doom.loop.timing.total.avg_us=16620",
                "video.demo.doom.loop.timing.total.max_us=18100",
                "video.demo.doom.loop.seq_telemetry=1",
                "video.demo.doom.loop.seq.shared_missed_frames=0",
                "video.demo.doom.loop.seq.shared_max_sequence_gap_frames=0",
                "video.demo.doom.loop.flip_telemetry=pageflip-event-delta-us",
                "video.demo.doom.loop.flip_events=180",
                "video.demo.doom.loop.flip_delta_avg_us=16670",
                "video.demo.doom.loop.flip_delta_max_us=21000",
                "A90P1 END seq=7 cmd=video rc=0 errno=0 duration_ms=1 flags=0x1 status=ok",
            ])
        )

        self.assertTrue(parsed["producer_markers_ok"])
        self.assertEqual(parsed["pre_scaled_count"], 1)
        self.assertEqual(parsed["frame_scale"], "1:1-pre-scaled")
        self.assertEqual(parsed["scale_path"], "producer-pre-scaled-raw-rowcopy")
        self.assertTrue(parsed["shared_seq_clean"])
        self.assertTrue(parsed["pageflip_stable"])
        self.assertTrue(parsed["pageflip_60hz_stable"])
        self.assertFalse(parsed["pageflip_30hz_stable"])
        self.assertEqual(runner.loop_classification(parsed, 180), "prescaled-producer-clean")

    def test_parse_loop_output_classifies_stable_two_vblank_path(self) -> None:
        parsed = runner.parse_loop_output(
            "\n".join([
                "video.demo.doom.loop=doomgeneric-sd-wad-visible-playable-loop",
                "video.demo.doom.loop.verify.ok=1",
                "video.demo.doom.dashboard.pre_scaled_large_frame=1",
                "video.demo.doom.dashboard.frame_mode=minimal-large-pre-scaled-producer",
                "video.demo.doom.dashboard.frame_scale=1:1-pre-scaled",
                "video.demo.doom.dashboard.scale_path=producer-pre-scaled-raw-rowcopy",
                "video.demo.doom.loop.frames_presented=180",
                "video.demo.doom.loop.rc=0",
                "video.demo.doom.loop.seq.shared_missed_frames=0",
                "video.demo.doom.loop.flip_delta_avg_us=32802",
                "video.demo.doom.loop.flip_delta_max_us=33342",
                "A90P1 END seq=7 cmd=video rc=0 errno=0 duration_ms=1 flags=0x1 status=ok",
            ])
        )

        self.assertTrue(parsed["producer_markers_ok"])
        self.assertTrue(parsed["shared_seq_clean"])
        self.assertTrue(parsed["pageflip_stable"])
        self.assertFalse(parsed["pageflip_60hz_stable"])
        self.assertTrue(parsed["pageflip_30hz_stable"])
        self.assertEqual(runner.loop_classification(parsed, 180), "prescaled-producer-two-vblank")

    def test_parse_loop_output_keeps_timing_review_as_valid_evidence(self) -> None:
        parsed = runner.parse_loop_output(
            "\n".join([
                "video.demo.doom.loop=doomgeneric-sd-wad-visible-playable-loop",
                "video.demo.doom.loop.verify.ok=1",
                "video.demo.doom.dashboard.pre_scaled_large_frame=1",
                "video.demo.doom.dashboard.frame_mode=minimal-large-pre-scaled-producer",
                "video.demo.doom.dashboard.frame_scale=1:1-pre-scaled",
                "video.demo.doom.dashboard.scale_path=producer-pre-scaled-raw-rowcopy",
                "video.demo.doom.loop.frames_presented=180",
                "video.demo.doom.loop.rc=0",
                "video.demo.doom.loop.seq.shared_missed_frames=1",
                "video.demo.doom.loop.flip_delta_avg_us=16670",
                "video.demo.doom.loop.flip_delta_max_us=50000",
                "A90P1 END seq=7 cmd=video rc=0 errno=0 duration_ms=1 flags=0x1 status=ok",
            ])
        )

        self.assertTrue(parsed["producer_markers_ok"])
        self.assertFalse(parsed["shared_seq_clean"])
        self.assertFalse(parsed["pageflip_stable"])
        self.assertEqual(runner.loop_classification(parsed, 180), "prescaled-producer-timing-review")

    def test_live_pass_accepts_timing_review_after_health_and_rollback_safe_loop(self) -> None:
        result = {
            "preflash_selftest_fail0": True,
            "candidate_version_ok": True,
            "candidate_selftest_fail0": True,
            "candidate_hide_before_loop_ok": True,
            "doom_loop_rc": 0,
            "doom_loop_protocol_end_present": True,
            "loop_classification": "prescaled-producer-two-vblank",
            "candidate_selftest_after_loop_fail0": True,
            "doom_loop": {"producer_markers_ok": True},
        }

        self.assertTrue(runner.live_pass(result))

    def test_preflight_and_report_contract(self) -> None:
        args = argparse.Namespace(live=False, frames=180, flash_timeout=900.0, loop_timeout=180.0)
        state = runner.preflight_state(args)
        self.assertTrue(runner.preflight_ok(state))
        self.assertEqual(state["candidate_version"], runner.CANDIDATE_VERSION)
        self.assertEqual(state["candidate_tag"], runner.CANDIDATE_TAG)
        report = runner.render_report({
            "decision": "dry-run",
            "pass": False,
            "live_executed": False,
            "out_dir": "workspace/private/runs/video/example",
            "preflight": state,
            "preflight_ok": True,
            "rollback_attempted": False,
        })

        self.assertIn("Native Init V3117 DOOMGENERIC Pre-Scaled Producer Live Validation", report)
        self.assertIn("boot_linux_v3116_doomgeneric_prescaled_producer.img", report)
        self.assertIn(runner.CANDIDATE_SHA256, report)
        self.assertIn("pre-scaled producer", report)
        self.assertIn("producer-pre-scaled-raw-rowcopy", report)
        self.assertIn("native_doomgeneric_prescaled_producer_live_validation_v3117.py", report)
        payload = runner.dry_run_payload(args, state)
        commands = " ".join(payload["commands"])
        self.assertIn("flash exact V3116 image", commands)
        self.assertIn("parse pre-scaled producer markers", commands)
        self.assertIn("rollback v2321", commands)


if __name__ == "__main__":
    unittest.main()
