#!/usr/bin/env python3
"""Analyse exploratoire d'une image pour préparer sa compression Huffman."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path

from PIL import Image


def calculate_entropy(frequencies: Counter[int], total_pixels: int) -> float:
    """Calcule l'entropie Shannon en bits/pixel de la distribution."""
    entropy = 0.0
    for count in frequencies.values():
        probability = count / total_pixels
        entropy -= probability * math.log2(probability)
    return entropy


def huffman_average_length(frequencies: Counter[int]) -> float:
    """Calcule la longueur moyenne théorique d'un code Huffman."""
    if not frequencies:
        return 0.0
    if len(frequencies) == 1:
        # En pratique, on réserve un code d'au moins un bit à un symbole unique.
        return 1.0

    import heapq

    heap = list(frequencies.values())
    heapq.heapify(heap)
    weighted_length_sum = 0

    while len(heap) > 1:
        first = heapq.heappop(heap)
        second = heapq.heappop(heap)
        combined = first + second
        weighted_length_sum += combined
        heapq.heappush(heap, combined)

    return weighted_length_sum / sum(frequencies.values())


def analyze_image(image_path: Path, top_n: int = 10) -> None:
    if not image_path.exists():
        raise FileNotFoundError(f"Image introuvable : {image_path}")

    with Image.open(image_path) as original:
        width, height = original.size
        grayscale = original.convert("L")
        pixels = list(grayscale.getdata())

    total_pixels = len(pixels)
    frequencies = Counter(pixels)
    entropy = calculate_entropy(frequencies, total_pixels)
    average_huffman_bits = huffman_average_length(frequencies)

    raw_bits = total_pixels * 8
    estimated_bits = total_pixels * average_huffman_bits
    theoretical_saving = (1 - estimated_bits / raw_bits) * 100 if raw_bits else 0.0

    print("=" * 60)
    print("ANALYSE D'IMAGE POUR HUFFMAN")
    print("=" * 60)
    print(f"Fichier              : {image_path}")
    print(f"Dimensions           : {width} x {height}")
    print(f"Nombre de pixels     : {total_pixels:,}")
    print("Mode analysé         : niveaux de gris (8 bits/pixel)")
    print(f"Valeurs distinctes   : {len(frequencies)} / 256")
    print(f"Entropie             : {entropy:.4f} bits/pixel")
    print(f"Moyenne Huffman      : {average_huffman_bits:.4f} bits/pixel")
    print(f"Taille brute théorique: {raw_bits:,} bits ({raw_bits / 8:,.0f} octets)")
    print(
        "Taille codée estimée : "
        f"{estimated_bits:,.0f} bits ({estimated_bits / 8:,.1f} octets)"
    )
    print(f"Gain théorique estimé: {theoretical_saving:.2f}%")
    print()
    print(f"TOP {min(top_n, len(frequencies))} VALEURS DE PIXELS")
    print("-" * 60)
    print("Valeur | Fréquence | Proportion")
    for value, count in frequencies.most_common(top_n):
        percentage = count / total_pixels * 100
        print(f"{value:>6} | {count:>9,} | {percentage:>8.3f}%")

    print()
    print("ÉCHANTILLON DE PIXELS (premiers 40)")
    print("-" * 60)
    print(pixels[:40])

    print()
    print("Note : l'estimation ne tient pas compte de l'en-tête, du dictionnaire")
    print("       ni du remplissage éventuel du dernier octet.")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse la distribution des pixels d'une image en niveaux de gris."
    )
    parser.add_argument("image", type=Path, help="Chemin vers l'image à analyser")
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Nombre de valeurs de pixels les plus fréquentes à afficher (10 par défaut)",
    )
    args = parser.parse_args()

    if args.top <= 0:
        parser.error("--top doit être strictement positif")

    analyze_image(args.image, args.top)


if __name__ == "__main__":
    main()
