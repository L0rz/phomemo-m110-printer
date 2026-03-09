#!/usr/bin/env python3
"""
FINE-TUNING BIT-MANIPULATION
Basierend auf Variante 5 (beste Ergebnisse) - weitere Optimierungen
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
    """Das exakte komplexe Bild"""
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

def test_fine_tuned_variants():
    """Testet Feinabstimmungen basierend auf Variante 5"""
    logger.info("🔧 FINE-TUNING BIT-MANIPULATION")
    
    try:
        printer = EnhancedPhomemoM110(PRINTER_MAC)
        
        if not printer.is_connected():
            if not printer.connect_bluetooth():
                logger.error("❌ Cannot connect to printer")
                return False
        
        img = create_complex_test_image()
        original_method = printer.image_to_printer_format
        
        # Variante 5 war: Shifted MSB (-1) = beste Ergebnisse
        # Lass uns das verfeinern
        
        fine_tuned_variants = [
            ("Variant 5 Original", lambda bit_index: (1 << max(0, (7 - bit_index - 1)))),
            ("Variant 5 + Mask", lambda bit_index: (1 << max(0, (7 - bit_index - 1))) & 0xFF),
            ("Variant 5 + Boundary Fix", None),  # Spezielle Behandlung
            ("MSB -1 with Clamp", lambda bit_index: (1 << max(0, min(7, (7 - bit_index - 1))))),
            ("MSB -1 + Wrap", lambda bit_index: (1 << ((7 - bit_index - 1) % 8))),
            ("Perfect Mix", None),  # Spezielle Mischung
        ]
        
        for i, (variant_name, shift_func) in enumerate(fine_tuned_variants, 1):
            logger.info(f"\n📤 Fine-Tune Test {i}: {variant_name}")
            
            if shift_func is None:
                # Spezielle Varianten
                if "Boundary Fix" in variant_name:
                    def boundary_fix_variant(printer, img):
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
                                        # Variante 5 mit Boundary-Protection
                                        shift = max(0, (7 - bit_index - 1))
                                        if shift >= 0 and shift <= 7:  # Zusätzliche Boundary-Checks
                                            line_bytes[byte_index] |= (1 << shift)
                                
                                # Extra: Prüfe auf Byte-Overflow
                                for j in range(len(line_bytes)):
                                    line_bytes[j] = line_bytes[j] & 0xFF
                                
                                image_bytes.extend(line_bytes)
                            
                            return bytes(image_bytes)
                            
                        except Exception as e:
                            logger.error(f"❌ Boundary fix error: {e}")
                            return None
                    
                    printer.image_to_printer_format = lambda img: boundary_fix_variant(printer, img)
                
                elif "Perfect Mix" in variant_name:
                    def perfect_mix_variant(printer, img):
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
                                        # Mischung: Verwende verschiedene Shifts je nach Position
                                        if y < height // 2:  # Obere Hälfte
                                            shift = 7 - bit_index  # Normale MSB
                                        else:  # Untere Hälfte 
                                            shift = max(0, (7 - bit_index - 1))  # Variante 5
                                        
                                        line_bytes[byte_index] |= (1 << shift)
                                
                                image_bytes.extend(line_bytes)
                            
                            return bytes(image_bytes)
                            
                        except Exception as e:
                            logger.error(f"❌ Perfect mix error: {e}")
                            return None
                    
                    printer.image_to_printer_format = lambda img: perfect_mix_variant(printer, img)
            else:
                # Standard Varianten
                def create_variant(shift_func):
                    def variant_converter(printer, img):
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
                                        line_bytes[byte_index] |= shift_func(bit_index)
                                
                                image_bytes.extend(line_bytes)
                            
                            return bytes(image_bytes)
                            
                        except Exception as e:
                            logger.error(f"❌ Variant converter error: {e}")
                            return None
                    
                    return variant_converter
                
                printer.image_to_printer_format = lambda img: create_variant(shift_func)(printer, img)
            
            print(f"Print Fine-Tune Test {i} ({variant_name})? (y/n/s): ", end="")
            response = input()
            
            if response.lower().startswith('s'):
                break
            elif response.lower().startswith('y'):
                success = printer._print_image_direct(img)
                if success:
                    logger.info(f"✅ {variant_name} printed")
                    print(f"📝 Check: Is this PERFECT (no shifting + correct image)?")
                    input(f"   Press Enter when ready...")
                else:
                    logger.error(f"❌ {variant_name} failed")
            else:
                logger.info(f"⏭️ Skipping {variant_name}")
        
        # Original wiederherstellen
        printer.image_to_printer_format = original_method
        
        print(f"\n🎯 FINAL QUESTION:")
        print(f"Which variant was PERFECT?")
        print(f"(No shifting + correct image appearance)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fine-tuning test error: {e}")
        return False

def main():
    logger.info("🔧 FINE-TUNING BIT-MANIPULATION")
    logger.info("=" * 60)
    logger.info("Based on Variant 5 results - optimizing further")
    logger.info("=" * 60)
    
    success = test_fine_tuned_variants()
    
    if success:
        logger.info("✅ Fine-tuning completed")
        print(f"\nIf we found the perfect variant, we can implement it permanently!")
    else:
        logger.error("❌ Fine-tuning failed")

if __name__ == "__main__":
    main()
