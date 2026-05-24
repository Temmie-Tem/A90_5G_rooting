#!/usr/bin/env python3
"""V712 current-boot orchestrator for helper v121 provider-first ICNSS edge proof."""

from __future__ import annotations

from typing import Any

import native_wifi_provider_first_cnss_orchestrator_v708 as v708


v700 = v708.v700
v700.DEFAULT_OUT_DIR = v700.Path("tmp/wifi/v712-provider-first-icnss-edge-v121-orchestrated")
v700.V700_SCRIPT = "scripts/revalidation/native_wifi_provider_first_icnss_edge_v712.py"
v700.V700_APPROVAL = (
    "approve v712 provider-first ICNSS edge v121 capture proof only; "
    "no Wi-Fi HAL start, no scan/connect/link-up, no DHCP and no external ping"
)
v700.HELPER_SHA256 = "547232ddb352740bb7a7f1d0f9116162584e34a536b9d9b77869ed8d838e7c89"
v700.HELPER_MARKER = "a90_android_execns_probe v121"

_build_manifest = v708._build_manifest
_render_summary = v708._render_summary


def _replace(value: object) -> object:
    if isinstance(value, str):
        return (
            value.replace("v700", "v712")
            .replace("V700", "V712")
            .replace("v708", "v712")
            .replace("V708", "V712")
            .replace("v119", "v121")
            .replace("v120", "v121")
        )
    if isinstance(value, dict):
        return {key: _replace(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace(item) for item in value]
    return value


def build_manifest(args: v700.argparse.Namespace,
                   prep: dict[str, Any] | None,
                   arm: dict[str, Any] | None) -> dict[str, Any]:
    manifest = _build_manifest(args, prep, arm)
    manifest = _replace(manifest)
    assert isinstance(manifest, dict)
    manifest["cycle"] = "v712"
    manifest["helper_marker"] = v700.HELPER_MARKER
    manifest["helper_sha256"] = v700.HELPER_SHA256
    manifest["icnss_edge_captured"] = bool(
        ((arm or {}).get("live") or {}).get("v712_icnss_edge_captured")
    )
    return manifest


def render_summary(manifest: dict[str, Any]) -> str:
    return (
        _render_summary(manifest)
        .replace("v700", "v712")
        .replace("V700", "V712")
        .replace("v708", "v712")
        .replace("V708", "V712")
        .replace("v119", "v121")
        .replace("v120", "v121")
    )


v700.build_manifest = build_manifest
v700.render_summary = render_summary


if __name__ == "__main__":
    raise SystemExit(v700.main())
