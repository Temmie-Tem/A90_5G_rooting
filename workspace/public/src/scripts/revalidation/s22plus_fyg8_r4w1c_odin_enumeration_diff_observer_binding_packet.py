#!/usr/bin/env python3
"""Emit the inert R4W1-C enumeration-observer policy binding packet.

This host-only helper does not contact a device, execute Odin, or edit policy.
It pins the reviewed observer source packet and exact Odin binary, renders the
exact reviewed policy clause without importing observer code, and writes
deterministic private review artifacts for a separate binding decision.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

SCHEMA = "s22plus_fyg8_r4w1c_odin_enumeration_diff_binding_packet_v1"
TARGET = "SM-S906N/g0q/S906NKSS7FYG8"
SOURCE_CHECKPOINT_COMMIT = "5056c2cda8b74802f9802b9266cd997ca3e43341"
OBSERVER_SCRIPT_RELATIVE = Path(
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_r4w1c_odin_enumeration_diff_observer.py"
)
OBSERVER_TEST_RELATIVE = Path(
    "tests/test_s22plus_fyg8_r4w1c_odin_enumeration_diff_observer.py"
)
POLICY_DRAFT = Path(
    "docs/operations/"
    "S22PLUS_FYG8_R4W1C_ODIN_ENUMERATION_DIFF_OBSERVER_EXCEPTION_DRAFT_2026-07-20.md"
)
SCRIPT_RELATIVE = Path(
    "workspace/public/src/scripts/revalidation/"
    "s22plus_fyg8_r4w1c_odin_enumeration_diff_observer_binding_packet.py"
)
TEST_RELATIVE = Path(
    "tests/test_s22plus_fyg8_r4w1c_odin_enumeration_diff_observer_binding_packet.py"
)
OUTPUT_ROOT = Path("workspace/private/outputs")
CLAUSE_FILENAME = "AGENTS_R4W1C_ENUM_DIFF_OBSERVER_CLAUSE.md"
PACKET_FILENAME = "packet.json"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_AGENTS_BYTES = 16 * 1024 * 1024
DEFAULT_ODIN = Path("/usr/bin/odin4")
EXPECTED_ODIN_SIZE = 3_746_744
EXPECTED_ODIN_SHA256 = (
    "6754aa54f2abe6e99ece32414cd34c8b23b28dbddde537a33203036813637c3b"
)
CONSUMED_STATE = Path(
    "workspace/private/state/"
    "s22plus_fyg8_r4w1c_odin_enumeration_diff_observer_consumed.json"
)
POLICY_MARKER = "S22+ FYG8 R4W1-C Odin enumeration-diff observation gate"
ACTIVE_SENTINEL = "S22PLUS_FYG8_R4W1C_ENUM_DIFF_OBSERVER_POLICY_STATE=ACTIVE"
POLICY_BEGIN = "BEGIN_S22PLUS_FYG8_R4W1C_ENUM_DIFF_OBSERVER_POLICY_V1"
POLICY_END = "END_S22PLUS_FYG8_R4W1C_ENUM_DIFF_OBSERVER_POLICY_V1"
POLICY_HASH_PREFIX = "S22PLUS_FYG8_R4W1C_ENUM_DIFF_POLICY_CLAUSE_SHA256="
OBSERVE_ACK_TOKEN = "S22PLUS-FYG8-R4W1C-ODIN-ENUMERATION-DIFF-OBSERVE"
DOWNLOAD_CONFIRM_TOKEN = (
    "S22PLUS-FYG8-R4W1C-ODIN-ENUMERATION-DIFF-NORMAL-DOWNLOAD-CONFIRMED"
)
RECOVERY_ACK_TOKEN = (
    "S22PLUS-FYG8-R4W1C-ODIN-ENUMERATION-DIFF-RECOVER-CONSUMED-OBSERVER"
)
EXPECTED_RENDERED_CLAUSE_SIZE = 5_444
EXPECTED_RENDERED_CLAUSE_SHA256 = (
    "9f42de1cb609f9897799f82d1e59f11fd1ec24cc018da3ed9099adb1e89d497e"
)
EXPECTED_NORMALIZED_CLAUSE_SHA256 = (
    "93d8959a7df8b52574ed4d734122d5799b5f36d0077e82532feed49d75aa2677"
)

EXPECTED_SOURCE_IDENTITIES = {
    str(OBSERVER_SCRIPT_RELATIVE): {
        "size": 104_055,
        "sha256": "90707b79c67080533c9c32f9d787f254d83c11ce98471b9a7bfb1c7d15871913",
    },
    str(OBSERVER_TEST_RELATIVE): {
        "size": 87_409,
        "sha256": "510bf46191f05096d716409f29a754c928c1f332b8ada767819495235998a545",
    },
    str(POLICY_DRAFT): {
        "size": 10_848,
        "sha256": "ddcf158a40d4cf56853340c8219535038afb99e99f21b81a9b5f42f902b02c4a",
    },
}


class BindingError(RuntimeError):
    pass


@dataclasses.dataclass
class PinnedInputFile:
    path: Path
    descriptor: int
    metadata: tuple[int, ...]
    payload: bytes
    identity: dict[str, Any]

    def validate(self) -> None:
        if self.descriptor < 0:
            raise BindingError(f"pinned input is closed: {self.path}")
        before = os.fstat(self.descriptor)
        payload = _read_fd(self.descriptor, before.st_size)
        after = os.fstat(self.descriptor)
        linked = os.stat(self.path, follow_symlinks=False)
        if (
            not stat.S_ISREG(after.st_mode)
            or after.st_nlink != 1
            or _metadata_tuple(before) != self.metadata
            or _metadata_tuple(after) != self.metadata
            or (after.st_dev, after.st_ino, after.st_size)
            != (linked.st_dev, linked.st_ino, linked.st_size)
            or payload != self.payload
        ):
            raise BindingError(f"pinned input changed: {self.path}")

    def close(self) -> None:
        if self.descriptor >= 0:
            os.close(self.descriptor)
            self.descriptor = -1


@dataclasses.dataclass
class InputBundle:
    files: dict[str, PinnedInputFile]

    def validate(self) -> None:
        for pinned in self.files.values():
            pinned.validate()

    def close(self) -> None:
        for pinned in reversed(tuple(self.files.values())):
            pinned.close()
        self.files.clear()


@dataclasses.dataclass
class PinnedDirectoryChain:
    path: Path
    descriptors: list[int]
    names: list[str]
    identities: list[tuple[int, int]]

    @property
    def leaf_descriptor(self) -> int:
        if not self.descriptors:
            raise BindingError("pinned directory chain is closed")
        return self.descriptors[-1]

    @property
    def leaf_identity(self) -> tuple[int, int]:
        if not self.identities:
            raise BindingError("pinned directory chain has no identity")
        return self.identities[-1]

    def validate(self) -> None:
        if (
            not self.descriptors
            or len(self.descriptors) != len(self.names)
            or len(self.descriptors) != len(self.identities)
            or any(descriptor < 0 for descriptor in self.descriptors)
        ):
            raise BindingError("pinned directory chain is invalid or closed")
        for index, descriptor in enumerate(self.descriptors):
            metadata = os.fstat(descriptor)
            if index == 0:
                linked = os.stat("/", follow_symlinks=False)
            else:
                linked = os.stat(
                    self.names[index],
                    dir_fd=self.descriptors[index - 1],
                    follow_symlinks=False,
                )
            identity = (metadata.st_dev, metadata.st_ino)
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or not stat.S_ISDIR(linked.st_mode)
                or identity != self.identities[index]
                or (linked.st_dev, linked.st_ino) != self.identities[index]
            ):
                raise BindingError("pinned directory chain identity changed")

    def close(self) -> None:
        for descriptor in reversed(self.descriptors):
            if descriptor >= 0:
                os.close(descriptor)
        self.descriptors.clear()


@dataclasses.dataclass
class PinnedOutputFile:
    name: str
    descriptor: int
    identity: tuple[int, int]
    payload: bytes


@dataclasses.dataclass
class OutputBundle:
    prefix: Path
    chain: PinnedDirectoryChain
    files: dict[str, PinnedOutputFile] = dataclasses.field(default_factory=dict)

    def artifact_name(self, logical_name: str) -> str:
        suffixes = {
            CLAUSE_FILENAME: ".clause.md",
            PACKET_FILENAME: ".packet.json",
        }
        try:
            return f"{self.prefix.name}{suffixes[logical_name]}"
        except KeyError as exc:
            raise BindingError("binding artifact name is not permitted") from exc

    def close(self) -> None:
        for pinned in self.files.values():
            if pinned.descriptor >= 0:
                os.close(pinned.descriptor)
                pinned.descriptor = -1
        self.files.clear()
        self.chain.close()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _metadata_tuple(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_uid,
        value.st_gid,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_fd(descriptor: int, size: int) -> bytes:
    payload = bytearray()
    offset = 0
    while offset < size:
        chunk = os.pread(descriptor, min(1024 * 1024, size - offset), offset)
        if not chunk:
            break
        payload.extend(chunk)
        offset += len(chunk)
    if len(payload) != size:
        raise BindingError("short read from pinned file")
    return bytes(payload)


def open_pinned_input(path: Path, *, maximum: int, label: str) -> PinnedInputFile:
    absolute = Path(os.path.abspath(path))
    if path.is_symlink() or path.resolve() != absolute:
        raise BindingError(f"{label} is indirect")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(absolute, flags)
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size <= 0
            or before.st_size > maximum
        ):
            raise BindingError(f"{label} has an invalid file shape")
        payload = _read_fd(descriptor, before.st_size)
        after = os.fstat(descriptor)
        linked = os.stat(absolute, follow_symlinks=False)
        if (
            _metadata_tuple(before) != _metadata_tuple(after)
            or (after.st_dev, after.st_ino, after.st_size)
            != (linked.st_dev, linked.st_ino, linked.st_size)
        ):
            raise BindingError(f"{label} changed while pinning")
        pinned = PinnedInputFile(
            path=absolute,
            descriptor=descriptor,
            metadata=_metadata_tuple(after),
            payload=payload,
            identity={"size": len(payload), "sha256": sha256_bytes(payload)},
        )
        pinned.validate()
        return pinned
    except Exception:
        os.close(descriptor)
        raise


def verified_odin_identity(pinned: PinnedInputFile | None = None) -> dict[str, Any]:
    owned = pinned is None
    current = pinned or open_pinned_input(
        DEFAULT_ODIN, maximum=EXPECTED_ODIN_SIZE, label="Odin4"
    )
    try:
        reduced = {"path": str(DEFAULT_ODIN), **current.identity}
        if reduced != {
            "path": str(DEFAULT_ODIN),
            "size": EXPECTED_ODIN_SIZE,
            "sha256": EXPECTED_ODIN_SHA256,
        }:
            raise BindingError(f"Odin identity mismatch: {reduced}")
        current.validate()
        return reduced
    finally:
        if owned:
            current.close()


def rendered_policy_clause(sources: dict[str, dict[str, Any]]) -> str:
    lines = [
        POLICY_BEGIN,
        ACTIVE_SENTINEL,
        POLICY_MARKER,
        f"helper_path={OBSERVER_SCRIPT_RELATIVE}",
        f"helper_sha256={sources['observer_helper']['sha256']}",
        f"test_path={OBSERVER_TEST_RELATIVE}",
        f"test_sha256={sources['observer_test']['sha256']}",
        f"draft_path={POLICY_DRAFT}",
        f"draft_sha256={sources['inactive_draft']['sha256']}",
        f"odin_path={DEFAULT_ODIN}",
        f"odin_size={EXPECTED_ODIN_SIZE}",
        f"odin_sha256={EXPECTED_ODIN_SHA256}",
        f"observe_ack={OBSERVE_ACK_TOKEN}",
        f"download_confirm={DOWNLOAD_CONFIRM_TOKEN}",
        f"recovery_ack={RECOVERY_ACK_TOKEN}",
        "authorization=one-exact-android-baseline+one-adb-reboot-download+one-bounded-odin4-list+physical-exit+exact-android-return",
        "target=one-attended-SM-S906N+g0q+S906NKSS7FYG8+same-cable-hub-port",
        "android_baseline=boot-complete+bootanim-stopped+orange+magisk-uid0+exact-known-boot+stock-vendor_boot+stock-dtbo+stock-recovery+exact-adb-serial+usb-topology+no-download-endpoint",
        "odin_executable=open-no-follow+exact-size-sha+held-fd+execute-through-fd+same-path-inode-before-after",
        "one_shot=exclusive-durable-consume-before-adb-reboot-download-attempt+immediate-open-no-follow-pin+path-inode-sha-check-across-all-subsequent-actions-and-final-result",
        "download_endpoint=only-bound-topology+04e8:685d+SAMSUNG-USB+Samsung+serial-absent+unambiguous",
        "stabilization=SIGINT+SIGTERM+SIGHUP-masked-from-each-sample-read-through-exclusive-create-fsync+failure-or-interruption-preserves-every-collected-sample+last-stable-sample-is-immutable-pre-odin-baseline",
        "pre_odin_binding=first-complete-pre-listing-bundle-must-match-stable-topology+full-sysfs+path+all-immutable-node-fields;replacement-or-device-number-change-stops-before-odin",
        "listing=exactly-one-bounded-10s-odin4-minus-l+bounded-output+no-other-subprocess-execution-surface",
        "post_odin_order=SIGINT+SIGTERM+SIGHUP-masked-through-closure+partial-output-and-original-interruption-preserved-even-if-process-cleanup-fails+on-return+failure+timeout+output-bound+interruption:first-capture-complete-after-bundle;independently-attempt-after-bundle+command-outcome-including-cleanup-error-and-after-persist-error+raw-stdout+raw-stderr-so-one-write-failure-cannot-skip-the-others;any-write-failure-is-non-PASS;then-rehash-parse-classify;unmask-or-reraise-only-after-closure",
        "evidence=bracketed-all-download-sysfs+complete-bounded-usbfs+exact-node-stat-fields+all-races-errors+raw-output+return-timeout-truncation+parsed-paths+per-field-diff+exclusive-create+fsync",
        "odin_output=raw-strict-utf8-path-only-stdout+at-most-one-final-LF+no-blank-or-whitespace-normalization+byte-empty-stderr+exactly-one-expected-path",
        "unsafe=topology-or-descriptor-or-device-number-or-immutable-change+inventory-change+ambiguity+disappearance+capture-error+command-failure+malformed-output",
        "android_return=same-exact-serial+topology+complete-pre-run-FYG8+Magisk+partition-identities",
        "recovery=only-exact-consumed-run+pinned-open-no-follow-state-fd+path-inode-sha-check-before-and-after-every-Android-return-polling-attempt+after-preclosure-fsync+immediately-before-final-result+separate-token+no-reboot-or-odin-or-transfer+exclusive-intent-before-contact+attempt-specific-evidence+interrupted-intent-counts+maximum-two-bounded-attempts",
        "authority=whole-observation-or-recovery-session+single-writer-nonblocking-lease+pinned-lock-fd-and-path-inode+pinned-policy-helper-test-draft+checks-before-and-after-initial-Android-baseline+authority-and-consumed-pin-checks-before-and-after-adb-reboot-download+around-every-stabilization-sample+confirmation+odin-observation+Android-return-polling-attempt+after-non-PASS-preclosure-fsync+immediately-before-final-result",
        "partition_writes=false",
        "odin_transfer=false",
        "acceptance_decision=false",
        "pass=only-PASS_R4W1C_ENUM_DIFF_OBSERVER_EVIDENCE_CAPTURED-after-evidence-closure-and-exact-android-return;never-authorizes-candidate-or-second-observer",
        "timeline=only-events-name-timestamp_utc+canonical-eight-ordered-slots+zero-flash-semantics+non-PASS-preclosure-preserves-actual-prefix-before-placeholder-completion+recovery-never-relabels-placeholders+recovery-activity-uses-separate-noncanonical-result-field+result-maps-each-slot-to-reached-or-not-reached-no-action-placeholder",
        "result_closure=exclusive-non-PASS-preclosure+post-fsync-authority-and-consumed-state-validation+final-PASS-result-created-only-after-validation",
        "policy_digest_semantics=embedded-policy-clause-sha256-is-sha256-of-normalized-clause-template-containing-literal-placeholder;authority-receipt-policy-clause-sha256-is-sha256-of-final-rendered-block",
        "forbidden=candidate-ap,odin-transfer,flash,partition-write,raw-dd,fastboot,module,panic,sysrq,rdx,sboot,ramdump,qdl,sahara,firehose,eud,uart,format,cleanup,a90,boot,recovery,vendor_boot,dtbo,vbmeta,bl,cp,csc,super,userdata,persist,efs,sec_efs,rpmb,keymaster,modem,bootloader,all-other-partitions",
        f"{POLICY_HASH_PREFIX}{{{{POLICY_CLAUSE_SHA256}}}}",
        POLICY_END,
    ]
    normalized = "\n".join(lines) + "\n"
    digest = sha256_bytes(normalized.encode("utf-8"))
    return normalized.replace("{{POLICY_CLAUSE_SHA256}}", digest)


def validate_rendered_clause(
    clause: str, sources: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    if not clause.endswith("\n") or "\r" in clause:
        raise BindingError("rendered clause is not canonical LF text")
    for marker in (POLICY_BEGIN, POLICY_END, ACTIVE_SENTINEL):
        if clause.count(marker) != 1:
            raise BindingError(f"rendered clause marker count is not one: {marker}")
    if "{{" in clause or "}}" in clause:
        raise BindingError("rendered clause retains a placeholder")
    prefix = POLICY_HASH_PREFIX
    digest_lines = [line for line in clause.splitlines() if line.startswith(prefix)]
    if len(digest_lines) != 1:
        raise BindingError("rendered clause digest line is not singular")
    digest = digest_lines[0][len(prefix) :]
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise BindingError("rendered clause digest is malformed")
    normalized = clause.replace(
        f"{prefix}{digest}", f"{prefix}{{{{POLICY_CLAUSE_SHA256}}}}", 1
    )
    if sha256_bytes(normalized.encode("utf-8")) != digest:
        raise BindingError("rendered clause normalized digest mismatch")
    if clause != rendered_policy_clause(sources):
        raise BindingError("rendered clause is not the frozen canonical output")
    identity = {
        "size": len(clause.encode("utf-8")),
        "sha256": sha256_bytes(clause.encode("utf-8")),
        "embedded_normalized_template_sha256": digest,
        "active_sentinel_count": 1,
    }
    if identity != {
        "size": EXPECTED_RENDERED_CLAUSE_SIZE,
        "sha256": EXPECTED_RENDERED_CLAUSE_SHA256,
        "embedded_normalized_template_sha256": EXPECTED_NORMALIZED_CLAUSE_SHA256,
        "active_sentinel_count": 1,
    }:
        raise BindingError(f"rendered clause identity changed: {identity}")
    return identity


def _required_draft_strings() -> tuple[str, ...]:
    return (
        "DRAFT_INACTIVE",
        POLICY_MARKER,
        ACTIVE_SENTINEL,
        OBSERVE_ACK_TOKEN,
        DOWNLOAD_CONFIRM_TOKEN,
        RECOVERY_ACK_TOKEN,
        str(OBSERVER_SCRIPT_RELATIVE),
        str(OBSERVER_TEST_RELATIVE),
        "{{HELPER_SHA256}}",
        "{{TEST_SHA256}}",
        "{{POLICY_DRAFT_SHA256}}",
        "{{POLICY_CLAUSE_SHA256}}",
        EXPECTED_ODIN_SHA256,
        "odin4 -l",
        "no transfer",
    )


def open_source_inputs(root: Path) -> InputBundle:
    paths = {
        "observer_helper": (root / OBSERVER_SCRIPT_RELATIVE, MAX_SOURCE_BYTES),
        "observer_test": (root / OBSERVER_TEST_RELATIVE, MAX_SOURCE_BYTES),
        "inactive_draft": (root / POLICY_DRAFT, MAX_SOURCE_BYTES),
        "binding_generator": (root / SCRIPT_RELATIVE, MAX_SOURCE_BYTES),
        "binding_generator_test": (root / TEST_RELATIVE, MAX_SOURCE_BYTES),
        "policy_base": (root / "AGENTS.md", MAX_AGENTS_BYTES),
        "odin": (DEFAULT_ODIN, EXPECTED_ODIN_SIZE),
    }
    files: dict[str, PinnedInputFile] = {}
    try:
        for label, (path, maximum) in paths.items():
            files[label] = open_pinned_input(path, maximum=maximum, label=label)
        bundle = InputBundle(files=files)
        bundle.validate()
        return bundle
    except Exception:
        for pinned in reversed(tuple(files.values())):
            pinned.close()
        raise


def qualify_source_snapshot(root: Path, inputs: InputBundle) -> dict[str, Any]:
    inputs.validate()
    sources: dict[str, dict[str, Any]] = {}
    for label, relative in (
        ("observer_helper", OBSERVER_SCRIPT_RELATIVE),
        ("observer_test", OBSERVER_TEST_RELATIVE),
        ("inactive_draft", POLICY_DRAFT),
    ):
        identity = inputs.files[label].identity
        if identity != EXPECTED_SOURCE_IDENTITIES[str(relative)]:
            raise BindingError(f"reviewed source identity changed: {relative}: {identity}")
        sources[label] = {"path": str(relative), **identity}

    try:
        agents_text = inputs.files["policy_base"].payload.decode("utf-8")
        draft_text = inputs.files["inactive_draft"].payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BindingError("binding text input is not UTF-8") from exc
    marker_counts = {
        "begin": agents_text.count(POLICY_BEGIN),
        "end": agents_text.count(POLICY_END),
        "active": agents_text.count(ACTIVE_SENTINEL),
    }
    if marker_counts != {"begin": 0, "end": 0, "active": 0}:
        raise BindingError(f"observer policy residue already exists: {marker_counts}")
    missing = [item for item in _required_draft_strings() if item not in draft_text]
    if missing:
        raise BindingError(f"observer policy draft mismatch: {missing}")
    consumed = root / CONSUMED_STATE
    if consumed.exists() or consumed.is_symlink():
        raise BindingError("observer one-shot state already exists")
    odin = verified_odin_identity(inputs.files["odin"])
    clause = rendered_policy_clause(sources)
    clause_identity = validate_rendered_clause(clause, sources)
    inputs.validate()
    return {
        "reviewed_source_checkpoint_commit": SOURCE_CHECKPOINT_COMMIT,
        "reviewed_sources": sources,
        "binding_generator": {
            "path": str(SCRIPT_RELATIVE),
            **inputs.files["binding_generator"].identity,
        },
        "binding_generator_test": {
            "path": str(TEST_RELATIVE),
            **inputs.files["binding_generator_test"].identity,
        },
        "policy_base": {
            "path": "AGENTS.md",
            **inputs.files["policy_base"].identity,
            "observer_marker_counts": marker_counts,
            "observer_policy_active": False,
        },
        "odin": odin,
        "rendered_clause": clause_identity,
        "observer_consumed": False,
    }


def source_gate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    inputs = open_source_inputs(root)
    try:
        return qualify_source_snapshot(root, inputs)
    finally:
        inputs.close()


def deterministic_packet(
    gate: dict[str, Any], *, rendered_clause_file: str
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "mode": "emit-binding",
        "target": TARGET,
        "binding": gate,
        "rendered_clause_file": rendered_clause_file,
        "policy_edited": False,
        "policy_active": False,
        "observer_consumed": False,
        "device_contact": False,
        "device_writes": False,
        "reboot": False,
        "download_transition": False,
        "odin_execution": False,
        "odin_enumeration": False,
        "odin_transfer": False,
        "flash": False,
        "partition_writes": False,
        "acceptance_decision": False,
        "verdict": "PENDING_R4W1C_ENUM_DIFF_OBSERVER_INDEPENDENT_BINDING_REVIEW",
    }


def open_pinned_directory_chain(path: Path) -> PinnedDirectoryChain:
    absolute = Path(os.path.abspath(path))
    if not absolute.is_absolute() or not absolute.parts or absolute.parts[0] != "/":
        raise BindingError("pinned directory path is not canonical absolute")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptors: list[int] = []
    names: list[str] = []
    identities: list[tuple[int, int]] = []
    try:
        root_descriptor = os.open("/", flags)
        descriptors.append(root_descriptor)
        names.append("/")
        root_metadata = os.fstat(root_descriptor)
        identities.append((root_metadata.st_dev, root_metadata.st_ino))
        for component in absolute.parts[1:]:
            descriptor = os.open(component, flags, dir_fd=descriptors[-1])
            descriptors.append(descriptor)
            names.append(component)
            metadata = os.fstat(descriptor)
            identities.append((metadata.st_dev, metadata.st_ino))
        chain = PinnedDirectoryChain(
            path=absolute,
            descriptors=descriptors,
            names=names,
            identities=identities,
        )
        chain.validate()
        return chain
    except OSError as exc:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise BindingError(f"cannot pin directory chain: {absolute}") from exc
    except Exception:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise


def require_output_pin(output: OutputBundle) -> None:
    output.chain.validate()
    for pinned in output.files.values():
        if pinned.descriptor < 0:
            raise BindingError("binding output descriptor is closed")
        before = os.fstat(pinned.descriptor)
        payload = _read_fd(pinned.descriptor, before.st_size)
        descriptor_metadata = os.fstat(pinned.descriptor)
        path_metadata = os.stat(
            pinned.name,
            dir_fd=output.chain.leaf_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(descriptor_metadata.st_mode)
            or not stat.S_ISREG(path_metadata.st_mode)
            or descriptor_metadata.st_nlink != 1
            or path_metadata.st_nlink != 1
            or (descriptor_metadata.st_dev, descriptor_metadata.st_ino)
            != pinned.identity
            or (path_metadata.st_dev, path_metadata.st_ino) != pinned.identity
            or descriptor_metadata.st_size != len(pinned.payload)
            or path_metadata.st_size != len(pinned.payload)
            or _metadata_tuple(before) != _metadata_tuple(descriptor_metadata)
            or payload != pinned.payload
        ):
            raise BindingError("binding output artifact identity or bytes changed")


def durable_create_bytes(output: OutputBundle, name: str, payload: bytes) -> None:
    if name not in {CLAUSE_FILENAME, PACKET_FILENAME}:
        raise BindingError("binding artifact name is not permitted")
    if name in output.files:
        raise BindingError("binding artifact was already created")
    require_output_pin(output)
    artifact_name = output.artifact_name(name)
    try:
        descriptor = os.open(
            artifact_name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=output.chain.leaf_descriptor,
        )
    except FileExistsError as exc:
        raise BindingError(f"binding artifact already exists: {artifact_name}") from exc
    try:
        created = os.fstat(descriptor)
        identity = (created.st_dev, created.st_ino)
        if not stat.S_ISREG(created.st_mode) or created.st_nlink != 1:
            raise BindingError(f"exclusive binding artifact has invalid shape: {artifact_name}")
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise BindingError(f"short write while creating {name}")
            offset += written
        os.fsync(descriptor)
        completed = os.fstat(descriptor)
        if (
            (completed.st_dev, completed.st_ino) != identity
            or completed.st_size != len(payload)
            or completed.st_nlink != 1
        ):
            raise BindingError(f"binding artifact changed while creating: {artifact_name}")
        output.files[name] = PinnedOutputFile(
            name=artifact_name,
            descriptor=descriptor,
            identity=identity,
            payload=payload,
        )
        os.fsync(output.chain.leaf_descriptor)
        require_output_pin(output)
    except Exception:
        if name not in output.files:
            os.close(descriptor)
        raise


def stable_output_file(
    output: OutputBundle, name: str, *, maximum: int, label: str
) -> tuple[bytes, dict[str, Any]]:
    if name not in {CLAUSE_FILENAME, PACKET_FILENAME}:
        raise BindingError("binding artifact name is not permitted")
    require_output_pin(output)
    try:
        pinned = output.files[name]
    except KeyError as exc:
        raise BindingError(f"{label} was not created by this invocation") from exc
    descriptor = pinned.descriptor
    before = os.fstat(descriptor)
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or before.st_size <= 0
        or before.st_size > maximum
    ):
        raise BindingError(f"{label} has an invalid file shape")
    payload = bytearray()
    offset = 0
    while offset < before.st_size:
        chunk = os.pread(
            descriptor, min(1024 * 1024, before.st_size - offset), offset
        )
        if not chunk:
            break
        payload.extend(chunk)
        offset += len(chunk)
    after = os.fstat(descriptor)
    path_after = os.stat(
        pinned.name,
        dir_fd=output.chain.leaf_descriptor,
        follow_symlinks=False,
    )
    if (
        len(payload) != before.st_size
        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        or (after.st_dev, after.st_ino, after.st_size)
        != (path_after.st_dev, path_after.st_ino, path_after.st_size)
    ):
        raise BindingError(f"{label} changed while reopening")
    require_output_pin(output)
    data = bytes(payload)
    return data, {"size": len(data), "sha256": sha256_bytes(data)}


def allocate_output(
    root: Path, requested: Path | None, helper_sha256: str
) -> OutputBundle:
    absolute_root = Path(os.path.abspath(root))
    base_path = absolute_root / OUTPUT_ROOT
    relative = requested or OUTPUT_ROOT / f"s22plus-r4w1c-enum-diff-binding-{helper_sha256[:12]}"
    if relative.is_absolute() or ".." in relative.parts:
        raise BindingError("binding output must be a contained relative path")
    if relative.parent != OUTPUT_ROOT or not relative.name:
        raise BindingError("binding output prefix must be a direct child of the private output root")
    candidate = absolute_root / relative
    chain = open_pinned_directory_chain(base_path)
    try:
        chain.validate()
        output = OutputBundle(prefix=candidate, chain=chain)
        require_output_pin(output)
        return output
    except Exception:
        chain.close()
        raise


def emit_binding(root: Path, requested: Path | None) -> dict[str, Any]:
    root = root.resolve()
    inputs = open_source_inputs(root)
    output: OutputBundle | None = None
    try:
        before = qualify_source_snapshot(root, inputs)
        output = allocate_output(
            root, requested, before["reviewed_sources"]["observer_helper"]["sha256"]
        )
        clause_text = rendered_policy_clause(before["reviewed_sources"])
        clause_identity_before_write = validate_rendered_clause(
            clause_text, before["reviewed_sources"]
        )
        if clause_identity_before_write != before["rendered_clause"]:
            raise BindingError("rendered clause differs from the frozen source snapshot")
        clause = clause_text.encode("utf-8")
        packet = deterministic_packet(
            before,
            rendered_clause_file=output.artifact_name(CLAUSE_FILENAME),
        )
        packet_bytes = (json.dumps(packet, indent=2, sort_keys=True) + "\n").encode("utf-8")
        durable_create_bytes(output, CLAUSE_FILENAME, clause)
        durable_create_bytes(output, PACKET_FILENAME, packet_bytes)
        after = qualify_source_snapshot(root, inputs)
        if after != before:
            raise BindingError("binding inputs changed during packet emission")
        clause_payload, clause_identity = stable_output_file(
            output, CLAUSE_FILENAME, maximum=MAX_SOURCE_BYTES, label="rendered clause artifact"
        )
        packet_payload, packet_identity = stable_output_file(
            output, PACKET_FILENAME, maximum=MAX_SOURCE_BYTES, label="binding packet artifact"
        )
        if clause_payload != clause or packet_payload != packet_bytes:
            raise BindingError("binding artifacts differ from deterministic payloads")
        inputs.validate()
        if qualify_source_snapshot(root, inputs) != before:
            raise BindingError("binding inputs changed before artifact closure")
        require_output_pin(output)
        absolute_root = Path(os.path.abspath(root))
        return {
            "output_prefix": str(output.prefix.relative_to(absolute_root)),
            "clause": {
                "path": str(OUTPUT_ROOT / output.artifact_name(CLAUSE_FILENAME)),
                **clause_identity,
            },
            "packet": {
                "path": str(OUTPUT_ROOT / output.artifact_name(PACKET_FILENAME)),
                **packet_identity,
            },
            **packet,
            "packet_verdict": packet["verdict"],
            "verdict": "PASS_R4W1C_ENUM_DIFF_OBSERVER_BINDING_PACKET_EMITTED_HOST_ONLY",
        }
    finally:
        if output is not None:
            output.close()
        inputs.close()


def offline_check(root: Path) -> dict[str, Any]:
    gate = source_gate(root)
    return {
        "schema": SCHEMA,
        "mode": "offline-check",
        "target": TARGET,
        "binding": gate,
        "policy_active": False,
        "observer_consumed": False,
        "device_contact": False,
        "device_writes": False,
        "reboot": False,
        "download_transition": False,
        "odin_execution": False,
        "odin_enumeration": False,
        "odin_transfer": False,
        "flash": False,
        "partition_writes": False,
        "acceptance_decision": False,
        "verdict": "PASS_R4W1C_ENUM_DIFF_OBSERVER_BINDING_SOURCE_OFFLINE_CHECK",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--offline-check", action="store_true")
    modes.add_argument("--emit-binding", action="store_true")
    parser.add_argument("--out-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root()
    try:
        if args.offline_check:
            if args.out_dir is not None:
                raise BindingError("offline check does not accept --out-dir")
            result = offline_check(root)
        else:
            result = emit_binding(root, args.out_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (BindingError, OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"schema": SCHEMA, "verdict": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
