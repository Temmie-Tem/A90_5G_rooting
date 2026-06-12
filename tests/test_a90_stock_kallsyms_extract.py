"""Regression tests for a90_stock_kallsyms_extract.

Uses small synthetic kallsyms-like token/name/address tables to pin pure decode
and layout validation helpers. No real kernel image or private artifact needed.
"""

import struct
import tempfile
import unittest
from pathlib import Path

from _loader import load_revalidation

extract = load_revalidation("a90_stock_kallsyms_extract")


def make_token_table_blob() -> tuple[bytes, list[int], list[bytes], int]:
    blob = bytearray()
    cumulative: list[int] = []
    tokens: list[bytes] = []
    for index in range(256):
        cumulative.append(len(blob))
        token = b"" if index == 0 else f"tok{index}".encode()
        tokens.append(token)
        blob += token + b"\0"
    table_end = len(blob)
    blob += b"\xaa\xbb"
    for value in cumulative:
        blob += struct.pack("<H", value)
    return bytes(blob), cumulative, tokens, table_end


class KernelImageAndScalarHelpers(unittest.TestCase):
    def test_sha_and_little_endian_reads(self):
        data = bytes(range(16))
        self.assertEqual(extract.sha256_bytes(b""), "e3b0c44298fc1c149afbf4c8996fb924"
                                                  "27ae41e4649b934ca495991b7852b855")
        self.assertEqual(extract.u16(data, 1), 0x0201)
        self.assertEqual(extract.u32(data, 2), 0x05040302)
        self.assertEqual(extract.u64(data, 4), 0x0b0a090807060504)

    def test_unwrap_kernel_accepts_raw_and_uncompressed_img_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_path = root / "Image"
            raw_payload = b"raw-kernel"
            raw_path.write_bytes(raw_payload)

            raw_image = extract.unwrap_kernel(raw_path)
            self.assertEqual(raw_image.raw, raw_payload)
            self.assertEqual(raw_image.raw_offset, 0)
            self.assertEqual(raw_image.wrapper_size, len(raw_payload))
            self.assertEqual(raw_image.wrapper_sha256, extract.sha256_bytes(raw_payload))

            wrapper_path = root / "wrapped"
            wrapper = b"UNCOMPRESSED_IMG" + struct.pack("<I", len(raw_payload)) + raw_payload
            wrapper_path.write_bytes(wrapper)

            wrapped_image = extract.unwrap_kernel(wrapper_path)
            self.assertEqual(wrapped_image.raw, raw_payload)
            self.assertEqual(wrapped_image.raw_offset, 20)
            self.assertEqual(wrapped_image.wrapper_size, len(wrapper))
            self.assertEqual(wrapped_image.wrapper_sha256, extract.sha256_bytes(wrapper))
            self.assertEqual(wrapped_image.raw_sha256, extract.sha256_bytes(raw_payload))

    def test_unwrap_kernel_rejects_short_or_truncated_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            short = root / "short"
            short.write_bytes(b"UNCOMPRESSED_IMG")
            with self.assertRaises(ValueError):
                extract.unwrap_kernel(short)

            truncated = root / "truncated"
            truncated.write_bytes(b"UNCOMPRESSED_IMG" + struct.pack("<I", 8) + b"abc")
            with self.assertRaises(ValueError):
                extract.unwrap_kernel(truncated)


class TokenTableHelpers(unittest.TestCase):
    def test_printable_token_rejects_non_printable_bytes(self):
        self.assertTrue(extract.printable_token(b"abc_DEF\t"))
        self.assertFalse(extract.printable_token(b"abc\x01"))

    def test_parse_token_run_and_token_table_with_padding(self):
        data, cumulative, tokens, table_end = make_token_table_blob()

        parsed = extract.parse_token_run(data, 0)
        self.assertIsNotNone(parsed)
        parsed_end, parsed_cumulative, parsed_tokens = parsed
        self.assertEqual(parsed_end, table_end)
        self.assertEqual(parsed_cumulative, cumulative)
        self.assertEqual(parsed_tokens, tokens)

        table = extract.token_table_at(data, 0)
        self.assertIsNotNone(table)
        self.assertEqual(table.table_start, 0)
        self.assertEqual(table.table_end, table_end)
        self.assertEqual(table.index_start, table_end + 2)
        self.assertEqual(table.token_index, cumulative)
        self.assertEqual(table.tokens, tokens)

    def test_parse_token_run_rejects_short_or_bad_tokens(self):
        self.assertIsNone(extract.parse_token_run(b"a\0b\0", 0))

        data, _, _, _ = make_token_table_blob()
        bad = bytearray(data)
        bad[bad.find(b"tok1")] = 0x01
        self.assertIsNone(extract.parse_token_run(bytes(bad), 0))


