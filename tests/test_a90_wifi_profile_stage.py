from __future__ import annotations

import argparse
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from _loader import load_script


stage_mod = load_script("workspace/public/src/scripts/revalidation/a90_wifi_profile_stage.py")


def args(**overrides):
    defaults = {
        "profile": "lab",
        "root": "persistent",
        "band": "any",
        "priority": 100,
        "connect_timeout_sec": 35,
        "retry_count": 1,
        "dhcp": True,
        "scan_before_connect": True,
        "autoconnect": False,
        "out_dir": "",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class FakeStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.writes: dict[str, object] = {}

    def mkdir(self, name: str) -> Path:
        path = self.root / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_json(self, name: str, value: object) -> Path:
        self.writes[name] = value
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        return path


class PathAndFileHelpers(unittest.TestCase):
    def test_root_paths_selects_persistent_or_cache_and_rejects_unknown(self) -> None:
        self.assertEqual(
            stage_mod.root_paths("persistent"),
            {
                "config": "/mnt/sdext/a90/config/wifi",
                "profiles": "/mnt/sdext/a90/config/wifi/profiles",
                "secrets": "/mnt/sdext/a90/secrets/wifi",
            },
        )
        self.assertEqual(
            stage_mod.root_paths("cache"),
            {
                "config": "/cache/a90-wifi/config",
                "profiles": "/cache/a90-wifi/config/profiles",
                "secrets": "/cache/a90-wifi/config/secrets",
            },
        )
        with self.assertRaises(ValueError):
            stage_mod.root_paths("tmpfs")

    def test_write_private_file_creates_0600_secret_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "secret.txt"
            stage_mod.write_private_file(path, "value\n")

            self.assertEqual(path.read_text(encoding="utf-8"), "value\n")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


class StageFileBuilder(unittest.TestCase):
    def test_build_stage_files_invalid_wifi_env_is_fail_closed_and_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(stage_mod.v2174, "selected_profile_name", return_value="lab"), \
                mock.patch.object(stage_mod.v2174, "wifi_secret_status", return_value={"valid": False, "reason": "missing"}):
            result = stage_mod.build_stage_files(FakeStore(Path(tmp)), args(profile="lab"))

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "wifi-env-invalid")
        self.assertEqual(result["profile"], "lab")
        self.assertEqual(result["secret_values_logged"], 0)
        self.assertNotIn("files", result)

    def test_build_stage_files_writes_profile_and_secret_files_without_manifest_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"A90_WIFI_SSID": "TestSSID", "A90_WIFI_PSK": "TestPassword"}, clear=False), \
                mock.patch.object(stage_mod.v2174, "selected_profile_name", return_value="lab"), \
                mock.patch.object(
                    stage_mod.v2174,
                    "wifi_secret_status",
                    return_value={"valid": True, "ssid_len": 8, "psk_len": 12},
                ):
            result = stage_mod.build_stage_files(
                FakeStore(Path(tmp)),
                args(root="cache", profile="lab", autoconnect=True, band="5g", priority=77, retry_count=3),
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["root"], "cache")
            self.assertEqual(result["autoconnect"], 1)
            self.assertEqual(result["band"], "5g")
            self.assertEqual(result["priority"], 77)
            self.assertEqual(result["ssid_len"], 8)
            self.assertEqual(result["psk_len"], 12)
            self.assertEqual(result["secret_values_logged"], 0)
            self.assertEqual(result["remote"]["ssid"], "/cache/a90-wifi/config/secrets/lab.ssid")
            self.assertEqual(result["remote"]["psk"], "/cache/a90-wifi/config/secrets/lab.psk")
            self.assertNotIn("TestSSID", repr(stage_mod.compact_stage(result)))
            self.assertNotIn("TestPassword", repr(stage_mod.compact_stage(result)))

            autoconnect = result["files"]["autoconnect"].read_text(encoding="utf-8")
            profile = result["files"]["profile"].read_text(encoding="utf-8")
            ssid = result["files"]["ssid"].read_text(encoding="utf-8")
            psk = result["files"]["psk"].read_text(encoding="utf-8")
            self.assertIn("autoconnect=1", autoconnect)
            self.assertIn("retry_count=3", autoconnect)
            self.assertIn("ssid_file=/cache/a90-wifi/config/secrets/lab.ssid", profile)
            self.assertIn("band=5g", profile)
            self.assertEqual(ssid, "TestSSID\n")
            self.assertEqual(psk, "TestPassword\n")
            self.assertEqual(result["files"]["ssid"].stat().st_mode & 0o777, 0o600)
            self.assertEqual(result["files"]["psk"].stat().st_mode & 0o777, 0o600)

    def test_compact_stage_removes_local_paths_but_keeps_remote_metadata(self) -> None:
        compact = stage_mod.compact_stage({
            "ok": True,
            "files": {"psk": Path("/private/psk")},
            "remote": {"psk": "/cache/psk"},
            "secret_values_logged": 0,
        })
        self.assertEqual(compact, {"ok": True, "remote": {"psk": "/cache/psk"}, "secret_values_logged": 0})


