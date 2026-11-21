#!/usr/bin/env python3
"""Compress an image using three lossless Huffman strategies."""

from __future__ import annotations

import argparse
import csv
import sys
import warnings
from collections import Counter
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # dossier python, pour huffmancoding.py
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from codec import encode_symbols, write_container
from decompress_image import decode_container


METHODS = ("grayscale", "rgb_channels", "rgb_pixels")


def write_pixel_dump(image, path):
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if image.mode == "L":
            writer.writerow(["pixel_value"])
            width, height = image.size
            values = list(image.getdata())
            for y in range(height):
                writer.writerow(values[y * width:(y + 1) * width])
        else:
            writer.writerow(["R", "G", "B"] + (["A"] if image.mode == "RGBA" else []))
            writer.writerows(image.getdata())


def prepare_method(image, method):
    """Return metadata, symbol sections, and the raster used as the lossless target."""
    width, height = image.size
    if method == "grayscale":
        target = image.convert("L")
        symbols = list(target.getdata())
        section = {
            "name": "gray",
            "symbol_count": len(symbols),
            "alphabet_size": 256,
        }
        return {"mode": "L", "sections": [section]}, [symbols], [target], None

    target_rgb = image.convert("RGB")
    pixels = list(target_rgb.getdata())
    alpha_values = list(image.getchannel("A").getdata()) if "A" in image.getbands() else None
    target = target_rgb.copy()
    if alpha_values is not None:
        target.putalpha(image.getchannel("A"))

    if method == "rgb_channels":
        channels = [
            [pixel[channel] for pixel in pixels]
            for channel in range(3)
        ]
        sections = [
            {"name": name, "symbol_count": len(values), "alphabet_size": 256}
            for name, values in zip(("R", "G", "B"), channels)
        ]
        extras = [{"name": "alpha", "kind": "raw", "symbol_count": len(alpha_values)}] if alpha_values is not None else []
        return {"mode": target.mode, "sections": sections, "raw_sections": extras}, channels, [target], {"raw_values": [alpha_values] if alpha_values is not None else []}

    if method == "rgb_pixels":
        palette = sorted(set(pixels))
        color_to_index = {color: index for index, color in enumerate(palette)}
        symbols = [color_to_index[pixel] for pixel in pixels]
        section = {
            "name": "rgb_palette_index",
            "symbol_count": len(symbols),
            "alphabet_size": len(palette),
        }
        palette_bytes = bytes(component for color in palette for component in color)
        return (
            {"mode": target.mode, "sections": [section], "palette_count": len(palette),
             "raw_sections": [{"name": "alpha", "kind": "raw", "symbol_count": len(alpha_values)}] if alpha_values is not None else []},
            [symbols],
            [target],
            {"distinct_colors": len(palette), "palette_payload": palette_bytes,
             "raw_values": [alpha_values] if alpha_values is not None else []},
        )

    raise ValueError(f"Unknown method: {method}")


