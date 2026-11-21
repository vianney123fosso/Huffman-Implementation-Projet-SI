import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT.parent
sys.path.insert(0, str(PYTHON_ROOT))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from codec import encode_symbols, decode_symbols
from compress_image import compress_one
from decompress_image import decode_container


class HuffmanImageTests(unittest.TestCase):
    def test_symbol_round_trip(self):
        original = [0, 0, 3, 3, 3, 1, 2, 0, 3, 1, 1, 1]
        packed, lengths, bit_length, bit_text = encode_symbols(original, 4)
        decoded = decode_symbols(packed, lengths, len(original), bit_length)
        self.assertEqual(decoded, original)
        self.assertEqual(len(bit_text), bit_length)

    def test_single_symbol_round_trip(self):
        original = [5] * 17
        packed, lengths, bit_length, bit_text = encode_symbols(original, 6)
        decoded = decode_symbols(packed, lengths, len(original), bit_length)
        self.assertEqual(decoded, original)
        self.assertEqual(bit_length, 17)

    def test_all_three_methods_exact_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "alpha_test.png"
            image = Image.new("RGBA", (8, 6))
            pixels = []
            for y in range(6):
                for x in range(8):
                    pixels.append(((x * 29) % 256, (y * 41) % 256, ((x+y)*17) % 256, (x*31+y*7) % 256))
            image.putdata(pixels)
            image.save(source)

            for method in ("grayscale", "rgb_channels", "rgb_pixels"):
                compressed = compress_one(source, method, tmp / "out")
                decoded = decode_container(compressed)
                if method == "grayscale":
                    expected = image.convert("L")
                else:
                    expected = image
                self.assertEqual(decoded.mode, expected.mode)
                self.assertEqual(decoded.size, expected.size)
                self.assertEqual(list(decoded.getdata()), list(expected.getdata()))


if __name__ == "__main__":
    unittest.main()