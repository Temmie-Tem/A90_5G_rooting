"""Regression tests for V1393 native-init fast build selection."""

from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path

from _loader import load_script


builder = load_script("workspace/public/archive/scripts/revalidation/build_native_init_wifi_test_boot_v1393.py")


class BuildNativeInitWifiTestBootV1393FastBuild(unittest.TestCase):
    def test_run_init_build_defaults_to_fast_and_preserves_one_shot_override(self) -> None:
        old_fast = builder._run_fast_init_build
        old_one_shot = builder._run_one_shot_init_build
        calls: list[tuple[str, list[object]]] = []
        command = ["gcc", "-o", Path("init"), Path("init.c")]
        try:
            builder._run_fast_init_build = lambda args, cmd: calls.append(("fast", cmd))
            builder._run_one_shot_init_build = lambda args, cmd: calls.append(("one-shot", cmd))

            builder._run_init_build(types.SimpleNamespace(), command)
            builder._run_init_build(types.SimpleNamespace(init_build_mode="one-shot"), command)
        finally:
            builder._run_fast_init_build = old_fast
            builder._run_one_shot_init_build = old_one_shot

        self.assertEqual(calls, [("fast", command), ("one-shot", command)])

    def test_fast_build_compiles_sources_to_objects_then_links_strips_and_files(self) -> None:
        old_run = builder.run
        old_subprocess_run = builder.subprocess.run
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                source_one = root / "init_v724.c"
                source_two = root / "a90_qrtr.c"
                source_one.write_text("void init_entry(void) {}\n", encoding="utf-8")
                source_two.write_text("void helper(void) {}\n", encoding="utf-8")
                output = root / "out" / "init"
                run_commands: list[list[object]] = []
                compile_commands: list[list[str]] = []

                def fake_subprocess_run(command, **_kwargs):
                    if command == ["gcc", "--version"]:
                        return types.SimpleNamespace(stdout="gcc fake 1.0\n")
                    compile_commands.append(command)
                    object_path = Path(command[command.index("-o") + 1])
                    depfile = Path(command[command.index("-MF") + 1])
                    source_path = Path(command[command.index("-c") + 1])
                    object_path.write_bytes(b"object")
                    depfile.write_text(f"{object_path}: {source_path}\n", encoding="utf-8")
                    return types.SimpleNamespace(stdout="")

                def fake_run(command, **_kwargs):
                    run_commands.append(command)
                    if command and command[0] == "gcc":
                        output_path = Path(command[command.index("-o") + 1])
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_bytes(b"linked")
                    return types.SimpleNamespace()

                builder.subprocess.run = fake_subprocess_run
                builder.run = fake_run

                builder._run_init_build(
                    types.SimpleNamespace(
                        strip="strip",
                        init_binary=output,
                        init_fast_jobs=1,
                        init_fast_cache_dir=root / "cache",
                        init_fast_verify_one_shot=False,
                    ),
                    ["gcc", "-static", "-DTEST=1", "-o", output, source_one, source_two],
                )
        finally:
            builder.run = old_run
            builder.subprocess.run = old_subprocess_run

        self.assertEqual(len(compile_commands), 2)
        self.assertEqual([Path(cmd[cmd.index("-c") + 1]) for cmd in compile_commands], [source_one, source_two])
        self.assertIn("-MMD", compile_commands[0])
        self.assertIn("-MF", compile_commands[0])
        self.assertEqual(run_commands[0][0:4], ["gcc", "-static", "-DTEST=1", "-o"])
        self.assertEqual(run_commands[0][4], output)
        self.assertEqual(len(run_commands[0][5:]), 2)
        self.assertTrue(all(Path(item).suffix == ".o" for item in run_commands[0][5:]))
        self.assertEqual(run_commands[1], ["strip", output])
        self.assertEqual(run_commands[2], ["file", output])


if __name__ == "__main__":
    unittest.main()
