"""Tests for the V2806 deploy-first ADSP publication discriminator."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIVE = REPO / "workspace/public/src/scripts/revalidation/native_audio_deploy_first_adsp_probe_live_handoff_v2806.py"


def load_module():
    sys.path.insert(0, str(LIVE.parent))
    spec = importlib.util.spec_from_file_location("v2806_live", LIVE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class NativeAudioDeployFirstAdspProbeV2806(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.live = load_module()

    def test_preflight_reuses_v2804_candidate_without_playback(self) -> None:
        module = self.live
        args = module.parse_args(["--dry-run"])
        state = module.preflight_state()
        payload = module.dry_run_payload(args, state)

        self.assertEqual(module.CYCLE, "V2806")
        self.assertEqual(module.base.CANDIDATE_VERSION, "0.9.314")
        self.assertEqual(module.base.CANDIDATE_TAG, "v2804-audio-adsp-kick-no-wait")
        self.assertIn("boot_linux_v2804_audio_adsp_kick_no_wait.img", str(module.base.CANDIDATE_IMAGE))
        self.assertIn("boot_linux_v2321_usb_clean_identity_rodata.img", " ".join(payload["commands"]["rollback"]))
        self.assertEqual(payload["commands"]["direct_adsp_boot_after_deploy"], ["audio", "adsp-boot-once", module.ADSP_TOKEN])
        self.assertNotIn("play", payload["commands"])
        self.assertTrue(payload["preflight_ok"], payload)

    def test_runner_orders_deploy_before_direct_adsp(self) -> None:
        text = LIVE.read_text(encoding="utf-8")

        self.assertLess(
            text.index('"runtime_artifacts"] = base.install_runtime_artifacts'),
            text.index('"candidate-audio-direct-adsp-boot-once-after-deploy"'),
        )
        self.assertLess(
            text.index('"candidate-audio-direct-adsp-boot-once-after-deploy"'),
            text.index("card_wait = card_first.wait_for_sound_card"),
        )
        self.assertIn('"stage runtime ACDB artifacts before direct ADSP boot"', text)
        self.assertIn('"no audio play, no route, no SET-cal ioctl, no PCM"', text)

    def test_report_path_and_decision_names_are_v2806_scoped(self) -> None:
        module = self.live
        text = LIVE.read_text(encoding="utf-8")

        self.assertIn("NATIVE_INIT_V2806_AUDIO_DEPLOY_FIRST_ADSP_PROBE_LIVE", str(module.REPORT_PATH))
        self.assertIn("v2806-deploy-first-direct-adsp-card-present-before-rollback", text)
        self.assertIn("v2806-deploy-first-direct-adsp-no-card-before-rollback", text)


if __name__ == "__main__":
    unittest.main()
