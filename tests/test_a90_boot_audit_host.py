"""Tests for the host side of the read-only boot-target auditor (parse + assess)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), "..", "workspace", "public", "src", "scripts", "revalidation"))

from a90_boot_audit_host import (  # noqa: E402
    assess,
    audit_to_identity,
    parse_audit_output,
    proposed_pin,
)
from a90_boot_target_guard import evaluate_boot_target, pin_is_confirmed  # noqa: E402

GOOD = """
A90BOOTAUDIT begin
A90BOOTAUDIT target=/dev/block/by-name/boot
A90BOOTAUDIT canonical=/dev/block/sda24
A90BOOTAUDIT open=ok
A90BOOTAUDIT is_block=1
A90BOOTAUDIT rdev=259:8
A90BOOTAUDIT size_bytes=67108864
A90BOOTAUDIT logical_sector=4096
A90BOOTAUDIT physical_sector=4096
A90BOOTAUDIT sysfs=/sys/dev/block/259:8
A90BOOTAUDIT partname=boot
A90BOOTAUDIT diskseq=12
A90BOOTAUDIT sysfs_sectors=131072
A90BOOTAUDIT end rc=0
"""

OPEN_FAIL = """
A90BOOTAUDIT begin
A90BOOTAUDIT target=/dev/block/by-name/boot
A90BOOTAUDIT canonical=/dev/block/by-name/boot (not-a-symlink errno=22)
A90BOOTAUDIT open=fail errno=13 (Permission denied)
A90BOOTAUDIT end rc=-13
"""

FORBIDDEN = GOOD.replace("partname=boot", "partname=modem")


class ParseTests(unittest.TestCase):
    def test_parse_keys(self):
        p = parse_audit_output(GOOD)
        self.assertEqual(p["open"], "ok")
        self.assertEqual(p["rdev"], "259:8")
        self.assertEqual(p["size_bytes"], "67108864")
        self.assertEqual(p["partname"], "boot")
        self.assertEqual(p["diskseq"], "12")

    def test_identity_fields(self):
        ident = audit_to_identity(parse_audit_output(GOOD))
        self.assertEqual((ident.rdev_major, ident.rdev_minor), (259, 8))
        self.assertEqual(ident.size_bytes, 67108864)
        self.assertTrue(ident.is_block)
        self.assertEqual(ident.diskseq, 12)


class AssessTests(unittest.TestCase):
    def test_good_boot_assessed_ok(self):
        r = assess(GOOD)
        self.assertTrue(r["ok"])
        self.assertTrue(r["evaluate_ok"])

    def test_proposed_pin_is_confirmed_and_round_trips(self):
        ident = audit_to_identity(parse_audit_output(GOOD))
        pin = proposed_pin(ident)
        self.assertTrue(pin_is_confirmed(pin))
        # the audited identity must pass under its own proposed pin
        self.assertTrue(evaluate_boot_target(ident, pin).ok)

    def test_open_fail_is_not_ok(self):
        r = assess(OPEN_FAIL)
        self.assertFalse(r["ok"])
        self.assertIn("open", r["error"])

    def test_forbidden_partname_refused(self):
        r = assess(FORBIDDEN)
        self.assertFalse(r["ok"])
        self.assertFalse(r["evaluate_ok"])


if __name__ == "__main__":
    unittest.main()
