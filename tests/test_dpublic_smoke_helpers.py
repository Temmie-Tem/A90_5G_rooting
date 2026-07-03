"""Static checks for the D-public smoke helper sources."""

from __future__ import annotations

import unittest
from pathlib import Path


SMOKE_HTTPD = Path("workspace/public/src/scripts/server-distro/a90_dpublic_smoke_httpd.c")
HTTP_GET = Path("workspace/public/src/scripts/server-distro/a90_dpublic_http_get.c")


class DpublicSmokeHelperTests(unittest.TestCase):
    def test_smoke_httpd_defaults_to_loopback_only(self) -> None:
        source = SMOKE_HTTPD.read_text(encoding="utf-8")
        self.assertIn('const char *bind_ip = "127.0.0.1";', source)
        self.assertIn("A90_DPUBLIC_SMOKE_OK", source)
        self.assertIn("public_exposure=outbound-tunnel-only", source)
        self.assertNotIn('const char *bind_ip = "0.0.0.0";', source)

    def test_smoke_httpd_handles_partial_writes(self) -> None:
        source = SMOKE_HTTPD.read_text(encoding="utf-8")
        self.assertIn("write_all_best_effort", source)
        self.assertIn("Connection: close", source)
        self.assertIn("Cache-Control: no-store", source)

    def test_http_get_is_device_local_validation_helper(self) -> None:
        source = HTTP_GET.read_text(encoding="utf-8")
        self.assertIn('const char *host = "127.0.0.1";', source)
        self.assertIn("GET / HTTP/1.1", source)
        self.assertIn("connect(fd", source)
        self.assertNotIn("trycloudflare.com", source)


if __name__ == "__main__":
    unittest.main()
