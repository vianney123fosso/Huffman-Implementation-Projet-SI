import sys
import subprocess
import math

from pathlib import Path
from collections import Counter

from huffmancoding import FrequencyTable, CanonicalCode


# --------------------------------------------------
# 1. CALCUL DE L'ENTROPIE
# --------------------------------------------------

def calculate_entropy(sequence):
    """
    Calcule l'entropie d'une séquence quelconque.
    Ici, elle sera utilisée sur la séquence de bits.
    """
    if len(sequence) == 0:
        return 0.0

    frequencies = Counter(sequence)
    total = len(sequence)

    entropy = 0.0

    for frequency in frequencies.values():
        probability = frequency / total
        entropy -= probability * math.log2(probability)

    return entropy


# --------------------------------------------------
# 2. RECONSTRUCTION DU CODE DE HUFFMAN
# --------------------------------------------------

def generate_huffman_bits(data):
    """
    Reconstruit le code de Huffman utilisé par le programme
    et génère la séquence binaire correspondant aux données.

    Aucun symbole EOF n'est ajouté à la séquence.
    """

    freqs = FrequencyTable([0] * 257)

    for byte in data:
        freqs.increment(byte)

    # L'EOF est nécessaire pour reconstruire le même arbre
    # que celui utilisé par le programme de compression.
    freqs.increment(256)

    tree = freqs.build_code_tree()

    canoncode = CanonicalCode(
        tree=tree,
        symbollimit=freqs.get_symbol_limit()
    )

    code = canoncode.to_code_tree()

    bits = []

    for byte in data:
        symbol_code = code.get_code(byte)

        for bit in symbol_code:
            bits.append(str(bit))

    return "".join(bits), code


# --------------------------------------------------
# 3. COMPRESSION ET ANALYSE
# --------------------------------------------------

def analyze_file(input_path):

    input_path = Path(input_path)

    if not input_path.exists():
        print("Fichier introuvable :", input_path)
        return

    # Lecture du fichier original
    data = input_path.read_bytes()

    # Nom du fichier compressé
    compressed_path = input_path.with_name(
        input_path.stem + "_compressed.huff"
    )

    # Lancement du programme de compression
    compressor = Path(__file__).parent / "huffman-compress.py"

    subprocess.run(
        [
            sys.executable,
            str(compressor),
            str(input_path),
            str(compressed_path)
        ],
        check=True
    )

    # --------------------------------------------------
    # Génération de la séquence binaire pure
    # --------------------------------------------------

    data_bits, code = generate_huffman_bits(data)

    # Sauvegarde de la séquence binaire
    bits_path = input_path.with_name(
        input_path.stem + "_bits.txt"
    )

    bits_path.write_text(data_bits)

    # --------------------------------------------------
    # Entropie de la séquence binaire
    # --------------------------------------------------

    bit_entropy = calculate_entropy(data_bits)

    # Fréquences des bits
    bit_counts = Counter(data_bits)

    total_bits = len(data_bits)

    p0 = bit_counts.get("0", 0) / total_bits if total_bits else 0
    p1 = bit_counts.get("1", 0) / total_bits if total_bits else 0

    # --------------------------------------------------
    # Entropie de la source originale
    # --------------------------------------------------

    source_entropy = calculate_entropy(data)

    # --------------------------------------------------
    # Longueur moyenne des codes Huffman
    # --------------------------------------------------

    if len(data) > 0:
        average_length = len(data_bits) / len(data)
    else:
        average_length = 0

    # --------------------------------------------------
    # Efficacité du code de Huffman
    # --------------------------------------------------

    if average_length > 0:
        efficiency = (source_entropy / average_length) * 100
    else:
        efficiency = 0

    # --------------------------------------------------
    # Taille réelle du fichier compressé
    # --------------------------------------------------

    original_size = len(data)
    compressed_size = compressed_path.stat().st_size

    # --------------------------------------------------
    # AFFICHAGE DES RÉSULTATS
    # --------------------------------------------------

    print("\n" + "=" * 55)
    print("              ANALYSE DE COMPRESSION")
    print("=" * 55)

    print("\nFICHIER ORIGINAL")
    print("-" * 55)
    print(f"Taille originale       : {original_size} octets")
    print(f"Nombre de symboles     : {len(data)}")

    print("\nSÉQUENCE BINAIRE HUFFMAN")
    print("-" * 55)
    print(f"Nombre de bits         : {total_bits}")
    print(f"Nombre de 0            : {bit_counts.get('0', 0)}")
    print(f"Nombre de 1            : {bit_counts.get('1', 0)}")
    print(f"Proportion de 0        : {p0:.4f}")
    print(f"Proportion de 1        : {p1:.4f}")
    print(f"Entropie de la séquence: {bit_entropy:.6f} bits")

    print("\nEFFICACITÉ DU CODE HUFFMAN")
    print("-" * 55)
    print(f"Entropie de la source  : {source_entropy:.6f} bits/symbole")
    print(f"Longueur moyenne       : {average_length:.6f} bits/symbole")
    print(f"Efficacité             : {efficiency:.2f} %")

    print("\nCOMPRESSION")
    print("-" * 55)
    print(f"Taille compressée      : {compressed_size} octets")
    print(f"Taille compressée      : {compressed_size * 8} bits")

    if original_size > 0:
        ratio = compressed_size / original_size
        gain = (1 - ratio) * 100

        print(f"Ratio de compression  : {ratio:.4f}")
        print(f"Gain de taille         : {gain:.2f} %")

    print("\nFICHIERS GÉNÉRÉS")
    print("-" * 55)
    print(f"Fichier compressé      : {compressed_path.name}")
    print(f"Séquence binaire       : {bits_path.name}")

    print("=" * 55)


# --------------------------------------------------
# 4. POINT D'ENTRÉE
# --------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Utilisation : python test.py nom_du_fichier")
    else:
        analyze_file(sys.argv[1])