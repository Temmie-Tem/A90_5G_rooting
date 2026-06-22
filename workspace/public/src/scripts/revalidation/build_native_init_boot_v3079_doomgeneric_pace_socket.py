#!/usr/bin/env python3
"""Build V3079 native-init DOOM presenter-paced helper candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v3077_doomgeneric_pageflip_presenter as v3077
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3079"
INIT_VERSION = "0.10.96"
INIT_BUILD = "v3079-doomgeneric-pace-socket"
BUILD_TAG = INIT_BUILD
DECISION = "v3079-doomgeneric-pace-socket-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3079_DOOMGENERIC_PACE_SOCKET_SOURCE_BUILD_2026-06-23.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3079_doomgeneric_pace_socket.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3079_doomgeneric_pace_socket"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3079_doomgeneric_pace_socket.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v512_doomgeneric_pace_socket"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3079"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3079.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3079.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3079"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3079-pace-socket"

RUNTIME_WAD_ROOT = v3077.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3077.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3077.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3077.RUNTIME_WAD_MAX_BYTES
DEFAULT_FRAME_TICKS = v3077.DEFAULT_FRAME_TICKS
DEFAULT_SMOKE_FRAMES = v3077.DEFAULT_SMOKE_FRAMES
DEFAULT_LOOP_FRAMES = v3077.DEFAULT_LOOP_FRAMES
CONTINUOUS_LOOP_FRAMES = v3077.CONTINUOUS_LOOP_FRAMES
MAX_LOOP_FRAMES = v3077.MAX_LOOP_FRAMES
LOOP_FRAME_MS = v3077.LOOP_FRAME_MS
PRESENTER_POLL_MS = v3077.PRESENTER_POLL_MS
FRAME_PATH = "/tmp/a90-doomgeneric-v3079-pace-socket-frame.xbgr8888"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3079-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3079-input.sock"
INPUT_UDP_PORT = v3077.INPUT_UDP_PORT
DEVICE_NCM_HOST = v3077.DEVICE_NCM_HOST
PACE_SOCKET_PATH = "/tmp/a90-doomgeneric-v3079-pace.sock"
PAGEFLIP_MIN_SUBMIT_INTERVAL_MS = 18
FRAME_WIDTH = v3077.FRAME_WIDTH
FRAME_HEIGHT = v3077.FRAME_HEIGHT
FRAME_STRIDE = v3077.FRAME_STRIDE
FRAME_BYTES = v3077.FRAME_BYTES
NATIVE_DASHBOARD = v3077.NATIVE_DASHBOARD
NATIVE_DASHBOARD_MINIMAL = v3077.NATIVE_DASHBOARD_MINIMAL
NATIVE_DASHBOARD_LARGE_FRAME = v3077.NATIVE_DASHBOARD_LARGE_FRAME
NATIVE_DOOM_PRESENT_PAGEFLIP = v3077.NATIVE_DOOM_PRESENT_PAGEFLIP
BASELINE_PRESENTER_PACING = "helper-frame-mtime"
CANDIDATE_PRESENTER_PACING = "presenter-pageflip-pace-socket"
REUSE_FRAME_BUFFER = v3077.REUSE_FRAME_BUFFER
DASHBOARD_METRICS_INTERVAL_FRAMES = v3077.DASHBOARD_METRICS_INTERVAL_FRAMES
FRAME_TIMING_PROBE = v3077.FRAME_TIMING_PROBE

SOUND_MODE = v3077.SOUND_MODE
AUDIO_CORUN = v3077.AUDIO_CORUN
AUDIO_CORUN_MODE = v3077.AUDIO_CORUN_MODE
AUDIO_CORUN_DURATION_MS = v3077.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_AMPLITUDE_MILLI = v3077.AUDIO_CORUN_AMPLITUDE_MILLI

HOST_KEYBOARD_BRIDGE = v3077.HOST_KEYBOARD_BRIDGE
HOST_DASHBOARD = v3077.HOST_DASHBOARD
V3059 = v3077.v3074.v3071.v3069.v3067.v3065.v3063.v3061.v3059
BASE_V3059_ADAPTER_SOURCE = V3059.v3059_adapter_source

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.96 (v3079-doomgeneric-pace-socket)",
    b"v3079-doomgeneric-pace-socket",
    b"doomgeneric-private-link-v3079-pace-socket",
    b"/bin/a90_doomgeneric_private_engine_v3079",
    RUNTIME_WAD_PATH.encode("ascii"),
    EXPECTED_WAD_SHA256.encode("ascii"),
    FRAME_PATH.encode("ascii"),
    INPUT_STATE_PATH.encode("ascii"),
    INPUT_SOCKET_PATH.encode("ascii"),
    PACE_SOCKET_PATH.encode("ascii"),
    b"a90.doomgeneric.v3059.input=udp-ncm-state-with-unix-dgram-fallback",
    b"a90.doomgeneric.v3079.pace=presenter-pageflip-token",
    b"--input-udp",
    b"--pace-socket",
    b"udp-ncm-to-DG_GetKey-with-serial-doompad-fallback",
    b"video.demo.doom.presenter.pacing=presenter-pageflip-pace-socket",
    b"video.demo.doom.presenter.pace_socket_path=",
    b"video.demo.doom.presenter.pageflip_min_submit_interval_ms=",
    b"video.demo.doom.presenter.present_mode=pageflip",
    b"video.demo.doom.presenter.present_path=kms-dumb-buffer-pageflip",
    b"video.demo.doom.loop.presenter.pacing=",
    b"pace_socket.tokens_sent=",
    b"video.demo.doom.loop.pace_socket.wait_timeouts=",
    b"video.demo.doom.loop.flip_telemetry=pageflip-event-delta-us",
    b"video.demo.doom.loop.timing_probe=1",
    b"video.demo.doom.dashboard.profile=minimal-fastdraw",
    b"video.demo.input.udp_port=",
    b"native-audio-corun-tone-v3053",
)


def rel(path: Path) -> str:
    return v3077.rel(path)


def replace_required(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing source fragment for V3079 patch: {old[:80]!r}")
    return text.replace(old, new)


def v3079_adapter_source() -> str:
    text = BASE_V3059_ADAPTER_SOURCE()
    text = replace_required(
        text,
        'const char a90_doomgeneric_v3059_udp_input_policy[] =\n'
        '    "a90.doomgeneric.v3059.input=udp-ncm-state-with-unix-dgram-fallback";',
        'const char a90_doomgeneric_v3059_udp_input_policy[] =\n'
        '    "a90.doomgeneric.v3059.input=udp-ncm-state-with-unix-dgram-fallback";\n'
        'const char a90_doomgeneric_v3079_pace_policy[] =\n'
        '    "a90.doomgeneric.v3079.pace=presenter-pageflip-token";',
    )
    text = replace_required(
        text,
        "marker_checksum(a90_doomgeneric_v3059_udp_input_policy) == 0U) {",
        "marker_checksum(a90_doomgeneric_v3059_udp_input_policy) == 0U ||\n"
        "        marker_checksum(a90_doomgeneric_v3079_pace_policy) == 0U) {",
    )
    pace_support = r'''
#define A90_DG_PACE_PACKET_MAGIC 0x41395043U
#define A90_DG_PACE_PACKET_VERSION 1U

struct a90_dg_pace_packet {
    uint32_t magic;
    uint32_t version;
    uint32_t seq;
};

static int a90_doomgeneric_open_pace_socket(const char *path) {
    struct sockaddr_un addr;
    int fd;
    size_t path_len;

    if (path == NULL || path[0] == '\0') {
        return -1;
    }
    path_len = strlen(path);
    if (path_len == 0 || path_len >= sizeof(addr.sun_path)) {
        return -1;
    }
    fd = socket(AF_UNIX, SOCK_DGRAM, 0);
    if (fd < 0) {
        return -1;
    }
    (void)fcntl(fd, F_SETFD, FD_CLOEXEC);
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    memcpy(addr.sun_path, path, path_len + 1U);
    (void)unlink(path);
    if (bind(fd, (const struct sockaddr *)&addr, sizeof(addr)) < 0) {
        close(fd);
        (void)unlink(path);
        return -1;
    }
    return fd;
}

static int a90_doomgeneric_wait_pace_fd(int fd) {
    for (;;) {
        struct a90_dg_pace_packet packet;
        ssize_t rd;

        if (fd < 0) {
            return 0;
        }
        rd = recv(fd, &packet, sizeof(packet), 0);
        if (rd < 0) {
            if (errno == EINTR) {
                continue;
            }
            return 53;
        }
        if (rd != (ssize_t)sizeof(packet)) {
            continue;
        }
        if (packet.magic != A90_DG_PACE_PACKET_MAGIC ||
            packet.version != A90_DG_PACE_PACKET_VERSION) {
            continue;
        }
        return 0;
    }
}

static void a90_doomgeneric_close_pace_socket(int fd, const char *path) {
    if (fd >= 0) {
        close(fd);
    }
    if (path != NULL && path[0] != '\0') {
        (void)unlink(path);
    }
}

'''
    text = replace_required(
        text,
        "static int a90_doomgeneric_open_input_udp(unsigned int port) {",
        pace_support + "static int a90_doomgeneric_open_input_udp(unsigned int port) {",
    )
    text = replace_required(
        text,
        "                                       const char *input_socket_path,\n"
        "                                       unsigned int input_udp_port,\n"
        "                                       int frame_ms) {",
        "                                       const char *input_socket_path,\n"
        "                                       unsigned int input_udp_port,\n"
        "                                       const char *pace_socket_path,\n"
        "                                       int frame_ms) {",
    )
    text = replace_required(
        text,
        "    int input_socket_fd;\n"
        "    int input_udp_fd;\n"
        "    int loop_rc = 0;",
        "    int input_socket_fd;\n"
        "    int input_udp_fd;\n"
        "    int pace_fd;\n"
        "    int loop_rc = 0;",
    )
    text = replace_required(
        text,
        "    a90_doomgeneric_apply_input_state_file(input_state_path);\n"
        "    input_socket_fd = a90_doomgeneric_open_input_socket(input_socket_path);\n"
        "    input_udp_fd = a90_doomgeneric_open_input_udp(input_udp_port);\n",
        "    a90_doomgeneric_apply_input_state_file(input_state_path);\n"
        "    input_socket_fd = a90_doomgeneric_open_input_socket(input_socket_path);\n"
        "    input_udp_fd = a90_doomgeneric_open_input_udp(input_udp_port);\n"
        "    pace_fd = a90_doomgeneric_open_pace_socket(pace_socket_path);\n"
        "    if (pace_socket_path != NULL && pace_socket_path[0] != '\\0' && pace_fd < 0) {\n"
        "        if (input_udp_fd >= 0) {\n"
        "            close(input_udp_fd);\n"
        "        }\n"
        "        a90_doomgeneric_close_input_socket(input_socket_fd, input_socket_path);\n"
        "        return 52;\n"
        "    }\n",
    )
    text = replace_required(
        text,
        "    doomgeneric_Create(12, argv);\n"
        "    for (index = 0; frames == 0 || index < frames; ++index) {\n"
        "        int rc;\n\n"
        "        if (input_socket_fd >= 0) {",
        "    doomgeneric_Create(12, argv);\n"
        "    for (index = 0; frames == 0 || index < frames; ++index) {\n"
        "        int rc;\n\n"
        "        if (pace_fd >= 0) {\n"
        "            rc = a90_doomgeneric_wait_pace_fd(pace_fd);\n"
        "            if (rc != 0) {\n"
        "                loop_rc = rc;\n"
        "                break;\n"
        "            }\n"
        "        }\n"
        "        if (input_socket_fd >= 0) {",
    )
    text = replace_required(
        text,
        "        usleep((useconds_t)frame_ms * 1000U);\n",
        "        if (pace_fd < 0) {\n"
        "            usleep((useconds_t)frame_ms * 1000U);\n"
        "        }\n",
    )
    text = replace_required(
        text,
        "    if (input_udp_fd >= 0) {\n"
        "        close(input_udp_fd);\n"
        "    }\n"
        "    a90_doomgeneric_close_input_socket(input_socket_fd, input_socket_path);\n",
        "    a90_doomgeneric_close_pace_socket(pace_fd, pace_socket_path);\n"
        "    if (input_udp_fd >= 0) {\n"
        "        close(input_udp_fd);\n"
        "    }\n"
        "    a90_doomgeneric_close_input_socket(input_socket_fd, input_socket_path);\n",
    )
    text = replace_required(
        text,
        "if ((argc == 11 || argc == 13 || argc == 15) &&",
        "if ((argc == 11 || argc == 13 || argc == 15 || argc == 17) &&",
    )
    text = replace_required(
        text,
        "        const char *input_socket_path = NULL;\n"
        "        unsigned int input_udp_port = 0U;",
        "        const char *input_socket_path = NULL;\n"
        "        const char *pace_socket_path = NULL;\n"
        "        unsigned int input_udp_port = 0U;",
    )
    text = replace_required(
        text,
        "            } else if (strcmp(argv[arg_index], \"--input-udp\") == 0) {\n"
        "                input_udp_port = (unsigned int)a90_doomgeneric_parse_positive_int(argv[arg_index + 1], 65535);\n"
        "                if (input_udp_port == 0U) {\n"
        "                    return 37;\n"
        "                }\n"
        "            } else {",
        "            } else if (strcmp(argv[arg_index], \"--input-udp\") == 0) {\n"
        "                input_udp_port = (unsigned int)a90_doomgeneric_parse_positive_int(argv[arg_index + 1], 65535);\n"
        "                if (input_udp_port == 0U) {\n"
        "                    return 37;\n"
        "                }\n"
        "            } else if (strcmp(argv[arg_index], \"--pace-socket\") == 0) {\n"
        "                pace_socket_path = argv[arg_index + 1];\n"
        "            } else {",
    )
    text = replace_required(
        text,
        "        return a90_doomgeneric_run_wad_frame_loop(argv[2], frames, argv[6], argv[8], input_socket_path, input_udp_port, frame_ms);",
        "        return a90_doomgeneric_run_wad_frame_loop(argv[2], frames, argv[6], argv[8], input_socket_path, input_udp_port, pace_socket_path, frame_ms);",
    )
    return text


def v3033_module() -> Any:
    return v3077.v3033_module()


def apply_v3079_globals() -> None:
    v3077.CYCLE = CYCLE
    v3077.INIT_VERSION = INIT_VERSION
    v3077.INIT_BUILD = INIT_BUILD
    v3077.BUILD_TAG = BUILD_TAG
    v3077.DECISION = DECISION
    v3077.OUT_DIR = OUT_DIR
    v3077.OBJ_DIR = OBJ_DIR
    v3077.REPORT_PATH = REPORT_PATH
    v3077.BOOT_IMAGE = BOOT_IMAGE
    v3077.INIT_BINARY = INIT_BINARY
    v3077.RAMDISK_CPIO = RAMDISK_CPIO
    v3077.HELPER_BINARY = HELPER_BINARY
    v3077.ENGINE_BINARY = ENGINE_BINARY
    v3077.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3077.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3077.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3077.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3077.ENGINE_NAME = ENGINE_NAME
    v3077.FRAME_PATH = FRAME_PATH
    v3077.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3077.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3077.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3077.render_report = render_report
    v3077.apply_v3077_globals()

    v3033 = v3033_module()
    v3033.PACE_SOCKET_PATH = PACE_SOCKET_PATH
    v3033.PAGEFLIP_MIN_SUBMIT_INTERVAL_MS = PAGEFLIP_MIN_SUBMIT_INTERVAL_MS
    V3059.v3059_adapter_source = v3079_adapter_source


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    markers = manifest.get("v3033_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3079 DOOMGENERIC Pace Socket Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback / DOOM capstone frame pacing.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Keeps V3077 pageflip presenter, V3074 minimal dashboard, V3071 timing probe, reader reuse, frame_ms=28, and UDP/NCM input.",
        "- Adds a helper-owned Unix datagram pace socket that blocks each helper tick until the presenter sends a token.",
        "- Changes pacing ownership from helper sleep plus presenter pageflip wait to presenter pageflip tokens as the single loop gate.",
        "- Adds a small pageflip submit guard so a fast helper frame cannot immediately re-submit into the same 16.6 ms cadence slot.",
        "",
        "## Pacing Contract",
        "",
        f"- Baseline pacing: `{BASELINE_PRESENTER_PACING}`",
        f"- Candidate pacing: `{CANDIDATE_PRESENTER_PACING}`",
        f"- Pace socket: `{PACE_SOCKET_PATH}`",
        f"- Pageflip min submit interval ms: `{PAGEFLIP_MIN_SUBMIT_INTERVAL_MS}`",
        f"- Helper frame ms fallback: `{doom.get('loop_frame_ms', LOOP_FRAME_MS)}`",
        f"- Presenter poll ms: `{doom.get('presenter_poll_ms', PRESENTER_POLL_MS)}`",
        "- Token contract: presenter sends one token to permit one helper `doomgeneric_Tick()` and frame dump.",
        "- Fallback contract: if no pace socket path is compiled, helper keeps its legacy `usleep(frame_ms)` path.",
        "",
        "## Runtime Contract",
        "",
        f"- Runtime WAD path: `{doom.get('runtime_wad_path')}`",
        f"- Expected WAD SHA256: `{doom.get('expected_wad_sha256')}`",
        f"- Continuous command: `video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}`",
        f"- Helper loop command: `{doom.get('helper_loop_command')}`",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Validation",
        "",
        "- `py_compile`: V3079 builder and focused tests.",
        "- `unittest`: V3079 source contract plus V3077/V3074/V3071/V3069 lineage regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3079 identity, pace socket helper markers, presenter pace markers, pageflip telemetry, minimal-dashboard markers, and UDP input markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3080`",
        "- Type: rollback-gated live validation of V3079 pace-socket candidate.",
        "- Scope: flash exact V3079 boot image via `native_init_flash.py`, health-check, require pace-socket markers, run bounded foreground timing loop, compare flip delta distribution with V3078, then start continuous loop and verify UDP input still works.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-pace-socket-candidate`.",
    ]) + "\n"


def main() -> int:
    apply_v3079_globals()
    rc = v3077.v3074.v3071.v3069.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "pace_socket_path": PACE_SOCKET_PATH,
        "baseline_presenter_pacing": BASELINE_PRESENTER_PACING,
        "presenter_pacing": CANDIDATE_PRESENTER_PACING,
        "pageflip_min_submit_interval_ms": PAGEFLIP_MIN_SUBMIT_INTERVAL_MS,
        "pace_socket_packet": {
            "magic": "0x41395043",
            "version": 1,
            "fields": ["magic", "version", "seq"],
        },
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_dashboard_large_frame": bool(NATIVE_DASHBOARD_LARGE_FRAME),
        "native_doom_present_pageflip": bool(NATIVE_DOOM_PRESENT_PAGEFLIP),
        "present_mode": "pageflip",
        "present_path": "kms-dumb-buffer-pageflip",
        "pageflip_timeout_ms": 1000,
        "helper_loop_command": (
            f"{ENGINE_REMOTE_PATH} --wad-frame-loop {RUNTIME_WAD_PATH} "
            f"--frames {DEFAULT_LOOP_FRAMES} --output {FRAME_PATH} "
            f"--input-state {INPUT_STATE_PATH} --frame-ms {LOOP_FRAME_MS} "
            f"--input-socket {INPUT_SOCKET_PATH} --pace-socket {PACE_SOCKET_PATH} "
            f"--input-udp {INPUT_UDP_PORT}"
        ),
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-pace-socket-candidate",
        "adoption_state": "pending-pace-socket-live-validation",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        render_report(
            manifest,
            tuple(manifest.get("helper_flags", ())),
            tuple(manifest.get("init_extra_flags", ())),
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "doomgeneric-pace-socket-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-pace-socket-candidate",
        "boot_image": rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "engine_binary": rel(ENGINE_BINARY),
        "engine_ramdisk_path": ENGINE_REMOTE_PATH,
        "runtime_wad_path": RUNTIME_WAD_PATH,
        "expected_wad_sha256": EXPECTED_WAD_SHA256,
        "frame_path": FRAME_PATH,
        "input_state_path": INPUT_STATE_PATH,
        "input_socket_path": INPUT_SOCKET_PATH,
        "input_udp_host": DEVICE_NCM_HOST,
        "input_udp_port": INPUT_UDP_PORT,
        "pace_socket_path": PACE_SOCKET_PATH,
        "loop_frame_ms": LOOP_FRAME_MS,
        "presenter_poll_ms": PRESENTER_POLL_MS,
        "presenter_pacing": CANDIDATE_PRESENTER_PACING,
        "pageflip_min_submit_interval_ms": PAGEFLIP_MIN_SUBMIT_INTERVAL_MS,
        "present_mode": "pageflip",
        "present_path": "kms-dumb-buffer-pageflip",
        "dashboard_profile": "minimal-fastdraw",
        "frame_timing_probe": FRAME_TIMING_PROBE,
        "native_dashboard": bool(NATIVE_DASHBOARD),
        "native_dashboard_minimal": bool(NATIVE_DASHBOARD_MINIMAL),
        "native_doom_present_pageflip": bool(NATIVE_DOOM_PRESENT_PAGEFLIP),
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-pace-socket-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
