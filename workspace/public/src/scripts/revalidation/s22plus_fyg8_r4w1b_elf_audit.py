#!/usr/bin/env python3
"""Inspect the final R4W1-B AArch64 ELF without third-party Python modules."""

from __future__ import annotations

import hashlib
import hmac
import mmap
import struct
from pathlib import Path
from typing import Any, Iterator


ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
SECTION_HEADER = struct.Struct("<IIQQQQIIQQ")
SYMBOL = struct.Struct("<IBBHQQ")
EM_AARCH64 = 183
PT_LOAD = 1
PF_X = 1
SHT_SYMTAB = 2
FIPS_HMAC_KEY = b"The quick brown fox jumps over the lazy dog"
FIPS_EXPECTED_RANGE_COUNT = 499
FIPS_EXPECTED_COVERED_BYTES = 304_460
SEC_LOG_PHYS_ADDR = 0x800200000
SEC_LOG_MAGIC = 0x4D474F4C
SEC_LOG_PAYLOAD_SIZE = 0x1FFFF0
EXPECTED_KERNEL_INIT_SHA256 = (
    "dacddb3286920baf4fc3881911fea99be2f01abcf99cf199bf6e91955d3738c3"
)
EXPECTED_RUN_INIT_PROCESS_SHA256 = (
    "3bed76ded7dd2b461ea1ea2ffb7365672384757de9bd6d9de50b95d09dc0337f"
)
EXPECTED_STRCMP_SIZE = 344
EXPECTED_STRCMP_SHA256 = (
    "ee7736b5b9ab9addfba6ae9be89efb527de0d10c38f5553069270a9b2529408e"
)
EXPECTED_MEMCPY_SIZE = 340
EXPECTED_MEMCPY_SHA256 = (
    "492177dbeca5809af54bb91670982a373a753a840e65ab58e0c46a25e6562802"
)


