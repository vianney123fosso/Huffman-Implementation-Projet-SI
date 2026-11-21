Huffman - Compression d'images (sans perte)
Cette partie du projet compare trois stratégies basées sur le Huffman statique déjà

implémenté dans ../huffmancoding.py (le module commun se trouve dans le dossier

python/ du projet).
Réutilisation du code Huffman existant
Le module src/codec.py ne reconstruit pas l'algorithme Huffman. Il réutilise :
·	FrequencyTable pour compter et construire l'arbre ;
·	CanonicalCode pour reconstruire les codes canoniques ;
·	HuffmanEncoder et HuffmanDecoder pour encoder/décoder les symboles ;
·	BitOutputStream et BitInputStream pour écrire/lire les bits dans les octets.
La partie image s'occupe seulement de convertir l'image en séquences de symboles,

puis de conserver les informations nécessaires à la reconstruction.
Trois méthodes
1.	grayscale : conversion en niveaux de gris, puis Huffman sur les valeurs 0..255.

La compression/décompression des données en niveaux de gris est sans perte; la

conversion depuis une image couleur n'est pas réversible.
2.	rgb_channels : Huffman indépendant sur R, G et B. Si l'image source possède

un canal alpha, celui-ci est conservé sans compression comme section brute auxiliaire.
3.	rgb_pixels : chaque couleur RGB distincte devient un symbole de palette

(indice entier), puis Huffman compresse la séquence des indices. La palette est stockée

dans l'en-tête. L'alpha éventuel est conservé en section brute.
Installation
Depuis le dossier python/image_compression :
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Compression
Lancer les trois méthodes :
python3 compress_image.py images/mon_image.png

Lancer une seule méthode :
python3 compress_image.py images/mon_image.png --method grayscale
python3 compress_image.py images/mon_image.png --method rgb_channels
python3 compress_image.py images/mon_image.png --method rgb_pixels

Décompression indépendante
python3 decompress_image.py output/mon_image/rgb_channels/mon_image_rgb_channels.huff

Option pour choisir le fichier de sortie :
python3 decompress_image.py mon_fichier.huff --output image_reconstruite.png

Résultats
Les résultats sont organisés par image et par méthode :
output/
└── mon_image/
    ├── grayscale/
    │   ├── mon_image_grayscale.huff
    │   ├── compressed_bits.txt
    │   ├── gray_bits.txt
    │   ├── digitized.png
    │   ├── reconstructed.png
    │   └── pixels.csv
    ├── rgb_channels/
    │   ├── mon_image_rgb_channels.huff
    │   ├── compressed_bits.txt
    │   ├── R_bits.txt
    │   ├── G_bits.txt
    │   ├── B_bits.txt
    │   ├── digitized.png
    │   ├── reconstructed.png
    │   └── pixels.csv
    └── rgb_pixels/
        └── ...

·	compressed_bits.txt : bits Huffman exacts (hors padding), avec noms de sections.
·	*_bits.txt : séquence pure de bits d'une section, sans commentaire ni padding.
·	digitized.png : raster qui est effectivement encodé par cette méthode.
·	reconstructed.png : résultat de la décompression.
·	pixels.csv : valeurs numériques des pixels.
·	.huff : conteneur compressé avec métadonnées et payload binaire.
Le programme décompresse immédiatement chaque résultat et compare les pixels avec la

cible de la méthode. Il affiche Vérification sans perte: OK si les données

reconstruites sont exactement identiques.
Comparaison des tailles
Le rapport distingue :
·	la taille brute des pixels de la cible (1 octet/pixel pour L, 3 pour RGB,

4 pour RGBA si alpha est conservé) ;
·	le payload Huffman et éventuelles sections brutes ;
·	la taille du fichier .huff complet, en-tête inclus.
Pour grayscale, la référence est l'image convertie en L. Elle ne permet pas de

reconstruire l'image couleur initiale. Les deux méthodes RGB, elles, reconstruisent

exactement les pixels RGB; l'alpha est également préservé si présent.
Format de conteneur maison
Le fichier .huff contient :
·	signature HFIM et taille de l'en-tête JSON ;
·	méthode, dimensions, mode ;
·	longueur des codes Huffman et nombre de symboles par section ;
·	palette RGB (uniquement pour rgb_pixels) ;
·	longueurs de sections, puis payloads packed en octets.
Les sections Huffman n'utilisent pas de symbole EOF. Le nombre de symboles et la

longueur exacte des bits sont enregistrés dans l'en-tête; les zéros ajoutés pour

compléter le dernier octet sont donc exclus de *_bits.txt.
Tests
python3 -m unittest discover -s tests -v

Export des fichiers de diagnostic (optionnel)
Par défaut, le programme ne crée plus compressed_bits.txt ni pixels.csv, car ce sont des représentations textuelles qui peuvent être beaucoup plus volumineuses que les données binaires.
·	--export-bits crée le fichier texte contenant les séquences de bits Huffman exactes (sans étiquettes ni padding). Il peut prendre environ 8 fois la taille du payload binaire.
·	--export-csv crée le dump CSV des pixels, qui peut lui aussi être énorme.
Exemple : python3 compress_image.py image.png --method rgb_channels --export-bits
Les en-têtes des fichiers .huff sont maintenant compressés avec zlib. Le décompresseur reconnaît aussi les anciens fichiers à en-tête JSON non compressé.
