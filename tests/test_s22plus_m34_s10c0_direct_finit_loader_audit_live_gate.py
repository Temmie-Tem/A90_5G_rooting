import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path("workspace/public/src/scripts/revalidation/s22plus_m34_s10c0_direct_finit_loader_audit_live_gate.py")
MANIFEST = Path("workspace/private/outputs/s22plus_native_init/m34_runtime_gadget_split_v0_13/manifest.json")


def load_module():
    script_dir = str(SCRIPT.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("s22plus_m34_s10c0_direct_finit_loader_audit_live_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class S22PlusM34S10C0DirectFinitLoaderAuditLiveGateTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_policy_markers_include_hashes_tokens_and_s10c0_semantics(self):
        markers = self.module.policy_required_markers()
        self.assertIn(self.module.LIVE_ACK_TOKEN, markers)
        self.assertIn(self.module.ROLLBACK_ACK_TOKEN, markers)
        self.assertIn(self.module.EXPECTED_M34_AP_SHA256, markers)
        self.assertIn(self.module.EXPECTED_M34_BOOT_SHA256, markers)
        self.assertIn(self.module.EXPECTED_M34_INIT_SHA256, markers)
        self.assertIn(self.module.EXPECTED_M34_TEMPLATE_SOURCE_SHA256, markers)
        self.assertIn(self.module.EXPECTED_MAGISK_AP_SHA256, markers)
        self.assertIn(self.module.EXPECTED_STOCK_BOOT_AP_SHA256, markers)
        self.assertIn(self.module.EXPECTED_STOCK_BOOT_RAW_SHA256, markers)
        self.assertIn("S10C0 starts from the S9/S10A/S10B 89-module recipe", markers)
        self.assertIn("S10C0 separates direct cmd-db.ko finit_module rc from /proc/modules observation failure", markers)
        self.assertIn("s10c_loader_audit=1", markers)
        self.assertIn("module_load_probe=finit_cmd_db_accepted", markers)
        self.assertIn("predicate=cmd_db_finit_accepted", markers)
        self.assertIn("phase=s10c_module_loader_audit_probe", markers)
        self.assertIn("proc_modules=0", markers)
        self.assertIn("direct_finit_rc=1", markers)
        self.assertIn("probe_module=cmd-db.ko", markers)
        self.assertIn("probe_proc_name=cmd_db", markers)
        self.assertIn("cmd_db_file=cmd-db.ko", markers)
        self.assertIn("cmd_db=1", markers)
        self.assertIn("cmd_db_seen=", markers)
        self.assertIn("cmd_db_rc=", markers)
        self.assertIn("modules_open_rc=", markers)
        self.assertIn("modules_read_rc=", markers)
        self.assertIn("attempted=", markers)
        self.assertIn("ok=", markers)
        self.assertIn("eexist=", markers)
        self.assertIn("fail=", markers)
        self.assertIn("first_fail_index=", markers)
        self.assertIn("first_fail_rc=", markers)
        self.assertIn("first_fail_name=", markers)
        self.assertIn("driver_load_only=1", markers)
        self.assertIn("manual_power_write=0", markers)
        self.assertIn("configfs_gadget=0", markers)
        self.assertIn("udc_bind=0", markers)
        self.assertIn("typec_readback=0", markers)
        self.assertIn("role_write_discriminator=0", markers)
        self.assertIn("true_action=reboot_download", markers)
        self.assertIn("false_action=park", markers)
        self.assertIn("S10C0 HIT means cmd-db.ko finit_module returned 0 or -EEXIST under native-init", markers)
        self.assertIn("S10C0 MISS means cmd-db.ko was not attempted or direct finit_module failed", markers)

    def test_missing_policy_markers_fail_closed_for_empty_text(self):
        missing = self.module.missing_policy_markers("")
        self.assertIn(self.module.LIVE_ACK_TOKEN, missing)
        self.assertIn(self.module.ROLLBACK_ACK_TOKEN, missing)
        self.assertIn(self.module.EXPECTED_M34_AP_SHA256, missing)
        self.assertIn(self.module.EXPECTED_M34_MARKER, missing)
        self.assertIn("module_load_probe=finit_cmd_db_accepted", missing)
        self.assertIn("probe_module=cmd-db.ko", missing)
        self.assertIn("cmd_db_rc=", missing)
        self.assertIn("true_action=reboot_download", missing)
        self.assertIn("false_action=park", missing)

    def test_agents_exception_draft_and_active_template_policy(self):
        draft = self.module.agents_exception_draft()
        self.assertEqual(self.module.missing_policy_markers(draft), [])
        self.assertTrue(self.module.has_draft_only_m34_exception(draft))
        self.assertIn("DRAFT ONLY", draft)
        self.assertIn("This draft is not active authorization", draft)
        self.assertIn("does not authorize S10B1/S10B2/S10B3/S10B4/S10B5/", draft)

        active = self.module.agents_exception_active_template()
        self.assertEqual(self.module.missing_policy_markers(active), [])
        self.assertFalse(self.module.has_draft_only_m34_exception(active))
        self.assertNotIn("DRAFT ONLY", active)
        self.assertNotIn("This draft is not active authorization", active)
        self.assertIn("Narrow operator-authorized exception", active)

    def test_verify_agents_exception_requires_exact_active_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "agents.log"
            (root / "AGENTS.md").write_text(self.module.agents_exception_draft(), encoding="utf-8")
            with self.assertRaises(SystemExit) as caught:
                self.module.verify_agents_exception(root, log_path)
            self.assertIn("draft-only M34 S10C0", str(caught.exception))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "agents.log"
            (root / "AGENTS.md").write_text(self.module.agents_exception_active_template(), encoding="utf-8")
            self.module.verify_agents_exception(root, log_path)
            text = log_path.read_text(encoding="utf-8")
            self.assertIn("agents_exception_draft_only_present=0", text)
            self.assertIn("agents_exception_missing=[]", text)
            self.assertIn("agents_exception_exact_active_template_present=1", text)

    @unittest.skipUnless(MANIFEST.exists(), "private M34 v0.13 manifest missing")
    def test_current_manifest_contract_matches_s10c0_live_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.module.verify_m34_manifest(MANIFEST, Path(tmp) / "manifest.log")

        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        by_label = {stage["label"]: stage for stage in data["stages"]}
        self.assertEqual(
            by_label["S10C0"]["hashes"]["ap_tar_md5"],
            self.module.EXPECTED_M34_AP_SHA256,
        )
        self.assertEqual(
            by_label["S10C0"]["runtime_steps"]["module_load_probe"],
            self.module.EXPECTED_PROBE,
        )
        self.assertEqual(
            by_label["S10C0"]["ramdisk"]["added_subset_entry"],
            self.module.EXPECTED_MODULE_ENTRY,
        )

    @unittest.skipUnless(MANIFEST.exists(), "private M34 v0.13 manifest missing")
    def test_offline_check_verifies_artifacts_without_agents_or_device(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "offline"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = self.module.main(["--offline-check", "--run-dir", str(run_dir)])
            self.assertEqual(rc, 0)
            self.assertIn("offline-check ok", stdout.getvalue())
            log_text = (run_dir / "s22plus_m34_s10c0_direct_finit_loader_audit_live_gate.txt").read_text(
                encoding="utf-8"
            )
            self.assertIn("offline_check=ok device_action=0 agents_exception_checked=0 android_checked=0", log_text)
            self.assertFalse((run_dir / "result.json").exists())
            self.assertFalse((run_dir / "timeline.json").exists())


if __name__ == "__main__":
    unittest.main()
