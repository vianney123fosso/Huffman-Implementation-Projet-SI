"""Shared Huffman image codec using the existing huffmancoding.py classes."""

from __future__ import annotations

import json
import struct
import zlib
from collections import Counter
from io import BytesIO
from pathlib import Path

from huffmancoding import (
    FrequencyTable, CanonicalCode, HuffmanEncoder, HuffmanDecoder,
    BitOutputStream, BitInputStream,
)

MAGIC = b"HFIM"
VERSION = 1


class _NonClosingBytesIO(BytesIO):
    """Allow BitOutputStream.close() to pad without closing our buffer."""
    def close(self):
        pass


def encode_symbols(symbols, alphabet_size, export_bits=True):
    """Encode integer symbols and return packed bytes, code lengths, pure bit count.

    No EOF marker is used: the section stores its symbol count and exact bit length.
    """
    symbols = list(symbols)
    if alphabet_size < 1:
        raise ValueError("alphabet_size must be positive")
    table_size = max(2, alphabet_size)
    frequencies = [0] * table_size
    for symbol in symbols:
        if not 0 <= symbol < alphabet_size:
            raise ValueError(f"Symbol {symbol} outside alphabet")
        frequencies[symbol] += 1

    freqs = FrequencyTable(frequencies)
    tree = freqs.build_code_tree()
    canonical = CanonicalCode(tree=tree, symbollimit=freqs.get_symbol_limit())
    code_tree = canonical.to_code_tree()

    buffer = _NonClosingBytesIO()
    bitout = BitOutputStream(buffer)
    encoder = HuffmanEncoder(bitout)
    encoder.codetree = code_tree

    pure_bit_length = 0
    bit_chunks = [] if export_bits else None
    current_text_chunk = [] if export_bits else None
    symbols_in_chunk = 0
    for symbol in symbols:
        code = code_tree.get_code(symbol)
        encoder.write(symbol)
        pure_bit_length += len(code)
        if export_bits:
            current_text_chunk.append("".join(str(bit) for bit in code))
            symbols_in_chunk += 1
            if symbols_in_chunk >= 8192:
                bit_chunks.append("".join(current_text_chunk))
                current_text_chunk = []
                symbols_in_chunk = 0
    if export_bits and current_text_chunk:
        bit_chunks.append("".join(current_text_chunk))
    bitout.close()  # writes only byte-alignment padding

    pure_bits = "".join(bit_chunks) if export_bits else None
    packed = buffer.getvalue()
    code_lengths = canonical.codelengths
    return packed, code_lengths, pure_bit_length, pure_bits


def decode_symbols(packed, code_lengths, symbol_count, bit_length):
    """Decode exactly symbol_count symbols from a packed section."""
    canonical = CanonicalCode(codelengths=code_lengths)
    tree = canonical.to_code_tree()
    bitin = BitInputStream(BytesIO(packed))
    decoder = HuffmanDecoder(bitin)
    decoder.codetree = tree

    result = []
    for _ in range(symbol_count):
        result.append(decoder.read())
    # The exact bit length is stored for validation and to distinguish payload
    # from padding. Decoder stops by symbol_count, so it never consumes padding.
    return result


def write_container(path, metadata, payloads):
    """Write a small container: magic, JSON-header length, header, section bytes."""
    path = Path(path)
    header = dict(metadata)
    header["payload_lengths"] = [len(payload) for payload in payloads]
    # Compress metadata (especially RGB palettes) to avoid wasting space.
    encoded_header = json.dumps(header, separators=(",", ":")).encode("utf-8")
    compressed_header = zlib.compress(encoded_header, level=9)
    # High bit of the length field indicates a zlib-compressed header.
    header_length_field = len(compressed_header) | 0x80000000
    with path.open("wb") as f:
        f.write(MAGIC)
        f.write(struct.pack(">I", header_length_field))
        f.write(compressed_header)
        for payload in payloads:
            f.write(payload)


def read_container(path):
    with Path(path).open("rb") as f:
        if f.read(4) != MAGIC:
            raise ValueError("Ce fichier ne semble pas être un fichier image Huffman (.huff).")
        raw_len = f.read(4)
        if len(raw_len) != 4:
            raise ValueError("En-tête incomplet.")
        header_field = struct.unpack(">I", raw_len)[0]
        is_compressed = bool(header_field & 0x80000000)
        header_len = header_field & 0x7FFFFFFF
        header_bytes = f.read(header_len)
        if len(header_bytes) != header_len:
            raise ValueError("En-tête tronqué.")
        if is_compressed:
            header_bytes = zlib.decompress(header_bytes)
        header = json.loads(header_bytes.decode("utf-8"))
        payloads = []
        for length in header["payload_lengths"]:
            payload = f.read(length)
            if len(payload) != length:
                raise ValueError("Section compressée tronquée.")
            payloads.append(payload)
    return header, payloads