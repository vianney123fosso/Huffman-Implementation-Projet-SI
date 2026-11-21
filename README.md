# Codage de Huffman : implémentation, analyse et compression d'images

Ce dépôt est un fork de [Reference Huffman coding](https://github.com/nayuki/Reference-Huffman-coding) de Project Nayuki. Il constitue la partie pratique d'un exposé sur le codage de Huffman.

Le travail ajouté à l'original porte sur la version Python :

- des scripts qui mesurent l'efficacité du code de Huffman sur un fichier (entropie, longueur moyenne, taux de compression) ;
- un module de compression d'images sans perte qui réutilise les classes de Nayuki ;
- des tests automatisés.

## Origine du code et licence

La logique algorithmique principale n'est pas de moi. Elle provient du projet de référence de Project Nayuki :

- page du projet : <https://www.nayuki.io/page/reference-huffman-coding>
- dépôt d'origine : <https://github.com/nayuki/Reference-Huffman-coding>

Cela concerne en particulier `python/huffmancoding.py` (arbre de Huffman, code canonique, lecture et écriture de bits, encodeur et décodeur), les quatre scripts de compression et de décompression de `python/`, ainsi que les versions Java et C++ qui n'ont pas été modifiées. L'historique des commits de Nayuki est conservé.

Le projet est distribué sous licence MIT. Le texte complet se trouve dans [`LICENSE`](LICENSE) et le README d'origine est conservé dans [`README-upstream.markdown`](README-upstream.markdown). Mes ajouts sont placés sous la même licence.

### Modification apportée à un fichier d'origine

Dans `python/huffmancoding.py`, la méthode `CodeTree.__str__` ajoutait « 0 » au préfixe pour les deux branches. Elle ajoute maintenant « 1 » pour la branche droite, ce qui affiche les bons codes. Un test vérifie cette correction.

## Organisation du dépôt

```
.
├── README.md                      ce fichier
├── README-upstream.markdown       README d'origine (Project Nayuki)
├── LICENSE                        licence MIT
├── java/                          version Java d'origine (non modifiée)
├── cpp/                           version C++ d'origine (non modifiée)
└── python/
    ├── huffmancoding.py           classes de base (Nayuki, une correction)
    ├── huffman-compress.py        compression, Huffman statique (Nayuki)
    ├── huffman-decompress.py      décompression, Huffman statique (Nayuki)
    ├── adaptive-huffman-compress.py     compression, Huffman adaptatif (Nayuki)
    ├── adaptive-huffman-decompress.py   décompression, Huffman adaptatif (Nayuki)
    ├── test-compression.py        analyse d'un fichier compressé (ajout)
    ├── test-decompression.py      décompression et vérification des tailles (ajout)
    ├── test-code.py               affichage d'un arbre de Huffman (ajout)
    ├── samples/                   fichiers texte d'exemple
    ├── tests/                     tests unitaires
    └── image_compression/         compression d'images sans perte (ajout)
```

Les fichiers marqués « Nayuki » sont ceux du projet d'origine. Les fichiers marqués « ajout » sont les miens.

## Prérequis

- Python 3 pour les scripts de `python/` (bibliothèque standard uniquement ; testé avec Python 3.13) ;
- Pillow pour la compression d'images (voir [`python/image_compression/README.md`](python/image_compression/README.md)).

Toutes les commandes ci-dessous se lancent depuis le dossier `python/` :

```bash
cd python
```

## Utilisation

### Compresser et décompresser un fichier

```bash
python3 huffman-compress.py samples/inp.txt inp.huff
python3 huffman-decompress.py inp.huff inp_restaure.txt
```

La variante adaptative s'utilise de la même façon avec `adaptive-huffman-compress.py` et `adaptive-huffman-decompress.py`.

Le fichier compressé commence par 257 longueurs de code, à raison d'un octet chacune (une par valeur d'octet, plus une pour le symbole de fin de fichier), suivies des données codées. Sur un très petit fichier, cet en-tête de 257 octets rend le fichier compressé plus grand que l'original.

### Analyser la compression d'un fichier

```bash
python3 test-compression.py samples/inp.txt
```

Le script compresse le fichier, puis affiche l'entropie de la source, la longueur moyenne des codes, l'efficacité du code, les proportions de 0 et de 1, et le gain de taille. Il écrit à côté du fichier source `inp_compressed.huff` et `inp_bits.txt` (la séquence de bits en texte).

Résultat obtenu sur `samples/inp.txt` (21 812 octets) :

| Mesure | Valeur |
|---|---|
| Entropie de la source | 4,823 bits/symbole |
| Longueur moyenne du code | 4,856 bits/symbole |
| Efficacité du code | 99,32 % |
| Taille du fichier compressé | 13 499 octets |
| Gain de taille | 38,11 % |

### Décompresser et vérifier

```bash
python3 test-decompression.py samples/inp_compressed.huff
```

Le fichier restauré est écrit sous le nom `inp_compressed_decompressed.txt`, avec l'affichage des tailles avant et après.

### Afficher un arbre de Huffman

```bash
python3 test-code.py
```

Le script construit l'arbre pour les fréquences 5, 4, 3, 2, 1 et affiche le code de chaque symbole.

### Compresser une image

Voir [`python/image_compression/README.md`](python/image_compression/README.md).

## Tests

Depuis `python/` :

```bash
python3 -m unittest discover -s tests -v
```

Depuis `python/image_compression/` :

```bash
python3 -m unittest discover -s tests -v
```

Les tests vérifient que la décompression redonne exactement le fichier d'origine (Huffman statique et adaptatif, fichier vide compris), que l'affichage de l'arbre est correct, et que les trois méthodes de compression d'images sont sans perte.

## Java et C++

Les versions Java et C++ sont celles du projet d'origine, sans modification. Voir la page de Nayuki pour leur description.

## Références

- Project Nayuki, [Reference Huffman coding](https://www.nayuki.io/page/reference-huffman-coding)
- D. A. Huffman, *A Method for the Construction of Minimum-Redundancy Codes*, Proceedings of the IRE, 1952