def compress_one(image_path, method, output_root, export_bits=False, export_csv=False):
    image_path = Path(image_path)
    with Image.open(image_path) as opened:
        source = opened.copy()

    metadata_extra, symbol_sections, targets, method_extra = prepare_method(source, method)
    target = targets[0]
    width, height = target.size
    method_dir = Path(output_root) / image_path.stem / method
    method_dir.mkdir(parents=True, exist_ok=True)

    digitized_path = method_dir / "digitized.png"
    target.save(digitized_path)
    pixel_dump_path = method_dir / "pixels.csv" if export_csv else None
    if export_csv:
        write_pixel_dump(target, pixel_dump_path)

    payloads = []
    section_metadata = []
    bit_dump_parts = []

    for section_info, symbols in zip(metadata_extra["sections"], symbol_sections):
        payload, lengths, bit_length, pure_bits = encode_symbols(
            symbols, section_info["alphabet_size"], export_bits=export_bits
        )
        payloads.append(payload)
        section = dict(section_info)
        section.update({
            "code_lengths": lengths,
            "bit_length": bit_length,
            "payload_bytes": len(payload),
        })
        section_metadata.append(section)
        if export_bits:
            bit_dump_parts.append(pure_bits)

    palette_payload = (method_extra or {}).get("palette_payload")
    if palette_payload is not None:
        payloads.append(palette_payload)
    raw_payloads = [bytes(values) for values in (method_extra or {}).get("raw_values", [])]
    payloads.extend(raw_payloads)

    container_metadata = {
        "version": 1,
        "method": method,
        "width": width,
        "height": height,
        "mode": metadata_extra["mode"],
        "sections": section_metadata,
        "raw_sections": metadata_extra.get("raw_sections", []),
    }
    if "palette_count" in metadata_extra:
        container_metadata["palette_count"] = metadata_extra["palette_count"]
    if method_extra:
        container_metadata.update({key: value for key, value in method_extra.items() if key not in ("raw_values", "palette_payload")})

    compressed_path = method_dir / f"{image_path.stem}_{method}.huff"
    write_container(compressed_path, container_metadata, payloads)

    bit_path = method_dir / "compressed_bits.txt" if export_bits else None
    if export_bits:
        # Bits are text (1 character = 1 byte), so this file can be ~8x
        # larger than the packed Huffman payload. It is intentionally opt-in.
        bit_path.write_text("\n".join(bit_dump_parts), encoding="ascii")

    # Run the decoder immediately and verify exact pixel equality against the
    # normalized target (the grayscale conversion or RGB conversion).
    reconstructed = decode_container(compressed_path)
    reconstructed_path = method_dir / "reconstructed.png"
    reconstructed.save(reconstructed_path)
    if reconstructed.mode != target.mode or reconstructed.size != target.size:
        raise AssertionError("Decoded image mode/dimensions do not match")
    if list(reconstructed.getdata()) != list(target.getdata()):
        raise AssertionError("Lossless verification failed: pixels differ")

    raw_pixel_bytes = width * height * ({"L": 1, "RGB": 3, "RGBA": 4}[target.mode])
    compressed_bytes = compressed_path.stat().st_size
    huffman_payload_bytes = sum(len(p) for p in payloads[:len(section_metadata)])
    auxiliary_payload_bytes = sum(len(p) for p in payloads[len(section_metadata):])
    payload_bytes = huffman_payload_bytes + auxiliary_payload_bytes
    saving = (1 - compressed_bytes / raw_pixel_bytes) * 100 if raw_pixel_bytes else 0

    print(f"\n--- {method} ---")
    print(f"Image: {image_path.name} | {width} x {height} | mode cible {target.mode}")
    print(f"Pixel brut (référence): {raw_pixel_bytes:,} octets")
    print(f"Payload Huffman       : {huffman_payload_bytes:,} octets")
    if auxiliary_payload_bytes:
        print(f"Payload auxiliaire    : {auxiliary_payload_bytes:,} octets")
    print(f"Payload total         : {payload_bytes:,} octets")
    print(f"Fichier .huff complet : {compressed_bytes:,} octets (en-tête inclus)")
    print(f"Gain vs pixels bruts  : {saving:.2f}%")
    print("Vérification sans perte: OK (pixels identiques)")
    if bit_path:
        print(f"Bits consultables     : {bit_path} (texte, potentiellement volumineux)")
    print(f"Image numérisée       : {digitized_path}")
    print(f"Image reconstruite    : {reconstructed_path}")
    if pixel_dump_path:
        print(f"Pixels (CSV)          : {pixel_dump_path}")
    return compressed_path


def main():
    parser = argparse.ArgumentParser(
        description="Compression d'image lossless avec trois variantes de Huffman."
    )
    parser.add_argument("image", type=Path, help="Image source")
    parser.add_argument(
        "--method", choices=(*METHODS, "all"), default="all",
        help="Méthode à exécuter (par défaut : all)",
    )
    parser.add_argument("--export-bits", action="store_true",
                        help="Créer compressed_bits.txt (très volumineux : 1 bit devient 1 caractère).")
    parser.add_argument("--export-csv", action="store_true",
                        help="Exporter les pixels en CSV (fichier texte potentiellement énorme).")
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parent / "output",
        help="Dossier de sortie",
    )
    args = parser.parse_args()

    if not args.image.exists():
        parser.error(f"Image introuvable : {args.image}")

    methods = METHODS if args.method == "all" else (args.method,)
    print("Compression lossless des données normalisées (L ou RGB).")
    for method in methods:
        compress_one(args.image, method, args.output, args.export_bits, args.export_csv)


if __name__ == "__main__":
    main()