class ElfAuditError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sign_extend(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def branch_target(pc: int, word: int) -> int | None:
    if word & 0xFC000000 not in (0x14000000, 0x94000000):
        return None
    return pc + sign_extend((word & 0x03FFFFFF) << 2, 28)


def compare_branch(word: int) -> dict[str, int] | None:
    if word & 0x7E000000 != 0x34000000:
        return None
    return {
        "nonzero": (word >> 24) & 1,
        "register": word & 0x1F,
        "target_delta": sign_extend((word >> 5) & 0x7FFFF, 19) << 2,
    }


def conditional_branch(word: int) -> dict[str, int] | None:
    if word & 0xFF000010 != 0x54000000:
        return None
    return {
        "condition": word & 0xF,
        "target_delta": sign_extend((word >> 5) & 0x7FFFF, 19) << 2,
    }


def test_branch(word: int) -> dict[str, int] | None:
    if word & 0x7E000000 != 0x36000000:
        return None
    return {
        "nonzero": (word >> 24) & 1,
        "register": word & 0x1F,
        "bit": ((word >> 19) & 0x1F) | (((word >> 31) & 1) << 5),
        "target_delta": sign_extend((word >> 5) & 0x3FFF, 14) << 2,
    }


def direct_control_target(pc: int, word: int) -> int | None:
    target = branch_target(pc, word)
    if target is not None:
        return target
    for decoded in (compare_branch(word), conditional_branch(word), test_branch(word)):
        if decoded is not None:
            return pc + decoded["target_delta"]
    return None


def adrp_target(pc: int, word: int) -> tuple[int, int] | None:
    if word & 0x9F000000 != 0x90000000:
        return None
    immediate = sign_extend(
        (((word >> 5) & 0x7FFFF) << 2) | ((word >> 29) & 0x3),
        21,
    )
    return word & 0x1F, (pc & ~0xFFF) + (immediate << 12)


def add_immediate(word: int) -> dict[str, int] | None:
    if word & 0xFF000000 != 0x91000000:
        return None
    shift = 12 if (word >> 22) & 1 else 0
    return {
        "destination": word & 0x1F,
        "source": (word >> 5) & 0x1F,
        "immediate": ((word >> 10) & 0xFFF) << shift,
    }


def compare_w_immediate(word: int) -> dict[str, int] | None:
    if word & 0x7F00001F != 0x7100001F:
        return None
    shift = 12 if (word >> 22) & 1 else 0
    return {
        "register": (word >> 5) & 0x1F,
        "immediate": ((word >> 10) & 0xFFF) << shift,
    }


def is_mrs_sp_el0(word: int) -> bool:
    return word & 0xFFFFFFE0 == 0xD5384100


def load_unsigned(word: int) -> dict[str, int] | None:
    kind = word & 0xFFC00000
    if kind == 0xF9400000:
        scale = 8
        width = 64
    elif kind == 0xB9400000:
        scale = 4
        width = 32
    else:
        return None
    return {
        "destination": word & 0x1F,
        "base": (word >> 5) & 0x1F,
        "offset": ((word >> 10) & 0xFFF) * scale,
        "width": width,
    }


def store_w_unsigned(word: int) -> dict[str, int] | None:
    if word & 0xFFC00000 != 0xB9000000:
        return None
    return {
        "source": word & 0x1F,
        "base": (word >> 5) & 0x1F,
        "offset": ((word >> 10) & 0xFFF) * 4,
    }


def move_register(word: int, *, width: int = 64) -> dict[str, int] | None:
    expected = 0xAA0003E0 if width == 64 else 0x2A0003E0
    mask = 0xFFE0FFE0 if width == 64 else 0x7FE0FFE0
    if word & mask != expected:
        return None
    return {
        "destination": word & 0x1F,
        "source": (word >> 16) & 0x1F,
        "width": width,
    }


def add_w_immediate(word: int) -> dict[str, int] | None:
    if word & 0xFF000000 != 0x11000000:
        return None
    shift = 12 if (word >> 22) & 1 else 0
    return {
        "destination": word & 0x1F,
        "source": (word >> 5) & 0x1F,
        "immediate": ((word >> 10) & 0xFFF) << shift,
    }


def sub_register(word: int, *, width: int = 64) -> dict[str, int] | None:
    expected = 0xCB000000 if width == 64 else 0x4B000000
    if word & 0xFFE0FC00 != expected:
        return None
    return {
        "destination": word & 0x1F,
        "left": (word >> 5) & 0x1F,
        "right": (word >> 16) & 0x1F,
        "width": width,
    }


def add_register(word: int) -> dict[str, int] | None:
    if word & 0xFFE0FC00 != 0x8B000000:
        return None
    return {
        "destination": word & 0x1F,
        "left": (word >> 5) & 0x1F,
        "right": (word >> 16) & 0x1F,
    }


def csel_register(word: int) -> dict[str, int] | None:
    if word & 0xFFE00C00 != 0x9A800000:
        return None
    return {
        "destination": word & 0x1F,
        "left": (word >> 5) & 0x1F,
        "right": (word >> 16) & 0x1F,
        "condition": (word >> 12) & 0xF,
    }


def instruction_writes_register(word: int, register: int) -> bool:
    branch = word & 0xFC000000
    if branch in (0x14000000, 0x94000000):
        return register == 30 and branch == 0x94000000
    if (
        compare_branch(word) is not None
        or conditional_branch(word) is not None
        or test_branch(word) is not None
        or compare_w_immediate(word) is not None
        or store_w_unsigned(word) is not None
        or is_return(word)
        or is_indirect_control_transfer(word)
        or is_dmb_ishst(word)
        or word in {0xD503201F, 0xD5033F9F, 0xD5033BBF, 0xD5033FDF}
    ):
        return False
    writers = [
        adrp_target(0, word),
        add_immediate(word),
        add_w_immediate(word),
        add_register(word),
        sub_register(word),
        sub_register(word, width=32),
        csel_register(word),
        load_unsigned(word),
        move_register(word),
        move_register(word, width=32),
    ]
    for decoded in writers:
        if decoded is None:
            continue
        destination = decoded[0] if isinstance(decoded, tuple) else decoded["destination"]
        return destination == register
    if is_mrs_sp_el0(word):
        return word & 0x1F == register
    # Unknown data-processing instructions are treated as writes when their
    # architectural destination field names the tracked register.
    return word & 0x1F == register


def is_return(word: int) -> bool:
    return word & 0xFFFFFC1F == 0xD65F0000


def is_indirect_control_transfer(word: int) -> bool:
    return word & 0xFFFFFC1F in {
        0xD61F0000,  # BR
        0xD63F0000,  # BLR
        0xD69F0000,  # ERET and related exception returns
    }


def is_dmb_ishst(word: int) -> bool:
    return word == 0xD5033ABF


class Elf64:
    def __init__(self, path: Path):
        self.path = path
        self.file = path.open("rb")
        self.data = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        if len(self.data) < ELF_HEADER.size:
            raise ElfAuditError("ELF is shorter than its header")
        fields = ELF_HEADER.unpack_from(self.data)
        ident = fields[0]
        if ident[:4] != b"\x7fELF" or ident[4] != 2 or ident[5] != 1:
            raise ElfAuditError("expected ELF64 little-endian input")
        if fields[2] != EM_AARCH64:
            raise ElfAuditError(f"expected AArch64 ELF, machine={fields[2]}")
        self.program_offset = fields[5]
        self.section_offset = fields[6]
        self.program_entry_size = fields[9]
        self.program_count = fields[10]
        self.section_entry_size = fields[11]
        self.section_count = fields[12]
        self.section_name_index = fields[13]
        if self.program_entry_size != PROGRAM_HEADER.size:
            raise ElfAuditError("unexpected ELF program-header size")
        if self.section_entry_size != SECTION_HEADER.size:
            raise ElfAuditError("unexpected ELF section-header size")
        self.programs = self._read_programs()
        self.sections = self._read_sections()

    def close(self) -> None:
        self.data.close()
        self.file.close()

    def __enter__(self) -> "Elf64":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _bounded(self, offset: int, size: int, label: str) -> None:
        if offset < 0 or size < 0 or offset + size > len(self.data):
            raise ElfAuditError(f"{label} exceeds ELF bounds")

    def _read_programs(self) -> list[dict[str, int]]:
        rows = []
        for index in range(self.program_count):
            offset = self.program_offset + index * self.program_entry_size
            self._bounded(offset, PROGRAM_HEADER.size, "program header")
            row = PROGRAM_HEADER.unpack_from(self.data, offset)
            rows.append(
                {
                    "type": row[0],
                    "flags": row[1],
                    "offset": row[2],
                    "vaddr": row[3],
                    "file_size": row[5],
                    "memory_size": row[6],
                }
            )
        return rows

    def _read_sections(self) -> list[dict[str, int]]:
        raw = []
        for index in range(self.section_count):
            offset = self.section_offset + index * self.section_entry_size
            self._bounded(offset, SECTION_HEADER.size, "section header")
            row = SECTION_HEADER.unpack_from(self.data, offset)
            raw.append(
                {
                    "name_offset": row[0],
                    "type": row[1],
                    "address": row[3],
                    "offset": row[4],
                    "size": row[5],
                    "link": row[6],
                    "entry_size": row[9],
                }
            )
        if self.section_name_index >= len(raw):
            raise ElfAuditError("invalid section-name table index")
        names = raw[self.section_name_index]
        for row in raw:
            row["name"] = self.cstring(
                names["offset"] + row["name_offset"], names["offset"] + names["size"]
            )
        return raw

    def cstring(self, offset: int, limit: int) -> str:
        self._bounded(offset, 0, "string offset")
        end = self.data.find(b"\0", offset, min(limit, len(self.data)))
        if end < 0:
            raise ElfAuditError("unterminated ELF string")
        return self.data[offset:end].decode("utf-8", errors="strict")

    def symbols(self, requested: set[str]) -> dict[str, dict[str, int | str]]:
        matches: dict[str, list[dict[str, int | str]]] = {
            name: [] for name in requested
        }
        for section in self.sections:
            if section["type"] != SHT_SYMTAB:
                continue
            if section["entry_size"] != SYMBOL.size or section["link"] >= len(
                self.sections
            ):
                raise ElfAuditError("invalid ELF symbol table")
            strings = self.sections[section["link"]]
            count = section["size"] // SYMBOL.size
            for index in range(count):
                offset = section["offset"] + index * SYMBOL.size
                self._bounded(offset, SYMBOL.size, "symbol table")
                name_offset, info, other, section_index, value, size = SYMBOL.unpack_from(
                    self.data, offset
                )
                if not name_offset:
                    continue
                name = self.cstring(
                    strings["offset"] + name_offset,
                    strings["offset"] + strings["size"],
                )
                if name in matches and section_index != 0:
                    matches[name].append(
                        {
                            "name": name,
                            "value": value,
                            "size": size,
                            "section_index": section_index,
                            "info": info,
                            "other": other,
                        }
                    )
        result: dict[str, dict[str, int | str]] = {}
        for name, rows in matches.items():
            concrete = [row for row in rows if row["value"] and row["size"]]
            if len(concrete) != 1:
                raise ElfAuditError(
                    f"expected one concrete symbol {name}, found {len(concrete)}"
                )
            result[name] = concrete[0]
        return result

    def symbol_bytes(self, symbol: dict[str, int | str]) -> bytes:
        offset = self.symbol_file_offset(symbol)
        return self.data[offset : offset + int(symbol["size"])]

    def symbol_file_offset(self, symbol: dict[str, int | str]) -> int:
        section_index = int(symbol["section_index"])
        if section_index >= len(self.sections):
            raise ElfAuditError(f"symbol {symbol['name']} has invalid section")
        section = self.sections[section_index]
        delta = int(symbol["value"]) - section["address"]
        if delta < 0 or delta + int(symbol["size"]) > section["size"]:
            raise ElfAuditError(f"symbol {symbol['name']} exceeds its section")
        section_offset = section["offset"] + delta
        size = int(symbol["size"])
        self._bounded(section_offset, size, f"symbol {symbol['name']} section")
        start = int(symbol["value"])
        end = start + size
        matches = [
            row
            for row in self.programs
            if row["type"] == PT_LOAD
            and row["vaddr"] <= start
            and end <= row["vaddr"] + row["file_size"]
        ]
        if len(matches) != 1:
            raise ElfAuditError(
                f"symbol {symbol['name']} maps to {len(matches)} file-backed PT_LOAD segments"
            )
        segment = matches[0]
        load_offset = segment["offset"] + start - segment["vaddr"]
        self._bounded(load_offset, size, f"symbol {symbol['name']} PT_LOAD")
        if section_offset != load_offset:
            raise ElfAuditError(
                f"symbol {symbol['name']} section/PT_LOAD mapping is incongruent"
            )
        return load_offset

    def file_offset_to_vaddr(self, offset: int) -> int:
        matches = [
            row
            for row in self.programs
            if row["type"] == PT_LOAD
            and row["offset"] <= offset < row["offset"] + row["file_size"]
        ]
        if len(matches) != 1:
            raise ElfAuditError(
                f"file offset {offset:#x} maps to {len(matches)} PT_LOAD segments"
            )
        row = matches[0]
        return row["vaddr"] + offset - row["offset"]

    def mapped_file_offset_to_vaddr(self, offset: int) -> int | None:
        matches = [
            row
            for row in self.programs
            if row["type"] == PT_LOAD
            and row["offset"] <= offset < row["offset"] + row["file_size"]
        ]
        if not matches:
            return None
        if len(matches) != 1:
            raise ElfAuditError(
                f"file offset {offset:#x} maps to multiple PT_LOAD segments"
            )
        row = matches[0]
        return row["vaddr"] + offset - row["offset"]

    def vaddr_range_bytes(self, start: int, end: int) -> bytes:
        if start >= end:
            raise ElfAuditError(f"invalid virtual address range {start:#x}..{end:#x}")
        matches = [
            row
            for row in self.programs
            if row["type"] == PT_LOAD
            and row["vaddr"] <= start
            and end <= row["vaddr"] + row["file_size"]
        ]
        if len(matches) != 1:
            raise ElfAuditError(
                f"virtual range {start:#x}..{end:#x} maps to {len(matches)} segments"
            )
        row = matches[0]
        offset = row["offset"] + start - row["vaddr"]
        size = end - start
        self._bounded(offset, size, "virtual address range")
        return self.data[offset : offset + size]

    def load_base(self) -> int:
        loads = [row["vaddr"] for row in self.programs if row["type"] == PT_LOAD]
        if not loads:
            raise ElfAuditError("ELF has no PT_LOAD segment")
        return min(loads)

    def executable_words(self) -> Iterator[tuple[int, int]]:
        for row in self.programs:
            if row["type"] != PT_LOAD or not row["flags"] & PF_X:
                continue
            if row["offset"] % 4 or row["vaddr"] % 4 or row["file_size"] % 4:
                raise ElfAuditError("executable PT_LOAD is not instruction-aligned")
            self._bounded(row["offset"], row["file_size"], "executable PT_LOAD")
            for delta in range(0, row["file_size"], 4):
                yield (
                    row["vaddr"] + delta,
                    struct.unpack_from("<I", self.data, row["offset"] + delta)[0],
                )

    def load_segment_manifest(self) -> list[dict[str, int | str]]:
        base = self.load_base()
        result: list[dict[str, int | str]] = []
        for index, row in enumerate(self.programs):
            if row["type"] != PT_LOAD or not row["file_size"]:
                continue
            self._bounded(row["offset"], row["file_size"], "file-backed PT_LOAD")
            data = self.data[row["offset"] : row["offset"] + row["file_size"]]
            result.append(
                {
                    "program_index": index,
                    "flags": row["flags"],
                    "file_offset": row["offset"],
                    "vaddr": row["vaddr"],
                    "file_size": row["file_size"],
                    "memory_size": row["memory_size"],
                    "image_offset": row["vaddr"] - base,
                    "sha256": sha256_bytes(data),
                }
            )
        return result

    def find_all(self, needle: bytes) -> list[int]:
        offsets = []
        cursor = 0
        while True:
            cursor = self.data.find(needle, cursor)
            if cursor < 0:
                return offsets
            offsets.append(cursor)
            cursor += 1


def iter_words(code: bytes, start: int) -> Iterator[tuple[int, int, int]]:
    if len(code) % 4:
        raise ElfAuditError("AArch64 function size is not instruction-aligned")
    for index in range(0, len(code), 4):
        yield index // 4, start + index, struct.unpack_from("<I", code, index)[0]


def adrp_add_references(
    instructions: list[tuple[int, int, int]], targets: set[int]
) -> list[dict[str, int]]:
    references = []
    successors, _ = build_cfg(instructions)
    for left in instructions:
        _, pc, first = left
        page = adrp_target(pc, first)
        if page is None:
            continue
        register, base = page
        pending = list(successors[left[0]])
        seen: set[int] = set()
        while pending:
            index = pending.pop()
            if index in seen:
                continue
            seen.add(index)
            right = instructions[index]
            add = add_immediate(right[2])
            if (
                add is not None
                and add["destination"] == register
                and add["source"] == register
            ):
                target = base + add["immediate"]
                if target in targets:
                    references.append(
                        {
                            "index": left[0],
                            "pc": pc,
                            "register": register,
                            "consumer_index": right[0],
                            "consumer_pc": right[1],
                            "target": target,
                        }
                    )
                continue
            if instruction_writes_register(right[2], register):
                continue
            pending.extend(successors[index] - seen)
    return references


def adrp_load_references(
    instructions: list[tuple[int, int, int]], targets: set[int]
) -> list[dict[str, int]]:
    references = []
    successors, _ = build_cfg(instructions)
    for left in instructions:
        _, pc, first = left
        page = adrp_target(pc, first)
        if page is None:
            continue
        register, base = page
        pending = list(successors[left[0]])
        seen: set[int] = set()
        while pending:
            index = pending.pop()
            if index in seen:
                continue
            seen.add(index)
            right = instructions[index]
            load = load_unsigned(right[2])
            if load is not None and load["base"] == register:
                target = base + load["offset"]
                if target in targets:
                    references.append(
                        {
                            "index": right[0],
                            "pc": right[1],
                            "producer_index": left[0],
                            "producer_pc": pc,
                            "base_register": register,
                            "destination": load["destination"],
                            "offset": load["offset"],
                            "width": load["width"],
                            "target": target,
                        }
                    )
                if load["destination"] == register:
                    continue
            if instruction_writes_register(right[2], register):
                continue
            pending.extend(successors[index] - seen)
    return references


def instruction_successors(
    instructions: list[tuple[int, int, int]], index: int
) -> set[int]:
    _, pc, word = instructions[index]
    address_to_index = {row[1]: row[0] for row in instructions}
    next_index = index + 1 if index + 1 < len(instructions) else None
    if is_return(word):
        return set()
    if is_indirect_control_transfer(word):
        return set()
    if word & 0xFC000000 == 0x14000000:
        target = branch_target(pc, word)
        return {address_to_index[target]} if target in address_to_index else set()
    compare = compare_branch(word)
    condition = conditional_branch(word)
    tested = test_branch(word)
    if compare is not None:
        target = pc + compare["target_delta"]
    elif condition is not None:
        target = pc + condition["target_delta"]
    elif tested is not None:
        target = pc + tested["target_delta"]
    else:
        return {next_index} if next_index is not None else set()
    result = {address_to_index[target]} if target in address_to_index else set()
    if next_index is not None:
        result.add(next_index)
    return result


def build_cfg(
    instructions: list[tuple[int, int, int]],
) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
    successors = {
        row[0]: instruction_successors(instructions, row[0]) for row in instructions
    }
    predecessors = {row[0]: set() for row in instructions}
    for source, targets in successors.items():
        for target in targets:
            predecessors[target].add(source)
    return successors, predecessors


def is_reachable(successors: dict[int, set[int]], start: int, target: int) -> bool:
    pending = [start]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current in seen:
            continue
        seen.add(current)
        pending.extend(successors.get(current, set()) - seen)
    return False


def is_reachable_within(
    successors: dict[int, set[int]],
    start: int,
    target: int,
    *,
    minimum: int,
    maximum: int,
) -> bool:
    if not (minimum <= start <= maximum and minimum <= target <= maximum):
        return False
    pending = [start]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current in seen or not minimum <= current <= maximum:
            continue
        seen.add(current)
        pending.extend(
            candidate
            for candidate in successors.get(current, set())
            if candidate not in seen and minimum <= candidate <= maximum
        )
    return False


def direct_ingress_to_range(
    elf: Elf64,
    *,
    target_start: int,
    target_end: int,
) -> list[dict[str, int]]:
    ingress: list[dict[str, int]] = []
    for pc, word in elf.executable_words():
        target = direct_control_target(pc, word)
        if target is None or not target_start <= target < target_end:
            continue
        ingress.append({"source_pc": pc, "target_pc": target, "word": word})
    return ingress


def parse_fips_address_table(
    elf: Elf64, table: bytes
) -> tuple[list[tuple[int, int]], bytes]:
    if len(table) != 65536 or len(table) % 16:
        raise ElfAuditError("FIPS address table has unexpected size")
    ranges: list[tuple[int, int]] = []
    terminated = False
    digest = hmac.new(FIPS_HMAC_KEY, digestmod=hashlib.sha256)
    previous_end = 0
    for offset in range(0, len(table), 16):
        start, end = struct.unpack_from("<QQ", table, offset)
        if start == 0:
            if end != 0 or any(table[offset:]):
                raise ElfAuditError("FIPS address table has nonzero data after terminator")
            terminated = True
            break
        if terminated or end <= start or start < previous_end:
            raise ElfAuditError("FIPS address table is unsorted or malformed")
        digest.update(elf.vaddr_range_bytes(start, end))
        ranges.append((start, end))
        previous_end = end
    if not terminated or not ranges:
        raise ElfAuditError("FIPS address table has no bounded nonempty range list")
    return ranges, digest.digest()


def target_index(
    instructions: list[tuple[int, int, int]], pc: int, delta: int
) -> int | None:
    addresses = {row[1]: row[0] for row in instructions}
    return addresses.get(pc + delta)


def find_ring_publication_chains(
    *,
    instructions: list[tuple[int, int, int]],
    successors: dict[int, set[int]],
    witness_index: int,
    marker_reference: dict[str, int],
    memstart_reference: dict[str, int],
    memcpy_address: int,
    marker_size: int,
) -> list[dict[str, int]]:
    if marker_size != 99 or witness_index + 47 > len(instructions):
        return []
    rows = instructions[witness_index : witness_index + 47]
    words = [row[2] for row in rows]
    exact_words = {
        1: 0xD2A00409, 2: 0xF2C00109, 3: 0xCB080128, 4: 0xB2596116,
        5: 0x5289E989, 6: 0x910012C8, 7: 0x72A9A8E9, 8: 0x88DFFD08,
        9: 0x6B09011F, 11: 0x910022C8, 12: 0x88DFFD17,
        13: 0x52810028, 14: 0x72A20008, 15: 0x53047EEB,
        16: 0x9BA87D68, 17: 0x321C43E9, 18: 0x529FF1AA,
        19: 0xD36DFD08, 20: 0x72A003EA, 21: 0x1B09DD18,
        22: 0x52800C6B, 23: 0x6B0A031F, 24: 0xCB180128,
        26: 0x910042D3, 27: 0x9A8B8114, 29: 0x8B180260,
        30: 0xAA1503E1, 31: 0xAA1403E2, 33: 0x529FF1C8,
        34: 0x72A003E8, 35: 0x6B08031F, 37: 0x52800C68,
        38: 0x8B1402A1, 39: 0xCB140102, 40: 0xAA1303E0,
        42: 0xD5033ABF, 44: 0x11018EE8, 46: 0xB9000AC8,
    }
    if any(words[offset] != expected for offset, expected in exact_words.items()):
        return []
    first_memcpy = branch_target(rows[32][1], words[32])
    second_memcpy = branch_target(rows[41][1], words[41])
    magic_guard = conditional_branch(words[10])
    wrap_guard = conditional_branch(words[36])
    if (
        memstart_reference["index"] != witness_index
        or memstart_reference["base_register"] != 22
        or memstart_reference["destination"] != 8
        or memstart_reference["width"] != 64
        or marker_reference["index"] != witness_index + 25
        or marker_reference["consumer_index"] != witness_index + 28
        or marker_reference["register"] != 21
        or first_memcpy != memcpy_address
        or second_memcpy != memcpy_address
        or magic_guard is None
        or magic_guard["condition"] != 1
        or wrap_guard is None
        or wrap_guard["condition"] != 3
    ):
        return []
    magic_failure = target_index(instructions, rows[10][1], magic_guard["target_delta"])
    wrap_skip = target_index(instructions, rows[36][1], wrap_guard["target_delta"])
    if magic_failure is None or wrap_skip != witness_index + 42:
        return []
    marker_index = marker_reference["index"]
    gates = {
        "head_phys_exact": SEC_LOG_PHYS_ADDR == 0x800200000,
        "head_uses_memstart_addr": memstart_reference["target"] > 0,
        "magic_exact": SEC_LOG_MAGIC == 0x4D474F4C,
        "payload_size_exact": SEC_LOG_PAYLOAD_SIZE == 0x1FFFF0,
        "magic_match_reaches_marker": is_reachable_within(
            successors,
            witness_index + 11,
            marker_index,
            minimum=witness_index,
            maximum=witness_index + 46,
        ),
        "magic_mismatch_cannot_reach_marker": not is_reachable_within(
            successors,
            magic_failure,
            marker_index,
            minimum=witness_index,
            maximum=witness_index + 46,
        ),
        "first_copy_reaches_publish": is_reachable_within(
            successors,
            witness_index + 32,
            witness_index + 42,
            minimum=witness_index,
            maximum=witness_index + 46,
        ),
        "wrap_copy_reaches_publish": is_reachable_within(
            successors,
            witness_index + 41,
            witness_index + 42,
            minimum=witness_index,
            maximum=witness_index + 46,
        ),
    }
    if not all(gates.values()):
        return []
    return [
        {
            "memstart_reference_pc": memstart_reference["producer_pc"],
            "head_load_pc": rows[0][1],
            "magic_guard_pc": rows[10][1],
            "idx_load_pc": rows[12][1],
            "marker_reference_pc": rows[25][1],
            "marker_materialize_pc": rows[28][1],
            "first_memcpy_call_pc": rows[32][1],
            "wrap_guard_pc": rows[36][1],
            "wrap_memcpy_call_pc": rows[41][1],
            "dmb_ishst_pc": rows[42][1],
            "idx_add_pc": rows[44][1],
            "idx_store_pc": rows[46][1],
            "head_base_register": 22,
            "idx_source_register": 23,
            "idx_destination_register": 8,
            "gates": gates,
        }
    ]


def expected_witness_ingress(
    instructions: list[tuple[int, int, int]],
    witness_index: int,
    branch: tuple[int, int, int],
) -> set[tuple[int, int]]:
    return {
        (branch[1], instructions[witness_index][1]),
        (
            instructions[witness_index + 36][1],
            instructions[witness_index + 42][1],
        ),
    }


def inspect_final_vmlinux(path: Path, marker: bytes) -> dict[str, Any]:
    required_symbols = {
        "kernel_init",
        "run_init_process",
        "strcmp",
        "memcpy",
        "memstart_addr",
        "ramdisk_execute_command",
        "builtime_crypto_hmac",
        "integrity_crypto_addrs",
        "crypto_buildtime_address",
    }
    with Elf64(path) as elf:
        symbols = elf.symbols(required_symbols)
        marker_offsets = elf.find_all(marker)
        marker_vaddrs = {elf.file_offset_to_vaddr(offset) for offset in marker_offsets}
        init_offsets = elf.find_all(b"/init\0")
        init_vaddrs = {
            address
            for offset in init_offsets
            if (address := elf.mapped_file_offset_to_vaddr(offset)) is not None
        }
        kernel_init = symbols["kernel_init"]
        code = elf.symbol_bytes(kernel_init)
        run_init_process_code = elf.symbol_bytes(symbols["run_init_process"])
        strcmp_code = elf.symbol_bytes(symbols["strcmp"])
        memcpy_code = elf.symbol_bytes(symbols["memcpy"])
        instructions = list(iter_words(code, int(kernel_init["value"])))
        kernel_init_start = int(kernel_init["value"])
        kernel_init_end = kernel_init_start + int(kernel_init["size"])
        marker_references = adrp_add_references(instructions, marker_vaddrs)
        init_references = adrp_add_references(instructions, init_vaddrs)
        ramdisk_address = int(symbols["ramdisk_execute_command"]["value"])
        ramdisk_references = adrp_load_references(
            instructions, {ramdisk_address}
        )
        memstart_address = int(symbols["memstart_addr"]["value"])
        memstart_references = adrp_load_references(
            instructions, {memstart_address}
        )
        successors, predecessors = build_cfg(instructions)
        unsupported_control_transfers = [
            {"index": row[0], "pc": row[1], "word": row[2]}
            for row in instructions
            if is_indirect_control_transfer(row[2])
        ]

        run_address = int(symbols["run_init_process"]["value"])
        strcmp_address = int(symbols["strcmp"]["value"])
        memcpy_address = int(symbols["memcpy"]["value"])
        run_calls = [
            row
            for row in instructions
            if row[2] & 0xFC000000 == 0x94000000
            and branch_target(row[1], row[2]) == run_address
        ]
        strcmp_calls = [
            row
            for row in instructions
            if row[2] & 0xFC000000 == 0x94000000
            and branch_target(row[1], row[2]) == strcmp_address
        ]

        success_edges = []
        for run_call in run_calls:
            run_index = run_call[0]
            if run_index < 2 or run_index + 11 >= len(instructions):
                continue
            run_inputs = [
                row
                for row in ramdisk_references
                if row["index"] == run_index - 2
                and row["destination"] == 0
                and row["width"] == 64
            ]
            entry_guard = instructions[run_index - 1]
            entry_decoded = compare_branch(entry_guard[2])
            return_guard = instructions[run_index + 2]
            return_decoded = compare_branch(return_guard[2])
            if not (
                len(run_inputs) == 1
                and run_inputs[0]["producer_index"] == run_index - 3
                and run_inputs[0]["base_register"] == 19
                and entry_decoded is not None
                and entry_decoded["nonzero"] == 0
                and entry_decoded["register"] == 0
                and return_decoded is not None
                and return_decoded["nonzero"] == 1
                and return_decoded["register"] == 0
            ):
                continue
            run_input = run_inputs[0]
            reloaded_path = instructions[run_index + 1]
            decoded_reload = load_unsigned(reloaded_path[2])
            if not (
                decoded_reload is not None
                and decoded_reload["base"] == run_input["base_register"]
                and decoded_reload["offset"] == run_input["offset"]
                and decoded_reload["width"] == 64
                and decoded_reload["destination"] == 8
            ):
                continue
            strcmp_call = instructions[run_index + 6]
            if strcmp_call not in strcmp_calls:
                continue
            path_refs = [
                row
                for row in init_references
                if row["index"] == run_index + 3
                and row["consumer_index"] == run_index + 4
                and row["register"] == 1
            ]
            path_move = instructions[run_index + 5]
            decoded_move = move_register(path_move[2])
            path_guard = instructions[run_index + 7]
            path_decoded = compare_branch(path_guard[2])
            pid_mrs, pid_load, pid_compare, branch = instructions[
                run_index + 8 : run_index + 12
            ]
            decoded_pid_load = load_unsigned(pid_load[2])
            decoded_pid_compare = compare_w_immediate(pid_compare[2])
            decoded_branch = conditional_branch(branch[2])
            mrs_register = pid_mrs[2] & 0x1F
            if not (
                len(path_refs) == 1
                and decoded_move is not None
                and decoded_move["destination"] == 0
                and decoded_move["source"] == 8
                and path_decoded is not None
                and path_decoded["nonzero"] == 1
                and path_decoded["register"] == 0
                and is_mrs_sp_el0(pid_mrs[2])
                and mrs_register == 8
                and decoded_pid_load is not None
                and decoded_pid_load["width"] == 32
                and decoded_pid_load["base"] == 8
                and decoded_pid_load["destination"] == 8
                and decoded_pid_load["offset"] == 1480
                and decoded_pid_compare is not None
                and decoded_pid_compare["register"]
                == decoded_pid_load["destination"]
                and decoded_pid_compare["immediate"] == 1
                and decoded_branch is not None
                and decoded_branch["condition"] == 0
            ):
                continue
            assert decoded_branch is not None
            witness_index = target_index(
                instructions, branch[1], decoded_branch["target_delta"]
            )
            assert return_decoded is not None and path_decoded is not None
            entry_failure_index = target_index(
                instructions, entry_guard[1], entry_decoded["target_delta"]
            )
            return_failure_index = target_index(
                instructions, return_guard[1], return_decoded["target_delta"]
            )
            path_failure_index = target_index(
                instructions, path_guard[1], path_decoded["target_delta"]
            )
            if None in (
                witness_index,
                entry_failure_index,
                return_failure_index,
                path_failure_index,
            ):
                continue
            assert witness_index is not None
            assert return_failure_index is not None
            assert path_failure_index is not None
            target_marker_refs = [
                row
                for row in marker_references
                if is_reachable(successors, witness_index, row["index"])
            ]
            if len(target_marker_refs) != 1:
                continue
            marker_reference = target_marker_refs[0]
            target_memstart_refs = [
                row
                for row in memstart_references
                if row["index"] == witness_index
            ]
            if len(target_memstart_refs) != 1:
                continue
            witness_end_index = witness_index + 47
            if witness_end_index > len(instructions):
                continue
            external_ingress = direct_ingress_to_range(
                elf,
                target_start=instructions[witness_index][1],
                target_end=(
                    instructions[witness_end_index][1]
                    if witness_end_index < len(instructions)
                    else kernel_init_end
                ),
            )
            expected_ingress = expected_witness_ingress(
                instructions, witness_index, branch
            )
            actual_ingress = {
                (row["source_pc"], row["target_pc"]) for row in external_ingress
            }
            unexpected_ingress = [
                row
                for row in external_ingress
                if (row["source_pc"], row["target_pc"]) not in expected_ingress
            ]
            cfg_gates = {
                "entry_guard_fallthrough_exact": successors[entry_guard[0]]
                == {run_index, entry_failure_index},
                "run_call_predecessors_exact": predecessors[run_index]
                == {entry_guard[0]},
                "witness_entry_predecessors_exact": predecessors[witness_index]
                == {branch[0]},
                "global_direct_witness_ingress_exact": actual_ingress
                == expected_ingress,
                "exec_success_reaches_marker": is_reachable_within(
                    successors,
                    return_guard[0] + 1,
                    marker_reference["index"],
                    minimum=run_index,
                    maximum=len(instructions) - 1,
                ),
                "exec_failure_cannot_reach_marker": not is_reachable_within(
                    successors,
                    return_failure_index,
                    marker_reference["index"],
                    minimum=run_index,
                    maximum=len(instructions) - 1,
                ),
                "path_success_reaches_marker": is_reachable_within(
                    successors,
                    path_guard[0] + 1,
                    marker_reference["index"],
                    minimum=run_index,
                    maximum=len(instructions) - 1,
                ),
                "path_failure_cannot_reach_marker": not is_reachable_within(
                    successors,
                    path_failure_index,
                    marker_reference["index"],
                    minimum=run_index,
                    maximum=len(instructions) - 1,
                ),
                "pid_true_reaches_marker": is_reachable_within(
                    successors,
                    witness_index,
                    marker_reference["index"],
                    minimum=run_index,
                    maximum=len(instructions) - 1,
                ),
                "pid_false_cannot_reach_marker": not is_reachable_within(
                    successors,
                    branch[0] + 1,
                    marker_reference["index"],
                    minimum=run_index,
                    maximum=len(instructions) - 1,
                ),
            }
            if not all(cfg_gates.values()):
                continue
            publication_chains = find_ring_publication_chains(
                instructions=instructions,
                successors=successors,
                witness_index=witness_index,
                marker_reference=marker_reference,
                memstart_reference=target_memstart_refs[0],
                memcpy_address=memcpy_address,
                marker_size=len(marker),
            )
            if len(publication_chains) != 1:
                continue
            success_edges.append(
                {
                    "run_init_process_call_pc": run_call[1],
                    "ramdisk_nonnull_guard_pc": entry_guard[1],
                    "ramdisk_load_pc": run_input["pc"],
                    "ramdisk_reload_pc": reloaded_path[1],
                    "return_zero_guard_pc": return_guard[1],
                    "init_path_reference_pc": path_refs[0]["pc"],
                    "strcmp_argument_move_pc": path_move[1],
                    "strcmp_call_pc": strcmp_call[1],
                    "path_match_guard_pc": path_guard[1],
                    "sp_el0_read_pc": pid_mrs[1],
                    "pid_load_pc": pid_load[1],
                    "pid_one_compare_pc": pid_compare[1],
                    "pid_equal_branch_pc": branch[1],
                    "witness_block_pc": instructions[witness_index][1],
                    "marker_reference_pc": marker_reference["pc"],
                    "global_direct_witness_ingress": external_ingress,
                    "unexpected_direct_witness_ingress": unexpected_ingress,
                    "cfg": cfg_gates,
                    "ring_publication": publication_chains[0],
                }
            )

        hmac_symbol = symbols["builtime_crypto_hmac"]
        hmac_bytes = elf.symbol_bytes(hmac_symbol)
        address_table = elf.symbol_bytes(symbols["integrity_crypto_addrs"])
        build_address = elf.symbol_bytes(symbols["crypto_buildtime_address"])
        ranges, recomputed_hmac = parse_fips_address_table(elf, address_table)
        build_address_value = (
            struct.unpack("<Q", build_address)[0] if len(build_address) == 8 else None
        )
        fips = {
            "hmac_symbol_address": int(hmac_symbol["value"]),
            "hmac_size": len(hmac_bytes),
            "hmac_hex": hmac_bytes.hex(),
            "hmac_sha256": sha256_bytes(hmac_bytes),
            "recomputed_hmac_hex": recomputed_hmac.hex(),
            "recomputed_hmac_sha256": sha256_bytes(recomputed_hmac),
            "hmac_exact_match": hmac_bytes == recomputed_hmac,
            "address_table_size": len(address_table),
            "address_table_sha256": sha256_bytes(address_table),
            "address_range_count": len(ranges),
            "address_range_bytes": sum(end - start for start, end in ranges),
            "address_ranges": [
                {"start": start, "end": end, "size": end - start}
                for start, end in ranges
            ],
            "build_address_size": len(build_address),
            "build_address_hex": build_address.hex(),
            "build_address_sha256": sha256_bytes(build_address),
            "build_address_value": build_address_value,
            "load_base": elf.load_base(),
            "image_offsets": {
                "builtime_crypto_hmac": int(hmac_symbol["value"])
                - elf.load_base(),
                "integrity_crypto_addrs": int(
                    symbols["integrity_crypto_addrs"]["value"]
                )
                - elf.load_base(),
                "crypto_buildtime_address": int(
                    symbols["crypto_buildtime_address"]["value"]
                )
                - elf.load_base(),
            },
            "build_address_matches_symbol": (
                build_address_value
                == int(symbols["crypto_buildtime_address"]["value"])
            ),
        }
        fips["verified"] = (
            fips["hmac_size"] == 32
            and fips["hmac_exact_match"]
            and fips["address_table_size"] == 65536
            and fips["address_range_count"] > 0
            and fips["address_range_count"] == FIPS_EXPECTED_RANGE_COUNT
            and fips["address_range_bytes"] == FIPS_EXPECTED_COVERED_BYTES
            and fips["build_address_matches_symbol"]
        )
        control_flow = {
            "kernel_init_address": int(kernel_init["value"]),
            "kernel_init_size": int(kernel_init["size"]),
            "kernel_init_sha256": sha256_bytes(code),
            "kernel_init_sha256_expected": EXPECTED_KERNEL_INIT_SHA256,
            "kernel_init_sha256_exact": sha256_bytes(code)
            == EXPECTED_KERNEL_INIT_SHA256,
            "run_init_process_sha256": sha256_bytes(run_init_process_code),
            "run_init_process_sha256_expected": EXPECTED_RUN_INIT_PROCESS_SHA256,
            "run_init_process_sha256_exact": sha256_bytes(run_init_process_code)
            == EXPECTED_RUN_INIT_PROCESS_SHA256,
            "strcmp_size": len(strcmp_code),
            "strcmp_size_expected": EXPECTED_STRCMP_SIZE,
            "strcmp_sha256": sha256_bytes(strcmp_code),
            "strcmp_sha256_expected": EXPECTED_STRCMP_SHA256,
            "strcmp_exact": (
                len(strcmp_code) == EXPECTED_STRCMP_SIZE
                and sha256_bytes(strcmp_code) == EXPECTED_STRCMP_SHA256
            ),
            "memcpy_size": len(memcpy_code),
            "memcpy_size_expected": EXPECTED_MEMCPY_SIZE,
            "memcpy_sha256": sha256_bytes(memcpy_code),
            "memcpy_sha256_expected": EXPECTED_MEMCPY_SHA256,
            "memcpy_exact": (
                len(memcpy_code) == EXPECTED_MEMCPY_SIZE
                and sha256_bytes(memcpy_code) == EXPECTED_MEMCPY_SHA256
            ),
            "load_segments": elf.load_segment_manifest(),
            "run_init_process_address": run_address,
            "run_init_process_call_count": len(run_calls),
            "strcmp_address": strcmp_address,
            "strcmp_call_count": len(strcmp_calls),
            "memcpy_address": memcpy_address,
            "memstart_addr_address": memstart_address,
            "memstart_reference_count_in_kernel_init": len(memstart_references),
            "ramdisk_execute_command_address": ramdisk_address,
            "ramdisk_reference_count_in_kernel_init": len(ramdisk_references),
            "init_string_count_in_elf": len(init_offsets),
            "init_reference_count_in_kernel_init": len(init_references),
            "marker_count_in_elf": len(marker_offsets),
            "marker_reference_count_in_kernel_init": len(marker_references),
            "success_edge_count": len(success_edges),
            "success_edges": success_edges,
            "unsupported_control_transfers": unsupported_control_transfers,
            "unsupported_control_transfer_count": len(
                unsupported_control_transfers
            ),
        }
        control_flow["verified"] = (
            len(marker_offsets) == 1
            and len(marker_references) == 1
            and len(success_edges) == 1
            and not unsupported_control_transfers
            and control_flow["kernel_init_sha256_exact"]
            and control_flow["run_init_process_sha256_exact"]
            and control_flow["strcmp_exact"]
            and control_flow["memcpy_exact"]
        )
        return {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
            "machine": "AArch64",
            "symbols": symbols,
            "fips": fips,
            "control_flow": control_flow,
            "verified": fips["verified"] and control_flow["verified"],
        }
