#!/usr/bin/env python3
"""
BIT-SHIFT VARIATIONS TEST
Testet verschiedene Bit-Verschiebungs-Kombinationen um das perfekte Format zu finden
"""

import sys
import time
import logging
from PIL import Image, ImageDraw

from printer_controller import EnhancedPhomemoM110
from config import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_complex_test_image():
    """Das exakte komplexe Bild das die Verschiebung verursacht"""
    img = Image.new('1', (320, 240), 1)
    draw = ImageDraw.Draw(img)
    
    # Rahmen
    draw.rectangle([0, 0, 319, 239], outline=0, width=2)
    
    # Text
    draw.text((10, 20), "TEST IMAGE", fill=0)
    draw.text((10, 50), "X-OFFSET = 0", fill=0)
    draw.text((10, 80), "NO WRAPPING", fill=0)
    
    # Marker
    draw.rectangle([5, 5, 25, 25], outline=0, width=3)
    draw.text((8, 8), "L", fill=0)
    draw.rectangle([295, 5, 315, 25], outline=0, width=3)
    draw.text((298, 8), "R", fill=0)
    
    # Gesicht
    center_x, center_y = 160, 120
    draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], outline=0, width=2)
    draw.ellipse([center_x-15, center_y-15, center_x-5, center_y-5], fill=0)
    draw.ellipse([center_x+5, center_y-15, center_x+15, center_y-5], fill=0)
    
    # Horizontale Linien
    for y in [160, 180, 200, 220]:
        draw.line([30, y, 290, y], fill=0, width=1)
    
    return img

def create_bit_shift_variant(variant_name, shift_method):
    """Erstellt eine Bit-Shift-Variante"""
    def custom_image_to_printer_format(printer, img):
        try:
            if img.mode != '1':
                img = img.convert('1')
            
            width, height = img.size
            
            if width < printer.width_pixels:
                expanded_img = Image.new('1', (printer.width_pixels, height), 1)
                expanded_img.paste(img, (0, 0))
                img = expanded_img
                width = printer.width_pixels
            elif width > printer.width_pixels:
                img = img.crop((0, 0, printer.width_pixels, height))
                width = printer.width_pixels
            
            pixels = list(img.getdata())
            image_bytes = []
            
            for y in range(height):
                line_bytes = [0] * printer.bytes_per_line
                
                for pixel_x in range(printer.width_pixels):
                    pixel_idx = y * width + pixel_x
                    
                    if pixel_idx < len(pixels):
                        pixel_value = pixels[pixel_idx]
                    else:
                        pixel_value = 1
                    
                    byte_index = pixel_x // 8
                    bit_index = pixel_x % 8
                    
                    if pixel_value == 0:  # Schwarz
                        # HIER DIE VERSCHIEDENEN VARIANTEN:
                        line_bytes[byte_index] |= shift_method(bit_index)
                
                image_bytes.extend(line_bytes)
            
            return bytes(image_bytes)
            
        except Exception as e:
            logger.error(f"❌ {variant_name} conversion error: {e}")
            return None
    
    return custom_image_to_printer_format

def test_bit_shift_variations():
    """Testet verschiedene Bit-Shift-Varianten"""
    logger.info("🧪 TESTING MULTIPLE BIT-SHIFT VARIATIONS")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer")
                return False
        
        img = create_complex_test_image()
        original_method = printer.image_to_printer_format
        
        # Test-Varianten definieren
        variants = [
            ("MSB-First (Original)", lambda bit_index: (1 << (7 - bit_index))),
            ("LSB-First", lambda bit_index: (1 << bit_index)),
            ("MSB with Byte-Swap", lambda bit_index: (1 << (7 - bit_index))),  # Wir werden byte-level swappen
            ("LSB + Bit-Invert", lambda bit_index: (1 << (7 - (7 - bit_index)))),  # Doppelt umgekehrt
            ("Shifted MSB (-1)", lambda bit_index: (1 << max(0, (7 - bit_index - 1)))),
            ("Shifted MSB (+1)", lambda bit_index: (1 << min(7, (7 - bit_index + 1)))),
        ]
        
        print(f"\n🖨️ BIT-SHIFT VARIATION TESTS")
        print(f"We'll test {len(variants)} different bit arrangements")
        print(f"Look for the one that has:")
        print(f"  ✅ NO shifting/alignment issues")
        print(f"  ✅ CORRECT image appearance")
        print(f"")
        
        for i, (variant_name, shift_func) in enumerate(variants, 1):
            logger.info(f"\n📤 Test {i}: {variant_name}")
            
            # Spezielle Behandlung für Byte-Swap Variante
            if "Byte-Swap" in variant_name:
                def byte_swap_variant(printer, img):
                    # Normale MSB-First Konvertierung
                    data = create_bit_shift_variant("temp", lambda bit_index: (1 << (7 - bit_index)))(printer, img)
                    if not data:
                        return None
                    
                    # Bytes innerhalb jeder Zeile umkehren
                    swapped_data = []
                    bytes_per_line = 48
                    
                    for line_start in range(0, len(data), bytes_per_line):
                        line = data[line_start:line_start + bytes_per_line]
                        # Bytes in der Zeile umkehren
                        reversed_line = line[::-1]
                        swapped_data.extend(reversed_line)
                    
                    return bytes(swapped_data)
                
                printer.image_to_printer_format = lambda img: byte_swap_variant(printer, img)
            else:
                printer.image_to_printer_format = lambda img: create_bit_shift_variant(variant_name, shift_func)(printer, img)
            
            print(f"Print Test {i} ({variant_name})? (y/n/s to skip remaining): ", end="")
            response = input()
            
            if response.lower().startswith('s'):
                logger.info("⏭️ Skipping remaining tests")
                break
            elif response.lower().startswith('y'):
                success = printer._print_image_direct(img)
                if success:
                    logger.info(f"✅ {variant_name} printed successfully")
                    print(f"📝 Check this label for:")
                    print(f"   - Correct alignment (no shifting)")
                    print(f"   - Correct image appearance")
                    input(f"   Press Enter when ready for next test...")
                else:
                    logger.error(f"❌ {variant_name} failed to print")
            else:
                logger.info(f"⏭️ Skipping {variant_name}")
        
        # Originale Methode wiederherstellen
        printer.image_to_printer_format = original_method
        
        print(f"\n📋 ANALYSIS INSTRUCTIONS:")
        print(f"Compare all printed labels:")
        print(f"1. Which one has PERFECT alignment (no shifting)?")
        print(f"2. Which one has CORRECT image appearance?")
        print(f"3. The ideal variant should have BOTH!")
        print(f"")
        print(f"If none are perfect, we may need to test Print Master's protocol...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Bit shift variations test error: {e}")
        return False

def main():
    logger.info("🔧 BIT-SHIFT VARIATIONS TEST")
    logger.info("=" * 60)
    logger.info("Testing multiple bit arrangements to find the perfect one")
    logger.info("=" * 60)
    
    success = test_bit_shift_variations()
    
    if success:
        logger.info("✅ Bit-shift variations test completed")
    else:
        logger.error("❌ Test failed")

if __name__ == "__main__":
    main()
