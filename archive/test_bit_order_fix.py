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
    """Erstellt das EXAKTE komplexe Bild aus test_zero_offset.py"""
    try:
        # EXAKT das gleiche komplexe Bild das die Verschiebung verursacht
        img = Image.new('1', (320, 240), 1)  # Weiß
        draw = ImageDraw.Draw(img)
        
        # Rahmen
        draw.rectangle([0, 0, 319, 239], outline=0, width=2)
        
        # Text-ähnliche Elemente
        draw.text((10, 20), "TEST IMAGE", fill=0)
        draw.text((10, 50), "X-OFFSET = 0", fill=0)
        draw.text((10, 80), "NO WRAPPING", fill=0)
        
        # Visuelle Marker für Links/Rechts
        # Links-Marker
        draw.rectangle([5, 5, 25, 25], outline=0, width=3)
        draw.text((8, 8), "L", fill=0)
        
        # Rechts-Marker
        draw.rectangle([295, 5, 315, 25], outline=0, width=3)
        draw.text((298, 8), "R", fill=0)
        
        # Zentrale Struktur (wie die Gesichter)
        center_x, center_y = 160, 120
        
        # "Gesicht" simulation
        draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], outline=0, width=2)
        draw.ellipse([center_x-15, center_y-15, center_x-5, center_y-5], fill=0)  # Auge
        draw.ellipse([center_x+5, center_y-15, center_x+15, center_y-5], fill=0)   # Auge
        draw.arc([center_x-20, center_y, center_x+20, center_y+20], 0, 180, fill=0)  # Mund
        
        # Horizontale Linien zum Erkennen von Verschiebungen
        for y in [160, 180, 200, 220]:
            draw.line([30, y, 290, y], fill=0, width=1)
        
        logger.info(f"✅ Created COMPLEX test image: {img.width}x{img.height} (this should show shifting)")
        return img
        
    except Exception as e:
        logger.error(f"❌ Error creating complex test image: {e}")
        return None

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
        logger.info("📤 Test 1: Current bit order (MSB-first) - SHOULD HAVE SHIFTING")
        img = create_bit_test_pattern()
        
        print("Print current bit order test (the one with shifting)? (y/n): ", end="")
        if input().lower().startswith('y'):
            success1 = printer._print_image_direct(img)
            logger.info(f"Current bit order result: {'✅' if success1 else '❌'}")
            
            print("⚠️ This label should show SHIFTING in the lower parts!")
            input("Check the printed result (should have shifting), then press Enter to continue...")
        
        # Patch für LSB-first Test
        logger.info("🔧 Patching for LSB-first bit order test...")
        logger.info("📤 Test 2: LSB-first bit order - SHOULD BE PERFECT")
        
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
        print("Print LSB-first bit order test (should be PERFECT)? (y/n): ", end="")
        if input().lower().startswith('y'):
            success2 = printer._print_image_direct(img)
            logger.info(f"LSB-first bit order result: {'✅' if success2 else '❌'}")
            
            print("✅ This label should be PERFECTLY aligned (no shifting)!")
            input("Check the result - is it perfect? Press Enter to continue...")
        
        # Originale Methode wiederherstellen
        printer.image_to_printer_format = original_method
        
        print(f"\n🔍 CRITICAL ANALYSIS:")
        print(f"Compare the two printed labels:")
        print(f"")
        print(f"Label 1 (MSB-first): Should show SHIFTING in bottom part")  
        print(f"Label 2 (LSB-first):  Should be PERFECTLY aligned")
        print(f"")
        print(f"If Label 2 is perfect → WE FOUND THE BUG!")
        print(f"If both are wrong → Problem is deeper")
        print(f"")
        print(f"EXPECTED: Label 2 fixes the shifting problem completely!")
        
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
