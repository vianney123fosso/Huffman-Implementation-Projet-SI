#!/usr/bin/env python3
"""Decompress .huff image containers created by compress_image.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # dossier python, pour huffmancoding.py
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from codec import read_container, decode_symbols


def decode_container(path):
    header, payloads = read_container(path)
    width, height = header["width"], header["height"]
    method = header["method"]
    sections = header["sections"]

    huffman_payloads = payloads[:len(sections)]
    auxiliary_payloads = payloads[len(sections):]
    decoded_sections = []
    for section, payload in zip(sections, huffman_payloads):
        decoded = decode_symbols(
            payload,
            section["code_lengths"],
            section["symbol_count"],
            section["bit_length"],
        )
        actual_bits = sum(section["code_lengths"][symbol] for symbol in decoded)
        if actual_bits != section["bit_length"]:
            raise ValueError(
                f"Bit length mismatch in section {section['name']}: "
                f"metadata={section['bit_length']}, decoded={actual_bits}"
            )
        decoded_sections.append(decoded)

    if method == "grayscale":
        pixels = decoded_sections[0]
        if len(pixels) != width * height:
            raise ValueError("Pixel count does not match image dimensions")
        return _image_from_data("L", (width, height), pixels)

    if method == "rgb_channels":
        if len(decoded_sections) != 3:
            raise ValueError("RGB channel method expects three sections")
        red, green, blue = decoded_sections
        expected = width * height
        if any(len(channel) != expected for channel in decoded_sections):
            raise ValueError("Channel size does not match image dimensions")
        pixels = list(zip(red, green, blue))
        image = _image_from_data("RGB", (width, height), pixels)
        if header.get("raw_sections"):
            alpha = list(auxiliary_payloads[0])
            if len(alpha) != width * height:
                raise ValueError("Alpha channel size does not match image dimensions")
            image.putalpha(_image_from_data("L", (width, height), alpha))
        return image

    if method == "rgb_pixels":
        indices = decoded_sections[0]
        # Support both the compact binary palette (new format) and old files
        # that stored the palette as JSON in the header.
        if "palette" in header:
            palette = [tuple(color) for color in header["palette"]]
            alpha_payload_index = 0
        else:
            palette_count = header["palette_count"]
            if not auxiliary_payloads:
                raise ValueError("Palette payload missing")
            palette_bytes = auxiliary_payloads[0]
            if len(palette_bytes) != palette_count * 3:
                raise ValueError("Invalid binary palette size")
            palette = [tuple(palette_bytes[i:i + 3]) for i in range(0, len(palette_bytes), 3)]
            alpha_payload_index = 1
        if len(indices) != width * height:
            raise ValueError("Pixel count does not match image dimensions")
        try:
            pixels = [palette[index] for index in indices]
        except IndexError as exc:
            raise ValueError("Palette index outside palette") from exc
        image = _image_from_data("RGB", (width, height), pixels)
        if header.get("raw_sections"):
            if len(auxiliary_payloads) <= alpha_payload_index:
                raise ValueError("Alpha payload missing")
            alpha = list(auxiliary_payloads[alpha_payload_index])
            if len(alpha) != width * height:
                raise ValueError("Alpha channel size does not match image dimensions")
            image.putalpha(_image_from_data("L", (width, height), alpha))
        return image

    raise ValueError(f"Unknown method in file: {method}")


def _image_from_data(mode, size, data):
    image = Image.new(mode, size)
    image.putdata(data)
    return image


def main():
    parser = argparse.ArgumentParser(description="Décompresse une image Huffman .huff")
    parser.add_argument("compressed", type=Path, help="Fichier .huff")
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Image reconstruite (PNG). Par défaut, nom automatique.",
    )
    args = parser.parse_args()
    if not args.compressed.exists():
        parser.error(f"Fichier introuvable : {args.compressed}")

    image = decode_container(args.compressed)
    output = args.output or args.compressed.with_name(args.compressed.stem + "_decoded.png")
    image.save(output)
    print(f"Décompression terminée : {output}")
    print(f"Dimensions : {image.width} x {image.height} | mode : {image.mode}")


if __name__ == "__main__":
    main()