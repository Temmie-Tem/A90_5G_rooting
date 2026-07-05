from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _loader import load_script


runner = load_script("workspace/public/src/scripts/server-distro/run_wsta139_dpublic_hud_presenter_service_model.py")
SOURCE = Path("workspace/public/src/scripts/server-distro/run_wsta139_dpublic_hud_presenter_service_model.py")


class ServerDistroWsta139DpublicHudPresenterServiceModelTests(unittest.TestCase):
    def private_tmp(self):
        return tempfile.TemporaryDirectory(dir=runner.PRIVATE_ROOT)

    def args(self, root: Path, *extra: str):
        return runner.build_arg_parser().parse_args([
            "--run-dir",
            str(root / "wsta139"),
            *extra,
        ])

    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(runner.json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def wsta130_model_result(self) -> dict:
        model = runner.wsta130.presenter_architecture_model()
        checks = runner.wsta130.validate_model(model)
        return {
            "decision": runner.wsta130.PASS_DECISION,
            "run_dir": "workspace/private/runs/server-distro/wsta130-test",
            "presenter_architecture_model": model,
            "checks": checks,
        }

    def wsta137_live_result(self) -> dict:
        proof = {
            "decision": runner.wsta137.PASS_DECISION,
            "run_dir": "workspace/private/runs/server-distro/wsta137-test",
            "source_run_dir": "workspace/private/runs/server-distro/wsta137-source-test",
            "candidate": {
                "init_version": runner.wsta137.INIT_VERSION,
                "init_build": runner.wsta137.INIT_BUILD,
                "boot_image": runner.wsta137.HELPER_BOOT_IMAGE,
                "boot_sha256": runner.wsta137.BOOT_SHA256,
            },
            "checked_flash": {
                "used_checked_helper": True,
                "local_sha_match": True,
                "remote_sha_match": True,
                "boot_readback_sha_match": True,
                "booted_v3398": True,
                "boot_ok": True,
                "selftest_fail_zero": True,
                "transport_serial_ready": True,
                "transport_tcpctl_ready": True,
            },
            "validate_proof": {
                "intent_schema": runner.wsta137.INTENT_SCHEMA,
                "sequence": 13701,
                "age_ms": 653,
                "intent_valid": True,
                "forbidden_fields_reject": True,
                "unknown_fields_reject": True,
                "stale_after_ms": runner.wsta137.STALE_AFTER_MS,
                "stale_after_marker": True,
                "presenter_owner_native_root": True,
                "debian_direct_kms_zero": True,
                "validate_only": True,
            },
            "present_proof": {
                "sequence": 13702,
                "age_ms": 556,
                "intent_valid": True,
                "present_begin_frame_rc_zero": True,
                "present_rc_zero": True,
                "present_done": True,
                "framebuffer": "1080x2400",
                "crtc": 133,
            },
            "reject_proof": {
                "forbidden_command_rejected": True,
                "forbidden_rc": -1,
                "stale_rejected": True,
                "stale_rc": -110,
                "stale_age_ms": 102866,
                "stale_after_ms": runner.wsta137.STALE_AFTER_MS,
            },
            "final_health": {
                "v3398_resident": True,
                "selftest_fail_zero": True,
                "transport_serial_ready": True,
                "transport_tcpctl_ready": True,
            },
            "public_url_value_logged": False,
            "secret_values_logged": 0,
        }
        proof["checks"] = runner.wsta137.validate_proof(proof)
        return proof

    def test_default_invocation_is_inert(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            result = runner.run(self.args(root))

        self.assertEqual(result["decision"], "wsta139-blocked-emit-service-model-required")
        self.assertFalse(result["safety"]["device_action"])
        self.assertFalse(result["safety"]["boot_flash"])
        self.assertFalse(result["safety"]["switch_root"])
        self.assertFalse(result["safety"]["drm_open"])
        self.assertFalse(result["safety"]["kms_setcrtc"])

    def test_model_defines_durable_native_presenter_service(self) -> None:
        model = runner.service_model(self.wsta130_model_result(), self.wsta137_live_result())
        checks = runner.validate_model(model)

        self.assertTrue(runner.model_passes(checks))
        self.assertEqual(model["state"], runner.MODEL_STATE)
        service = model["native_presenter_service"]
        self.assertEqual(service["owner"], "native-init")
        self.assertEqual(service["process_model"], "forked-native-child-survives-switch-root")
        self.assertEqual(service["start_phase"], "native-pre-switch-root")
        self.assertTrue(service["survives_debian_handoff"])
        self.assertEqual(service["start_command"], runner.start_command())
        self.assertEqual(service["stop_command"], runner.stop_command())
        self.assertTrue(service["bounded_shutdown"]["release_drm_on_stop"])

    def test_handoff_contract_keeps_debian_as_intent_writer_only(self) -> None:
        model = runner.service_model(self.wsta130_model_result(), self.wsta137_live_result())

        handoff = model["handoff_contract"]
        self.assertEqual(handoff["runtime_dir"], "/run/a90-dpublic")
        self.assertEqual(handoff["runtime_dir_mode"], "1770")
        self.assertEqual(handoff["intent_file"], "/run/a90-dpublic/hud-intent.json")
        self.assertEqual(handoff["producer_user"], "a90hud")
        self.assertTrue(handoff["producer_no_drm"])
        self.assertTrue(handoff["producer_no_network"])
        self.assertTrue(handoff["native_reads_intent_after_handoff"])

        drm = model["drm_ownership"]
        self.assertEqual(drm["sole_owner"], "native-dpublic-hud-presenter")
        self.assertFalse(drm["debian_opens_drm"])
        self.assertFalse(drm["debian_direct_kms"])
        self.assertTrue(drm["handoff_cleanup_policy"]["preserve_durable_presenter_when_armed"])
        self.assertTrue(drm["handoff_cleanup_policy"]["fail_if_unexpected_drm_holder"])

    def test_intent_watch_and_proof_plan_are_fail_closed(self) -> None:
        model = runner.service_model(self.wsta130_model_result(), self.wsta137_live_result())

        watch = model["intent_watch"]
        self.assertEqual(watch["transport"], "bounded-atomic-json-intent-file")
        self.assertEqual(watch["intent_schema"], "a90-dpublic-hud-intent-v1")
        self.assertLessEqual(watch["max_bytes"], 4096)
        self.assertLessEqual(watch["stale_after_ms"], 2000)
        self.assertTrue(watch["latest_sequence_wins"])
        self.assertTrue(watch["reject_unknown_fields"])
        self.assertTrue(watch["no_shell_expansion"])
        self.assertTrue(watch["no_path_open_from_intent"])
        self.assertTrue(watch["no_public_url_rendering"])
        for field in ("command", "path", "url", "ssid", "psk", "token", "secret"):
            self.assertIn(field, watch["forbidden_fields"])

        proof_ids = {entry["id"] for entry in model["proof_plan"]}
        self.assertIn("post_handoff_same_presenter_alive", proof_ids)
        self.assertIn("debian_has_no_drm_fd", proof_ids)
        self.assertIn("fresh_intent_consumed_after_handoff", proof_ids)
        self.assertIn("cleanup_releases_drm", proof_ids)

    def test_emit_service_model_writes_private_source_pass(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            wsta130_path = root / "inputs" / "wsta130.json"
            wsta137_path = root / "inputs" / "wsta137.json"
            self.write_json(wsta130_path, self.wsta130_model_result())
            self.write_json(wsta137_path, self.wsta137_live_result())
            result = runner.run(self.args(
                root,
                "--emit-service-model",
                "--wsta130-hud-presenter-model-json",
                str(wsta130_path),
                "--wsta137-hud-presenter-live-proof-json",
                str(wsta137_path),
            ))
            saved = root / "wsta139" / runner.RESULT_NAME
            saved_exists = saved.is_file()

        self.assertEqual(result["decision"], runner.PASS_DECISION)
        self.assertTrue(saved_exists)
        self.assertTrue(result["checks"]["native_root_service_survives_handoff"])
        self.assertTrue(result["checks"]["sole_drm_owner_policy"])
        self.assertTrue(result["checks"]["handoff_cleanup_preserves_presenter"])
        self.assertTrue(result["checks"]["intent_watch_fail_closed"])
        self.assertFalse(result["safety"]["device_action"])
        self.assertFalse(result["safety"]["switch_root"])
        self.assertEqual(result["safety"]["secret_values_logged"], 0)

    def test_missing_or_nonpass_preconditions_block(self) -> None:
        with self.private_tmp() as tmp:
            root = Path(tmp)
            result = runner.run(self.args(root, "--emit-service-model"))
        self.assertEqual(result["decision"], "wsta139-blocked-wsta130-hud-presenter-model-required")

        with self.private_tmp() as tmp:
            root = Path(tmp)
            wsta130_path = root / "inputs" / "wsta130.json"
            wsta137_path = root / "inputs" / "wsta137.json"
            wsta130_result = self.wsta130_model_result()
            wsta130_result["decision"] = "wsta130-blocked"
            self.write_json(wsta130_path, wsta130_result)
            self.write_json(wsta137_path, self.wsta137_live_result())
            result = runner.run(self.args(
                root,
                "--emit-service-model",
                "--wsta130-hud-presenter-model-json",
                str(wsta130_path),
                "--wsta137-hud-presenter-live-proof-json",
                str(wsta137_path),
            ))
        self.assertEqual(result["decision"], "wsta139-blocked-wsta130-model-not-pass")

        with self.private_tmp() as tmp:
            root = Path(tmp)
            wsta130_path = root / "inputs" / "wsta130.json"
            wsta137_path = root / "inputs" / "wsta137.json"
            wsta137_result = self.wsta137_live_result()
            wsta137_result["decision"] = "wsta137-blocked"
            self.write_json(wsta130_path, self.wsta130_model_result())
            self.write_json(wsta137_path, wsta137_result)
            result = runner.run(self.args(
                root,
                "--emit-service-model",
                "--wsta130-hud-presenter-model-json",
                str(wsta130_path),
                "--wsta137-hud-presenter-live-proof-json",
                str(wsta137_path),
            ))
        self.assertEqual(result["decision"], "wsta139-blocked-wsta137-live-proof-not-pass")

    def test_nonprivate_run_dir_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = runner.run(self.args(Path(tmp), "--emit-service-model"))

        self.assertEqual(result["decision"], "wsta139-blocked-nonprivate-run-dir")

    def test_template_contract_plan_and_source_are_host_only(self) -> None:
        template = runner.template()
        script = runner.contract_plan_shell()
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("--emit-service-model", template["command"])
        self.assertIn("--wsta130-hud-presenter-model-json", template["command"])
        self.assertIn("--wsta137-hud-presenter-live-proof-json", template["command"])
        self.assertFalse(template["device_action"])
        self.assertFalse(template["public_tunnel"])
        self.assertFalse(template["drm_open"])
        self.assertFalse(template["kms_setcrtc"])
        self.assertIn("A90WSTA139_DURABLE_PRESENTER_MODEL_BEGIN", script)
        self.assertIn("A90WSTA139_SURVIVES_HANDOFF=1", script)
        self.assertIn("A90WSTA139_DEBIAN_DRM_OPEN=0", script)
        self.assertIn(runner.MODEL_STATE, source)
        self.assertIn("forked-native-child-survives-switch-root", source)
        self.assertIn("preserve_durable_presenter_when_armed", source)
        self.assertIn("public_url_value_logged", source)
        self.assertNotIn("native_init_flash.py", source)
        self.assertNotIn("trycloudflare.com", source.lower())
        self.assertNotIn("ssid=", source.lower())
        self.assertNotIn("psk=", source.lower())


if __name__ == "__main__":
    unittest.main()
