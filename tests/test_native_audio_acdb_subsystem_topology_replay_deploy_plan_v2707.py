import json
import tempfile
import unittest
from pathlib import Path

import native_audio_acdb_subsystem_topology_replay_deploy_plan_v2707 as v2707


class NativeAudioAcdbSubsystemTopologyReplayDeployPlanV2707(unittest.TestCase):
    def make_helper(self, root: Path) -> Path:
        helper = root / "helper.bin"
        helper.write_bytes(("\n".join(v2707.REQUIRED_HELPER_STRINGS.values()) + "\n").encode())
        helper.chmod(0o700)
        return helper

    def make_v2705_manifest(self, root: Path, *, replay_entries: int = 12) -> Path:
        old_dir = "/cache/a90-acdb-setcal-replay-v2705"
        helper = root / "old-helper.bin"
        helper.write_bytes(b"old-helper")
        helper_digest = v2707.sha256_file(helper)
        files = [
            {
                "kind": "helper",
                "local": {
                    "local_path_private": str(helper),
                    "exists": True,
                    "ok": True,
                    "size": helper.stat().st_size,
                    "sha256": helper_digest,
                    "nonzero": True,
                    "size_matches": True,
                    "sha256_matches": True,
                    "private_only": True,
                },
                "remote_path": f"{old_dir}/a90_acdb_setcal_replay_execute_v2635",
                "remote_mode": "0700",
                "remote_sha256_command": f"sha256sum {old_dir}/a90_acdb_setcal_replay_execute_v2635",
                "ok": True,
            },
            {
                "kind": "topology",
                "local": {"ok": True, "sha256": "a", "size": 1, "private_only": True},
                "remote_path": f"{old_dir}/00-core_custom_topologies.bin",
                "remote_sha256_command": f"sha256sum {old_dir}/00-core_custom_topologies.bin",
                "ok": True,
            },
        ]
        argv = [f"{old_dir}/a90_acdb_setcal_replay_execute_v2635", "--execute"]
        entries = []
        for index in range(replay_entries):
            argv.extend(["--exact-set", f"{old_dir}/{index:02d}-set-arg.bin"])
            entries.append({"kind": "exact-set", "cal_type": index})
        manifest = {
            "run_id": "V2705",
            "build_tag": "v2705-audio-acdb-subsystem-topology-replay-deploy-plan",
            "ok": True,
            "all_inputs_ok": True,
            "remote_dir": old_dir,
            "files": files,
            "files_redacted": files,
            "remote_argv": argv,
            "replay_entries": entries,
            "summary": {"replay_entry_count": replay_entries},
        }
        path = root / "v2705.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_rewrites_helper_and_remote_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper = self.make_helper(root)
            digest = v2707.sha256_file(helper)
            manifest = v2707.build_manifest(
                self.make_v2705_manifest(root),
                helper,
                remote_dir="/cache/a90-v2707",
                expected_helper_sha256=digest,
            )
            self.assertTrue(manifest["ok"])
            self.assertEqual(manifest["remote_dir"], "/cache/a90-v2707")
            self.assertEqual(manifest["remote_argv"][0], "/cache/a90-v2707/a90_acdb_setcal_replay_execute_v2635")
            self.assertNotIn("v2705", " ".join(manifest["remote_argv"]))
            helper_files = [entry for entry in manifest["files"] if entry["kind"] == "helper"]
            self.assertEqual(helper_files[0]["local"]["sha256"], digest)
            self.assertEqual(manifest["helper_contract"]["declared_replay_entries"], 12)
            self.assertTrue(manifest["helper_contract"]["entry_count_fits"])

    def test_blocks_when_replay_entry_count_exceeds_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper = self.make_helper(root)
            digest = v2707.sha256_file(helper)
            manifest = v2707.build_manifest(
                self.make_v2705_manifest(root, replay_entries=17),
                helper,
                expected_helper_sha256=digest,
            )
            self.assertFalse(manifest["ok"])
            self.assertIn("declared replay entry count exceeds helper max", manifest["replay_blockers"])

    def test_helper_string_gate_rejects_wrong_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper = root / "bad-helper.bin"
            helper.write_bytes(b"A90_ACDB_SETCAL_REPLAY_START\n")
            helper.chmod(0o700)
            digest = v2707.sha256_file(helper)
            manifest = v2707.build_manifest(
                self.make_v2705_manifest(root),
                helper,
                expected_helper_sha256=digest,
            )
            self.assertFalse(manifest["ok"])
            self.assertIn("entry-cap helper artifact validation failed", manifest["replay_blockers"])


if __name__ == "__main__":
    unittest.main()