class ManifestAndRunFlow(unittest.TestCase):
    def test_finalize_manifest_adds_total_phase_residual_state_and_writes_manifest(self) -> None:
        store = FakeStore(Path(tempfile.mkdtemp()))
        manifest = {
            "pass": False,
            "stage": {"profile": "lab", "root": "cache", "remote_roots": {"config": "/cache"}},
            "transfer_results": {"ssid": {"ok": True}},
        }
        with mock.patch.object(stage_mod.transport, "add_total_phase") as add_phase, \
                mock.patch.object(stage_mod.transport, "set_residual_state") as set_residual:
            result = stage_mod.finalize_manifest(store, manifest, started_monotonic=1.0)

        self.assertIs(result, manifest)
        add_phase.assert_called_once_with(manifest, "wifi_profile_stage_total", 1.0, ok=False)
        residual = set_residual.call_args.args[1]
        self.assertEqual(residual["profile"], "lab")
        self.assertEqual(residual["root"], "cache")
        self.assertEqual(residual["partial_transfer_count"], 1)
        self.assertTrue(residual["cleanup_required"])
        self.assertIn("manifest.json", store.writes)

    def test_run_stops_at_preflight_failure_and_writes_secret_free_manifest(self) -> None:
        tmp_parent = stage_mod.WORKSPACE_PRIVATE_ROOT / "runs" / "tests"
        tmp_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_parent) as tmp, \
                mock.patch.object(stage_mod.v2174, "load_wifi_env", return_value={"loaded": False}), \
                mock.patch.object(stage_mod.v2174, "selected_profile_name", return_value="lab"), \
                mock.patch.object(stage_mod.v2174, "wifi_secret_status", return_value={"valid": False, "reason": "missing"}), \
                mock.patch.object(stage_mod.transport, "add_total_phase"), \
                mock.patch.object(stage_mod.transport, "set_residual_state"), \
                mock.patch.object(stage_mod.time, "monotonic", return_value=10.0):
            manifest = stage_mod.run(args(out_dir=tmp))

        self.assertEqual(manifest["decision"], "wifi-profile-stage-preflight-failed")
        self.assertFalse(manifest["pass"])
        self.assertEqual(manifest["stage"]["secret_values_logged"], 0)
        self.assertNotIn("A90_WIFI_PSK", repr(manifest))

    def test_run_success_uses_tcpctl_secret_transfers_and_verifies_profile_prepare(self) -> None:
        tmp_parent = stage_mod.WORKSPACE_PRIVATE_ROOT / "runs" / "tests"
        tmp_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_parent) as tmp, \
                mock.patch.dict(os.environ, {"A90_WIFI_SSID": "TestSSID", "A90_WIFI_PSK": "TestPassword"}, clear=False), \
                mock.patch.object(stage_mod.v2174, "load_wifi_env", return_value={"loaded": True}), \
                mock.patch.object(stage_mod.v2174, "selected_profile_name", return_value="lab"), \
                mock.patch.object(stage_mod.v2174, "wifi_secret_status", return_value={"valid": True, "ssid_len": 8, "psk_len": 12}), \
                mock.patch.object(stage_mod.v2174, "ensure_netservice_tcpctl", return_value={"ok": True}), \
                mock.patch.object(stage_mod.v2174, "ensure_host_ncm_ipv4", return_value={"ok": True}), \
                mock.patch.object(stage_mod.v2174, "ping_device_over_ncm", return_value=True), \
                mock.patch.object(stage_mod.v2174, "fetch_tcpctl_token_redacted", return_value="TOKEN"), \
                mock.patch.object(stage_mod.v2174, "tcpctl_args", return_value=["tcpctl", "--token", "TOKEN"]), \
                mock.patch.object(stage_mod.v2174, "wait_for_tcpctl_ready", return_value=True), \
                mock.patch.object(stage_mod.v2174, "tcpctl_run_line", side_effect=lambda argv: " ".join(argv)), \
                mock.patch.object(stage_mod.v2174, "tcpctl_step", return_value={"ok": True}) as tcpctl_step, \
                mock.patch.object(stage_mod.v2174, "tcpctl_transfer_file", return_value={"ok": True, "reason": "ok", "method": "tcpctl", "remote_size": "8"}) as transfer, \
                mock.patch.object(
                    stage_mod.v2174,
                    "a90ctl_step",
                    side_effect=[
                        {"ok": True, "stdout": "decision=wifi-profile-ready\n"},
                        {"ok": True, "stdout": "decision=wifi-config-supplicant-prepared\n"},
                    ],
                ) as a90ctl_step, \
                mock.patch.object(stage_mod.transport, "add_total_phase"), \
                mock.patch.object(stage_mod.transport, "set_residual_state"), \
                mock.patch.object(stage_mod.time, "monotonic", return_value=10.0):
            manifest = stage_mod.run(args(out_dir=tmp, root="cache", autoconnect=True))

        self.assertEqual(manifest["decision"], "wifi-profile-stage-pass")
        self.assertTrue(manifest["pass"])
        self.assertEqual(manifest["secret_values_logged"], 0)
        self.assertEqual(set(manifest["transfer_results"]), {"autoconnect", "profile", "ssid", "psk"})
        self.assertEqual(tcpctl_step.call_count, 8)
        self.assertEqual([call.kwargs["label"] for call in transfer.call_args_list], [
            "profile-stage-autoconnect",
            "profile-stage-profile",
            "profile-stage-ssid",
            "profile-stage-psk",
        ])
        self.assertEqual([call.kwargs["secret_file"] for call in transfer.call_args_list], [False, False, True, True])
        self.assertEqual([call.kwargs["mode"] for call in transfer.call_args_list], ["600", "600", "600", "600"])
        self.assertEqual(
            [call.kwargs["transfer_port"] for call in transfer.call_args_list],
            [stage_mod.v2174.TCPCTL_TRANSFER_BASE_PORT + offset for offset in (40, 41, 42, 43)],
        )
        self.assertEqual(
            [call.args[2] for call in a90ctl_step.call_args_list],
            ["wifi-profile-stage-profile-status", "wifi-profile-stage-config-prepare"],
        )
        self.assertNotIn("TestPassword", repr(manifest))


if __name__ == "__main__":
    unittest.main()
