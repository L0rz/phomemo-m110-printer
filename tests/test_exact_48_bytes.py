import unittest
from PIL import Image
from printer_controller import EnhancedPhomemoM110

class TestExact48BytesPerLine(unittest.TestCase):
    def setUp(self):
        self.printer = EnhancedPhomemoM110('00:00:00:00:00:00')
        # Ensure bytes_per_line is 48
        self.assertEqual(self.printer.bytes_per_line, 48)

    def test_white_image_100px_height(self):
        img = Image.new('1', (384, 100), 1)  # white
        data = self.printer.image_to_printer_format(img)
        self.assertIsNotNone(data)
        # Each line must be 48 bytes
        self.assertEqual(len(data), 100 * 48)

    def test_black_image_1px_height(self):
        img = Image.new('1', (384, 1), 0)  # black
        data = self.printer.image_to_printer_format(img)
        self.assertIsNotNone(data)
        self.assertEqual(len(data), 1 * 48)

if __name__ == '__main__':
    unittest.main()