class NameAndMarkerHelpers(unittest.TestCase):
    def test_marker_candidate_requires_monotonic_reasonable_offsets(self):
        start = 0x20
        values = [0] + [6000 + index * 32768 for index in range(35)]
        token_table_start = start + 8 * len(values)
        data = bytearray(token_table_start + 32)
        for index, value in enumerate(values):
            struct.pack_into("<Q", data, start + 8 * index, value)

        self.assertEqual(extract.marker_candidate(bytes(data), start, token_table_start), values)

        non_monotonic = bytearray(data)
        struct.pack_into("<Q", non_monotonic, start + 8 * 2, 1)
        self.assertIsNone(extract.marker_candidate(bytes(non_monotonic), start, token_table_start))

    def test_parse_record_offsets_handles_padding_and_rejects_bad_records(self):
        records = bytes([2, 1, 2, 1, 3])
        self.assertEqual(extract.parse_record_offsets(records, 0, len(records)), ([0, 3], 5))

        padded = records + b"\0\0"
        self.assertEqual(
            extract.parse_record_offsets(padded, 0, len(padded), allow_zero_padding=True),
            ([0, 3], 5),
        )
        self.assertIsNone(extract.parse_record_offsets(padded, 0, len(padded)))
        self.assertIsNone(extract.parse_record_offsets(bytes([129]) + b"x" * 129, 0, 130))

    def test_decode_names_joins_token_bytes(self):
        records = bytes([2, 1, 2, 1, 3])
        tokens = [b"", b"T", b"_text", b"foo"] + [b""] * 252
        self.assertEqual(extract.decode_names(records, 0, [0, 3], tokens), ["T_text", "foo"])

    def test_find_num_syms_position_finds_preceding_qword(self):
        data = b"prefix" + struct.pack("<Q", 1234) + b"names"
        self.assertEqual(extract.find_num_syms_position(data, len(b"prefix") + 8, 1234), len(b"prefix"))
        with self.assertRaises(RuntimeError):
            extract.find_num_syms_position(data, len(data), 999)


class AddressAndRenderingHelpers(unittest.TestCase):
    def test_find_address_table_validates_monotonic_offsets_and_sets_synthetic_base(self):
        num_syms = 4101
        relative_base_pos = 4 * num_syms
        num_syms_pos = relative_base_pos + 8
        data = bytearray(num_syms_pos + 8)
        for index in range(num_syms):
            struct.pack_into("<I", data, 4 * index, index * 4)
        struct.pack_into("<Q", data, relative_base_pos, 0xabcdef)
        struct.pack_into("<Q", data, num_syms_pos, num_syms)
        names = ["T_text"] + [f"Tsym{index}" for index in range(1, num_syms)]
        name_table = extract.NameTable(
            names_start=num_syms_pos + 8,
            names_end=num_syms_pos + 8,
            marker_start=num_syms_pos + 8,
            marker_count=17,
            num_syms_pos=num_syms_pos,
            num_syms=num_syms,
            names=names,
            record_offsets=list(range(num_syms)),
        )

        addresses = extract.find_address_table(bytes(data), name_table, 0x100000)

        self.assertEqual(addresses.offsets_start, 0)
        self.assertEqual(addresses.relative_base_pos, relative_base_pos)
        self.assertEqual(addresses.relative_base, 0xabcdef)
        self.assertEqual(addresses.low_offsets[:3], [0, 4, 8])
        self.assertEqual(addresses.text_offset, 0)
        self.assertEqual(addresses.synthetic_base, 0x100000)

        bad = bytearray(data)
        for index in range(num_syms):
            struct.pack_into("<I", bad, 4 * index, num_syms - index)
        with self.assertRaises(RuntimeError):
            extract.find_address_table(bytes(bad), name_table, 0x100000)

    def test_render_system_map_skips_empty_rows_and_strips_kind_prefix(self):
        names = extract.NameTable(
            names_start=0,
            names_end=0,
            marker_start=0,
            marker_count=0,
            num_syms_pos=0,
            num_syms=4,
            names=["T_text", "", "T", "tworker"],
            record_offsets=[0, 1, 2, 3],
        )
        addresses = extract.AddressTable(
            offsets_start=0,
            relative_base_pos=0,
            relative_base=0,
            low_offsets=[0x10, 0x20, 0x30, 0x40],
            synthetic_base=0x1000,
            text_offset=0x10,
        )

        self.assertEqual(
            extract.render_system_map(names, addresses),
            "0000000000001010 T _text\n0000000000001040 t worker\n",
        )


if __name__ == "__main__":
    unittest.main()
