"""Regression tests for a90harness.path_safety (safety-critical host-side checks).

Characterizes CURRENT behavior of the path / raw-arg validators that gate every
device-side path and bridge command. Both accepted inputs and the reject cases
(traversal, absolute/relative, shell metacharacters, control chars) are pinned.

Pure host-side. No device interaction.
"""

import unittest

from _loader import load_harness

ps = load_harness("path_safety")


class RequireSafeComponent(unittest.TestCase):
    def test_accepts_plain_and_safe_punctuation(self):
        for value in ("run01", "v2199", "a.b", "a-b", "a_b", "a:b", "a@b",
                      "a%b", "a+b", "a=b", "a,b", "boot.img"):
            self.assertEqual(ps.require_safe_component(value, "x"), value)

    def test_rejects_empty_and_dot_components(self):
        for bad in ("", ".", ".."):
            with self.assertRaises(RuntimeError):
                ps.require_safe_component(bad, "x")

    def test_rejects_path_separators(self):
        for bad in ("a/b", "a\\b", "/abs"):
            with self.assertRaises(RuntimeError):
                ps.require_safe_component(bad, "x")

    def test_rejects_whitespace(self):
        for bad in ("a b", "a\tb"):
            with self.assertRaises(RuntimeError):
                ps.require_safe_component(bad, "x")

    def test_rejects_shell_metacharacters(self):
        for bad in ("a;b", "a|b", "a&b", "a$b", "a`b", "a*b", "a?b", "a(b)", "a!b"):
            with self.assertRaises(RuntimeError):
                ps.require_safe_component(bad, "x")

    def test_rejects_unsupported_and_control_chars(self):
        for bad in ("héllo", "a\x01b", "a\x00b"):
            with self.assertRaises(RuntimeError):
                ps.require_safe_component(bad, "x")


class NormalizeDevicePath(unittest.TestCase):
    def test_accepts_absolute_normalized_paths(self):
        for value in ("/a", "/data/local/tmp", "/data/local/tmp/runs/v1"):
            self.assertEqual(ps.normalize_device_path(value, "x"), value)

    def test_rejects_relative(self):
        with self.assertRaises(RuntimeError):
            ps.normalize_device_path("data/local", "x")

    def test_rejects_empty_segments_and_trailing_slash(self):
        for bad in ("/a//b", "/a/", "/data/local/tmp/"):
            with self.assertRaises(RuntimeError):
                ps.normalize_device_path(bad, "x")

    def test_rejects_dot_and_dotdot_segments(self):
        for bad in ("/a/./b", "/a/../b", "/../etc"):
            with self.assertRaises(RuntimeError):
                ps.normalize_device_path(bad, "x")

    def test_rejects_whitespace_and_backslash(self):
        for bad in ("/a b", "/a\\b"):
            with self.assertRaises(RuntimeError):
                ps.normalize_device_path(bad, "x")

    def test_bare_root_is_rejected(self):
        # "/" splits to an empty segment and is rejected by the segment check.
        with self.assertRaises(RuntimeError):
            ps.normalize_device_path("/", "x")


class RequirePathUnder(unittest.TestCase):
    def test_accepts_equal_root_and_descendant(self):
        self.assertEqual(ps.require_path_under("/root", "/root", "x"), "/root")
        self.assertEqual(ps.require_path_under("/root/sub", "/root", "x"), "/root/sub")

    def test_rejects_sibling_with_shared_prefix(self):
        # boundary: "/rootother" must NOT count as under "/root".
        with self.assertRaises(RuntimeError):
            ps.require_path_under("/rootother", "/root", "x")

    def test_rejects_outside_root(self):
        with self.assertRaises(RuntimeError):
            ps.require_path_under("/other/x", "/root", "x")


class RequireRunChild(unittest.TestCase):
    def test_builds_child_under_root(self):
        self.assertEqual(
            ps.require_run_child("/data/local/tmp/runs", "v1"),
            "/data/local/tmp/runs/v1",
        )

    def test_rejects_unsafe_run_id(self):
        for bad in ("..", "../escape", "a b", "a/b"):
            with self.assertRaises(RuntimeError):
                ps.require_run_child("/data/local/tmp/runs", bad)


class RequireSafeRawArg(unittest.TestCase):
    def test_accepts_paths_and_safe_punctuation(self):
        # unlike a path component, raw args may contain '/'.
        for value in ("DRIVER", "a=b,c", "192.168.1.1", "/data/local/tmp/x", "COUNTRY"):
            self.assertEqual(ps.require_safe_raw_arg(value, "x"), value)

    def test_rejects_whitespace_and_metacharacters(self):
        for bad in ("a b", "a;b", "$(x)", "a|b", "a`b", "a&b"):
            with self.assertRaises(RuntimeError):
                ps.require_safe_raw_arg(bad, "x")


if __name__ == "__main__":
    unittest.main()
