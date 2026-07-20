import ast
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_r4w1c_odin_enumeration_diff_observer_binding_packet.py"
)


def load_module():
    script_dir = str(SCRIPT.parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("r4w1c_enum_diff_binding_tested", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class R4W1CEnumerationDiffBindingPacketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def copy_root(self, temporary: str) -> Path:
        module = self.module
        root = Path(temporary)
        for relative in (
            module.OBSERVER_SCRIPT_RELATIVE,
            module.OBSERVER_TEST_RELATIVE,
            module.POLICY_DRAFT,
            module.SCRIPT_RELATIVE,
            module.TEST_RELATIVE,
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path.cwd() / relative).read_bytes())
        (root / "AGENTS.md").write_text("# inert test policy base\n", encoding="utf-8")
        (root / module.OUTPUT_ROOT).mkdir(parents=True)
        (root / module.CONSUMED_STATE.parent).mkdir(parents=True, exist_ok=True)
        return root

    def odin(self):
        module = self.module
        return {
            "path": str(module.DEFAULT_ODIN),
            "size": module.EXPECTED_ODIN_SIZE,
            "sha256": module.EXPECTED_ODIN_SHA256,
        }

    def source_gate(self, root: Path):
        with mock.patch.object(self.module, "verified_odin_identity", return_value=self.odin()):
            return self.module.source_gate(root)

    def emit(self, root: Path, requested: Path | None = None):
        with mock.patch.object(self.module, "verified_odin_identity", return_value=self.odin()):
            return self.module.emit_binding(root, requested)

    def test_parser_exposes_only_host_modes(self):
        parser = self.module.build_parser()
        options = {action.dest for action in parser._actions}
        self.assertIn("offline_check", options)
        self.assertIn("emit_binding", options)
        for forbidden in ("ack", "live", "recovery", "odin", "serial"):
            self.assertNotIn(forbidden, options)

    def test_reviewed_source_pins_match_exact_files(self):
        module = self.module
        for relative, expected in module.EXPECTED_SOURCE_IDENTITIES.items():
            payload = (Path.cwd() / relative).read_bytes()
            self.assertEqual(len(payload), expected["size"])
            self.assertEqual(module.sha256_bytes(payload), expected["sha256"])

    def test_source_gate_binds_generator_policy_base_odin_and_clause(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            gate = self.source_gate(root)
        self.assertEqual(gate["reviewed_source_checkpoint_commit"], module.SOURCE_CHECKPOINT_COMMIT)
        self.assertEqual(gate["odin"], self.odin())
        self.assertEqual(gate["policy_base"]["observer_marker_counts"], {"begin": 0, "end": 0, "active": 0})
        self.assertFalse(gate["observer_consumed"])
        self.assertEqual(gate["rendered_clause"]["active_sentinel_count"], 1)

    def test_source_gate_rejects_any_policy_residue(self):
        module = self.module
        for residue in (
            module.POLICY_BEGIN,
            module.POLICY_END,
            module.ACTIVE_SENTINEL,
        ):
            with self.subTest(residue=residue), tempfile.TemporaryDirectory() as temporary:
                root = self.copy_root(temporary)
                (root / "AGENTS.md").write_text(f"{residue}\n", encoding="utf-8")
                with mock.patch.object(module, "verified_odin_identity", return_value=self.odin()), self.assertRaises(module.BindingError):
                    module.source_gate(root)

    def test_source_gate_rejects_consumed_state_and_source_mutation(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            consumed = root / module.CONSUMED_STATE
            consumed.write_text("{}", encoding="ascii")
            with mock.patch.object(module, "verified_odin_identity", return_value=self.odin()), self.assertRaises(module.BindingError):
                module.source_gate(root)
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            with (root / module.OBSERVER_SCRIPT_RELATIVE).open("ab") as stream:
                stream.write(b"\n")
            with mock.patch.object(module, "verified_odin_identity", return_value=self.odin()), self.assertRaises(module.BindingError):
                module.source_gate(root)

    def test_rendered_clause_has_valid_distinct_digest_preimage(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            gate = self.source_gate(root)
            sources = gate["reviewed_sources"]
            clause = module.rendered_policy_clause(sources)
            identity = module.validate_rendered_clause(clause, sources)
        self.assertEqual(identity["sha256"], module.sha256_bytes(clause.encode("utf-8")))
        self.assertNotEqual(identity["embedded_normalized_template_sha256"], identity["sha256"])
        self.assertNotIn("{{POLICY_CLAUSE_SHA256}}", clause)

    def test_rendered_clause_validation_rejects_mutation_and_placeholder(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            gate = self.source_gate(root)
            sources = gate["reviewed_sources"]
            clause = module.rendered_policy_clause(sources)
            with self.assertRaises(module.BindingError):
                module.validate_rendered_clause(clause.replace("acceptance_decision=false", "acceptance_decision=true"), sources)
            with self.assertRaises(module.BindingError):
                module.validate_rendered_clause(clause.replace(module.ACTIVE_SENTINEL, "{{ACTIVE}}"), sources)

    def test_emit_is_deterministic_and_does_not_edit_agents(self):
        module = self.module
        packets = []
        clauses = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temporary:
                root = self.copy_root(temporary)
                agents_before = (root / "AGENTS.md").read_bytes()
                result = self.emit(root)
                packets.append((root / result["packet"]["path"]).read_bytes())
                clauses.append((root / result["clause"]["path"]).read_bytes())
                self.assertEqual((root / "AGENTS.md").read_bytes(), agents_before)
                self.assertFalse(result["device_contact"])
                self.assertFalse(result["odin_execution"])
                self.assertFalse(result["policy_edited"])
                self.assertFalse(result["acceptance_decision"])
        self.assertEqual(packets[0], packets[1])
        self.assertEqual(clauses[0], clauses[1])

    def test_emit_rejects_noncanonical_local_clause_before_creating_artifacts(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            original = module.rendered_policy_clause

            def altered(sources):
                return original(sources).replace(
                    "acceptance_decision=false", "acceptance_decision=true"
                )

            with mock.patch.object(module, "rendered_policy_clause", side_effect=altered), self.assertRaises(module.BindingError):
                module.emit_binding(root, module.OUTPUT_ROOT / "transient")
            self.assertFalse(
                (root / module.OUTPUT_ROOT / "transient.clause.md").exists()
            )
            self.assertFalse(
                (root / module.OUTPUT_ROOT / "transient.packet.json").exists()
            )

    def test_packet_binds_exact_clause_and_all_actions_false(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            result = self.emit(root, module.OUTPUT_ROOT / "packet-under-test")
            packet = json.loads(
                (root / result["packet"]["path"]).read_text(encoding="utf-8")
            )
            clause = (root / result["clause"]["path"]).read_text(encoding="utf-8")
        self.assertEqual(packet["binding"]["rendered_clause"]["sha256"], module.sha256_bytes(clause.encode("utf-8")))
        self.assertEqual(
            packet["verdict"],
            "PENDING_R4W1C_ENUM_DIFF_OBSERVER_INDEPENDENT_BINDING_REVIEW",
        )
        self.assertEqual(
            result["verdict"],
            "PASS_R4W1C_ENUM_DIFF_OBSERVER_BINDING_PACKET_EMITTED_HOST_ONLY",
        )
        for field in (
            "policy_edited",
            "policy_active",
            "observer_consumed",
            "device_contact",
            "device_writes",
            "reboot",
            "download_transition",
            "odin_execution",
            "odin_enumeration",
            "odin_transfer",
            "flash",
            "partition_writes",
            "acceptance_decision",
        ):
            self.assertFalse(packet[field], field)

    def test_allocate_output_rejects_escape_nested_and_existing_artifact(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            digest = "a" * 64
            for requested in (Path("../escape"), module.OUTPUT_ROOT / "nested" / "path"):
                with self.subTest(requested=requested), self.assertRaises(module.BindingError):
                    module.allocate_output(root, requested, digest)
            output = module.allocate_output(
                root, module.OUTPUT_ROOT / "existing", digest
            )
            try:
                (root / module.OUTPUT_ROOT / output.artifact_name(module.CLAUSE_FILENAME)).write_bytes(
                    b"preexisting\n"
                )
                with self.assertRaises(module.BindingError):
                    module.durable_create_bytes(
                        output, module.CLAUSE_FILENAME, b"pending\n"
                    )
            finally:
                output.close()

    def test_allocate_output_rejects_symlinked_private_root(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            output = root / module.OUTPUT_ROOT
            output.rmdir()
            real = root / "real-output"
            real.mkdir()
            output.symlink_to(real, target_is_directory=True)
            with self.assertRaises(module.BindingError):
                module.allocate_output(root, None, "a" * 64)

    def test_allocate_output_blocks_intermediate_ancestor_replacement_race(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            private = root / "workspace" / "private"
            displaced = root / "workspace" / "private-displaced"
            redirect = root / "redirect-private"
            (redirect / "outputs").mkdir(parents=True)
            real_open = module.os.open
            triggered = False

            def replace_before_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal triggered
                if path == "private" and dir_fd is not None and not triggered:
                    triggered = True
                    private.rename(displaced)
                    private.symlink_to(redirect, target_is_directory=True)
                if dir_fd is None:
                    return real_open(path, flags, mode)
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(module.os, "open", side_effect=replace_before_open), self.assertRaises(module.BindingError):
                module.allocate_output(
                    root, module.OUTPUT_ROOT / "acquisition-race", "a" * 64
                )
            self.assertTrue(triggered)
            self.assertFalse((redirect / "outputs" / "acquisition-race").exists())
            self.assertFalse((displaced / "outputs" / "acquisition-race").exists())

    def test_pinned_output_fd_blocks_parent_symlink_redirection(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            output = module.allocate_output(
                root, module.OUTPUT_ROOT / "race", "a" * 64
            )
            output_root = root / module.OUTPUT_ROOT
            displaced = root / "outputs-displaced"
            redirect = root / "redirect-target"
            redirect.mkdir()
            original_check = module.require_output_pin
            calls = 0

            def replace_after_check(current):
                nonlocal calls
                calls += 1
                if calls == 1:
                    output_root.rename(displaced)
                    output_root.symlink_to(redirect, target_is_directory=True)
                    return
                original_check(current)

            try:
                with mock.patch.object(
                    module, "require_output_pin", side_effect=replace_after_check
                ), self.assertRaises(module.BindingError):
                    module.durable_create_bytes(output, module.CLAUSE_FILENAME, b"pending\n")
                artifact_name = output.artifact_name(module.CLAUSE_FILENAME)
                self.assertFalse((redirect / artifact_name).exists())
                self.assertEqual(
                    (displaced / artifact_name).read_bytes(), b"pending\n"
                )
            finally:
                output.close()

    def test_atomic_artifact_create_rejects_interposed_existing_file(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            output = module.allocate_output(
                root, module.OUTPUT_ROOT / "artifact-race", "a" * 64
            )
            replacement = (
                root
                / module.OUTPUT_ROOT
                / output.artifact_name(module.CLAUSE_FILENAME)
            )
            real_open = module.os.open
            triggered = False

            def create_before_exclusive_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal triggered
                if path == replacement.name and dir_fd is not None and not triggered:
                    triggered = True
                    replacement.write_bytes(b"attacker\n")
                if dir_fd is None:
                    return real_open(path, flags, mode)
                return real_open(path, flags, mode, dir_fd=dir_fd)

            try:
                with mock.patch.object(module.os, "open", side_effect=create_before_exclusive_open), self.assertRaises(module.BindingError):
                    module.durable_create_bytes(
                        output, module.CLAUSE_FILENAME, b"pending\n"
                    )
                self.assertTrue(triggered)
                self.assertEqual(replacement.read_bytes(), b"attacker\n")
            finally:
                output.close()

    def test_emit_rechecks_all_inputs_after_writes(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            original = module.qualify_source_snapshot
            calls = 0

            def changed(current_root, inputs):
                nonlocal calls
                calls += 1
                value = original(current_root, inputs)
                if calls == 2:
                    value = {**value, "observer_consumed": True}
                return value

            with mock.patch.object(module, "verified_odin_identity", return_value=self.odin()), mock.patch.object(module, "qualify_source_snapshot", side_effect=changed), self.assertRaises(module.BindingError):
                module.emit_binding(root, module.OUTPUT_ROOT / "changed")
            packet = json.loads(
                (root / module.OUTPUT_ROOT / "changed.packet.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                packet["verdict"],
                "PENDING_R4W1C_ENUM_DIFF_OBSERVER_INDEPENDENT_BINDING_REVIEW",
            )

    def test_emit_rejects_pinned_source_mutation_during_local_render(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            helper = root / module.OBSERVER_SCRIPT_RELATIVE
            original = module.rendered_policy_clause
            mutated = False

            def mutate_after_render(sources):
                nonlocal mutated
                clause = original(sources)
                if not mutated:
                    with helper.open("ab") as stream:
                        stream.write(b"# concurrent mutation\n")
                    mutated = True
                return clause

            with mock.patch.object(
                module, "rendered_policy_clause", side_effect=mutate_after_render
            ), self.assertRaises(module.BindingError):
                module.emit_binding(root, module.OUTPUT_ROOT / "mutated-source")
            self.assertTrue(mutated)

    def test_emit_rejects_same_length_output_mutation_after_initial_reads(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            original = module.stable_output_file
            mutated = False

            def mutate_after_packet_read(output, name, **kwargs):
                nonlocal mutated
                value = original(output, name, **kwargs)
                if name == module.PACKET_FILENAME and not mutated:
                    pinned = output.files[module.CLAUSE_FILENAME]
                    replacement = bytearray(pinned.payload)
                    replacement[0] ^= 1
                    self.assertEqual(
                        module.os.pwrite(pinned.descriptor, replacement, 0),
                        len(replacement),
                    )
                    module.os.fsync(pinned.descriptor)
                    mutated = True
                return value

            with mock.patch.object(
                module, "stable_output_file", side_effect=mutate_after_packet_read
            ), self.assertRaises(module.BindingError):
                module.emit_binding(root, module.OUTPUT_ROOT / "mutated-output")
            self.assertTrue(mutated)

    def test_offline_check_is_non_authorizing(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            with mock.patch.object(module, "verified_odin_identity", return_value=self.odin()):
                result = module.offline_check(root)
        self.assertEqual(result["verdict"], "PASS_R4W1C_ENUM_DIFF_OBSERVER_BINDING_SOURCE_OFFLINE_CHECK")
        self.assertFalse(result["policy_active"])
        self.assertFalse(result["device_contact"])
        self.assertFalse(result["odin_execution"])

    def test_main_fails_closed_without_creating_output_when_policy_exists(self):
        module = self.module
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy_root(temporary)
            (root / "AGENTS.md").write_text(module.POLICY_BEGIN + "\n", encoding="utf-8")
            with mock.patch.object(module, "repo_root", return_value=root), mock.patch.object(module, "verified_odin_identity", return_value=self.odin()):
                rc = module.main(["--emit-binding", "--out-dir", str(module.OUTPUT_ROOT / "blocked")])
            self.assertEqual(rc, 1)
            self.assertFalse((root / module.OUTPUT_ROOT / "blocked.clause.md").exists())
            self.assertFalse((root / module.OUTPUT_ROOT / "blocked.packet.json").exists())

    def test_generator_source_has_no_process_or_device_execution_surface(self):
        source = SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertNotIn("subprocess", imported)
        self.assertNotIn("usb", imported)
        self.assertFalse(
            any(name.endswith("odin_enumeration_diff_observer") for name in imported)
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr, {"Popen", "run", "call", "system", "execv", "spawnv"})
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"exec", "eval", "compile", "__import__"})
        for forbidden in ("adb devices", "reboot download", "-l\"]", "--AP", "flash_exact"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
