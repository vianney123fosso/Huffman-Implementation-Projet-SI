import sys
import subprocess
from pathlib import Path


def decompress_file(compressed_path):

    compressed_path = Path(compressed_path)

    # Vérifier que le fichier existe
    if not compressed_path.exists():
        print("Erreur : fichier compressé introuvable.")
        return

    # Vérifier l'extension
    if compressed_path.suffix != ".huff":
        print("Attention : le fichier sélectionné n'a pas l'extension .huff")

    # Définir le nom du fichier décompressé
    output_path = compressed_path.with_name(
        compressed_path.stem + "_decompressed.txt"
    )

    # Localiser le programme de décompression
    decompressor = Path(__file__).parent / "huffman-decompress.py"

    if not decompressor.exists():
        print("Erreur : huffman-decompress.py introuvable.")
        return

    print("\nDécompression en cours...")

    try:
        # Lancer le programme de décompression
        subprocess.run(
            [
                sys.executable,
                str(decompressor),
                str(compressed_path),
                str(output_path)
            ],
            check=True
        )

        # Récupérer les tailles des fichiers
        compressed_size = compressed_path.stat().st_size
        decompressed_size = output_path.stat().st_size

        print("\n" + "=" * 45)
        print("          DÉCOMPRESSION TERMINÉE")
        print("=" * 45)

        print(f"\nFichier compressé   : {compressed_path.name}")
        print(f"Fichier décompressé : {output_path.name}")

        print(f"\nTaille compressée   : {compressed_size} octets")
        print(f"Taille décompressée : {decompressed_size} octets")

        print("\nFichier créé avec succès !")
        print("=" * 45)

    except subprocess.CalledProcessError:
        print("\nErreur pendant la décompression.")

    except Exception as error:
        print(f"\nUne erreur est survenue : {error}")


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Utilisation : python test-decompression.py fichier.huff")

    else:
        decompress_file(sys.argv[1])