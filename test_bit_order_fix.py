#!/usr/bin/env python3
"""
CRITICAL FIX: Bit-Mapping-Reihenfolge korrigieren
Das Problem: MSB vs LSB Bit-Reihenfolge verursacht Verschiebungen bei komplexen Bildern
"""

import sys
import time
import logging
from PIL import Image, ImageDraw

from printer_controller import EnhancedPhomemoM110
from config import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_bit_test_pattern():
    """Erstellt ein spezifisches Testmuster um Bit-Reihenfolge zu testen"""
    img = Image.new('1', (320, 240), 1)  # Weiß
    draw = ImageDraw.Draw(img)
    
    # Spezifisches Bit-Test-Muster
    # Vertikale Linien alle 8 Pixel (Byte-Grenzen)
    for x in range(0, 320, 8):
        draw.line([x, 0, x, 239], fill=0, width=1)
    
    # Text oben
    draw.text((10, 10), "BIT ORDER TEST", fill=0)
    
    # Horizontale Linien um Verschiebung zu zeigen
    for y in range(50, 200, 20):
        draw.line([10, y, 310, y], fill=0, width=1)
    
    return img

def test_different_bit_orders():
    """Testet beide Bit-Reihenfolgen"""
    logger.info("🧪 TESTING BIT ORDER VARIATIONS")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer")
                return False
        
        # Teste aktuell (MSB-first)
        logger.info("📤 Test 1: Current bit order (MSB-first)")
        img = create_bit_test_pattern()
        
        print("Print current bit order test? (y/n): ", end="")
        if input().lower().startswith('y'):
            success1 = printer._print_image_direct(img)
            logger.info(f"Current bit order result: {'✅' if success1 else '❌'}")
            
            input("Check the printed result, then press Enter to continue...")
        
        # Patch für LSB-first Test
        logger.info("🔧 Patching for LSB-first bit order test...")
        
        # Backup der originalen Methode
        original_method = printer.image_to_printer_format
        
        def lsb_first_image_to_printer_format(img):
            """Modifizierte Version mit LSB-First Bit-Reihenfolge"""
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
                        
                        # *** KRITISCHE ÄNDERUNG: LSB-First statt MSB-First ***
                        if pixel_value == 0:  # Schwarz
                            line_bytes[byte_index] |= (1 << bit_index)  # OHNE (7 - bit_index)!
                    
                    image_bytes.extend(line_bytes)
                
                return bytes(image_bytes)
                
            except Exception as e:
                logger.error(f"❌ LSB-first conversion error: {e}")
                return None
        
        # Ersetze temporär die Methode
        printer.image_to_printer_format = lsb_first_image_to_printer_format
        
        logger.info("📤 Test 2: LSB-first bit order")
        print("Print LSB-first bit order test? (y/n): ", end="")
        if input().lower().startswith('y'):
            success2 = printer._print_image_direct(img)
            logger.info(f"LSB-first bit order result: {'✅' if success2 else '❌'}")
        
        # Originale Methode wiederherstellen
        printer.image_to_printer_format = original_method
        
        print(f"\n🔍 ANALYSIS:")
        print(f"If LSB-first version is CORRECT (no shifting),")
        print(f"then we found the bug and need to fix the bit order!")
        print(f"If MSB-first is correct, the problem is elsewhere.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Bit order test error: {e}")
        return False

def main():
    logger.info("🔧 BIT ORDER DEBUGGING")
    logger.info("=" * 60)
    logger.info("Testing MSB-first vs LSB-first bit mapping")
    logger.info("This should reveal if bit order causes the shifting")
    logger.info("=" * 60)
    
    success = test_different_bit_orders()
    
    if success:
        logger.info("✅ Bit order test completed")
        print(f"\n📋 INSTRUCTIONS:")
        print(f"1. Compare both printed labels")
        print(f"2. Which one has NO shifting/alignment issues?")
        print(f"3. If LSB-first is perfect → We found the bug!")
        print(f"4. If both have issues → Problem is deeper")
    else:
        logger.error("❌ Bit order test failed")

if __name__ == "__main__":
    main()
