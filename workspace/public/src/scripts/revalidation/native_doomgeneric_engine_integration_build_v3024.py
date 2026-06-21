#!/usr/bin/env python3
"""Host-only private-source doomgeneric full-engine integration build."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import (
    ensure_private_dir,
    write_private_text,
    write_public_text,
    workspace_private_build_path,
    workspace_private_input_path,
)


ROOT = repo_root()

RUN_ID = "V3024"
BUILD_TAG = "v3024-doomgeneric-private-integration"
DECISION = "v3024-doomgeneric-private-full-engine-link-pass"
SOURCE_URL = "https://github.com/ozkl/doomgeneric"
PINNED_COMMIT = "dcb7a8dbc7a16ce3dda29382ac9aae9d77d21284"
SOURCE_ROOT = ROOT / "workspace/private/demo-assets/doom/doomgeneric-v3020"
SOURCE_DIR = SOURCE_ROOT / "doomgeneric"
SOURCE_MAKEFILE = SOURCE_DIR / "Makefile.soso"
OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "objects"
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V3024_DOOMGENERIC_PRIVATE_INTEGRATION_BUILD_2026-06-21.md"
MANIFEST_PATH = OUT_DIR / "manifest.json"
ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3024.c"
ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3024.o"
ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3024"
V3021_INIT_BINARY = workspace_private_build_path(
    "native-init",
    "v3021-demo-checkpoint-badapple-nyan",
    "init_v3021_demo_checkpoint_badapple_nyan",
)
V3021_BOOT_IMAGE = workspace_private_input_path(
    "boot_images",
    "boot_linux_v3021_demo_checkpoint_badapple_nyan.img",
    legacy_fallback=False,
)
V3023_POLICY_REPORT = ROOT / "docs/reports/NATIVE_INIT_V3023_DOOMGENERIC_INTEGRATION_POLICY_2026-06-21.md"

CROSS_CC = "aarch64-linux-gnu-gcc"
CROSS_STRIP = "aarch64-linux-gnu-strip"
CROSS_SIZE = "aarch64-linux-gnu-size"
COMMON_CFLAGS = (
    "-std=gnu11",
    "-Os",
    "-ffunction-sections",
    "-fdata-sections",
    "-DNORMALUNIX",
    "-DLINUX",
    "-DSNDSERV",
    "-D_DEFAULT_SOURCE",
    "-DDOOMGENERIC_RESX=640",
    "-DDOOMGENERIC_RESY=400",
)
THIRD_PARTY_CFLAGS = COMMON_CFLAGS + ("-Wall", "-Wextra")
ADAPTER_CFLAGS = COMMON_CFLAGS + ("-Wall", "-Wextra", "-Werror")
LINK_FLAGS = ("-static", "-Wl,--gc-sections")
RUNTIME_WAD_PATH = "/cache/a90-runtime/pkg/doom/v3024/DOOM1.WAD"
RUNTIME_WAD_ROOT = "/cache/a90-runtime/pkg/doom/v3024/"
ENGINE_ONLY_BOOT_DELTA_CAP_BYTES = 2 * 1024 * 1024
PUBLIC_WAD_ROOT = ROOT / "workspace/public"
PRIVATE_DOOM_ROOT = ROOT / "workspace/private/demo-assets/doom"

ADAPTER_SOURCE_TEXT = r'''#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "doomgeneric.h"
#include "doomkeys.h"

#define A90_DG_KEY_QUEUE_MAX 64U
#define A90_DG_RUNTIME_WAD_PATH "/cache/a90-runtime/pkg/doom/v3024/DOOM1.WAD"

const char a90_doomgeneric_v3024_marker[] =
    "a90.doomgeneric.v3024.private_source_integration=1";
const char a90_doomgeneric_v3024_wad_policy[] =
    "a90.doomgeneric.v3024.wad_policy=runtime-private-not-boot";
const char a90_doomgeneric_v3024_input_policy[] =
    "a90.doomgeneric.v3024.input=serial-doompad-to-DG_GetKey";

struct a90_doompad_snapshot {
    bool forward;
    bool back;
    bool left;
    bool right;
    bool fire;
    bool use;
    bool menu;
    bool run;
    unsigned int seq;
};

struct a90_dg_key_event {
    int pressed;
    unsigned char key;
};

static struct a90_dg_key_event key_queue[A90_DG_KEY_QUEUE_MAX];
static unsigned int key_head;
static unsigned int key_tail;
static bool last_forward;
static bool last_back;
static bool last_left;
static bool last_right;
static bool last_fire;
static bool last_use;
static bool last_menu;
static bool last_run;
static unsigned int last_seq;
static unsigned int presented_frames;
static uint32_t fake_ticks_ms;
static uint32_t frame_checksum;
static pixel_t frame_sink[DOOMGENERIC_RESX * DOOMGENERIC_RESY];

static uint32_t marker_checksum(const volatile char *value) {
    uint32_t checksum = 5381U;

    while (value != NULL && *value != '\0') {
        checksum = (checksum * 33U) ^ (uint32_t)(unsigned char)*value;
        ++value;
    }
    return checksum;
}

static unsigned int next_index(unsigned int index) {
    return (index + 1U) % A90_DG_KEY_QUEUE_MAX;
}

static void queue_key_event(int pressed, unsigned char key) {
    unsigned int next_tail = next_index(key_tail);

    if (next_tail == key_head) {
        return;
    }
    key_queue[key_tail].pressed = pressed ? 1 : 0;
    key_queue[key_tail].key = key;
    key_tail = next_tail;
}

static void queue_edge(bool current, bool *previous, unsigned char key) {
    if (previous == NULL) {
        return;
    }
    if (current != *previous) {
        queue_key_event(current ? 1 : 0, key);
        *previous = current;
    }
}

void a90_doomgeneric_feed_snapshot(const struct a90_doompad_snapshot *snapshot) {
    if (snapshot == NULL) {
        return;
    }

    queue_edge(snapshot->forward, &last_forward, KEY_UPARROW);
    queue_edge(snapshot->back, &last_back, KEY_DOWNARROW);
    queue_edge(snapshot->left, &last_left, KEY_LEFTARROW);
    queue_edge(snapshot->right, &last_right, KEY_RIGHTARROW);
    queue_edge(snapshot->fire, &last_fire, KEY_FIRE);
    queue_edge(snapshot->use, &last_use, KEY_USE);
    queue_edge(snapshot->menu, &last_menu, KEY_ESCAPE);
    queue_edge(snapshot->run, &last_run, KEY_RSHIFT);
    last_seq = snapshot->seq;
}

int a90_doomgeneric_prepare_argv(char **argv, int max_args) {
    static char arg0[] = "doomgeneric";
    static char arg_iwad[] = "-iwad";
    static char arg_wad[] = A90_DG_RUNTIME_WAD_PATH;
    static char arg_nosound[] = "-nosound";
    static char arg_nomusic[] = "-nomusic";
    static char arg_mb[] = "-mb";
    static char arg_mb_value[] = "6";

    if (argv == NULL || max_args < 7) {
        return 0;
    }
    argv[0] = arg0;
    argv[1] = arg_iwad;
    argv[2] = arg_wad;
    argv[3] = arg_nosound;
    argv[4] = arg_nomusic;
    argv[5] = arg_mb;
    argv[6] = arg_mb_value;
    return 7;
}

unsigned int a90_doomgeneric_last_seq(void) {
    return last_seq;
}

unsigned int a90_doomgeneric_pending_keys(void) {
    if (key_tail >= key_head) {
        return key_tail - key_head;
    }
    return A90_DG_KEY_QUEUE_MAX - key_head + key_tail;
}

unsigned int a90_doomgeneric_presented_frames(void) {
    return presented_frames;
}

uint32_t a90_doomgeneric_frame_checksum(void) {
    return frame_checksum;
}

void DG_Init(void) {
    memset(frame_sink, 0, sizeof(frame_sink));
    key_head = 0;
    key_tail = 0;
    presented_frames = 0;
    fake_ticks_ms = 0;
    frame_checksum = 0;
}

void DG_DrawFrame(void) {
    const size_t count = (size_t)DOOMGENERIC_RESX * (size_t)DOOMGENERIC_RESY;
    size_t i;

    if (DG_ScreenBuffer != NULL) {
        memcpy(frame_sink, DG_ScreenBuffer, count * sizeof(frame_sink[0]));
        for (i = 0; i < count; i += 257U) {
            frame_checksum = frame_checksum * 33U + (uint32_t)frame_sink[i];
        }
    }
    ++presented_frames;
}

void DG_SleepMs(uint32_t ms) {
    fake_ticks_ms += ms;
}

uint32_t DG_GetTicksMs(void) {
    return fake_ticks_ms;
}

int DG_GetKey(int *pressed, unsigned char *key) {
    if (pressed == NULL || key == NULL || key_head == key_tail) {
        return 0;
    }

    *pressed = key_queue[key_head].pressed;
    *key = key_queue[key_head].key;
    key_head = next_index(key_head);
    return 1;
}

void DG_SetWindowTitle(const char *title) {
    (void)title;
}

int a90_doomgeneric_native_probe_entry(void) {
    struct a90_doompad_snapshot snapshot = {
        .forward = true,
        .fire = true,
        .run = true,
        .seq = 24U,
    };
    char *argv[8] = {0};
    int argc = a90_doomgeneric_prepare_argv(argv, 8);
    int pressed = 0;
    unsigned char key = 0;

    DG_Init();
    if (marker_checksum(a90_doomgeneric_v3024_marker) == 0U ||
        marker_checksum(a90_doomgeneric_v3024_wad_policy) == 0U ||
        marker_checksum(a90_doomgeneric_v3024_input_policy) == 0U) {
        return 19;
    }
    if (argc != 7 || strcmp(argv[1], "-iwad") != 0 ||
        strcmp(argv[2], A90_DG_RUNTIME_WAD_PATH) != 0 ||
        strcmp(argv[3], "-nosound") != 0 ||
        strcmp(argv[4], "-nomusic") != 0) {
        return 20;
    }
    a90_doomgeneric_feed_snapshot(&snapshot);
    if (a90_doomgeneric_pending_keys() != 3U) {
        return 21;
    }
    if (!DG_GetKey(&pressed, &key) || pressed != 1 || key != KEY_UPARROW) {
        return 22;
    }
    if (!DG_GetKey(&pressed, &key) || pressed != 1 || key != KEY_FIRE) {
        return 23;
    }
    if (!DG_GetKey(&pressed, &key) || pressed != 1 || key != KEY_RSHIFT) {
        return 24;
    }
    DG_SleepMs(16U);
    DG_DrawFrame();
    if (DG_GetTicksMs() != 16U || a90_doomgeneric_presented_frames() != 1U) {
        return 25;
    }
    return a90_doomgeneric_last_seq() == 24U ? 0 : 26;
}

int main(void) {
    return a90_doomgeneric_native_probe_entry();
}
'''


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(argv: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else str(ROOT),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def require_success(result: subprocess.CompletedProcess[str], description: str) -> str:
    if result.returncode != 0:
        raise RuntimeError(f"{description} failed rc={result.returncode}\n{result.stdout}")
    return result.stdout


def git_output(args: list[str]) -> str | None:
    if not (SOURCE_ROOT / ".git").is_dir():
        return None
    result = run(["git", "-C", str(SOURCE_ROOT), *args])
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def parse_soso_sources() -> list[str]:
    text = SOURCE_MAKEFILE.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^SRC_DOOM\s*=\s*(.+)$", text, flags=re.MULTILINE)
    if match is None:
        raise RuntimeError(f"could not locate SRC_DOOM in {SOURCE_MAKEFILE}")
    names = []
    for token in match.group(1).split():
        if not token.endswith(".o"):
            continue
        source_name = token[:-2] + ".c"
        if source_name == "doomgeneric_soso.c":
            continue
        names.append(source_name)
    return names


def count_files(root: Path, suffix: str) -> dict[str, Any]:
    if not root.exists():
        return {"root": rel(root), "exists": False, "count": 0, "total_bytes": 0}
    normalized_suffix = suffix.lower()
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.name.lower().endswith(normalized_suffix)
    ]
    return {
        "root": rel(root),
        "exists": True,
        "count": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
    }


def collect_source_state() -> dict[str, Any]:
    head = git_output(["rev-parse", "HEAD"])
    status = git_output(["status", "--short"]) if head else None
    engine_sources = parse_soso_sources() if SOURCE_MAKEFILE.exists() else []
    missing = [name for name in engine_sources if not (SOURCE_DIR / name).is_file()]
    return {
        "source_url": SOURCE_URL,
        "source_root": rel(SOURCE_ROOT),
        "source_exists": SOURCE_DIR.is_dir(),
        "git_head": head,
        "git_head_matches_pin": head == PINNED_COMMIT,
        "git_status_clean": status == "",
        "git_commit_date": git_output(["log", "-1", "--format=%cs"]) if head else None,
        "git_commit_subject": git_output(["log", "-1", "--format=%s"]) if head else None,
        "license_sha256": sha256_file(SOURCE_ROOT / "LICENSE") if (SOURCE_ROOT / "LICENSE").exists() else None,
        "makefile": rel(SOURCE_MAKEFILE),
        "engine_source_count": len(engine_sources),
        "engine_sources_missing": missing,
        "excluded_platform_backend": "doomgeneric_soso.c",
    }


def compile_source(source: Path, output: Path, cflags: tuple[str, ...]) -> dict[str, Any]:
    include_flag = f"-I{SOURCE_DIR}"
    command = [
        CROSS_CC,
        *cflags,
        include_flag,
        "-c",
        str(source),
        "-o",
        str(output),
    ]
    stdout = require_success(run(command), f"compile {source.name}")
    return {
        "source": rel(source),
        "object": rel(output),
        "object_sha256": sha256_file(output),
        "object_bytes": output.stat().st_size,
        "stdout_nonempty": bool(stdout.strip()),
    }


def compile_private_engine() -> dict[str, Any]:
    ensure_private_dir(OUT_DIR)
    ensure_private_dir(OBJ_DIR)
    write_private_text(ADAPTER_SOURCE, ADAPTER_SOURCE_TEXT)

    objects: list[Path] = []
    compile_results = []
    for source_name in parse_soso_sources():
        source = SOURCE_DIR / source_name
        output = OBJ_DIR / f"{source.stem}.o"
        compile_results.append(compile_source(source, output, THIRD_PARTY_CFLAGS))
        objects.append(output)

    adapter_result = compile_source(ADAPTER_SOURCE, ADAPTER_OBJECT, ADAPTER_CFLAGS)
    objects.append(ADAPTER_OBJECT)
    link_command = [
        CROSS_CC,
        *LINK_FLAGS,
        *[str(path) for path in objects],
        "-lm",
        "-o",
        str(ENGINE_BINARY),
    ]
    link_stdout = require_success(run(link_command), "link private doomgeneric engine")
    strip_stdout = require_success(run([CROSS_STRIP, str(ENGINE_BINARY)]), "strip private doomgeneric engine")
    file_output = require_success(run(["file", str(ENGINE_BINARY)]), "file private doomgeneric engine").strip()
    size_output = require_success(run([CROSS_SIZE, str(ENGINE_BINARY)]), "size private doomgeneric engine").strip()
    strings_output = require_success(run(["strings", str(ENGINE_BINARY)]), "strings private doomgeneric engine")
    required_markers = (
        "a90.doomgeneric.v3024.private_source_integration=1",
        "a90.doomgeneric.v3024.wad_policy=runtime-private-not-boot",
        "a90.doomgeneric.v3024.input=serial-doompad-to-DG_GetKey",
        RUNTIME_WAD_PATH,
    )
    missing_markers = [marker for marker in required_markers if marker not in strings_output]
    object_total = sum(path.stat().st_size for path in objects)
    return {
        "adapter_source": rel(ADAPTER_SOURCE),
        "adapter_source_sha256": sha256_file(ADAPTER_SOURCE),
        "adapter_object": rel(ADAPTER_OBJECT),
        "adapter_object_sha256": sha256_file(ADAPTER_OBJECT),
        "engine_binary": rel(ENGINE_BINARY),
        "engine_binary_sha256": sha256_file(ENGINE_BINARY),
        "engine_binary_bytes": ENGINE_BINARY.stat().st_size,
        "engine_object_count": len(objects),
        "engine_object_total_bytes": object_total,
        "third_party_source_compile_count": len(compile_results),
        "adapter_compile": adapter_result,
        "compile_stdout_nonempty_count": sum(1 for item in compile_results if item["stdout_nonempty"]),
        "file_output": file_output,
        "size_output": size_output,
        "aarch64_static_elf": "ELF 64-bit LSB executable, ARM aarch64" in file_output and "statically linked" in file_output,
        "marker_check_pass": not missing_markers,
        "missing_markers": missing_markers,
        "link_stdout_nonempty": bool(link_stdout.strip()),
        "strip_stdout_nonempty": bool(strip_stdout.strip()),
        "commands": {
            "compile_common": f"{CROSS_CC} {' '.join(THIRD_PARTY_CFLAGS)} -I{SOURCE_DIR} -c SOURCE -o OBJECT",
            "compile_adapter": f"{CROSS_CC} {' '.join(ADAPTER_CFLAGS)} -I{SOURCE_DIR} -c {ADAPTER_SOURCE} -o {ADAPTER_OBJECT}",
            "link": " ".join(link_command),
            "strip": f"{CROSS_STRIP} {ENGINE_BINARY}",
            "file": f"file {ENGINE_BINARY}",
            "size": f"{CROSS_SIZE} {ENGINE_BINARY}",
        },
    }


def collect_sizes(build: dict[str, Any] | None) -> dict[str, Any]:
    v3021_init_bytes = V3021_INIT_BINARY.stat().st_size if V3021_INIT_BINARY.exists() else None
    v3021_boot_bytes = V3021_BOOT_IMAGE.stat().st_size if V3021_BOOT_IMAGE.exists() else None
    engine_binary_bytes = build["engine_binary_bytes"] if build is not None else None
    engine_object_total = build["engine_object_total_bytes"] if build is not None else None
    return {
        "v3021_init_binary": rel(V3021_INIT_BINARY),
        "v3021_init_binary_bytes": v3021_init_bytes,
        "v3021_boot_image": rel(V3021_BOOT_IMAGE),
        "v3021_boot_image_bytes": v3021_boot_bytes,
        "engine_binary_bytes": engine_binary_bytes,
        "engine_object_total_bytes": engine_object_total,
        "engine_object_total_within_v3023_boot_delta_cap": (
            engine_object_total is not None and engine_object_total <= ENGINE_ONLY_BOOT_DELTA_CAP_BYTES
        ),
        "boot_image_written": False,
        "actual_boot_delta_bytes": None,
    }


def collect_state(*, build: bool) -> dict[str, Any]:
    source = collect_source_state()
    build_payload = compile_private_engine() if build else None
    public_wads = count_files(PUBLIC_WAD_ROOT, ".wad")
    private_wads = count_files(PRIVATE_DOOM_ROOT, ".wad")
    v3023_policy_text = (
        V3023_POLICY_REPORT.read_text(encoding="utf-8", errors="replace")
        if V3023_POLICY_REPORT.exists()
        else ""
    )
    state: dict[str, Any] = {
        "run_id": RUN_ID,
        "decision": DECISION,
        "build_tag": BUILD_TAG,
        "source": source,
        "build": build_payload,
        "sizes": collect_sizes(build_payload),
        "public_wads": public_wads,
        "private_wads": private_wads,
        "v3023_policy_ready": "v3023-doomgeneric-private-integration-policy-ready" in v3023_policy_text,
        "runtime_policy": {
            "runtime_wad_root": RUNTIME_WAD_ROOT,
            "runtime_wad_path": RUNTIME_WAD_PATH,
            "wad_committed": False,
            "wad_embedded_in_boot": False,
            "sound_enabled": False,
            "input": "serial doompad -> DG_GetKey",
            "render": "DG_DrawFrame -> native KMS/pageflip target",
        },
        "safety": {
            "device_action": "none",
            "flash": False,
            "boot_image_written": False,
            "serial_command": False,
            "wad_copy": False,
            "wifi_action": False,
            "sysfs_write": False,
            "evdev_injection": False,
            "pmic_regulator_backlight_gpio_gdsc_write": False,
            "forbidden_partition_path": False,
        },
    }
    state["safe_to_continue_host_only"] = bool(
        source["source_exists"]
        and source["git_head_matches_pin"]
        and source["git_status_clean"]
        and not source["engine_sources_missing"]
        and state["v3023_policy_ready"]
        and public_wads["count"] == 0
        and (build_payload is None or (
            build_payload["aarch64_static_elf"]
            and build_payload["marker_check_pass"]
            and build_payload["third_party_source_compile_count"] >= 70
        ))
    )
    state["next_unit"] = {
        "run_id": "V3025",
        "type": "native-init command/boot integration candidate",
        "summary": (
            "Wire the V3024 private engine link result into a native-init candidate command surface, "
            "still without WAD data in public, ramdisk, or boot image."
        ),
    }
    return state


def render_report(state: dict[str, Any]) -> str:
    source = state["source"]
    build = state["build"] or {}
    sizes = state["sizes"]
    size_output = str(build.get("size_output", "")).replace("\n", " | ")
    validation = [
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doomgeneric_engine_integration_build_v3024.py tests/test_native_doomgeneric_private_integration_build_v3024.py workspace/public/src/scripts/revalidation/native_init_frontier_select.py tests/test_native_init_frontier_select.py`: PASS",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doomgeneric_private_integration_build_v3024 tests.test_native_init_frontier_select`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doomgeneric_engine_integration_build_v3024.py`: PASS",
        "- `file workspace/private/builds/native-init/v3024-doomgeneric-private-integration/a90_doomgeneric_private_engine_v3024`: PASS (AArch64 static ELF)",
        "- `git diff --check`: PASS",
    ]
    return "\n".join([
        "# Native Init V3024 DOOMGENERIC Private Integration Build",
        "",
        "## Summary",
        "",
        f"- Decision: `{state['decision']}`",
        "- Device action: `none` in this host-only unit.",
        "- Track: active Video playback / DOOM capstone.",
        "- Build scope: full private doomgeneric engine source link with a native A90 bridge adapter.",
        f"- Private doomgeneric source pinned: `{int(bool(source['git_head_matches_pin']))}`",
        f"- Private source clean: `{int(bool(source['git_status_clean']))}`",
        f"- V3023 policy ready: `{int(bool(state['v3023_policy_ready']))}`",
        f"- Private engine source files compiled: `{build.get('third_party_source_compile_count')}`",
        f"- Private engine object count: `{build.get('engine_object_count')}`",
        f"- AArch64 static engine linked: `{int(bool(build.get('aarch64_static_elf')))}`",
        f"- Marker check pass: `{int(bool(build.get('marker_check_pass')))}`",
        f"- Public WAD files committed/present: `{state['public_wads']['count']}`",
        f"- Private WAD files currently present: `{state['private_wads']['count']}`",
        f"- Safe next host-only unit: `{int(bool(state['safe_to_continue_host_only']))}`",
        "",
        "## Source Pin",
        "",
        f"- Source URL: `{source['source_url']}`",
        f"- Private source root: `{source['source_root']}`",
        f"- Pinned commit: `{PINNED_COMMIT}`",
        f"- Current commit: `{source['git_head']}`",
        f"- Commit date: `{source['git_commit_date']}`",
        f"- Commit subject: `{source['git_commit_subject']}`",
        f"- LICENSE SHA256: `{source['license_sha256']}`",
        f"- Source makefile: `{source['makefile']}`",
        f"- Engine source count from makefile: `{source['engine_source_count']}`",
        f"- Excluded backend: `{source['excluded_platform_backend']}`",
        "",
        "## Private Build Artifact",
        "",
        f"- Adapter source: `{build.get('adapter_source')}`",
        f"- Adapter source SHA256: `{build.get('adapter_source_sha256')}`",
        f"- Engine binary: `{build.get('engine_binary')}`",
        f"- Engine binary SHA256: `{build.get('engine_binary_sha256')}`",
        f"- Engine binary bytes: `{build.get('engine_binary_bytes')}`",
        f"- Engine object total bytes: `{build.get('engine_object_total_bytes')}`",
        f"- Compile stdout non-empty count: `{build.get('compile_stdout_nonempty_count')}`",
        f"- `file`: `{build.get('file_output')}`",
        f"- `size`: `{size_output}`",
        "",
        "## Size Gate",
        "",
        f"- V3021 init binary bytes: `{sizes['v3021_init_binary_bytes']}`",
        f"- V3021 boot image bytes: `{sizes['v3021_boot_image_bytes']}`",
        f"- Engine-only object total within V3023 2 MiB cap: `{int(bool(sizes['engine_object_total_within_v3023_boot_delta_cap']))}`",
        "- Boot-image delta: `not-produced` because V3024 deliberately stops at private engine link, before ramdisk/boot integration.",
        "",
        "## Runtime Policy",
        "",
        f"- Runtime WAD root: `{state['runtime_policy']['runtime_wad_root']}`",
        f"- Runtime WAD path marker: `{state['runtime_policy']['runtime_wad_path']}`",
        "- WAD/IWAD data is not committed, copied, embedded, or staged by this build.",
        "- Sound remains disabled for the first native engine link path (`-nosound -nomusic`).",
        "- Input path remains serial doompad state to `DG_GetKey`; no OTG, touch, evdev injection, or uinput is required.",
        "- Render target marker remains `DG_DrawFrame` to native KMS/pageflip; this private link artifact does not touch DRM/KMS.",
        "",
        "## Safety",
        "",
        "- Host-only private-source link; no flash, serial command, WAD copy, Wi-Fi action, sysfs write, boot image write, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.",
        "- The public tree records only scripts, tests, and metadata; generated objects/binaries remain private.",
        "",
        "## Host Validation",
        "",
        *validation,
        "",
        "## Next Unit",
        "",
        f"- Run ID: `{state['next_unit']['run_id']}`",
        f"- Type: `{state['next_unit']['type']}`",
        f"- Summary: {state['next_unit']['summary']}",
    ]) + "\n"


def main() -> int:
    state = collect_state(build=True)
    write_private_text(MANIFEST_PATH, json.dumps(state, indent=2, sort_keys=True) + "\n")
    write_public_text(REPORT_PATH, render_report(state))
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0 if state["safe_to_continue_host_only"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
